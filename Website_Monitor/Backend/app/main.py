from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.routes.test import router as test_router
from app.routes.websites import router as websites_router
from app.auth.routers import router as auth_router
from app.monitor.scheduler import check_all_websites, recheck_ssl_for_all_websites
from app.database import db
from app.notify.emailer import send_down_alert, send_ssl_expiry_alert


# ===== FastAPI app create pannrom =====
app = FastAPI()

# 🔥 CORS middleware – IMPORTANT: only *after* app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "*",  # local dev ku ok
    ],
    allow_credentials=True,
    allow_methods=["*"],     # GET, POST, DELETE, OPTIONS ellame
    allow_headers=["*"],
)

print("🔥 Currently Connected DB:", db.name)

# Single global scheduler
scheduler = AsyncIOScheduler()


# ===== DEBUG ROUTES (helpful) =====
@app.get("/debug-routes")
def list_routes():
    """
    App la register aana ellaa path-um list pannum.
    Chrome / Postman la GET panna path list varum.
    """
    return [route.path for route in app.router.routes]


# ===== Include routers =====
# /auth/... → user create, login etc.
app.include_router(auth_router)

# /test/... → DB test, email test etc. (routes/test.py la irukkum)
app.include_router(test_router)

# /websites/... → website CRUD, per-user websites etc.
app.include_router(websites_router)

@app.on_event("startup")
async def startup_event():
    """
    Server start aana udane scheduler start pannum.
    Uptime check + SSL recheck jobs add pannuvom.
    """
    if not scheduler.running:
        if not scheduler.get_jobs():
            # ⏱ 1) Uptime check – 1 minute-ku oru thadava
            scheduler.add_job(
                check_all_websites,
                "interval",
                minutes=1,
                id="uptime_check_job",
            )

            # 🔒 2) SSL recheck – 24 hours-ku oru thadava
            scheduler.add_job(
                recheck_ssl_for_all_websites,
                "interval",
                hours=24,
                id="ssl_recheck_job",
            )

        # (Optional) server start aana udane oru thadava both checks run pannalam
        await check_all_websites()          # 👉 uptime first run
        await recheck_ssl_for_all_websites()  # 👉 ssl first run

        scheduler.start()
        print("🚀 Scheduler started!")
    else:
        print("⚠️ Scheduler already running, skip start")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Server stop aagum pothu scheduler ah safely stop pannuvom.
    """
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Scheduler stopped")


@app.get("/debug/run-ssl")
async def debug_run_ssl():
    """
    Manual-a ellaa HTTPS websites-um SSL recheck panna
    Example:
        GET http://127.0.0.1:8000/debug/run-ssl
    """
    await recheck_ssl_for_all_websites()
    return {"message": "Manual SSL recheck completed"}



# ===== OPTIONAL: TEST EMAIL ROUTE =====
@app.get("/test-email")
async def test_email():
    """
    Manual email test:
    GET http://127.0.0.1:8000/test-email
    """
    to_email = "Jegan28122005@gmail.com"  # unga real email

    send_down_alert(
        to_email=to_email,
        website_name="Test Site",
        url="https://example.com",
        error="Manual test error",
    )
    return {"message": f"Email test triggered to {to_email}"}



@app.get("/test-ssl-email")
async def test_ssl_email():
    """
    Manual SSL expiry email test:
    GET http://127.0.0.1:8000/test-ssl-email
    """
    to_email = "Jegan28122005@gmail.com"  # unga email
    website_name = "Test SSL Site"
    url = "https://example.com"

    # 👇 inga value maathi maathi different mails test pannalaam
    days_left = 5   # expiring soon
    # days_left = 0  # expired
    # days_left = -2 # expired, negative

    send_ssl_expiry_alert(
        to_email=to_email,
        website_name=website_name,
        url=url,
        days_left=days_left,
    )

    return {"message": f"SSL test email sent to {to_email} with days_left={days_left}"}
