# backend/app/utils/email_alert.py
from dotenv import load_dotenv
load_dotenv()

import os
from email.message import EmailMessage
import aiosmtplib

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Basic validation at import time so failures are obvious.
_missing = []
if not SMTP_HOST:
    _missing.append("SMTP_HOST")
if not SMTP_USER:
    _missing.append("SMTP_USER")
if not SMTP_PASS:
    _missing.append("SMTP_PASS")

if _missing:
    raise RuntimeError(f"Missing required SMTP env vars: {', '.join(_missing)}. Please set them in your .env")

async def send_alert_async(to_email: str, subject: str, body: str):
    """
    Send an email asynchronously using aiosmtplib.
    Requires SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS env vars to be set.
    """
    if not to_email:
        raise ValueError("to_email is required")

    msg = EmailMessage()
    # Ensure From header always set
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject or "(no subject)"
    msg.set_content(body or "")

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )
