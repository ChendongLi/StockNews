# StockNews

StockNews fetches latest Yahoo Finance RSS headlines for configured tickers, generates concise AI summaries, and sends a styled daily email digest.

## Folder Structure

```text
.
├── docs/
│   └── architecture.md
├── src/
│   ├── app.py
│   ├── config.py
│   ├── emailer.py
│   ├── fetcher.py
│   ├── renderer.py
│   └── summarizer.py
├── .env.example
├── .gitignore
├── main.py
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create your local env file:
   ```bash
   cp .env.example .env
   ```
4. Fill in real credentials in `.env`.

## Environment Variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `GMAIL_USER` | Yes (non-test mode) | Gmail sender address | `your-email@gmail.com` |
| `GMAIL_APP_PASSWORD` | Yes (non-test mode) | Gmail app password | `your-app-password` |
| `RECIPIENTS` | Yes | Comma-separated recipient emails | `a@example.com,b@example.com` |
| `ANTHROPIC_API_KEY` | Recommended | Anthropic API key for summaries | `your-anthropic-api-key` |
| `ANTHROPIC_MODEL` | No | Anthropic model name | `claude-haiku-4-5-20251001` |
| `RSS_URL` | No | RSS URL template (`{ticker}` placeholder) | Yahoo Finance default |
| `SMTP_HOST` | No | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | No | SMTP server port | `465` |
| `LOG_FILE` | No | Log file path | `logs/stock_news.log` |

## Run

- Test mode (prints email body, no send):
  ```bash
  python main.py --test
  ```
- Normal mode (sends email):
  ```bash
  python main.py
  ```
