"""Application orchestration."""

from __future__ import annotations

import logging
from typing import Sequence

from src.config import AppConfig, configure_logging
from src.emailer import send_email
from src.fetcher import fetch_breaking_news, fetch_market_indices, fetch_news, fetch_price_change, check_noon_trigger
from src.renderer import build_html
from src.summarizer import rank_breaking_news, rank_news, summarize_ticker_news


def validate_config(config: AppConfig, test_mode: bool) -> None:
    """Validate required settings before running."""
    if not config.recipients:
        raise ValueError("Set RECIPIENTS in .env (comma-separated emails).")
    if not test_mode and not config.agentmail_api_key:
        raise ValueError("Set AGENTMAIL_API_KEY in .env.")


def run(argv: Sequence[str] | None = None) -> int:
    """Run the stock news workflow."""
    args = list(argv or [])
    test_mode = "--test" in args
    noon_mode = "--noon" in args

    config = AppConfig.from_env()
    configure_logging(config.log_file)
    validate_config(config, test_mode=test_mode)

    label = " [TEST]" if test_mode else (" [NOON]" if noon_mode else "")
    logging.info("Run started%s", label)

    # Noon trigger check: only run if S&P 500 moved > ±0.5% from open
    if noon_mode:
        should_run, reason = check_noon_trigger(["^GSPC"])
        if not should_run:
            print(f"Noon trigger not met: {reason}")
            logging.info("Noon run skipped: %s", reason)
            return 0
        print(f"Noon trigger met: {reason}")

    print("Fetching breaking news...")
    breaking_news = rank_breaking_news(
        items=fetch_breaking_news(config.brave_api_key),
        api_key=config.anthropic_api_key,
        model=config.anthropic_model,
    )

    news_by_ticker: dict[str, list[dict]] = {}
    for ticker, info in config.stocks.items():
        items = fetch_news(ticker, info["name"], config.brave_api_key)
        news_by_ticker[ticker] = rank_news(
            items=items,
            ticker=ticker,
            company_name=info["name"],
            api_key=config.anthropic_api_key,
            model=config.anthropic_model,
        )

    print("Fetching price changes...")
    price_changes = {
        ticker: fetch_price_change(ticker)
        for ticker in config.stocks
    }

    print("Fetching market indices...")
    market_indices = fetch_market_indices()

    no_ai = "--no-ai" in args
    summaries: dict[str, str] = {}
    if no_ai:
        print("Skipping AI summaries (--no-ai)")
    else:
        print("Generating AI summaries...")
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
        price_changes=price_changes,
        breaking_news=breaking_news,
        market_indices=market_indices,
    )
    send_email(html, config=config, test_mode=test_mode)
    return 0
