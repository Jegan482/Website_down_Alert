# app/routes/websites.py

from fastapi import APIRouter, Body, HTTPException
from bson import ObjectId

from app.database import db
from app.utils.validators import is_valid_email

router = APIRouter(prefix="/websites", tags=["websites"])


# =====================================================================
# 🔵 1) CREATE WEBSITE (PER USER)
# =====================================================================

@router.post("/user_post")
async def add_website(website: dict = Body(...)):
    """
    Oru user oru website add pannumbodhu use aagura route.
    Frontend payload (script.js):
    {
      "username": "...",
      "name": "...",
      "url": "...",
      "email": "...",
      "check_interval": 60,
      "is_active": true
    }
    """

    print("POST /websites/user_post received:", website)

    username = website.get("username")
    name = website.get("name")
    url = website.get("url")
    email = website.get("email")

    # Basic validations
    if not username:
        raise HTTPException(status_code=400, detail="username is required")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Interval read pannrom (frontend send pannalana default 60)
    raw_interval = website.get("check_interval", 60)
    try:
        check_interval = int(raw_interval)
        if check_interval <= 0:
            check_interval = 60
    except Exception:
        check_interval = 60

    # ❗ IMPORTANT: Duplicate check = URL + EMAIL combination
    existing = await db.websites.find_one({
        "url": url,
        "email": email
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This URL and Email combination already exists"
        )

    # Insert into DB
    website["username"] = username
    website["check_interval"] = check_interval
    website["is_active"] = website.get("is_active", True)

    # optional defaults (scheduler later overwrite pannum)
    website.setdefault("status", "UNKNOWN")
    website.setdefault("status_code", None)
    website.setdefault("uptime", 0.0)
    website.setdefault("avg_response_time_ms", None)
    website.setdefault("last_checked", None)
    website.setdefault("error", None)

    result = await db.websites.insert_one(website)
    inserted = await db.websites.find_one({"_id": result.inserted_id})

    inserted["id"] = str(inserted["_id"])
    del inserted["_id"]

    return {"message": "Website added", "website": inserted}


# =====================================================================
# 🔵 2) GET ALL WEBSITES (FOR DASHBOARD) – (optional, not used by current JS)
# =====================================================================

@router.get("")
async def get_all_websites():
    """
    Full database la irukkura ellaa websites-um return pannum.
    Ippo un frontend per-user list use pannudhu (user_get), but
    in future global admin dash board-ku use panna mudiyum.
    """
    websites = []
    cursor = db.websites.find({})

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        websites.append(doc)

    return websites


# =====================================================================
# 🔵 3) GET WEBSITES OF A SPECIFIC USER
# =====================================================================

@router.get("/user_get")
async def get_user_websites(username: str):
    """
    /websites/user_get?username=jegan
    Frontend la status table-ku use aagura main route idhu.
    """
    websites = []
    cursor = db.websites.find({"username": username})

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        websites.append(doc)

    return websites


# =====================================================================
# 🔵 4) GET ONE WEBSITE BY ID
# =====================================================================

@router.get("/{website_id}")
async def get_website_by_id(website_id: str):
    try:
        oid = ObjectId(website_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    doc = await db.websites.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail="Website not found")

    doc["id"] = str(doc["_id"])
    del doc["_id"]

    return doc


# =====================================================================
# 🔵 5) UPDATE WEBSITE (OPTIONAL)
# =====================================================================

@router.put("/{website_id}")
async def update_website(
    website_id: str,
    username: str,
    website_update: dict = Body(...)
):
    """
    PUT /websites/<id>?username=jegan
    """
    try:
        oid = ObjectId(website_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if not website_update:
        raise HTTPException(status_code=400, detail="Empty body not allowed")

    existing = await db.websites.find_one({"_id": oid, "username": username})
    if not existing:
        raise HTTPException(status_code=404, detail="Website not found for this user")

    await db.websites.update_one(
        {"_id": oid, "username": username},
        {"$set": website_update}
    )

    updated = await db.websites.find_one({"_id": oid})
    updated["id"] = str(updated["_id"])
    del updated["_id"]

    return {"message": "Website updated", "website": updated}


# =====================================================================
# 🔵 6) DELETE WEBSITE
# =====================================================================

@router.delete("/{website_id}")
async def delete_website(website_id: str, username: str | None = None):
    """
    If username provided → restrict delete to that user.
    If not → id base la delete (frontend support).
    """

    try:
        oid = ObjectId(website_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if username:
        result = await db.websites.delete_one({"_id": oid, "username": username})
    else:
        result = await db.websites.delete_one({"_id": oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Website not found")

    return {"message": "Website deleted successfully"}
