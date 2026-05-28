"""HTML rendering for the email digest."""

from __future__ import annotations

from datetime import datetime

SECTION_ORDER = ["Big Mega", "Semiconductor", "SaaS Software"]


def _render_index_scoreboard(market_indices: dict | None) -> str:
    """Render a scoreboard strip for market indices in the email header."""
    if not market_indices:
        return ""

    cells = []
    items = list(market_indices.items())
    for i, (_key, data) in enumerate(items):
        label = data.get("label", "")
        pct = data.get("change_pct")
        price = data.get("price")

        if pct is not None:
            color = "#4ade80" if pct >= 0 else "#f87171"
            sign = "+" if pct >= 0 else ""
            arrow = "▲" if pct >= 0 else "▼"
            pct_str = f"{arrow} {sign}{pct}%"
        else:
            color = "#94a3b8"
            pct_str = "N/A"

        price_str = f"{price:,.2f}" if price is not None else ""

        sep = (
            '<td style="width:1px;background:rgba(255,255,255,0.15);padding:0 0"></td>'
            if i < len(items) - 1 else ""
        )

        cells.append(
            f'<td style="padding:14px 28px;text-align:center;width:50%">'
            f'<div style="font-size:11px;font-weight:700;color:#c4a882;'
            f'text-transform:uppercase;letter-spacing:1.2px;margin-bottom:4px">{label}</div>'
            f'<div style="font-family:Georgia,\'Times New Roman\',serif;font-size:22px;'
            f'font-weight:700;color:#fff;letter-spacing:-.3px">{price_str}</div>'
            f'<div style="font-family:Georgia,\'Times New Roman\',serif;font-size:15px;'
            f'font-weight:700;color:{color};margin-top:2px">{pct_str}</div>'
            f'</td>'
            + sep
        )

    return (
        '<table style="width:100%;border-collapse:collapse;margin-top:20px;'
        'background:rgba(0,0,0,0.25);border-radius:10px;overflow:hidden">'
        f'<tr>{"".join(cells)}</tr>'
        '</table>'
    )


def _render_stock_section(
    ticker: str,
    info: dict,
    color: str,
    items: list[dict],
    summary: str,
    price_data: dict | None,
) -> str:
    """Render one stock section (badge, price pill, summary box, news list)."""
    currency = info.get("currency", "USD")

    if price_data is not None:
        chg = price_data.get("change_pct")
        px = price_data.get("price")
        chg_color = "#16a34a" if (chg or 0) >= 0 else "#dc2626"
        chg_sign = "+" if (chg or 0) >= 0 else ""
        px_str = f"{px:,.2f} &nbsp;" if px is not None else ""
        price_pill = (
            f'<span style="background:{chg_color}22;color:{chg_color};'
            f'padding:3px 9px;border-radius:10px;font-size:12px;'
            f'font-weight:700;margin-left:8px;vertical-align:middle;'
            f'font-family:Georgia,serif">'
            f'{px_str}{chg_sign}{chg}%</span>'
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
        rows = '<li style="color:#9ca3af;font-style:italic">No news today.</li>'
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
                    if meta_parts else ""
                )
                + (
                    f'<br><span style="color:#4b5563;font-size:13px;line-height:1.5">{trimmed}</span>'
                    if trimmed else ""
                )
                + "</li>"
            )

    name = info["name"]
    return (
        '<div style="margin-bottom:36px;padding-bottom:28px;border-bottom:1px solid #f1f5f9">'
        f'<h2 style="margin:0 0 14px;font-size:19px;color:#0f172a">'
        f'{badge}{price_pill}{currency_label} &nbsp;{name}</h2>'
        f"{summary_box}"
        f'<ul style="padding:0;margin:0">{rows}</ul>'
        "</div>"
    )


