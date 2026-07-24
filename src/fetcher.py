"""News fetching utilities using Finnhub (primary) and Brave Search (fallback)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/news/search"
FINNHUB_COMPANY_NEWS_URL = "https://finnhub.io/api/v1/company-news"
FINNHUB_GENERAL_NEWS_URL = "https://finnhub.io/api/v1/news"


def _finnhub_filter_and_format(results: list[dict], limit: int) -> list[dict]:
    """Sort Finnhub articles by recency, apply the 24h cutoff, and map to our shape."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    items: list[dict] = []
    for r in sorted(results, key=lambda x: x.get("datetime", 0), reverse=True):
        ts = r.get("datetime")
        if not ts:
            continue
        published_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        if published_dt < cutoff:
            continue
        items.append(
            {
                "title": r.get("headline", ""),
                "url": r.get("url", "#"),
                "description": r.get("summary", ""),
                "published": published_dt.strftime("%Y-%m-%dT%H:%M"),
                "source": r.get("source", ""),
                "extra_snippets": [],
            }
        )
        if len(items) >= limit:
            break
    return items


def _fetch_news_finnhub(ticker: str, finnhub_api_key: str, limit: int) -> list[dict] | None:
    """Fetch company news from Finnhub. Returns None on failure/empty so the caller falls back to Brave.

    Finnhub's free tier only covers US-listed symbols — non-US tickers
    (e.g. ``2330.TW``, ``ASML.AS``, ``005930.KS``) return 403 and fall
    through to Brave automatically.
    """
    today = datetime.now(timezone.utc).date()
    frm = today - timedelta(days=2)
    try:
        resp = requests.get(
            FINNHUB_COMPANY_NEWS_URL,
            params={
                "symbol": ticker,
                "from": frm.isoformat(),
                "to": today.isoformat(),
                "token": finnhub_api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if not isinstance(results, list) or not results:
            return None
        return _finnhub_filter_and_format(results, limit) or None
    except Exception as exc:
        logging.warning("%s Finnhub company-news failed, falling back to Brave: %s", ticker, exc)
        return None


def _fetch_breaking_news_finnhub(finnhub_api_key: str, limit: int) -> list[dict] | None:
    """Fetch general market news from Finnhub. Returns None on failure/empty so the caller falls back to Brave."""
    try:
        resp = requests.get(
            FINNHUB_GENERAL_NEWS_URL,
            params={"category": "general", "token": finnhub_api_key},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if not isinstance(results, list) or not results:
            return None
        return _finnhub_filter_and_format(results, limit) or None
    except Exception as exc:
        logging.warning("Finnhub general news failed, falling back to Brave: %s", exc)
        return None


def fetch_news(
    ticker: str,
    company_name: str,
    brave_api_key: str,
    finnhub_api_key: str = "",
    limit: int = 1,
) -> list[dict]:
    """Fetch the top news item for a ticker, trying Finnhub before Brave Search.

    Requests 3 candidates (for freshness-filter headroom) and returns up to
    ``limit`` items after the 24-hour cutoff filter.
    """
    if finnhub_api_key:
        items = _fetch_news_finnhub(ticker, finnhub_api_key, limit=max(limit, 3))
        if items:
            logging.info("%s: %s items (finnhub)", ticker, len(items))
            return items[:limit]
    if ".TO" in ticker:
        query = "TSX stock market news"
    elif ".KS" in ticker:
        query = f'"{company_name}" semiconductor stock news'
    elif ".AS" in ticker:
        query = f'"{company_name}" stock news'
    elif ".TW" in ticker:
        query = f'"{company_name}" semiconductor stock news'
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
            params={"q": query, "count": 3, "freshness": "pd", "country": "us"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

        items = []
        for r in results:
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
        return filtered[:limit]
    except Exception as exc:
        logging.error("%s fetch failed (freshness=pd): %s", ticker, exc)
        return []


def fetch_breaking_news(brave_api_key: str, finnhub_api_key: str = "") -> list[dict]:
    """Fetch macro/market breaking news candidates from the past 24h, trying Finnhub before Brave Search."""
    if finnhub_api_key:
        items = _fetch_breaking_news_finnhub(finnhub_api_key, limit=5)
        if items:
            logging.info("Breaking news: %s candidates (finnhub)", len(items))
            return items

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


def fetch_market_indices() -> dict:
    """Fetch S&P 500, Nasdaq, and TSX Composite index change %.
    Returns dict like:
    {
        "sp500": {"label": "S&P 500", "change_pct": 0.83},
        "nasdaq": {"label": "Nasdaq", "change_pct": 1.12},
        "tsx": {"label": "TSX", "change_pct": -0.21},
    }
    Values are None on error.
    """
    import yfinance as yf

    indices = {
        "sp500": {"label": "S&P 500", "ticker": "^GSPC"},
        "nasdaq": {"label": "Nasdaq", "ticker": "^IXIC"},
        "tsx": {"label": "TSX", "ticker": "^GSPTSE"},
    }
    result = {}
    for key, meta in indices.items():
        try:
            info = yf.Ticker(meta["ticker"]).fast_info
            current = info.last_price
            prev = info.previous_close
            if current and prev:
                result[key] = {
                    "label": meta["label"],
                    "price": round(current, 2),
                    "change_pct": round((current - prev) / prev * 100, 2),
                }
            else:
                result[key] = {"label": meta["label"], "price": None, "change_pct": None}
        except Exception as exc:
            logging.error("%s index fetch failed: %s", meta["ticker"], exc)
            result[key] = {"label": meta["label"], "price": None, "change_pct": None}
    return result


def fetch_price_change(ticker) -> dict | None:
    """Return today's price and change % vs previous close.

    Returns dict with keys ``price`` and ``change_pct``, or None on error.
    """
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.fast_info
        current = info.last_price
        prev = info.previous_close
        if current and prev:
            return {
                "price": round(current, 2),
                "change_pct": round((current - prev) / prev * 100, 2),
            }
    except Exception as exc:
        logging.error("%s price change failed: %s", ticker, exc)
    return None


def fetch_price_vs_open(ticker: str) -> float | None:
    """Return today's price change % vs today's open price. Returns None on error."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.fast_info
        current = info.last_price
        open_price = info.open
        if current and open_price:
            return round((current - open_price) / open_price * 100, 2)
    except Exception as exc:
        logging.error("%s price vs open failed: %s", ticker, exc)
    return None


def check_noon_trigger(tickers: list[str], threshold_pct: float = 0.5) -> tuple[bool, str]:
    """Check if any ticker has moved > ±threshold_pct% from today's open.

    Returns (should_run, reason_message).
    """
    for ticker in tickers:
        change = fetch_price_vs_open(ticker)
        if change is not None and abs(change) > threshold_pct:
            direction = "+" if change > 0 else ""
            reason = f"{ticker} is {direction}{change:.2f}% vs open (threshold ±{threshold_pct}%)"
            logging.info("Noon trigger met: %s", reason)
            return True, reason
    reason = f"No ticker moved > ±{threshold_pct}% from open — skipping noon run"
    logging.info(reason)
    return False, reason
