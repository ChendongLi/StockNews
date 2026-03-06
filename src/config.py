"""Configuration loading for StockNews."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_STOCKS: dict[str, dict] = {
    "QQQ": {"name": "Invesco QQQ ETF", "section": "US Market", "currency": "USD"},
    "NVDA": {"name": "Nvidia", "section": "US Tech", "currency": "USD"},
    "TSLA": {"name": "Tesla", "section": "US Tech", "currency": "USD"},
    "BABA": {"name": "Alibaba", "section": "Global Market", "currency": "USD"},
    "MSFT": {"name": "Microsoft", "section": "US Tech", "currency": "USD"},
    "BRK-B": {"name": "Berkshire Hathaway", "section": "US Market", "currency": "USD"},
}

DEFAULT_COLORS = {
    "QQQ": "#6366f1",
    "NVDA": "#22c55e",
    "TSLA": "#ef4444",
    "BABA": "#f97316",
    "MSFT": "#0ea5e9",
    "BRK-B": "#ca8a04",
}


@dataclass
class AppConfig:
    """Container for runtime configuration."""

    stocks: dict[str, dict]
    colors: dict[str, str]
    recipients: list[str]
    brave_api_key: str
    agentmail_api_key: str
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
            brave_api_key=os.getenv("BRAVE_API_KEY", "BSA5-CTjN2peswcv-cozXKUOUAKPbMZ"),
            agentmail_api_key=os.getenv("AGENTMAIL_API_KEY", ""),
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
