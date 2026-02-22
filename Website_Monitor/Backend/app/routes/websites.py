from fastapi import APIRouter, Depends, HTTPException, Body
from bson import ObjectId
from datetime import datetime
from urllib.parse import urlparse

from app.database import db
from app.utils.validators import is_valid_email
from app.utils.ssl_utils import get_ssl_expiry_date
from app.auth.deps import get_current_user
from app.monitor.checker import check_single_website

router = APIRouter(prefix="/websites", tags=["websites"])


# ============================================================
# 🔵 CREATE WEBSITE
# ============================================================
@router.post("/user_post")
async def add_website(
    website: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    username = current_user["username"]

    name = website.get("name")
    url = website.get("url")
    email = website.get("email")

    if not name or not url or not email:
        raise HTTPException(400, "name, url and email are required")

    if not is_valid_email(email):
        raise HTTPException(400, "Invalid email format")

    # 🔥 URL NORMALIZATION
    url = url.strip().lower().rstrip("/")

    # Interval
    try:
        check_interval = int(website.get("check_interval", 60))
        if check_interval <= 0:
            check_interval = 60
    except:
        check_interval = 60

    # SSL alert days
    ssl_alert_days_before = website.get("ssl_alert_days_before")
    if ssl_alert_days_before is not None:
        try:
            ssl_alert_days_before = int(ssl_alert_days_before)
        except:
            ssl_alert_days_before = None

    # 🔥 DUPLICATE PREVENTION
    if await db.websites.find_one({"url": url, "user_id": user_id}):
        raise HTTPException(400, "This website already exists")

    # SSL CHECK
    ssl_expiry_date = None
    ssl_days_left = None
    ssl_valid = None

    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.hostname:
        try:
            ssl_expiry_date = get_ssl_expiry_date(parsed.hostname)
            ssl_days_left = (ssl_expiry_date - datetime.utcnow()).days
            ssl_valid = ssl_days_left > 0
        except:
            ssl_valid = False

    site = {
        "user_id": user_id,
        "username": username,
        "name": name,
        "url": url,
        "email": email,
        "check_interval": check_interval,
        "is_active": True,

        "total_checks": 0,
        "up_checks": 0,
        "uptime": 0.0,

        "last_status": None,
        "last_checked": None,
        "last_response_time": None,
        "last_status_code": None,
        "last_error": None,

        "ssl_expiry_date": ssl_expiry_date,
        "ssl_days_left": ssl_days_left,
        "ssl_valid": ssl_valid,
        "ssl_alert_days_before": ssl_alert_days_before,
    }

    res = await db.websites.insert_one(site)
    site_id = res.inserted_id

    # FIRST CHECK
    result = await check_single_website({**site, "_id": site_id})

    response_time = (
        round(result["response_time"] * 1000, 2)
        if result["response_time"] is not None
        else None
    )

    await db.websites.update_one(
        {"_id": site_id},
        {"$set": {
            "last_status": "UP" if result["is_up"] else "DOWN",
            "last_checked": datetime.utcnow(),
            "last_response_time": response_time,
            "last_status_code": result["status_code"],
            "last_error": result["error"],
            "total_checks": 1,
            "up_checks": 1 if result["is_up"] else 0,
            "uptime": 100.0 if result["is_up"] else 0.0,
        }}
    )

    await db.history.insert_one({
        "website_id": site_id,
        "checked_at": datetime.utcnow(),
        "response_time": response_time,
        "status": "UP" if result["is_up"] else "DOWN",
    })

    # 🔥 SAFE SERIALIZATION FIX
    updated_site = await db.websites.find_one({"_id": site_id})
    updated_site["id"] = str(updated_site["_id"])
    del updated_site["_id"]

    if updated_site.get("ssl_expiry_date"):
        updated_site["ssl_expiry_date"] = updated_site["ssl_expiry_date"].isoformat()

    if updated_site.get("last_checked"):
        updated_site["last_checked"] = updated_site["last_checked"].isoformat()

    return {
        "message": "Website added",
        "website": updated_site
    }


# ============================================================
# 🔵 GET USER WEBSITES
# ============================================================
@router.get("/user_get")
async def get_user_websites(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    websites = []
    async for w in db.websites.find({"user_id": user_id}):
        w["id"] = str(w["_id"])
        del w["_id"]

        if w.get("ssl_expiry_date"):
            w["ssl_expiry_date"] = w["ssl_expiry_date"].isoformat()

        if w.get("last_checked"):
            w["last_checked"] = w["last_checked"].isoformat()

        websites.append(w)

    return websites


# ============================================================
# 🔵 WEBSITE HISTORY
# ============================================================
@router.get("/{website_id}/history")
async def get_website_history(
    website_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    oid = ObjectId(website_id)

    website = await db.websites.find_one({"_id": oid, "user_id": user_id})
    if not website:
        raise HTTPException(404, "Website not found")

    website["id"] = str(website["_id"])
    del website["_id"]

    if website.get("ssl_expiry_date"):
        website["ssl_expiry_date"] = website["ssl_expiry_date"].isoformat()

    if website.get("last_checked"):
        website["last_checked"] = website["last_checked"].isoformat()

    history = []
    async for h in db.history.find({"website_id": oid}).sort("checked_at", 1):
        h["id"] = str(h["_id"])
        del h["_id"]
        h["website_id"] = str(oid)

        if h.get("checked_at"):
            h["checked_at"] = h["checked_at"].isoformat()

        history.append(h)

    return {"website": website, "history": history}


# ============================================================
# 🔵 DELETE WEBSITE
# ============================================================
@router.delete("/{website_id}")
async def delete_website(
    website_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    oid = ObjectId(website_id)

    await db.websites.delete_one({"_id": oid, "user_id": user_id})
    await db.history.delete_many({"website_id": oid})

    return {"message": "Website deleted successfully"}