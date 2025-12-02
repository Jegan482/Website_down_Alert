from fastapi import APIRouter
from ..database import checks_col

router = APIRouter()

@router.get("/{site_id}")
async def latest_status(site_id):
    from bson import ObjectId
    data = await checks_col.find({"websiteId": ObjectId(site_id)}).sort("checkedAt", -1).limit(1).to_list(1)
    return data[0] if data else {"status": "unknown"}
