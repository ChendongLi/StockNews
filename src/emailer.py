"""Email sending utilities."""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import AppConfig


def send_email(html: str, config: AppConfig, test_mode: bool = False) -> None:
    """Send the HTML digest email or print it in test mode."""
    subject = f"Daily Stock News - {datetime.now().strftime('%b %d, %Y')}"

    if test_mode:
        print(f"To: {', '.join(config.recipients)}")
        print(f"Subject: {subject}\n")
        print(html)
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = config.gmail_user
    message["To"] = ", ".join(config.recipients)
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port) as smtp:
        smtp.login(config.gmail_user, config.gmail_app_password)
        smtp.sendmail(config.gmail_user, config.recipients, message.as_string())

    logging.info("Sent to %s", config.recipients)
    print(f"Email sent to: {', '.join(config.recipients)}")

