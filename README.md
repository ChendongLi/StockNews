# ☕ Market Espresso

A daily market digest that fetches the top headline per stock via **Brave Search**, generates a concise **AI-powered paragraph**, and delivers a clean HTML email every weekday morning — fully automated on **GCP Cloud Run**.

A companion **static dashboard** (hosted on GCS) shows all tracked stocks grouped by sector with expand/collapse sections.

## What It Does

For each tracked stock, Market Espresso:
1. Fetches the top news headline from the past 24 hours (Brave Search API)
2. Fetches real-time price change % vs previous close (Yahoo Finance)
3. Generates a 40–60 word AI analysis paragraph (Bullish / Bearish / Neutral)
4. Sends a styled HTML email — only stocks that moved **±1%** or more appear (minimum 3 always included)
5. Uploads a full-sector dashboard to GCS for browsing all stocks

## Stocks Covered (21)

Configured in `stocks.yaml` at the repo root. **To add a stock: edit `stocks.yaml` and push — no code changes needed.**

### 🏆 Big Mega
| Ticker | Name |
|--------|------|
| AAPL | Apple |
| GOOGL | Alphabet |
| MSFT | Microsoft |
| TSLA | Tesla |
| NVDA | Nvidia |
| AMZN | Amazon |
| META | Meta |

### ⚡ Semiconductor
| Ticker | Name | Exchange |
|--------|------|----------|
| SMH | VanEck Semiconductor ETF | Nasdaq |
| 2330.TW | TSMC | Taiwan SE (TWD) |
| MU | Micron | Nasdaq |
| AMD | AMD | Nasdaq |
| INTC | Intel | Nasdaq |
| ASML.AS | ASML Holding | Amsterdam (EUR) |
| 005930.KS | Samsung Electronics | Korea SE (KRW) |
| SNDK | SanDisk | Nasdaq |
| LITE | Lumentum | Nasdaq |
| COHR | Coherent | NYSE |

### ☁️ SaaS Software
| Ticker | Name |
|--------|------|
| CRM | Salesforce |
| ADBE | Adobe |
| NOW | ServiceNow |
| WDAY | Workday |

## Project Structure

```
StockNews/
├── stocks.yaml          # Stock watchlist — edit here to add/remove stocks
├── src/
│   ├── app.py           # Orchestration — fetch, filter, summarize, render, send
│   ├── config.py        # Loads stocks.yaml + env vars into AppConfig
│   ├── fetcher.py       # Brave Search API + yfinance price data
│   ├── summarizer.py    # Claude AI analysis (single combined call per stock)
│   ├── renderer.py      # HTML email builder (sector-grouped, always visible)
│   ├── dashboard.py     # GCS static dashboard builder + uploader
│   └── emailer.py       # AgentMail sender
├── main.py              # Entry point
├── infra/
│   ├── job-morning.yaml # Cloud Run Job definition (morning run)
│   └── job-noon.yaml    # Cloud Run Job definition (noon conditional run)
├── cloudbuild.yaml      # Builds Docker image + deploys both Cloud Run Jobs
├── requirements.txt
└── .env.example
```

## Email Filter

The email only includes stocks that moved **±1%** or more vs the previous close. At least 3 stocks (the biggest movers) are always included even on quiet days.

All 21 stocks are fetched every run for the dashboard — Claude summarization is only called for stocks that make the email cut (cost gate).

## Run Schedule

| Run | Time (PT) | Days | Trigger condition |
|-----|-----------|------|-------------------|
| Morning | 8 AM | Mon–Fri | Always runs |
| Noon | 12 PM | Mon–Fri | Only if S&P 500 moved ±0.5% from open |

## Dashboard

A static HTML page is generated each run and uploaded to GCS:

```
https://storage.googleapis.com/market-espresso-dashboard/index.html
```

- All 21 stocks grouped by sector
- Click any sector header to collapse/expand
- Responsive card grid (mobile-friendly)
- Refreshes every time the morning or noon job runs

## Local Development

