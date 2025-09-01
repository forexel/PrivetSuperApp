from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings


def send_email(to: str, subject: str, body: str) -> bool:
    host: Optional[str] = settings.SMTP_HOST
    port: Optional[int] = settings.SMTP_PORT
    user: Optional[str] = settings.SMTP_USER
    password: Optional[str] = settings.SMTP_PASSWORD
    use_tls: bool = bool(settings.SMTP_TLS)
    sender: str = settings.SMTP_FROM or (user or "no-reply@example.com")

    if not host or not port:
        # SMTP not configured; treat as no-op success to avoid leaking presence
        return False

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if use_tls:
                try:
                    smtp.starttls()
                except smtplib.SMTPException:
                    # continue even if STARTTLS not supported
                    pass
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception:
        # swallow errors to keep API behavior uniform
        return False

