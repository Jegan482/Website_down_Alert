from fastapi import APIRouter
from bson import ObjectId
from app.database import db

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/plot-response-time/{website_id}")
async def plot_response_time(website_id: str):

    try:
        oid = ObjectId(website_id)   # 🔥 IMPORTANT FIX
    except Exception:
        return {"detail": "Invalid website_id"}

    cursor = db.checks.find(
        {"website_id": oid}
    ).sort("checked_at", 1)

    data = await cursor.to_list(length=20)

    if not data:
        return {"detail": "No data found"}

    return {
        "count": len(data),
        "points": [
            {
                "time": d["checked_at"],
                "response_time": d["response_time"]
            }
            for d in data
        ]
    }
