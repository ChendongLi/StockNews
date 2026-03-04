"""AI summary generation utilities."""

from __future__ import annotations

import json
import logging

import anthropic


def summarize_ticker_news(
    ticker: str,
    company_name: str,
    items: list[dict],
    api_key: str,
    model: str,
) -> str:
    """Generate a short investor-focused HTML summary for one ticker."""
    if not items:
        return "Could not fetch news for this ticker."
    if not api_key:
        return "AI summary unavailable because ANTHROPIC_API_KEY is not configured."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        headlines = "\n".join(
            f"- {it['title']}: {it['description'][:200]}" for it in items
        )
        prompt = f"""You are a sharp financial analyst. Based on these headlines for {company_name} ({ticker}):

{headlines}

Write a brief investor analysis in 3 parts (keep each part to 1-2 sentences max):
1. <strong>Key Theme:</strong> What's the main story
2. <strong>Why It Matters:</strong> Investment significance right now
3. <strong>Outlook:</strong> Bullish / Bearish / Neutral and the one-line reason

STRICT FORMATTING — HTML only, no markdown:
- Use <strong> for bold, <em> for italic, <br> for line breaks
- NO #, **, *, -, backticks, or markdown of any kind
- Do NOT wrap in <div> or <p> tags
- Total length: 80-120 words max. Be direct and specific."""
        response = client.messages.create(
            model=model,
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logging.error("AI summary failed for %s: %s", ticker, exc)
        return "AI summary unavailable."


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


def rank_news(
    items: list[dict],
    ticker: str,
    company_name: str,
    api_key: str,
    model: str,
) -> list[dict]:
    """Rank articles by financial impact and return top 3."""
    if len(items) < 3:
        return items
    if not api_key:
        return items[:3]

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
        prompt = f"""Rank these {ticker} ({company_name}) news items by financial importance/impact for investors.

Return only a JSON array of indices in ranked order, most important first.
No commentary, no markdown, no extra text.

Items:
{article_block}
"""
        response = client.messages.create(
            model=model,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end < start:
            raise ValueError("No JSON array found in ranking response")
        ranked_indices = json.loads(text[start : end + 1])
        if not isinstance(ranked_indices, list):
            raise ValueError("Ranking response is not a list")

        ranked_items: list[dict] = []
        for idx in ranked_indices:
            if isinstance(idx, int) and 0 <= idx < len(items):
                ranked_items.append(items[idx])
        if not ranked_items:
            raise ValueError("Ranking produced no valid indices")

        seen = {id(item) for item in ranked_items}
        for item in items:
            if id(item) not in seen:
                ranked_items.append(item)
                seen.add(id(item))

        return ranked_items[:3]
    except Exception as exc:
        logging.error("News ranking failed for %s: %s", ticker, exc)
        return items[:3]
