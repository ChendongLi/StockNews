"""Email sending utilities via AgentMail."""

from __future__ import annotations

import logging
from datetime import datetime

from agentmail import AgentMail


def send_email(html: str, config, test_mode: bool = False) -> None:
    """Send the HTML digest email via AgentMail, or print in test mode."""
    subject = f"Daily Stock News - {datetime.now().strftime('%b %d, %Y')}"

    if test_mode:
        print(f"To: {', '.join(config.recipients)}")
        print(f"Subject: {subject}\n")
        print(html)
        return

    client = AgentMail(api_key=config.agentmail_api_key)

    # Reuse existing inbox or create one if none exist
    existing = client.inboxes.list()
    if existing.inboxes:
        inbox_id = existing.inboxes[0].inbox_id
    else:
        inbox_id = client.inboxes.create().inbox_id

    for recipient in config.recipients:
        client.inboxes.messages.send(
            inbox_id,
            to=recipient,
            subject=subject,
            html=html,
        )

    logging.info("Sent to %s", config.recipients)
    print(f"Email sent to: {', '.join(config.recipients)}")
