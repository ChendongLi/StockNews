"""News fetching utilities using Brave Search API."""

from __future__ import annotations

import logging

import requests

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/news/search"


def fetch_news(ticker: str, company_name: str, brave_api_key: str, limit: int = 3) -> list[dict]:
    """Fetch latest news for a ticker via Brave Search API.

    Tries freshness="pd" (past day) first; falls back to "pw" (past week)
    if fewer than 3 results are returned.
    """
    # For Canadian/ETF tickers, use simplified search terms
    clean_ticker = ticker.replace(".TO", "")
    if ".TO" in ticker:
        query = f'"TSX 60" OR "S&P TSX" OR "Canadian stock market" OR "iShares XIU"'
    elif "-" in ticker:
        # e.g. BRK-B → search by company name
        query = f'"{company_name} stock news" OR "{company_name} stock"'
    else:
        query = f'"{company_name} stock news" OR "{clean_ticker} stock"'
    headers = {
        "X-Subscription-Token": brave_api_key,
        "Accept": "application/json",
    }

    for freshness in ("pd", "pw"):
        try:
            resp = requests.get(
                BRAVE_SEARCH_URL,
                headers=headers,
                params={"q": query, "count": 5, "freshness": freshness, "country": "us"},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

            if len(results) >= 3 or freshness == "pw":
                items = []
                for r in results[:limit]:
                    meta_url = r.get("meta_url") or {}
                    items.append(
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", "#"),
                            "description": r.get("description", ""),
                            "published": (r.get("page_age") or r.get("age") or "")[:16],
                            "source": meta_url.get("hostname", ""),
                        }
                    )
                logging.info("%s: %s items (freshness=%s)", ticker, len(items), freshness)
                return items

        except Exception as exc:
            logging.error("%s fetch failed (freshness=%s): %s", ticker, freshness, exc)

    return []


def fetch_price_change(ticker: str) -> float | None:
    """Return today's price change % vs previous close. Returns None on error."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.fast_info
        current = info.last_price
        prev = info.previous_close
        if current and prev:
            return round((current - prev) / prev * 100, 2)
    except Exception as exc:
        logging.error("%s price change failed: %s", ticker, exc)
    return None
