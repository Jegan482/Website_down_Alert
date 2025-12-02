from fastapi import APIRouter
from ..database import websites_col
from ..monitor import scheduler
import asyncio

router = APIRouter()

@router.post("/")
async def add_website(payload: dict):
    res = await websites_col.insert_one(payload)
    site = await websites_col.find_one({"_id": res.inserted_id})

    loop = asyncio.get_event_loop()
    await scheduler.schedule_site(loop, site)

    return {"status": "ok", "id": str(res.inserted_id)}

@router.get("/")
async def list_websites():
    return await websites_col.find({}).to_list(length=None)

@router.delete("/{site_id}")
async def delete_website(site_id):
    from bson import ObjectId
    await websites_col.delete_one({"_id": ObjectId(site_id)})
    return {"status": "deleted"}
