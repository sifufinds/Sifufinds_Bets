"""
notify.py — minimal outbound email helper shared by scheduled agents.

agent_seo_backlinks.py has a Hostinger-SMTP send path (SMTP_HOST/SMTP_PORT/
SMTP_USER/SMTP_PASS), but as of 2026-07-13 those secrets do not actually
exist in this repo (confirmed via `gh secret list`) — using them here would
silently no-op every run. agent_email_outreach.py's Gmail path
(OUTREACH_EMAIL_USER/OUTREACH_EMAIL_PASS) DOES have real secrets configured,
so that is what this defaults to. SMTP_HOST/PORT/USER/PASS/FROM_NAME are
still honoured first if ever set, so this upgrades automatically without a
code change if proper SMTP secrets are added later.
"""
from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST") or "smtp.gmail.com"
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER") or os.getenv("OUTREACH_EMAIL_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS") or os.getenv("OUTREACH_EMAIL_PASS", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SifuFinds Team")


def send_email(to_addr: str, subject: str, body_text: str) -> bool:
    """Send a plain-text email via Hostinger SMTP.

    Returns True on success, False on any failure (including missing
    credentials) — never raises, so a notification problem never crashes
    the calling agent's actual job (adding/removing a brand still matters
    even if the email about it fails to send).
    """
    if not SMTP_USER or not SMTP_PASS:
        print("[notify] SMTP_USER/SMTP_PASS not configured — skipping email")
        return False
    try:
        msg = MIMEText(body_text, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        msg["To"] = to_addr

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
            server.starttls()
        with server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_addr], msg.as_string())
        print(f"[notify] Sent email to {to_addr}: {subject}")
        return True
    except Exception as e:
        print(f"[notify] Failed to send email: {e}")
        return False
