"""AI summary generation utilities."""

from __future__ import annotations

import json  # used by rank_breaking_news
import logging

import anthropic


def rank_and_summarize(
    ticker: str,
    company_name: str,
    items: list[dict],
    api_key: str,
    model: str,
) -> tuple[list[dict], str]:
    """Summarize the top news item for a ticker in one Claude call.

    Returns ([top_item], summary_html).
    Falls back to (items[:1], "AI summary unavailable.") on any error.
    """
    if not items:
        return [], "No news today."
    if not api_key:
        return items[:1], "AI summary unavailable — ANTHROPIC_API_KEY not configured."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        item = items[0]

        prompt = f"""You are a sharp financial analyst. Given this {ticker} ({company_name}) news:

Title: {item['title']}
Description: {item['description'][:300]}

Write a concise investor analysis: 2-3 sentences, 40-60 words total. State what happened, the investment significance, and close with Bullish / Bearish / Neutral + one-line reason. Use <strong> for one key phrase only. No <div>, <p>, bullets, headers, or markdown — HTML inline tags only."""

        response = client.messages.create(
            model=model,
            max_tokens=180,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.content[0].text.strip()
        if not summary:
            raise ValueError("Empty response")
        return items[:1], summary

    except Exception as exc:
        logging.error("rank_and_summarize failed for %s: %s", ticker, exc)
        return items[:1], "AI summary unavailable."


def rank_breaking_news(items: list[dict], api_key: str, model: str) -> list[dict]:
    """Rank macro/market news by importance and return top 1."""
    if not items:
        return []
    if len(items) < 3:
        return items[:1]
    if not api_key:
        return items[:1]

    try:
        client = anthropic.Anthropic(api_key=api_key)
        lines = []
        for i, item in enumerate(items):
            snippets = item.get("extra_snippets") or []
            snippet_text = "\n".join(f"    - {s}" for s in snippets) if snippets else "    - (none)"
            lines.append(
                f"[{i}] Title: {item.get('title', '')}\n"
                f"    Description: {item.get('description', '')}\n"
                f"    Extra snippets:\n{snippet_text}"
            )
        article_block = "\n\n".join(lines)
        prompt = f"""Rank these macro/market news items by financial importance and market impact.

Return only a JSON array of indices in ranked order, most important first.
No commentary, no markdown, no extra text.

Items:
{article_block}
"""
        response = client.messages.create(
            model=model,
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found")
        ranked_indices = json.loads(text[start:end + 1])
        top_idx = ranked_indices[0]
        if isinstance(top_idx, int) and 0 <= top_idx < len(items):
            return [items[top_idx]]
        return items[:1]
    except Exception as exc:
        logging.error("Breaking news ranking failed: %s", exc)
        return items[:1]
