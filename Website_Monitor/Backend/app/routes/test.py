# app/routes/test.py

from fastapi import APIRouter
from app.database import db
from app.notify.emailer import send_down_alert, send_ssl_expiry_alert

router = APIRouter(prefix="/test", tags=["Test"])


# -----------------------------------------
# 🔹 DB CONNECTION TEST
# -----------------------------------------
@router.get("/check-db")
async def check_db():
    result = await db.test_collection.insert_one({"status": "ok"})
    count = await db.test_collection.count_documents({})
    return {
        "message": "DB connected & insert success",
        "inserted_id": str(result.inserted_id),
        "total_docs_in_test_collection": count
    }


# -----------------------------------------
# 🔹 SIMPLE PING ROUTE
# -----------------------------------------
@router.get("/ping")
async def ping():
    return {"message": "Test route ok"}


# -----------------------------------------
# 🔵 DOWN ALERT TEST
# -----------------------------------------
@router.get("/email-down")
async def test_down_email():
    to_email = "jegan28122005@gmail.com"
    send_down_alert(
        to_email=to_email,
        website_name="Test Down Site",
        url="https://example.com",
        error="Manual test error",
    )
    return {"message": f"Down alert test sent to {to_email}"}


# -----------------------------------------
# 🔒 SSL EXPIRY ALERT TEST
# -----------------------------------------
@router.get("/ssl-alert")
async def test_ssl_alert(
    to_email: str,
    days_left: int = 5,
):
    """
    Example:
      /test/ssl-alert?to_email=you@gmail.com&days_left=7
    """
    send_ssl_expiry_alert(
        to_email=to_email,
        website_name="Test SSL Site",
        url="https://example.com",
        days_left=days_left,
    )
    return {
        "message": f"SSL test alert sent to {to_email} with days_left={days_left}"
    }
