from fastapi import APIRouter
from app.database import db
from app.notify.emailer import send_down_alert

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/check-db")
async def check_db():
    result = await db.test_collection.insert_one({"status": "ok"})
    count = await db.test_collection.count_documents({})
    return {
        "message": "DB connected & insert success",
        "inserted_id": str(result.inserted_id),
        "total_docs_in_test_collection": count
    }


@router.get("/email")
def test_email():
    # YOUR real email here
    to_email = "jeganrealemail@gmail.com"

    send_down_alert(
        to_email=to_email,
        website_name="Test Site",
        url="https://example.com",
        error="This is a test error"
    )

    return {"message": "Test email triggered"}
