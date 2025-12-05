# app/notify/emailer.py

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# .env load
load_dotenv()

# Brevo SMTP defaults
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL") or SMTP_USER


def send_down_alert(to_email: str, website_name: str, url: str, error: str | None = None):
    """
    Website DOWN aana Brevo SMTP use panni mail anupura function.
    """

    print("DEBUG SMTP CONFIG:")
    print("  HOST:", SMTP_HOST)
    print("  USER:", SMTP_USER)
    print("  FROM:", FROM_EMAIL)

    if not (SMTP_USER and SMTP_PASS):
        print("⚠️ SMTP credentials missing, cannot send email.")
        return

    if not to_email:
        print("⚠️ No alert_email given, skipping email.")
        return

    # Plain-text body
    text_body = f"""Hi,

Your website '{website_name}' seems to be DOWN.

URL   : {url}
Error : {error or 'Unknown error'}

Please check the site as soon as possible.

Thanks,
Website Monitor Bot
"""

    # EmailMessage build
    msg = EmailMessage()
    msg["Subject"] = f"[ALERT] Website is DOWN: {website_name}"
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(text_body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"📧 Down alert sent to {to_email} for {website_name}")
    except Exception as e:
        print("❌ Failed to send email:", repr(e))
