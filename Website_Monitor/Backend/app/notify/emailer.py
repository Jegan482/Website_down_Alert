# app/notify/emailer.py

import os
import ssl
import time
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Brevo SMTP defaults (or other SMTP provider)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# From address:
#  - best practice: domain-based sender, like alerts@jeganprojects.in
#  - set FROM_EMAIL in .env; otherwise fallback to SMTP_USER
FROM_EMAIL = os.getenv("FROM_EMAIL") or SMTP_USER


def _open_smtp():
    """Helper to open SMTP connection with STARTTLS and login."""
    context = ssl.create_default_context()
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    server.starttls(context=context)
    server.login(SMTP_USER, SMTP_PASS)
    return server


def _common_headers(msg: EmailMessage):
    """Add some common helpful headers for deliverability / clarity."""
    msg["Message-ID"] = make_msgid(domain=(FROM_EMAIL.split("@")[-1] if FROM_EMAIL and "@" in FROM_EMAIL else None))
    msg["Date"] = formatdate(localtime=True)
    # Optional: if you have an unsubscribe endpoint, uncomment and set appropriately
    # msg["List-Unsubscribe"] = "<mailto:alerts@yourdomain.example?subject=unsubscribe>, <https://yourdomain.example/unsubscribe>"
    # You can also add: msg["Precedence"] = "bulk"  # sometimes used for mailing lists


def send_down_alert(to_email: str, website_name: str, url: str, error: str | None = None):
    """
    Send a 'website down' alert using configured SMTP.

    Small improvements included:
      - hidden preheader for inbox preview
      - larger readable font and line-height
      - more descriptive plain-text body
      - Message-ID and Date headers
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

    # Subject (simple, not spammy)
    subject = f"[Website Monitor] {website_name} might be down"

    # Preheader (hidden preview text)
    preheader = f"Alert: {website_name} might be down — open dashboard for details."

    # Plain-text body (slightly more detailed)
    text_body = f"""Hi,

This is an automatic notification from your Website Monitor.

We could not reach your website:

  Name : {website_name}
  URL  : {url}

Error details: {error or 'Unknown error'}

Detected at: {time.strftime('%Y-%m-%d %H:%M:%S')}

Suggested next steps:
  1) Check server / hosting status
  2) Verify DNS & SSL
  3) Inspect recent deploys or config changes

Open your monitoring dashboard to see the latest status or disable this alert temporarily.

Thanks,
Website Monitor
"""

    # HTML body with bigger font + hidden preheader
    html_body = f"""\
<html>
  <body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#111827; font-size:16px; line-height:1.45;">
    <!-- Hidden preheader : shows in many inbox previews -->
    <div style="display:none; max-height:0; overflow:hidden; mso-hide:all;">
      {preheader}
    </div>

    <p>Hi,</p>

    <p>This is an automatic notification from <strong>Website Monitor</strong>.</p>

    <p>We could not reach your website:</p>

    <ul>
      <li><strong>Name:</strong> {website_name}</li>
      <li><strong>URL:</strong> <a href="{url}">{url}</a></li>
    </ul>

    <p><strong>Error details:</strong> {error or 'Unknown error'}</p>

    <p>
      <strong>Detected at:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}
    </p>

    <p>
      <strong>Suggested next steps:</strong><br/>
      1) Check server/hosting status<br/>
      2) Verify DNS and SSL certificates<br/>
      3) Check recent deployments or config changes
    </p>

    <hr style="margin:16px 0; border:none; border-top:1px solid #e5e7eb;"/>

    <p style="font-size:13px; color:#6b7280;">
      You are receiving this email because you enabled alerts for this site.
      If you no longer want alerts, remove the site from your monitoring dashboard.
    </p>

    <p style="margin-top:16px;">
      Thanks,<br/>
      <strong>Website Monitor</strong>
    </p>
  </body>
</html>
"""

    # Build email
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Website Monitor <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Reply-To"] = FROM_EMAIL
    _common_headers(msg)

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        server = _open_smtp()
        server.send_message(msg)
        server.quit()
        print(f"📧 Down alert sent to {to_email} for {website_name}")
    except Exception as e:
        print("❌ Failed to send email:", repr(e))


def send_ssl_expiry_alert(to_email: str, website_name: str, url: str, days_left: int):
    """
    SSL expiry alert email.
    days_left <= 0  → SSL expired
    days_left > 0   → SSL expiring soon
    """

    print("DEBUG SMTP CONFIG (SSL ALERT):")
    print("  HOST:", SMTP_HOST)
    print("  USER:", SMTP_USER)
    print("  FROM:", FROM_EMAIL)

    if not (SMTP_USER and SMTP_PASS):
        print("⚠️ SMTP credentials missing, cannot send SSL alert email.")
        return

    if not to_email:
        print("⚠️ No alert_email given, skipping SSL email.")
        return

    # Subject & status text
    if days_left <= 0:
        subject = f"[Website Monitor] SSL certificate EXPIRED for {website_name}"
        status_line = "The SSL certificate has EXPIRED."
    else:
        subject = f"[Website Monitor] SSL certificate expiring soon for {website_name}"
        status_line = f"The SSL certificate will expire in {days_left} day(s)."

    # Preheader
    preheader = f"SSL alert for {website_name}: {status_line}"

    # Plain-text body
    text_body = f"""Hi,

This is an automatic SSL expiry notification from your Website Monitor.

Website:
  Name : {website_name}
  URL  : {url}

Status:
  {status_line}

Detected at: {time.strftime('%Y-%m-%d %H:%M:%S')}

Please renew the SSL certificate as soon as possible to avoid browser security warnings.

Thanks,
Website Monitor
"""

    # HTML body
    html_body = f"""\
<html>
  <body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#111827; font-size:16px; line-height:1.45;">
    <div style="display:none; max-height:0; overflow:hidden; mso-hide:all;">
      {preheader}
    </div>

    <p>Hi,</p>

    <p>This is an automatic <strong>SSL expiry notification</strong> from your Website Monitor.</p>

    <p>Website details:</p>
    <ul>
      <li><strong>Name:</strong> {website_name}</li>
      <li><strong>URL:</strong> <a href="{url}">{url}</a></li>
    </ul>

    <p><strong>Status:</strong> {status_line}</p>

    <p><strong>Detected at:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>

    <p>
      Please renew the SSL certificate as soon as possible to avoid browser security warnings for your visitors.
    </p>

    <hr style="margin:16px 0; border:none; border-top:1px solid #e5e7eb;"/>

    <p style="font-size:13px; color:#6b7280;">
      You are receiving this email because you enabled alerts for this site.
      If you no longer want alerts, remove the site from your monitoring dashboard.
    </p>

    <p style="margin-top:16px;">
      Thanks,<br/>
      <strong>Website Monitor</strong>
    </p>
  </body>
</html>
"""

    # Build email
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Website Monitor <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Reply-To"] = FROM_EMAIL
    _common_headers(msg)

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        server = _open_smtp()
        server.send_message(msg)
        server.quit()
        print(f"📧 SSL expiry alert sent to {to_email} for {website_name} (days_left={days_left})")
    except Exception as e:
        print("❌ Failed to send SSL expiry email:", repr(e))