def build_html(
    stocks: dict[str, dict],
    colors: dict[str, str],
    news_by_ticker: dict[str, list[dict]],
    summaries: dict[str, str],
    price_changes=None,
    breaking_news: list[dict] | None = None,
    market_indices: dict | None = None,
    email_tickers: list[str] | None = None,
    dashboard_url: str = "",
) -> str:
    """Build the HTML body for the stock digest email.

    email_tickers controls which stocks appear and in what order.
    When None, all stocks are shown (legacy behaviour).
    """
    today = datetime.now().strftime("%B %d, %Y")
    tickers_to_show = email_tickers if email_tickers is not None else list(stocks.keys())

    # Breaking news banner
    breaking_section = ""
    if breaking_news:
        item = breaking_news[0]
        source = item.get("source", "")
        published = item.get("published", "")
        meta = " &bull; ".join(filter(None, [source, published]))
        breaking_section = (
            '<div style="background:#fef2f2;border-left:5px solid #dc2626;'
            'padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:28px">'
            '<p style="margin:0 0 6px;font-size:11px;font-weight:800;color:#dc2626;'
            'text-transform:uppercase;letter-spacing:.8px">🔴 Breaking News</p>'
            f'<a href="{item["url"]}" style="color:#1d4ed8;font-weight:700;font-size:15px;'
            f'text-decoration:none;line-height:1.4">{item["title"]}</a>'
            + (f'<br><span style="color:#6b7280;font-size:11px">{meta}</span>' if meta else "")
            + (
                f'<br><span style="color:#4b5563;font-size:13px;line-height:1.5">'
                f'{item["description"][:280]}</span>'
                if item.get("description") else ""
            )
            + '</div>'
        )

    # Group tickers by section, preserving email_tickers order within each group
    grouped: dict[str, list[str]] = {s: [] for s in SECTION_ORDER}
    for ticker in tickers_to_show:
        section = stocks.get(ticker, {}).get("section", "Big Mega")
        if section not in grouped:
            grouped[section] = []
        grouped[section].append(ticker)

    sections_html = ""
    for section_idx, section_name in enumerate(SECTION_ORDER):
        tickers_in_section = grouped.get(section_name, [])
        if not tickers_in_section:
            continue

        stock_blocks = ""
        for ticker in tickers_in_section:
            info = stocks.get(ticker, {})
            stock_blocks += _render_stock_section(
                ticker=ticker,
                info=info,
                color=colors.get(ticker, "#334155"),
                items=news_by_ticker.get(ticker, []),
                summary=summaries.get(ticker, ""),
                price_data=(price_changes or {}).get(ticker),
            )

        count_label = (
            f'<span style="font-size:12px;font-weight:400;color:#64748b;margin-left:8px">'
            f'{len(tickers_in_section)} stock{"s" if len(tickers_in_section) != 1 else ""} today</span>'
        )

        # Big Mega starts open; other sections start collapsed
        open_attr = " open" if section_idx == 0 else ""
        arrow_open = "▼"
        arrow_closed = "▶"
        # Use CSS to flip the arrow based on open state — inline fallback for Gmail
        summary_style = (
            "cursor:pointer;list-style:none;padding:14px 0 10px;"
            "font-size:15px;font-weight:700;color:#0f172a;"
            "border-bottom:2px solid #e2e8f0;margin-bottom:20px;"
            "display:flex;align-items:center"
        )

        sections_html += (
            f'<details{open_attr} style="margin-bottom:8px">'
            f'<summary style="{summary_style}">'
            f'<span style="margin-right:8px">{arrow_open if section_idx == 0 else arrow_closed}</span>'
            f'{section_name}{count_label}'
            f'</summary>'
            f'<div style="padding-top:4px">{stock_blocks}</div>'
            f'</details>'
        )

    # Dashboard CTA button
    dashboard_cta = ""
    if dashboard_url:
        dashboard_cta = (
            '<div style="text-align:center;margin:28px 0 12px">'
            f'<a href="{dashboard_url}" style="background:#1a0c08;color:#c4a882;'
            'padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;'
            'text-decoration:none;display:inline-block;letter-spacing:.3px">'
            'View Full Dashboard →</a>'
            '</div>'
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
details summary::-webkit-details-marker {{ display:none; }}
details[open] summary span:first-child {{ content:"▼"; }}
</style>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
  background:#f1f5f9;margin:0;padding:24px 16px">
<div style="max-width:700px;margin:0 auto;background:#fff;border-radius:16px;
  box-shadow:0 4px 16px rgba(0,0,0,.10);overflow:hidden">
  <div style="background:linear-gradient(135deg,#1a0c08 0%,#3b1a0e 100%);padding:32px 36px">
    <h1 style="color:#fff;margin:0;font-size:26px;letter-spacing:-.3px">☕ Market Espresso</h1>
    <p style="color:#c4a882;margin:6px 0 0;font-size:13px;letter-spacing:.3px">{today}</p>
    {_render_index_scoreboard(market_indices)}
  </div>
  <div style="padding:36px">{breaking_section}{sections_html}
    {dashboard_cta}
    <p style="color:#9ca3af;font-size:11px;text-align:center;margin-top:8px">
      Powered by Brave Search and Claude AI
    </p>
  </div>
</div>
</body></html>"""
