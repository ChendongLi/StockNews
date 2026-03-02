"""Application orchestration."""

from __future__ import annotations

import logging
from typing import Sequence

from src.config import AppConfig, configure_logging
from src.emailer import send_email
from src.fetcher import fetch_news
from src.renderer import build_html
from src.summarizer import summarize_ticker_news


def validate_config(config: AppConfig, test_mode: bool) -> None:
    """Validate required settings before running."""
    if not config.recipients:
        raise ValueError("Set RECIPIENTS in .env (comma-separated emails).")
    if not test_mode and (not config.gmail_user or not config.gmail_app_password):
        raise ValueError("Set GMAIL_USER and GMAIL_APP_PASSWORD in .env.")


def run(argv: Sequence[str] | None = None) -> int:
    """Run the stock news workflow."""
    args = list(argv or [])
    test_mode = "--test" in args

    config = AppConfig.from_env()
    configure_logging(config.log_file)
    validate_config(config, test_mode=test_mode)
    logging.info("Run started%s", " [TEST]" if test_mode else "")

    news_by_ticker = {
        ticker: fetch_news(ticker, info["name"], config.brave_api_key)
        for ticker, info in config.stocks.items()
    }

    print("Generating AI summaries...")
    summaries: dict[str, str] = {}
    for ticker, info in config.stocks.items():
        summaries[ticker] = summarize_ticker_news(
            ticker=ticker,
            company_name=info["name"],
            items=news_by_ticker[ticker],
            api_key=config.anthropic_api_key,
            model=config.anthropic_model,
        )
        print(f"  {ticker} complete")

    html = build_html(
        stocks=config.stocks,
        colors=config.colors,
        news_by_ticker=news_by_ticker,
        summaries=summaries,
    )
    send_email(html, config=config, test_mode=test_mode)
    return 0
