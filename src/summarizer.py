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
        prompt = f"""You are a financial analyst. Based on these latest news headlines for {company_name} ({ticker}):

{headlines}

Write a concise investor-focused analysis covering:
1. What is the key theme across these news items
2. Why this matters to investors right now
3. Potential impact on the stock (bullish/bearish/neutral and why)

CRITICAL FORMATTING RULES — you must follow these exactly:
- Output ONLY valid HTML snippets. No markdown whatsoever.
- Use <strong> for bold text, <em> for italic text.
- Use <ul><li> for bullet points.
- Use <br> for line breaks.
- Do NOT use #, **, *, -, ```, or any markdown syntax.
- Do NOT use triple backticks or code blocks.
- Do NOT wrap the output in any outer tags like <div> or <p> — just the inline HTML content.
- Be specific, direct, and insightful. No fluff."""
        response = client.messages.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logging.error("AI summary failed for %s: %s", ticker, exc)
        return "AI summary unavailable."
