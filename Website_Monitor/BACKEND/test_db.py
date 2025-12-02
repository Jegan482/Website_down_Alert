import asyncio
from app.database import websites_col

async def run():
    count = await websites_col.count_documents({})
    print("Mongo Connection Success! Websites count:", count)

asyncio.run(run())
