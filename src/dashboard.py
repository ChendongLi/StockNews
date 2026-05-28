"""Static dashboard HTML generation and GCS upload."""

from __future__ import annotations

import logging

from src.renderer import SECTION_ORDER, _render_index_scoreboard

SECTION_LABELS = {
    "Big Mega": ("🏆", "#1a0c08"),
    "Semiconductor": ("⚡", "#1e1b4b"),
    "SaaS Software": ("☁️", "#022c22"),
}


def _render_card(
    ticker: str,
    info: dict,
    color: str,
    items: list[dict],
    summary: str,
    price_data: dict | None,
) -> str:
    """Render one stock card for the dashboard."""
    name = info["name"]
    currency = info.get("currency", "USD")
    section = info.get("section", "")
    is_etf = "ETF" in name

    if price_data is not None:
        chg = price_data.get("change_pct")
        px = price_data.get("price")
        chg_color = "#16a34a" if (chg or 0) >= 0 else "#dc2626"
        chg_sign = "+" if (chg or 0) >= 0 else ""
        px_str = f"{px:,.2f}" if px is not None else ""
        price_block = (
            f'<div style="margin-top:4px">'
            f'<span style="font-size:15px;font-weight:700;color:#0f172a">{px_str}</span>'
            f'<span style="font-size:11px;color:#64748b;margin-left:3px">{currency}</span>'
            f'<span style="margin-left:8px;background:{chg_color}18;color:{chg_color};'
            f'padding:2px 8px;border-radius:8px;font-size:12px;font-weight:700">'
            f'{chg_sign}{chg}%</span>'
            f'</div>'
        )
    else:
        price_block = '<div style="margin-top:4px;font-size:12px;color:#94a3b8">Price unavailable</div>'

    etf_label = (
        f'<span style="font-size:10px;font-weight:700;color:{color};'
        f'border:1px solid {color};padding:1px 6px;border-radius:4px;margin-left:6px;'
        f'vertical-align:middle">ETF</span>'
    ) if is_etf else ""

    summary_block = (
        f'<div style="background:#f8fafc;border-left:3px solid {color};'
        f'padding:10px 12px;border-radius:0 6px 6px 0;margin:12px 0;'
        f'font-size:13px;color:#1e293b;line-height:1.55">{summary}</div>'
    ) if summary else (
        '<div style="color:#94a3b8;font-size:12px;font-style:italic;margin:12px 0">'
        'No AI analysis — price unchanged</div>'
    )

    if not items:
        news_html = '<p style="color:#9ca3af;font-size:12px;font-style:italic">No news today.</p>'
    else:
        news_html = ""
        for item in items[:3]:
            source = item.get("source", "")
            published = item.get("published", "")
            meta = " · ".join(filter(None, [source, published]))
            news_html += (
                f'<div style="margin-bottom:10px">'
                f'<a href="{item["url"]}" style="color:#1d4ed8;font-size:13px;'
                f'font-weight:600;text-decoration:none;line-height:1.35">{item["title"]}</a>'
                + (f'<div style="color:#94a3b8;font-size:11px;margin-top:2px">{meta}</div>' if meta else "")
                + f'</div>'
            )

    return (
        f'<div class="card" style="background:#fff;border:1px solid #e2e8f0;'
        f'border-radius:12px;padding:18px;border-top:3px solid {color}">'
        f'<div style="display:flex;align-items:center;justify-content:space-between">'
        f'<div>'
        f'<span style="background:{color};color:#fff;padding:3px 10px;'
        f'border-radius:10px;font-size:12px;font-weight:700">{ticker}</span>{etf_label}'
        f'<div style="font-size:14px;font-weight:600;color:#0f172a;margin-top:6px">{name}</div>'
        f'{price_block}'
        f'</div>'
        f'</div>'
        f'{summary_block}'
        f'<div style="border-top:1px solid #f1f5f9;padding-top:10px">{news_html}</div>'
        f'</div>'
    )


def build_dashboard_html(
    stocks: dict[str, dict],
    colors: dict[str, str],
    news_by_ticker: dict[str, list[dict]],
    summaries: dict[str, str],
    price_changes: dict | None,
    market_indices: dict | None,
    generated_at: str,
) -> str:
    """Build the full sector-grouped static dashboard HTML."""

    sections_html = ""
    for section_name in SECTION_ORDER:
        tickers = [t for t, info in stocks.items() if info.get("section") == section_name]
        if not tickers:
            continue

        icon, header_bg = SECTION_LABELS.get(section_name, ("📊", "#0f172a"))

        cards = ""
        for ticker in tickers:
            info = stocks[ticker]
            cards += _render_card(
                ticker=ticker,
                info=info,
                color=colors.get(ticker, "#334155"),
                items=news_by_ticker.get(ticker, []),
                summary=summaries.get(ticker, ""),
                price_data=(price_changes or {}).get(ticker),
            )

        sections_html += (
            f'<section style="margin-bottom:48px">'
            f'<div style="background:{header_bg};color:#fff;'
            f'padding:12px 20px;border-radius:10px;margin-bottom:20px;'
            f'display:flex;align-items:center;gap:10px">'
            f'<span style="font-size:18px">{icon}</span>'
            f'<span style="font-size:17px;font-weight:700">{section_name}</span>'
            f'<span style="font-size:12px;color:rgba(255,255,255,0.6);margin-left:auto">'
            f'{len(tickers)} stocks</span>'
            f'</div>'
            f'<div class="grid">{cards}</div>'
            f'</section>'
        )

    scoreboard = _render_index_scoreboard(market_indices)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Espresso — Full Dashboard</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
    background:#f1f5f9;min-height:100vh}}
  .container{{max-width:1100px;margin:0 auto;padding:24px 16px}}
  .grid{{display:grid;grid-template-columns:1fr;gap:14px}}
  @media(min-width:580px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
  @media(min-width:900px){{.grid{{grid-template-columns:repeat(3,1fr)}}}}
  .card{{transition:box-shadow .15s}}
  .card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.10)}}
</style>
</head>
<body>
<div style="background:linear-gradient(135deg,#1a0c08 0%,#3b1a0e 100%);padding:32px 0">
  <div style="max-width:1100px;margin:0 auto;padding:0 16px">
    <h1 style="color:#fff;font-size:28px;letter-spacing:-.3px">☕ Market Espresso</h1>
    <p style="color:#c4a882;margin:6px 0 0;font-size:13px">Full Dashboard · All Sectors</p>
    {scoreboard}
  </div>
</div>
<div class="container">
  <div style="padding:20px 0 8px">{sections_html}</div>
  <p style="color:#94a3b8;font-size:11px;text-align:center;padding:16px 0 8px">
    Generated {generated_at} UTC · Updates at 8 AM and noon ET ·
    Powered by Brave Search and Claude AI
  </p>
</div>
</body>
</html>"""


def upload_to_gcs(html: str, bucket_name: str, object_path: str) -> str:
    """Upload HTML string to GCS as a public static page. Returns the public URL."""
    from google.cloud import storage  # lazy import — not needed in all environments

    client = storage.Client()
    blob = client.bucket(bucket_name).blob(object_path)
    blob.upload_from_string(html.encode("utf-8"), content_type="text/html")
    blob.cache_control = "no-cache, max-age=0"
    blob.patch()
    logging.info("Dashboard uploaded to gs://%s/%s", bucket_name, object_path)
    return f"https://storage.googleapis.com/{bucket_name}/{object_path}"
