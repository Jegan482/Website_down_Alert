# app/services/email.py

import smtplib
from email.mime.text import MIMEText
from app.core.config import settings  # .env values config.py la load agum


def send_down_alert(site, result):
    subject = f"ALERT: {site.get('name', site.get('url'))} is DOWN"

    body = (
        f"URL: {site.get('url')}\n"
        f"Status: DOWN\n"
        f"Error: {result.get('error')}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = site["email"]   # DB la 'email' field nu assume pannrom

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, [site["email"]], msg.as_string())

        print("✅ Alert email sent!")

    except Exception as e:
        print("❌ Email sending failed:", e)
