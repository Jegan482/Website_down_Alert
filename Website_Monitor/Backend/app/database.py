from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()  # .env file load pannum

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set in .env")
if not DB_NAME:
    raise RuntimeError("DB_NAME is not set in .env")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
