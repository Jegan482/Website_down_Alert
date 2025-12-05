from fastapi import FastAPI
from fastapi.routing import APIRoute
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.routes.test import router as test_router
from app.routes.websites import router as websites_router
from app.auth.routers import router as auth_router
from app.monitor.scheduler import check_all_websites
from app.database import db
from app.notify.emailer import send_down_alert


# ===== FastAPI app create pannrom =====
app = FastAPI()

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


# ===== Scheduler events =====
@app.on_event("startup")
async def startup_event():
    """
    Server start aana udane scheduler start pannum.
    check_all_websites() ku interval job add pannuvom.
    """
    if not scheduler.running:
        if not scheduler.get_jobs():
            # minutes=1 → 1 nimishathukku oru thadava ellaa sites-um check pannum
            scheduler.add_job(check_all_websites, "interval", minutes=1)
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


# ===== Manual debug route for scheduler =====
@app.get("/debug/run-check")
async def debug_run_check():
    """
    Scheduler a wait pannama, manual-a ellaa websites-um check panna
    intha route use panna mudiyum.
    Example:
        GET http://127.0.0.1:8000/debug/run-check
    """
    await check_all_websites()
    return {"message": "Manual check completed"}


# ===== OPTIONAL: TEST EMAIL ROUTE =====
# Ithu just manual test-ku. Project-ku thevai illa.
# Mail already sariyaa work aagiduchu na, inime use panna vendam.
# Ungalukku venumna comment pannalaam / delete pannalaam.

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
