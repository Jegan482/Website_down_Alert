# backend/app/main.py
import asyncio
from fastapi import FastAPI
from .database import ensure_indexes, websites_col
from .monitor import scheduler
import uvicorn
import os

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # create indexes
    await ensure_indexes()

    # start scheduler tasks (uses event loop)
    loop = asyncio.get_event_loop()
    await scheduler.start_scheduler(loop)

@app.on_event("shutdown")
async def shutdown_event():
    # cancel scheduler tasks cleanly
    # scheduler.start_scheduler cancels existing tasks when called; we can also cancel here
    for t in list(scheduler._tasks.values()):
        t.cancel()
    await asyncio.gather(*scheduler._tasks.values(), return_exceptions=True)
    scheduler._tasks.clear()

# mount your routes (example)
from .routes.websites import router as websites_router
app.include_router(websites_router, prefix="/websites")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