### 1. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in your API keys
```

### 3. Run locally

```bash
# Full run — sends live email and uploads dashboard
python main.py

# Test mode — prints HTML to stdout, no email sent, no GCS upload
python main.py --test

# Skip AI analysis (faster, for layout debugging)
python main.py --test --no-ai

# Noon conditional run — only proceeds if S&P 500 moved ±0.5% from open
python main.py --noon
```

## Deployment (GCP)

Runs as two **Cloud Run Jobs** on GCP (`agentlens-489006`, region: `us-west1`).

### Build & deploy
```bash
gcloud builds submit . --config=cloudbuild.yaml \
  --project=agentlens-489006 \
  --substitutions=COMMIT_SHA=$(git rev-parse HEAD)
```

Builds the Docker image, pushes to Artifact Registry, and updates both Cloud Run Jobs (`stocknews` and `stocknews-noon`) in one step.

### Environment variables (set in infra/job-*.yaml)

| Variable | Description |
|----------|-------------|
| `RECIPIENTS` | Comma-separated recipient emails |
| `GCS_DASHBOARD_BUCKET` | GCS bucket for dashboard upload (`market-espresso-dashboard`) |
| `GCS_DASHBOARD_PATH` | Object path within bucket (default: `index.html`) |

### Secrets (fetched from Secret Manager at runtime)

| Secret | Description |
|--------|-------------|
| `AGENTMAIL_API_KEY` | [AgentMail](https://agentmail.to) — email sending |
| `ANTHROPIC_API_KEY` | [Anthropic](https://console.anthropic.com/settings/keys) — Claude AI |
| `BRAVE_API_KEY` | [Brave Search](https://api.search.brave.com) — news headlines (free: 2,000 req/month) |

### GCS dashboard setup (one-time)
```bash
gsutil mb -p agentlens-489006 -l us-west1 gs://market-espresso-dashboard
gsutil uniformbucketlevelaccess set on gs://market-espresso-dashboard
gsutil iam ch allUsers:objectViewer gs://market-espresso-dashboard
gsutil iam ch serviceAccount:1056054306065-compute@developer.gserviceaccount.com:objectAdmin gs://market-espresso-dashboard
```

### Cloud Scheduler (one-time setup)
```bash
# Morning — always runs:
gcloud scheduler jobs create http stocknews-daily \
  --schedule="0 8 * * 1-5" --time-zone="America/Los_Angeles" \
  --uri="https://us-west1-run.googleapis.com/v2/projects/agentlens-489006/locations/us-west1/jobs/stocknews:run" \
  --http-method=POST --oauth-service-account-email=<SA_EMAIL> \
  --location=us-west1 --project=agentlens-489006

# Noon — triggers stocknews-noon job (--noon flag is baked in):
gcloud scheduler jobs create http stocknews-noon \
  --schedule="0 12 * * 1-5" --time-zone="America/Los_Angeles" \
  --uri="https://us-west1-run.googleapis.com/v2/projects/agentlens-489006/locations/us-west1/jobs/stocknews-noon:run" \
  --http-method=POST --oauth-service-account-email=<SA_EMAIL> \
  --location=us-west1 --project=agentlens-489006
```

### Check status & logs
```bash
# Recent executions
gcloud run jobs executions list --job=stocknews --region=us-west1

# Logs from an execution
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="stocknews"' \
  --project=agentlens-489006 --limit=50 --format="table(timestamp,textPayload)"
```

### Image cleanup
Artifact Registry auto-deletes images older than 2 days. Policy: `infra/cleanup-policy.json`.

```bash
gcloud artifacts repositories set-cleanup-policies voicebuddy \
  --project=agentlens-489006 --location=us-west1 \
  --policy=infra/cleanup-policy.json --no-dry-run
```

## PR Workflow

All changes go through pull requests — direct commits to `main` are not allowed.

1. Create a feature branch (`feat/`, `fix/`, `chore/` prefix)
2. Open a PR with description of what changed and how to test
3. CI smoke test must pass
4. Merge to `main` → manually trigger Cloud Build deploy
