# StockNews 📈

A daily stock news emailer that fetches relevant headlines via **Brave Search**, generates concise **AI-powered analysis**, and delivers a clean HTML email every morning.

## What It Does

For each tracked stock, StockNews:
1. Searches Brave News API for the 3 most relevant recent headlines
2. Fetches real-time price change % vs previous close (via Yahoo Finance)
3. Generates a short AI analysis (key theme → why it matters → bullish/bearish outlook)
4. Sends a styled HTML email to all configured recipients

## Stocks Covered (7)

| Ticker | Name | Market |
|--------|------|--------|
| QQQ | Invesco QQQ ETF | US Market |
| NVDA | Nvidia | US Tech |
| TSLA | Tesla | US Tech |
| BABA | Alibaba | Global |
| MSFT | Microsoft | US Tech |
| BRK-B | Berkshire Hathaway | US Market |
| XIU.TO | iShares S&P/TSX 60 ETF | 🍁 Canadian Market (CAD) |

## Project Structure

```
StockNews/
├── src/
│   ├── app.py          # Orchestration — fetch, summarize, render, send
│   ├── config.py       # Stock list, colors, env var loading
│   ├── fetcher.py      # Brave Search API + yfinance price change
│   ├── summarizer.py   # Claude AI analysis (HTML output)
│   ├── renderer.py     # HTML email builder
│   └── emailer.py      # Gmail SMTP sender
├── docs/
│   └── architecture.md
├── main.py             # Entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

### 1. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `GMAIL_USER` | Yes | Gmail sender address |
| `GMAIL_APP_PASSWORD` | Yes | [Gmail App Password](https://myaccount.google.com/apppasswords) |
| `RECIPIENTS` | Yes | Comma-separated recipient emails |
| `ANTHROPIC_API_KEY` | Yes | [Anthropic API key](https://console.anthropic.com/settings/keys) for AI analysis |
| `BRAVE_API_KEY` | Yes | [Brave Search API key](https://api.search.brave.com) (free tier: 2,000 req/month) |
| `ANTHROPIC_MODEL` | No | Defaults to `claude-haiku-4-5-20251001` |
| `LOG_FILE` | No | Defaults to `logs/stock_news.log` |

## Usage

```bash
# Send live email
python main.py

# Test mode — prints HTML to stdout, no email sent
python main.py --test

# Skip AI analysis (faster, for debugging)
python main.py --no-ai
```

## Schedule Daily at 8 AM PT

Add this cron job (8 AM PT = 16:00 UTC):
```bash
0 16 * * * cd /Users/yourname/Projects/StockNews && /usr/bin/python3 main.py >> logs/stock_news.log 2>&1
```

## Email Design

- Dark gradient header with date and ticker list
- Per-stock section with:
  - Color-coded ticker badge
  - **Price change % pill** (green = up, red = down)
  - Currency label (USD or CAD)
  - AI analysis box (theme, significance, outlook)
  - Top 3 news links with source and description
- Powered by Brave Search + Claude AI
