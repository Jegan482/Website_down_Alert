from datetime import datetime
from urllib.parse import urlparse

from app.database import db
from app.monitor.checker import check_single_website
from app.notify.emailer import send_down_alert, send_ssl_expiry_alert
from app.utils.ssl_utils import get_ssl_expiry_date


# =====================================================================
# 🔵 1) NORMAL UPTIME / STATUS CHECK (1 minute aligned)
# =====================================================================

async def check_all_websites():
    print("🛰  Running scheduled check_all_websites()...")

    cursor = db.websites.find({})
    websites = await cursor.to_list(length=200)

    if not websites:
        print("ℹ️  No websites found in DB.")
        return

    for doc in websites:
        url = doc.get("url")
        name = doc.get("name", url)
        email = doc.get("email")

        if not url:
            continue

        # 🔕 inactive website skip
        if not doc.get("is_active", True):
            continue

        # ⏱ interval logic
        check_interval = int(doc.get("check_interval", 60))
        last_checked = doc.get("last_checked")

        now = datetime.utcnow()

        if last_checked:
            diff = (now - last_checked).total_seconds()
            if diff < check_interval:
                continue

        # ==============================
        # 🟢 CHECK WEBSITE
        # ==============================
        result = await check_single_website(doc)

        is_up = result["is_up"]
        status_code = result["status_code"]

        # 🔥 response_time stored in milliseconds
        response_time = (
            round(result["response_time"] * 1000, 2)
            if result["response_time"] is not None
            else None
        )

        error = result["error"]
        new_status = "UP" if is_up else "DOWN"
        old_status = doc.get("last_status")

        # 🔥 checked_at aligned to minute
        now = datetime.utcnow().replace(second=0, microsecond=0)

        # ==============================
        # 🔢 UPTIME CALCULATION
        # ==============================
        total_checks = doc.get("total_checks", 0) + 1
        up_checks = doc.get("up_checks", 0) + (1 if is_up else 0)
        uptime = (up_checks / total_checks) * 100

        # ==============================
        # 💾 UPDATE websites COLLECTION
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
                    "total_checks": total_checks,
                    "up_checks": up_checks,
                    "uptime": uptime,
                }
            },
        )

        # =====================================================
        # 📝 INSERT HISTORY (🔥 FIXED – LINE CHART SOURCE)
        # =====================================================
        await db.history.insert_one(
            {
                "website_id": doc["_id"],      # ✅ SAME ObjectId
                "checked_at": now,             # datetime
                "response_time": response_time,  # ms
                "status": new_status,
                "status_code": status_code,
            }
        )

        print(
            f"✅ {name} | {new_status} | {status_code} | {response_time} ms"
        )

        # ==============================
        # 📩 DOWN ALERT (only first down)
        # ==============================
        if new_status == "DOWN" and old_status != "DOWN":
            try:
                send_down_alert(
                    to_email=email,
                    website_name=name,
                    url=url,
                    error=error,
                )
            except Exception as e:
                print("❌ Email error:", e)


# =====================================================================
# 🔵 2) SSL CERTIFICATE RECHECK
# =====================================================================

async def recheck_ssl_for_all_websites():
    print("🛰  Running scheduled recheck_ssl_for_all_websites()...")

    cursor = db.websites.find({})
    websites = await cursor.to_list(length=500)

    if not websites:
        return

    now = datetime.utcnow()

    for doc in websites:
        url = doc.get("url")
        if not url or not url.startswith("https"):
            continue

        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            continue

        name = doc.get("name", url)
        email = doc.get("email")
        old_days_left = doc.get("ssl_days_left")
        alert_days = doc.get("ssl_alert_days_before")

        try:
            expiry_date = get_ssl_expiry_date(hostname)
            days_left = (expiry_date - now).days
            ssl_valid = days_left > 0

            # 📩 SSL ALERT LOGIC
            if email and alert_days is not None:
                if old_days_left is not None and old_days_left > alert_days >= days_left:
                    send_ssl_expiry_alert(
                        to_email=email,
                        website_name=name,
                        url=url,
                        days_left=days_left,
                    )

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

        except Exception as e:
            print(f"❌ SSL check failed for {url}: {e}")
