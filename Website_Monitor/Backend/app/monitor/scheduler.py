# app/monitor/scheduler.py

from datetime import datetime

from app.database import db
from app.monitor.checker import check_single_website
from app.notify.emailer import send_down_alert


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
            print("⚠️  Skipping document (no URL):", doc.get("_id"))
            continue

        result = await check_single_website(doc)

        is_up = result["is_up"]
        status_code = result["status_code"]
        response_time = result["response_time"]
        error = result["error"]

        new_status = "UP" if is_up else "DOWN"
        old_status = doc.get("last_status")  # None / "UP" / "DOWN"

        now = datetime.utcnow()

        await db.websites.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "last_status": new_status,
                    "last_checked": now,
                    "last_response_time": response_time,
                    "last_status_code": status_code,
                    "last_error": error,
                }
            },
        )

        print(
            f"✅ Updated {name}: status={new_status}, "
            f"code={status_code}, rt={response_time}, error={error}"
        )

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
