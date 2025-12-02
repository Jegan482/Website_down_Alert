import aiohttp
from datetime import datetime

async def run_check(session, site):
    url = site["url"]
    timeout = site.get("timeout", 10)

    start = datetime.utcnow()

    try:
        async with session.get(url, timeout=timeout) as resp:
            status_code = resp.status
            response_time = (datetime.utcnow() - start).total_seconds() * 1000

            result = {
                "websiteId": site["_id"],
                "status": "UP" if status_code < 400 else "DOWN",
                "code": status_code,
                "checkedAt": datetime.utcnow(),
                "responseTimeMs": response_time,
                "error": None
            }
            return result

    except Exception as e:
        return {
            "websiteId": site["_id"],
            "status": "DOWN",
            "code": None,
            "checkedAt": datetime.utcnow(),
            "responseTimeMs": None,
            "error": str(e)
        }
