# app/notify/emailer.py

import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

# .env load
load_dotenv()

# Brevo SMTP defaults
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# From address:
#  - best practice: domain-based sender, like alerts@jeganprojects.in
#  - FROM_EMAIL .env-la set pannunga; illa na SMTP_USER fallback
FROM_EMAIL = os.getenv("FROM_EMAIL") or SMTP_USER


def send_down_alert(to_email: str, website_name: str, url: str, error: str | None = None):
    """
    Website DOWN aana Brevo SMTP use panni mail anupura function.
    Spam chance kammi aagura maari:
      - calm subject
      - plain text + simple HTML
      - proper From / Reply-To
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

    # ---------- Subject (simple, not spammy) ----------
    subject = f"[Website Monitor] {website_name} might be down"

    # ---------- Plain-text body ----------
    text_body = f"""Hi,

This is an automatic notification from your Website Monitor.

We could not reach your website:

  Name : {website_name}
  URL  : {url}

Error details: {error or "Unknown error"}

Please check your website or server configuration.
You can also open your monitoring dashboard to see the latest status.

If you no longer want alerts for this site, you can remove it
from the monitoring dashboard.

Thanks,
Website Monitor
"""

    # ---------- Simple HTML body ----------
    html_body = f"""\
<html>
  <body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#111827;">
    <p>Hi,</p>

    <p>This is an automatic notification from <strong>your Website Monitor</strong>.</p>

    <p>We could not reach your website:</p>

    <ul>
      <li><strong>Name:</strong> {website_name}</li>
      <li><strong>URL:</strong> <a href="{url}">{url}</a></li>
    </ul>

    <p><strong>Error details:</strong> {error or "Unknown error"}</p>

    <p>
      Please check your website or server configuration.<br/>
      You can open your monitoring dashboard to see the latest status
      or temporarily disable this alert if needed.
    </p>

    <p style="margin-top:16px;">
      Thanks,<br/>
      <strong>Website Monitor</strong>
    </p>
  </body>
</html>
"""

    # ---------- Build email ----------
    msg = EmailMessage()
    msg["Subject"] = subject
    # From: nice display name + verified email
    msg["From"] = f"Website Monitor <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Reply-To"] = FROM_EMAIL

    # both text + html versions
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"📧 Down alert sent to {to_email} for {website_name}")
    except Exception as e:
        print("❌ Failed to send email:", repr(e))
