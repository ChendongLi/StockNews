"""HTML rendering for the email digest."""

from __future__ import annotations

from datetime import datetime


def build_html(
    stocks: dict[str, dict],
    colors: dict[str, str],
    news_by_ticker: dict[str, list[dict]],
    summaries: dict[str, str],
    price_changes=None,
) -> str:
    """Build the HTML body for the stock digest email."""
    today = datetime.now().strftime("%B %d, %Y")
    sections = ""

    for ticker, info in stocks.items():
        name = info["name"]
        currency = info.get("currency", "USD")
        color = colors.get(ticker, "#334155")
        items = news_by_ticker.get(ticker, [])
        summary = summaries.get(ticker, "")

        change = (price_changes or {}).get(ticker)
        if change is not None:
            chg_color = "#16a34a" if change >= 0 else "#dc2626"
            chg_sign = "+" if change >= 0 else ""
            price_pill = (
                f'<span style="background:{chg_color}22;color:{chg_color};'
                f'padding:3px 9px;border-radius:10px;font-size:12px;'
                f'font-weight:700;margin-left:8px;vertical-align:middle">'
                f'{chg_sign}{change}%</span>'
            )
        else:
            price_pill = ""

        currency_label = (
            f'<span style="font-size:11px;font-weight:600;color:{color};'
            f'margin-left:6px;vertical-align:middle">{currency}</span>'
        )

        badge = (
            f'<span style="background:{color};color:#fff;padding:4px 12px;'
            f'border-radius:14px;font-size:13px;font-weight:700">{ticker}</span>'
        )

        summary_box = (
            f'<div style="background:#f8fafc;border-left:4px solid {color};'
            f'padding:14px 16px;border-radius:0 8px 8px 0;margin-bottom:18px;">'
            f'<p style="margin:0 0 4px;font-size:11px;font-weight:700;color:{color};'
            f'text-transform:uppercase;letter-spacing:.5px">AI Analysis</p>'
            f'<div style="margin:0;color:#1e293b;font-size:14px;line-height:1.6">{summary}</div>'
            f"</div>"
        ) if summary else ""

        if not items:
            rows = '<li style="color:#9ca3af;font-style:italic">No news available.</li>'
        else:
            rows = ""
            for item in items:
                desc = item.get("description", "")
                trimmed = f"{desc[:220]}..." if len(desc) > 220 else desc
                source = item.get("source", "")
                published = item.get("published", "")
                meta_parts = " &bull; ".join(filter(None, [source, published]))
                rows += (
                    '<li style="margin-bottom:16px;list-style:none;padding-left:0">'
                    f'<a href="{item["url"]}" style="color:#1d4ed8;font-weight:600;'
                    'font-size:14px;text-decoration:none;line-height:1.4">'
                    f'{item["title"]}</a>'
                    + (
                        f'<br><span style="color:#6b7280;font-size:11px">{meta_parts}</span>'
                        if meta_parts
                        else ""
                    )
                    + (
                        f'<br><span style="color:#4b5563;font-size:13px;line-height:1.5">{trimmed}</span>'
                        if trimmed
                        else ""
                    )
                    + "</li>"
                )

        sections += (
            '<div style="margin-bottom:36px;padding-bottom:28px;'
            'border-bottom:1px solid #f1f5f9">'
            f'<h2 style="margin:0 0 14px;font-size:19px;color:#0f172a">'
            f'{badge}{price_pill}{currency_label} &nbsp;{name}</h2>'
            f"{summary_box}"
            f'<ul style="padding:0;margin:0">{rows}</ul>'
            "</div>"
        )

    tickers = " · ".join(stocks.keys())
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
  background:#f1f5f9;margin:0;padding:24px 16px">
<div style="max-width:700px;margin:0 auto;background:#fff;border-radius:16px;
  box-shadow:0 4px 16px rgba(0,0,0,.10);overflow:hidden">
  <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);padding:32px 36px">
    <h1 style="color:#fff;margin:0;font-size:24px;letter-spacing:-.3px">Daily Stock News</h1>
    <p style="color:#94a3b8;margin:6px 0 0;font-size:14px">{today} &bull; {tickers}</p>
  </div>
  <div style="padding:36px">{sections}
    <p style="color:#9ca3af;font-size:11px;text-align:center;margin-top:8px">
      Powered by Brave Search and Claude AI
    </p>
  </div>
</div>
</body></html>"""
