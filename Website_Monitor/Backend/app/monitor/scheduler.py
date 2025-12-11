# app/monitor/scheduler.py

from datetime import datetime
from urllib.parse import urlparse

from app.database import db
from app.monitor.checker import check_single_website
from app.notify.emailer import send_down_alert, send_ssl_expiry_alert
from app.utils.ssl_utils import get_ssl_expiry_date


# =====================================================================
# 🔵 1) NORMAL UPTIME / STATUS CHECK  (+ interval support)
# =====================================================================

async def check_all_websites():
    print("🛰  Running scheduled check_all_websites()...")

    cursor = db.websites.find({})
    websites = await cursor.to_list(length=200)

    if not websites:
        print("ℹ️  No websites found in DB.")
        return

    now = datetime.utcnow()

    for doc in websites:
        url = doc.get("url")
        name = doc.get("name", url)
        email = doc.get("email")

        # 🔕 is_active = False na skip
        is_active = doc.get("is_active", True)
        if not is_active:
            print(f"⏸  Skipping {name} (is_active = False)")
            continue

        if not url:
            print("⚠️  Skipping document (no URL):", doc.get("_id"))
            continue

        # ======================================
        # ⏱  PER-WEBSITE CHECK INTERVAL LOGIC
        # ======================================
        check_interval = doc.get("check_interval", 60)  # seconds
        try:
            check_interval = int(check_interval)
            if check_interval <= 0:
                check_interval = 60
        except Exception:
            check_interval = 60

        last_checked = doc.get("last_checked")
        if last_checked:
            diff_seconds = (now - last_checked).total_seconds()
            if diff_seconds < check_interval:
                remaining = int(check_interval - diff_seconds)
                print(
                    f"⏳ Skipping {name} "
                    f"(next check in ~{remaining}s, interval={check_interval}s)"
                )
                continue

        # ==============================
        # 🟢 TIME TO CHECK WEBSITE
        # ==============================
        result = await check_single_website(doc)

        is_up = result["is_up"]
        status_code = result["status_code"]
        response_time = result["response_time"]
        error = result["error"]

        new_status = "UP" if is_up else "DOWN"
        old_status = doc.get("last_status")  # None / "UP" / "DOWN"

        now = datetime.utcnow()

        # ==============================
        # 🔢 UPTIME CALCULATION
        # ==============================
        old_total = doc.get("total_checks", 0)
        old_up = doc.get("up_checks", 0)

        new_total = old_total + 1
        new_up = old_up + (1 if is_up else 0)

        uptime = (new_up / new_total) * 100 if new_total > 0 else 0.0

        # ==============================
        # 💾 DB UPDATE (websites)
        # ==============================
        await db.websites.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "last_status": new_status,
                    "last_checked": now,
                    "last_response_time": response_time,
                    "last_status_code": status_code,
                    "last_error": error,
                    "total_checks": new_total,
                    "up_checks": new_up,
                    "uptime": uptime,
                }
            },
        )

        print(
            f"✅ Updated {name}: status={new_status}, "
            f"code={status_code}, rt={response_time}, error={error}, "
            f"uptime={uptime:.2f}% (up={new_up}/{new_total})"
        )

        # ==============================
        # 📝 CHECK LOG INSERT (history)
        # ==============================
        try:
            await db.checks.insert_one(
                {
                    "website_id": doc["_id"],           # websites._id (ObjectId)
                    "user_id": doc.get("user_id"),      # string user id
                    "url": url,
                    "name": name,
                    "is_up": is_up,
                    "status_code": status_code,
                    "response_time": response_time,     # seconds or None
                    "error": error,
                    "checked_at": now,                  # datetime.utcnow()
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to insert check log for {name}: {e}")

        # 🔥 IMPORTANT: first time DOWN aana mattum mail
        if new_status == "DOWN" and old_status != "DOWN":
            print(f"📩 Sending DOWN alert for {name} to {email} ...")
            try:
                send_down_alert(
                    to_email=email,
                    website_name=name,
                    url=url,
                    error=error,
                )
            except Exception as e:
                print("❌ Error while sending alert email:", repr(e))


# =====================================================================
# 🔵 2) SSL CERTIFICATE RECHECK FOR ALL HTTPS WEBSITES
# =====================================================================

async def recheck_ssl_for_all_websites():
    """
    Ellaa HTTPS websites-ukum SSL expiry info fresh-a update pannum +
    threshold cross aagumbodhu SSL expiry mail alert anupum.
    """
    print("🛰  Running scheduled recheck_ssl_for_all_websites()...")

    cursor = db.websites.find({})
    websites = await cursor.to_list(length=500)

    if not websites:
        print("ℹ️  No websites found in DB for SSL check.")
        return

    now = datetime.utcnow()

    for doc in websites:
        url = doc.get("url")
        if not url:
            continue

        parsed = urlparse(url)
        if parsed.scheme != "https":
            # HTTP site-ku SSL illa, skip
            continue

        hostname = parsed.hostname
        if not hostname:
            continue

        name = doc.get("name", url)
        email = doc.get("email")
        old_days_left = doc.get("ssl_days_left")

        # 🆕 user configured alert threshold (optional)
        alert_days = doc.get("ssl_alert_days_before")  # e.g. 7, 15 etc.

        try:
            expiry_date = get_ssl_expiry_date(hostname)
            days_left = (expiry_date - now).days
            ssl_valid = days_left > 0

            # ===============================
            # 🔥 SSL EXPIRY ALERT LOGIC (user-based)
            # ===============================
            if email:
                try:
                    # 1️⃣ First time set aagum case – already expired
                    if old_days_left is None and days_left <= 0:
                        send_ssl_expiry_alert(
                            to_email=email,
                            website_name=name,
                            url=url,
                            days_left=days_left,
                        )

                    # 2️⃣ User threshold alert (e.g. 7 days before)
                    if (
                        alert_days is not None
                        and old_days_left is not None
                        and old_days_left > alert_days
                        and 0 < days_left <= alert_days
                    ):
                        send_ssl_expiry_alert(
                            to_email=email,
                            website_name=name,
                            url=url,
                            days_left=days_left,
                        )

                    # 3️⃣ Expired threshold – always allowed
                    if (
                        old_days_left is not None
                        and old_days_left > 0
                        and days_left <= 0
                    ):
                        send_ssl_expiry_alert(
                            to_email=email,
                            website_name=name,
                            url=url,
                            days_left=days_left,
                        )

                except Exception as e:
                    print(f"❌ Error sending SSL expiry alert for {url}: {e}")

            # ===============================
            # 🔁 DB UPDATE
            # ===============================
            await db.websites.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "ssl_expiry_date": expiry_date,
                        "ssl_days_left": days_left,
                        "ssl_valid": ssl_valid,
                    }
                },
            )

            print(
                f"🔒 SSL updated for {url}: "
                f"expiry={expiry_date}, days_left={days_left}, valid={ssl_valid}"
            )

        except Exception as e:
            print(f"❌ SSL recheck failed for {url}: {e}")
