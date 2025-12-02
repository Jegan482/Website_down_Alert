# backend/app/utils/calculate_uptime.py
from datetime import datetime, timedelta
from typing import List

# Input: recent checks for a website (list of dicts with 'status' and 'checkedAt')
# Returns uptime percentage in last N checks or time window.
def calc_uptime_percent(checks: List[dict]) -> float:
    if not checks:
        return 0.0
    up = sum(1 for c in checks if c.get("status") == "UP")
    return round((up / len(checks)) * 100, 2)

# convenience: get time-windowed checks (last `minutes` minutes)
def filter_recent(checks: List[dict], minutes: int = 60):
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    return [c for c in checks if c.get("checkedAt") and c["checkedAt"] >= cutoff]
