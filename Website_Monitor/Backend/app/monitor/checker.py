# app/monitor/checker.py

import time
import httpx
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    URL format correct-a iruka nu basic-a check pannum.
    - scheme: http / https irukanum
    - netloc: domain / host irukanum
    """
    try:
        parsed = urlparse(url)

        # STEP 1: Scheme http / https irukanum
        if parsed.scheme not in ("http", "https"):
            return False

        # STEP 2: Domain/host irukanum
        if not parsed.netloc:
            return False

        return True
    except Exception:
        return False


async def check_single_website(website: dict) -> dict:
    """
    Oru single website oda status check pannum.
    Return:
        {
          "is_up": bool,
          "status_code": int | None,
          "response_time": float | None,
          "error": str | None
        }
    """
    url = website.get("url")
    if not url:
        return {
            "is_up": False,
            "status_code": None,
            "response_time": None,
            "error": "NO_URL",
        }

    # 🔹 URL format validate panna
    if not is_valid_url(url):
        return {
            "is_up": False,
            "status_code": None,
            "response_time": None,
            "error": "INVALID_URL",
        }

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
        response_time = time.time() - start

        # 200–399 → UP (success + redirect)
        is_up = 200 <= response.status_code < 400

        return {
            "is_up": is_up,
            "status_code": response.status_code,
            "response_time": response_time,
            "error": None,
        }
    except Exception as e:
        # Site down / timeout / connection error etc.
        return {
            "is_up": False,
            "status_code": None,
            "response_time": None,
            "error": str(e),
        }
