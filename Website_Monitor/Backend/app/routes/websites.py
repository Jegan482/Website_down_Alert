# app/routes/websites.py

from fastapi import APIRouter, Body, HTTPException
from bson import ObjectId

from app.database import db
from app.utils.validators import is_valid_email

router = APIRouter(prefix="/websites", tags=["websites"])


# ------------------ CREATE (PER USER) ------------------ #

@router.post("/user_post")
async def add_website(website: dict = Body(...)):

    print("POST /websites/user_post received:", website)

    username = website.get("username")
    name = website.get("name")
    url = website.get("url")
    email = website.get("email")

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

    # Prevent duplicate URLs for this user
    existing = await db.websites.find_one({
        "username": username,
        "url": url
    })
    if existing:
        raise HTTPException(status_code=400, detail="This URL already exists for this user")

    # Insert into DB
    website["username"] = username
    result = await db.websites.insert_one(website)
    inserted = await db.websites.find_one({"_id": result.inserted_id})

    inserted["id"] = str(inserted["_id"])
    del inserted["_id"]

    return {"message": "Website added", "website": inserted}


# ------------------ READ USER'S WEBSITES ------------------ #

@router.get("/user_get")
async def get_user_websites(username: str):
    """
    Only that user's websites list pannum.
    Example: /websites/user_get?username=jegan
    """
    websites = []

    cursor = db.websites.find({"username": username})

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        websites.append(doc)

    return websites


# ------------------ READ ONE ------------------ #

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


# ------------------ UPDATE (PER USER) ------------------ #

@router.put("/{website_id}")
async def update_website(website_id: str, username: str, website_update: dict = Body(...)):
    """
    Only 'username' match aagura website thaan update aagum.
    Usage:
      PUT /websites/<id>?username=jegan
    """

    try:
        oid = ObjectId(website_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if not website_update:
        raise HTTPException(status_code=400, detail="Empty body not allowed")

    # Check if this website belongs to this user
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


# ------------------ DELETE (PER USER) ------------------ #

@router.delete("/{website_id}")
async def delete_website(website_id: str, username: str):
    """
    Only that user's website delete aagum.
    Usage:
      DELETE /websites/<id>?username=jegan
    """

    try:
        oid = ObjectId(website_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await db.websites.delete_one({
        "_id": oid,
        "username": username
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Website not found for this user")

    return {"message": "Website deleted successfully"}
