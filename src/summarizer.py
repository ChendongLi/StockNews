"""AI summary generation utilities."""

from __future__ import annotations

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
