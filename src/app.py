"""Application orchestration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Sequence

from src.config import AppConfig, configure_logging
from src.dashboard import build_dashboard_html, upload_to_gcs
from src.emailer import send_email
from src.fetcher import fetch_breaking_news, fetch_market_indices, fetch_news, fetch_price_change, check_noon_trigger
from src.renderer import build_html
from src.summarizer import rank_breaking_news, rank_and_summarize

def validate_config(config: AppConfig, test_mode: bool) -> None:
    """Validate required settings before running."""
    if not config.recipients:
        raise ValueError("Set RECIPIENTS in .env (comma-separated emails).")
    if not test_mode and not config.agentmail_api_key:
        raise ValueError("Set AGENTMAIL_API_KEY in .env.")


def select_email_tickers(
    stocks: dict[str, dict],
    price_changes: dict,
    threshold_pct: float = EMAIL_PRICE_THRESHOLD,
    minimum: int = 3,
) -> list[str]:
    """Return tickers sorted by absolute price change, filtered to threshold.

    Always guarantees at least `minimum` tickers (top movers) even if none
    cross the threshold.
    """
    sorted_tickers = sorted(
        stocks,
        key=lambda t: abs((price_changes.get(t) or {}).get("change_pct") or 0),
        reverse=True,
    )
    above = [
        t for t in sorted_tickers
        if abs((price_changes.get(t) or {}).get("change_pct") or 0) >= threshold_pct
    ]
    return above if len(above) >= minimum else sorted_tickers[:minimum]


def run(argv: Sequence[str] | None = None) -> int:
    """Run the stock news workflow."""
    args = list(argv or [])
    test_mode = "--test" in args
    noon_mode = "--noon" in args
    no_ai = "--no-ai" in args

    config = AppConfig.from_env()
    configure_logging(config.log_file)
    validate_config(config, test_mode=test_mode)

    label = " [TEST]" if test_mode else (" [NOON]" if noon_mode else "")
    logging.info("Run started%s", label)

    if noon_mode:
        should_run, reason = check_noon_trigger(["^GSPC"])
        if not should_run:
            print(f"Noon trigger not met: {reason}")
            logging.info("Noon run skipped: %s", reason)
            return 0
        print(f"Noon trigger met: {reason}")

    if test_mode:
        # --test is used by CI's smoke test on every push/PR — never spend
        # real Brave Search quota just to verify the app runs end-to-end.
        print("Test mode: skipping Brave Search calls (breaking news + per-stock news)")
        breaking_news: list[dict] = []
        news_by_ticker: dict[str, list[dict]] = {ticker: [] for ticker in config.stocks}
    else:
        print("Fetching breaking news...")
        breaking_news = rank_breaking_news(
            items=fetch_breaking_news(config.brave_api_key, config.finnhub_api_key),
            api_key=config.anthropic_api_key,
            model=config.anthropic_model,
        )

        # Fetch news for ALL stocks (needed for dashboard + price filter)
        print(f"Fetching news for {len(config.stocks)} stocks...")
        news_by_ticker = {}
        for ticker, info in config.stocks.items():
            news_by_ticker[ticker] = fetch_news(
                ticker, info["name"], config.brave_api_key, config.finnhub_api_key
            )

    print("Fetching price changes...")
    price_changes = {ticker: fetch_price_change(ticker) for ticker in config.stocks}

    print("Fetching market indices...")
    market_indices = fetch_market_indices()

    # Determine which stocks appear in the email
    email_tickers = select_email_tickers(config.stocks, price_changes, threshold_pct=config.email_price_threshold)
    print(f"Email filter: {len(email_tickers)}/{len(config.stocks)} stocks qualify "
          f"(threshold ±{config.email_price_threshold}%, min 3)")

    # AI summaries only for email-qualifying stocks (cost gate)
    summaries: dict[str, str] = {}
    if no_ai:
        print("Skipping AI summaries (--no-ai)")
    else:
        print("Generating AI summaries...")
        for ticker in email_tickers:
            info = config.stocks[ticker]
            ranked_items, summary = rank_and_summarize(
                ticker=ticker,
                company_name=info["name"],
                items=news_by_ticker[ticker],
                api_key=config.anthropic_api_key,
                model=config.anthropic_model,
            )
            news_by_ticker[ticker] = ranked_items  # replace with ranked top-3
            summaries[ticker] = summary
            print(f"  {ticker} done")

    # Build static dashboard for ALL stocks
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    dashboard_html = build_dashboard_html(
        stocks=config.stocks,
        colors=config.colors,
        news_by_ticker=news_by_ticker,
        summaries=summaries,
        price_changes=price_changes,
        market_indices=market_indices,
        generated_at=generated_at,
    )

    # Upload dashboard to GCS (skipped if bucket not configured)
    dashboard_url = ""
    if config.gcs_bucket:
        try:
            dashboard_url = upload_to_gcs(dashboard_html, config.gcs_bucket, config.gcs_dashboard_path)
            print(f"Dashboard uploaded: {dashboard_url}")
        except Exception as exc:
            logging.error("GCS upload failed: %s", exc)
            print(f"GCS upload failed (continuing): {exc}")

    # Build email with filtered stock set
    html = build_html(
        stocks=config.stocks,
        colors=config.colors,
        news_by_ticker=news_by_ticker,
        summaries=summaries,
        price_changes=price_changes,
        breaking_news=breaking_news,
        market_indices=market_indices,
        email_tickers=email_tickers,
        dashboard_url=dashboard_url,
    )
    send_email(html, config=config, test_mode=test_mode)
    return 0
