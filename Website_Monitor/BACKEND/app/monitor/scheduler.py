# backend/app/monitor/scheduler.py
import asyncio
import aiohttp
import traceback
from datetime import datetime, timedelta
from ..database import websites_col, checks_col, alerts_col
from .checker import run_check
from ..utils.email_alert import send_alert_async
import os

# Simple alert rule: send alert when 3 consecutive DOWN in a row
CONSECUTIVE_DOWN_THRESHOLD = int(os.getenv("CONSECUTIVE_DOWN_THRESHOLD", 3))

# store running tasks per site _id
_tasks = {}

async def _monitor_site(loop, site_id):
    """
    Monitor a single site by its _id. We re-read the site document each iteration
    so changes (active flag, interval, ownerEmail, etc.) are respected.
    """
    async with aiohttp.ClientSession() as session:
        try:
            while True:
                # reload site doc from DB (so updates are respected)
                site = await websites_col.find_one({"_id": site_id})
                if not site or not site.get("active", True):
                    # stop monitoring if site removed or deactivated
                    break

                try:
                    # run_check should perform the check and optionally return a result dict.
                    # If run_check does not insert the check record, uncomment the insertion below.
                    result = await run_check(session, site)

                    # If run_check returns a result dict and you need to save it:
                    # if isinstance(result, dict):
                    #     await checks_col.insert_one(result)

                    # fetch recent checks (most recent first)
                    recent = await checks_col.find({"websiteId": site["_id"]}).sort("checkedAt", -1).limit(CONSECUTIVE_DOWN_THRESHOLD).to_list(length=CONSECUTIVE_DOWN_THRESHOLD)

                    # check consecutive down
                    if len(recent) >= CONSECUTIVE_DOWN_THRESHOLD and all(r.get("status") == "DOWN" for r in recent):
                        # avoid duplicate alerts — check last alert time
                        last_alert = await alerts_col.find_one({"websiteId": site["_id"], "type": "DOWN"}, sort=[("createdAt", -1)])
                        send = True
                        if last_alert:
                            if (datetime.utcnow() - last_alert["createdAt"]) < timedelta(minutes=30):
                                send = False
                        if send and site.get("ownerEmail"):
                            subj = f"[ALERT] {site.get('name', site.get('url'))} is DOWN"
                            body = f"Site {site.get('url')} appears DOWN. Last error: {recent[0].get('error')}. Time: {recent[0].get('checkedAt')}"
                            # send_alert_async may or may not need loop — keep your existing signature
                            await send_alert_async(loop, site["ownerEmail"], subj, body)
                            await alerts_col.insert_one({
                                "websiteId": site["_id"],
                                "type": "DOWN",
                                "sentTo": site.get("ownerEmail"),
                                "message": body,
                                "createdAt": datetime.utcnow()
                            })

                except asyncio.CancelledError:
                    # let the cancellation propagate after any necessary cleanup
                    raise
                except Exception:
                    traceback.print_exc()

                # respect site interval (default 60s)
                interval = site.get("interval", 60) if site else 60
                # allow cancellation during sleep
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            # task was cancelled externally — perform optional cleanup here
            return

async def start_scheduler(loop):
    # cancel and await existing tasks first
    if _tasks:
        for t in list(_tasks.values()):
            t.cancel()
        await asyncio.gather(*_tasks.values(), return_exceptions=True)
    _tasks.clear()

    sites = await websites_col.find({"active": True}).to_list(length=None)
    for s in sites:
        key = str(s["_id"])
        task = loop.create_task(_monitor_site(loop, s["_id"]))
        _tasks[key] = task

# Call this when a website is added/changed to restart scheduler or create per-site task
async def schedule_site(loop, site_doc):
    key = str(site_doc["_id"])
    # cancel existing task if running and await it
    if key in _tasks:
        _tasks[key].cancel()
        await asyncio.gather(_tasks[key], return_exceptions=True)
    task = loop.create_task(_monitor_site(loop, site_doc["_id"]))
    _tasks[key] = task
