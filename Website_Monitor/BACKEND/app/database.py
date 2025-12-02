# backend/app/database.py
from dotenv import load_dotenv
load_dotenv()

import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "website_monitor")

_client = AsyncIOMotorClient(MONGO_URI)
_db = _client[DB_NAME]

websites_col = _db["websites"]
checks_col = _db["checks"]
alerts_col = _db["alerts"]

async def ensure_indexes():
    # creates basic useful indexes
    await checks_col.create_index([("websiteId", 1), ("checkedAt", -1)])
    await alerts_col.create_index([("websiteId", 1), ("createdAt", -1)])
    await websites_col.create_index("active")
