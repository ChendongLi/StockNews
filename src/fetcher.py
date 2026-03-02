"""News fetching utilities."""

from __future__ import annotations

import logging

import feedparser


def fetch_news(ticker: str, rss_url_template: str, limit: int = 5) -> list[dict[str, str]]:
    """Fetch the latest RSS news items for a ticker."""
    try:
        feed = feedparser.parse(rss_url_template.format(ticker=ticker))
        items: list[dict[str, str]] = []
        for entry in feed.entries[:limit]:
            items.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", "#"),
                    "published": entry.get("published", "")[:16],
                    "summary": entry.get("summary", ""),
                }
            )
        logging.info("%s: %s items", ticker, len(items))
        return items
    except Exception as exc:
        logging.error("%s failed: %s", ticker, exc)
        return []

