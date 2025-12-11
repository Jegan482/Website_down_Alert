# app/routes/websites.py

from fastapi import APIRouter, Depends, HTTPException, Body
from bson import ObjectId
from datetime import datetime
from urllib.parse import urlparse
from datetime import datetime, timedelta
from app.monitor.checker import check_single_website

from app.database import db
from app.utils.validators import is_valid_email
from app.utils.ssl_utils import get_ssl_expiry_date
from app.auth.deps import get_current_user


router = APIRouter(prefix="/websites", tags=["websites"])


# =====================================================================
# 🔵 1) CREATE WEBSITE (PER USER) – STRICT user_id
# =====================================================================
@router.post("/user_post")
async def add_website(
    website: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    print("POST /websites/user_post received:", website)

    user_id = current_user["id"]
    username = current_user["username"]

    name = website.get("name")
    url = website.get("url")
    email = website.get("email")

    # Basic validations
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    # ===========================
    # ⏱ Check interval (seconds)
    # ===========================
    raw_interval = website.get("check_interval", 60)
    try:
        check_interval = int(raw_interval)
        if check_interval <= 0:
            check_interval = 60
    except Exception:
        check_interval = 60

    # ===========================
    # 🔔 (Future) SSL alert days
    # ===========================
    raw_alert_days = website.get("ssl_alert_days_before")
    ssl_alert_days_before = None
    if raw_alert_days is not None:
        try:
            ssl_alert_days_before = int(raw_alert_days)
            if ssl_alert_days_before <= 0:
                ssl_alert_days_before = None
        except Exception:
            ssl_alert_days_before = None

    # ❗ Duplicate = same user + same URL
    existing = await db.websites.find_one({
        "url": url,
        "user_id": user_id,
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This URL already exists for this user",
        )

    # -----------------------------------------------------------
    # 🔒 SSL Certificate Check (only for HTTPS)
    # -----------------------------------------------------------
    ssl_expiry_date = None
    ssl_days_left = None
    ssl_valid = None

    parsed = urlparse(url)
    if parsed.scheme == "https":
        hostname = parsed.hostname
        if hostname:
            try:
                ssl_expiry_date = get_ssl_expiry_date(hostname)
                ssl_days_left = (ssl_expiry_date - datetime.utcnow()).days
                ssl_valid = ssl_days_left > 0
            except Exception as e:
                print("SSL Check Error:", e)
                ssl_expiry_date = None
                ssl_days_left = None
                ssl_valid = False

    # -----------------------------------------------------------
    # 💾 Insert into DB (initial)
    # -----------------------------------------------------------
    new_site = {
        "user_id": user_id,
        "username": username,  # display only

        "name": name,
        "url": url,
        "email": email,

        "check_interval": check_interval,
        "is_active": website.get("is_active", True),

        # Uptime counters
        "total_checks": 0,
        "up_checks": 0,
        "uptime": 0.0,

        # Status / last check (will update after first check)
        "status": "UNKNOWN",
        "status_code": None,
        "avg_response_time_ms": None,
        "last_checked": None,
        "error": None,
        "last_error": None,
        "last_response_time": None,
        "last_status": None,
        "last_status_code": None,

        # SSL fields
        "ssl_expiry_date": ssl_expiry_date,
        "ssl_days_left": ssl_days_left,
        "ssl_valid": ssl_valid,

        # SSL alert config (user input)
        "ssl_alert_days_before": ssl_alert_days_before,
        "ssl_last_alert_days_left": None,
        "ssl_last_alert_at": None,
    }

    insert_result = await db.websites.insert_one(new_site)
    inserted_id = insert_result.inserted_id

    # -----------------------------------------------------------
    # 🔍 FIRST CHECK – immediately after adding website
    # -----------------------------------------------------------
    # fresh doc eduthukkalam (உள்ளே வேற default field add பண்ணிருந்தா use ஆகும்)
    doc = await db.websites.find_one({"_id": inserted_id})

    # single website check
    check_result = await check_single_website(doc)

    is_up = check_result["is_up"]
    status_code = check_result["status_code"]
    response_time = check_result["response_time"]
    error = check_result["error"]

    now = datetime.utcnow()
    new_status = "UP" if is_up else "DOWN"

    # first check-na:
    total_checks = 1
    up_checks = 1 if is_up else 0
    uptime = (up_checks / total_checks) * 100

    # 📌 website document update with first check details
    await db.websites.update_one(
        {"_id": inserted_id},
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

    # 📝 history collection la first row insert
    try:
        await db.checks.insert_one(
            {
                "website_id": inserted_id,
                "user_id": user_id,
                "url": url,
                "name": name,
                "is_up": is_up,
                "status_code": status_code,
                "response_time": response_time,
                "error": error,
                "checked_at": now,
            }
        )
    except Exception as e:
        print(f"⚠️ Failed to insert initial check log for {name}: {e}")

    # final doc (updated) return panna
    inserted = await db.websites.find_one({"_id": inserted_id})
    inserted["id"] = str(inserted["_id"])
    del inserted["_id"]

    return {"message": "Website added", "website": inserted}

# =====================================================================
# 🔵 2) GET ALL WEBSITES (FOR ADMIN / DEBUG)
# =====================================================================
@router.get("")
async def get_all_websites():
    """
    Full database la irukkura ellaa websites-um return pannum.
    (Admin debug ku use panna)
    """
    websites = []
    cursor = db.websites.find({})

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        websites.append(doc)

    return websites


# =====================================================================
# 🔵 3) GET WEBSITES OF CURRENT USER – STRICT user_id
# =====================================================================
@router.get("/user_get")
async def get_user_websites(current_user: dict = Depends(get_current_user)):
    """
    Current logged in user-oda websites list.
    """
    user_id = current_user["id"]

    websites = []
    cursor = db.websites.find({"user_id": user_id})

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        websites.append(doc)

    return websites


# =====================================================================
# 🔵 4) GET ONE WEBSITE BY ID (optionally could restrict to current user)
# =====================================================================
@router.get("/{website_id}")
async def get_website_by_id(website_id: str):
    try:
        oid = ObjectId(website_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    doc = await db.websites.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail="Website not found")

    doc["id"] = str(doc["_id"])
    del doc["_id"]

    return doc


# =====================================================================
# 🔵 5) UPDATE WEBSITE – STRICT JWT user_id
# =====================================================================
@router.put("/{website_id}")
async def update_website(
    website_id: str,
    website_update: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    PUT /websites/<id>
    Headers: Authorization: Bearer <token>
    Body: { ... fields to update ... }
    """
    try:
        oid = ObjectId(website_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if not website_update:
        raise HTTPException(status_code=400, detail="Empty body not allowed")

    user_id = current_user["id"]

    # 🔐 Ensure this website belongs to this user
    existing = await db.websites.find_one({"_id": oid, "user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Website not found for this user")

    # ❌ user_id / username change panna koodadhu
    website_update.pop("user_id", None)
    website_update.pop("username", None)

    # ✅ Optional: check_interval + ssl_alert_days_before clean pannalaam
    if "check_interval" in website_update:
        try:
            ci = int(website_update["check_interval"])
            if ci <= 0:
                ci = 60
            website_update["check_interval"] = ci
        except Exception:
            website_update["check_interval"] = existing.get("check_interval", 60)

    if "ssl_alert_days_before" in website_update:
        raw = website_update["ssl_alert_days_before"]
        try:
            alert_days = int(raw)
            if alert_days <= 0:
                alert_days = None
        except Exception:
            alert_days = existing.get("ssl_alert_days_before")
        website_update["ssl_alert_days_before"] = alert_days

    await db.websites.update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": website_update},
    )

    updated = await db.websites.find_one({"_id": oid})
    updated["id"] = str(updated["_id"])
    del updated["_id"]

    return {"message": "Website updated", "website": updated}
# =====================================================================
# 🔵 6) DELETE WEBSITE – STRICT user_id via token
# =====================================================================
@router.delete("/{website_id}")
async def delete_website(
    website_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    try:
        oid = ObjectId(website_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await db.websites.delete_one({"_id": oid, "user_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Website not found for this user")

    return {"message": "Website deleted successfully"}

# =====================================================================
# 🔵 7) GET WEBSITE HISTORY (for charts)
# =====================================================================
@router.get("/{website_id}/history")
async def get_website_history(
    website_id: str,
    limit: int = 50,
    minutes: int | None = None,   # 👈 new optional filter
    current_user: dict = Depends(get_current_user),
):
    """
    Last 'limit' checks history for this website.

    Query params:
      - limit   → max rows (default 50)
      - minutes → last X minutes only (optional)
    """
    try:
        oid = ObjectId(website_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    user_id = current_user["id"]

    site = await db.websites.find_one({"_id": oid, "user_id": user_id})
    if not site:
        raise HTTPException(status_code=404, detail="Website not found for this user")

    # 🔎 Base query
    query = {"website_id": oid, "user_id": user_id}

    # ⏱ If minutes given → filter by time window
    if minutes is not None and minutes > 0:
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=minutes)
        query["checked_at"] = {"$gte": cutoff}

    cursor = (
        db.checks.find(query)
        .sort("checked_at", -1)
        .limit(limit)
    )

    history = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["website_id"] = str(doc["website_id"])
        del doc["_id"]
        history.append(doc)

    history.reverse()
    return history


# =====================================================================
# 🔵 8) GET WEBSITE INCIDENTS (last N downs/errors)
# =====================================================================
@router.get("/{website_id}/incidents")
async def get_website_incidents(
    website_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    Last 'limit' incidents (DOWN / error / 4xx+5xx) for this website.
    Example:
      GET /websites/<id>/incidents?limit=10
    Headers:
      Authorization: Bearer <token>
    """
    try:
        oid = ObjectId(website_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    user_id = current_user["id"]

    # Site belong check
    site = await db.websites.find_one({"_id": oid, "user_id": user_id})
    if not site:
        raise HTTPException(status_code=404, detail="Website not found for this user")

    # Bad rows = DOWN / error / status_code >= 400
    query = {
        "website_id": oid,
        "user_id": user_id,
        "$or": [
            {"is_up": False},
            {"error": {"$ne": None}},
            {"status_code": {"$gte": 400}},
        ],
    }

    cursor = (
        db.checks.find(query)
        .sort("checked_at", -1)  # latest incidents first
        .limit(limit)
    )

    incidents = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["website_id"] = str(doc["website_id"])
        del doc["_id"]
        incidents.append(doc)

    return incidents
