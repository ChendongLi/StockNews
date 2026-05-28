"""Configuration loading for StockNews."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_stocks(path: str | Path = "stocks.yaml") -> tuple[dict, dict]:
    """Load stocks and colors from a YAML file.

    Returns (stocks_dict, colors_dict) where stocks_dict maps ticker →
    {name, section, currency} and colors_dict maps ticker → hex string.
    """
    data = yaml.safe_load(Path(path).read_text())
    stocks: dict[str, dict] = {}
    colors: dict[str, str] = {}
    for entry in data:
        ticker = entry["ticker"]
        stocks[ticker] = {
            "name": entry["name"],
            "section": entry["section"],
            "currency": entry.get("currency", "USD"),
        }
        if "color" in entry:
            colors[ticker] = entry["color"]
    return stocks, colors


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
    gcs_bucket: str = ""
    gcs_dashboard_path: str = "index.html"
    email_price_threshold: float = 1.0

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        recipients_raw = os.getenv("RECIPIENTS") or os.getenv("RECIPIENT_EMAIL", "")
        recipients = [item.strip() for item in recipients_raw.split(",") if item.strip()]

        stocks_path = os.getenv("STOCKS_CONFIG_PATH", "stocks.yaml")
        stocks, colors = load_stocks(stocks_path)

        try:
            threshold = float(os.getenv("EMAIL_PRICE_THRESHOLD", "1.0"))
        except ValueError:
            threshold = 1.0

        return cls(
            stocks=stocks,
            colors=colors,
            recipients=recipients,
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            agentmail_api_key=os.getenv("AGENTMAIL_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
            log_file=os.getenv("LOG_FILE", "logs/stock_news.log"),
            gcs_bucket=os.getenv("GCS_DASHBOARD_BUCKET", ""),
            gcs_dashboard_path=os.getenv("GCS_DASHBOARD_PATH", "index.html"),
            email_price_threshold=threshold,
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
