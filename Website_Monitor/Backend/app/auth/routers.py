from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.database import db
from app.auth.hashing import hash_password, verify_password
from app.auth.otp_utils import generate_otp, otp_expiry
from app.auth.jwt_utils import create_access_token
from app.notify.emailer import send_otp_email

router = APIRouter(prefix="/auth", tags=["Auth"])

# ================= SCHEMAS =================

class RegisterIn(BaseModel):
    username: str
    password: str
    email: EmailStr

class LoginIn(BaseModel):
    username: str
    password: str

class EmailIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str


# ================= REGISTER (AUTO LOGIN) =================
@router.post("/create")
async def register_user(data: RegisterIn):
    if await db.users.find_one({"username": data.username}):
        raise HTTPException(400, "Username already exists")

    if await db.users.find_one({"email": data.email}):
        raise HTTPException(400, "Email already registered")

    result = await db.users.insert_one({
        "username": data.username,
        "email": data.email,
        "password": hash_password(data.password),
        "created_at": datetime.utcnow()
    })

    user_id = str(result.inserted_id)

    token = create_access_token({"user_id": user_id})

    return {
        "message": "User created & logged in",
        "token": token,
        "user": {
            "id": user_id,
            "username": data.username,
            "email": data.email
        }
    }


# ================= LOGIN =================
@router.post("/login")
async def login_user(data: LoginIn):
    user = await db.users.find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(400, "Invalid credentials")

    token = create_access_token({"user_id": str(user["_id"])})

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }


# ================= FORGOT PASSWORD (SEND OTP) =================
@router.post("/forgot-password")
async def forgot_password(data: EmailIn):
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(404, "Email not found")

    otp = generate_otp()
    expiry = otp_expiry()

    await db.password_resets.update_one(
        {"email": data.email},
        {"$set": {"otp": otp, "expires_at": expiry}},
        upsert=True
    )

    send_otp_email(to_email=data.email, otp=otp)

    return {"message": "OTP sent to email"}


# ================= RESET PASSWORD =================
@router.post("/reset-password")
async def reset_password(data: ResetPasswordIn):
    record = await db.password_resets.find_one({"email": data.email})

    if not record:
        raise HTTPException(400, "OTP not requested")

    # 🔥 FIX: OTP datatype mismatch (int vs str)
    if str(record["otp"]) != str(data.otp):
        raise HTTPException(400, "Invalid OTP")

    if datetime.utcnow() > record["expires_at"]:
        raise HTTPException(400, "OTP expired")

    if data.new_password != data.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    await db.users.update_one(
        {"email": data.email},
        {"$set": {"password": hash_password(data.new_password)}}
    )

    await db.password_resets.delete_one({"email": data.email})

    return {"message": "Password reset successful"}
