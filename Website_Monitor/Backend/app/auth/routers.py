from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import db
from .hashing import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserIn(BaseModel):
    username: str
    password: str


@router.post("/create")
async def create_user(user: UserIn):
    print("🟢 /auth/create called with:", user.username)

    # user already irukana check
    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(user.password)

    await db.users.insert_one({
        "username": user.username,
        "password": hashed
    })

    return {"message": "User created successfully"}


@router.post("/login")
async def login_user(user: UserIn):
    print("🟢 /auth/login called with:", user.username)

    db_user = await db.users.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username")

    ok = verify_password(user.password, db_user["password"])
    if not ok:
        raise HTTPException(status_code=400, detail="Wrong password")

    return {"message": "Login Success", "username": user.username}
@router.get("/all-users")
async def get_all_users():
    cursor = db.users.find({}, {"_id": 0, "password": 0})  # _id & password hidden
    users = await cursor.to_list(length=100)
    return users





