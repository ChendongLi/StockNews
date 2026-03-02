"""Configuration loading for StockNews."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_STOCKS = {
    "QQQ": "Invesco QQQ ETF",
    "NVDA": "Nvidia",
    "TSLA": "Tesla",
    "BABA": "Alibaba",
}

DEFAULT_COLORS = {
    "QQQ": "#6366f1",
    "NVDA": "#22c55e",
    "TSLA": "#ef4444",
    "BABA": "#f97316",
}


@dataclass
class AppConfig:
    """Container for runtime configuration."""

    stocks: dict[str, str]
    colors: dict[str, str]
    recipients: list[str]
    rss_url: str
    smtp_host: str
    smtp_port: int
    gmail_user: str
    gmail_app_password: str
    anthropic_api_key: str
    anthropic_model: str
    log_file: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        recipients_raw = os.getenv("RECIPIENTS") or os.getenv("RECIPIENT_EMAIL", "")
        recipients = [item.strip() for item in recipients_raw.split(",") if item.strip()]

        return cls(
            stocks=DEFAULT_STOCKS,
            colors=DEFAULT_COLORS,
            recipients=recipients,
            rss_url=os.getenv(
                "RSS_URL",
                "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
            ),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            gmail_user=os.getenv("GMAIL_USER", ""),
            gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
            log_file=os.getenv("LOG_FILE", "logs/stock_news.log"),
        )


def configure_logging(log_file: str) -> None:
    """Initialize file logging."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

