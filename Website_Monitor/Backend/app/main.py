from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.routes.test import router as test_router
from app.routes.websites import router as websites_router
from app.auth.routers import router as auth_router
from app.monitor.scheduler import (
    check_all_websites,
    recheck_ssl_for_all_websites,
)
from app.database import db
from app.notify.emailer import send_down_alert, send_ssl_expiry_alert

# =====================================================
# 🔥 CREATE APP (ONLY ONCE)
# =====================================================
app = FastAPI()

# =====================================================
# 🔥 DEBUG PLOT ROUTER (IMPORTANT)
# =====================================================
from app.debug.plot import router as debug_plot_router
app.include_router(debug_plot_router)

# =====================================================
# 🔥 CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🔥 Currently Connected DB:", db.name)

# =====================================================
# 🔥 SCHEDULER
# =====================================================
scheduler = AsyncIOScheduler()

# =====================================================
# 🔎 DEBUG ROUTES
# =====================================================
@app.get("/debug-routes")
def list_routes():
    return [route.path for route in app.router.routes]

# =====================================================
# 🔗 MAIN ROUTERS
# =====================================================
app.include_router(auth_router)
app.include_router(test_router)
app.include_router(websites_router)

# =====================================================
# 🚀 STARTUP
# =====================================================
@app.on_event("startup")
async def startup_event():
    if not scheduler.running:
        if not scheduler.get_jobs():
            scheduler.add_job(
                check_all_websites,
                "interval",
                minutes=1,
                id="uptime_check_job",
            )

            scheduler.add_job(
                recheck_ssl_for_all_websites,
                "interval",
                hours=24,
                id="ssl_recheck_job",
            )

        await check_all_websites()
        await recheck_ssl_for_all_websites()

        scheduler.start()
        print("🚀 Scheduler started!")

# =====================================================
# 🛑 SHUTDOWN
# =====================================================
@app.on_event("shutdown")
async def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Scheduler stopped")

# =====================================================
# 🔧 DEBUG SSL
# =====================================================
@app.get("/debug/run-ssl")
async def debug_run_ssl():
    await recheck_ssl_for_all_websites()
    return {"message": "Manual SSL recheck completed"}

# =====================================================
# 📧 TEST EMAILS
# =====================================================
@app.get("/test-email")
async def test_email():
    send_down_alert(
        to_email="Jegan28122005@gmail.com",
        website_name="Test Site",
        url="https://example.com",
        error="Manual test error",
    )
    return {"message": "Email test sent"}

@app.get("/test-ssl-email")
async def test_ssl_email():
    send_ssl_expiry_alert(
        to_email="Jegan28122005@gmail.com",
        website_name="Test SSL Site",
        url="https://example.com",
        days_left=5,
    )
    return {"message": "SSL test email sent"}
