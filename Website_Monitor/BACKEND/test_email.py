# backend/test_email.py
import os
from dotenv import load_dotenv
load_dotenv()

print("DEBUG: SMTP_HOST=", os.getenv("SMTP_HOST"))
print("DEBUG: SMTP_PORT=", os.getenv("SMTP_PORT"))
print("DEBUG: SMTP_USER=", os.getenv("SMTP_USER"))
print("DEBUG: SMTP_PASS set? ", bool(os.getenv("SMTP_PASS")))

# Now try to send
import asyncio
from app.utils.email_alert import send_alert_async

async def test():
    await send_alert_async(
        os.getenv("SMTP_USER"),    # send to yourself
        "Test Alert from Monitoring System",
        "This is a test email from your monitoring backend."
    )

asyncio.run(test())
