# app/auth/routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import db
from .hashing import hash_password, verify_password
from app.auth.jwt_utils import create_access_token  # 👈 NEW import

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserIn(BaseModel):
    username: str
    password: str


# =====================================================
# 🔵 CREATE USER  →  returns id + JWT token
# =====================================================
@router.post("/create")
async def create_user(user: UserIn):
    print("🟢 /auth/create called with:", user.username)

    # user already irukana check
    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(user.password)

    result = await db.users.insert_one({
        "username": user.username,
        "password": hashed
    })

    user_id = str(result.inserted_id)

    # 🔐 JWT token create pannrom – payload-la user_id store
    token = create_access_token({"user_id": user_id})

    return {
        "message": "User created successfully",
        "user": {
            "id": user_id,
            "username": user.username,
        },
        "token": token,  # 👈 React/frontend store pannikum place
    }


# =====================================================
# 🔵 LOGIN USER  →  returns same id + new JWT token
# =====================================================
@router.post("/login")
async def login_user(user: UserIn):
    print("🟢 /auth/login called with:", user.username)

    db_user = await db.users.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username")

    ok = verify_password(user.password, db_user["password"])
    if not ok:
        raise HTTPException(status_code=400, detail="Wrong password")

    user_id = str(db_user["_id"])
    token = create_access_token({"user_id": user_id})

    return {
        "message": "Login Success",
        "user": {
            "id": user_id,
            "username": db_user["username"],
        },
        "token": token,
    }


# =====================================================
# 🔵 GET ALL USERS  →  (debug only)
# =====================================================
@router.get("/all-users")
async def get_all_users():
    cursor = db.users.find({})
    users = []
    async for doc in cursor:
        users.append({
            "id": str(doc["_id"]),
            "username": doc.get("username")
        })
    return users
