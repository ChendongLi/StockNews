"""News fetching utilities using Brave Search API."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/news/search"


def fetch_news(ticker: str, company_name: str, brave_api_key: str, limit: int = 5) -> list[dict]:
    """Fetch latest news for a ticker via Brave Search API.

    Uses freshness="pd" (past day) and returns up to ``limit`` items.
    """
    if ".TO" in ticker:
        query = "TSX stock market news"
    elif ticker == "QQQ":
        query = "US stock market OR Nasdaq OR S&P 500 breaking news OR technology stocks"
    else:
        query = f'"{company_name}" {ticker}'
    headers = {
        "X-Subscription-Token": brave_api_key,
        "Accept": "application/json",
    }

    try:
        resp = requests.get(
            BRAVE_SEARCH_URL,
            headers=headers,
            params={"q": query, "count": 5, "freshness": "pd", "country": "us"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

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
                    "extra_snippets": r.get("extra_snippets") or [],
                    "page_age": r.get("page_age"),
                }
            )

        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(hours=24)
        filtered: list[dict] = []
        for item in items:
            page_age = item.get("page_age")
            if not page_age:
                filtered.append(item)
                continue
            try:
                parsed = datetime.fromisoformat(page_age)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if parsed.astimezone(timezone.utc) >= cutoff:
                    filtered.append(item)
            except Exception:
                filtered.append(item)

        for item in filtered:
            item.pop("page_age", None)

        logging.info("%s: %s items (freshness=pd)", ticker, len(filtered))
        return filtered
    except Exception as exc:
        logging.error("%s fetch failed (freshness=pd): %s", ticker, exc)
        return []


def fetch_breaking_news(brave_api_key: str) -> list[dict]:
    """Fetch top 1 macro/market breaking news headline from the past 24h."""
    query = (
        "stock market breaking news OR S&P 500 OR Fed interest rate OR "
        "global economy OR Nasdaq OR recession OR inflation"
    )
    headers = {
        "X-Subscription-Token": brave_api_key,
        "Accept": "application/json",
    }
    try:
        resp = requests.get(
            BRAVE_SEARCH_URL,
            headers=headers,
            params={"q": query, "count": 5, "freshness": "pd", "country": "us"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(hours=24)
        items = []
        for r in results:
            page_age = r.get("page_age")
            if page_age:
                try:
                    parsed = datetime.fromisoformat(page_age)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    if parsed.astimezone(timezone.utc) < cutoff:
                        continue
                except Exception:
                    pass
            meta_url = r.get("meta_url") or {}
            items.append({
                "title": r.get("title", ""),
                "url": r.get("url", "#"),
                "description": r.get("description", ""),
                "published": (r.get("page_age") or r.get("age") or "")[:16],
                "source": meta_url.get("hostname", ""),
                "extra_snippets": r.get("extra_snippets") or [],
            })

        # AI-rank and return top 1
        logging.info("Breaking news: %s candidates", len(items))
        return items  # ranking + top-1 slicing done in app.py

    except Exception as exc:
        logging.error("Breaking news fetch failed: %s", exc)
        return []


def fetch_price_change(ticker):  # returns float or None
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
