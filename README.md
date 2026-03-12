# ☕ Market Espresso

A daily market digest that fetches relevant headlines via **Brave Search**, generates concise **AI-powered analysis**, and delivers a clean HTML email every weekday morning — fully automated via **GitHub Actions** (no local server needed).

## What It Does

For each tracked stock, StockNews:
1. Searches Brave News API for the 3 most relevant recent headlines
2. Fetches real-time price change % vs previous close (via Yahoo Finance)
3. Generates a short AI analysis (key theme → why it matters → bullish/bearish outlook)
4. Sends a styled HTML email to all configured recipients

## Stocks Covered (6)

| Ticker | Name | Market |
|--------|------|--------|
| QQQ | Invesco QQQ ETF | US Market |
| NVDA | Nvidia | US Tech |
| TSLA | Tesla | US Tech |
| BABA | Alibaba | Global Market |
| MSFT | Microsoft | US Tech |
| BRK-B | Berkshire Hathaway | US Market |

## Project Structure

```
StockNews/
├── .github/
│   └── workflows/
│       ├── ci.yml       # Runs on every push/PR — smoke test
│       └── deploy.yml   # CD to Cloud Run (GCP auth TODO)
├── src/
│   ├── app.py           # Orchestration — fetch, summarize, render, send
│   ├── config.py        # Stock list, colors, env var loading
│   ├── fetcher.py       # Brave Search API + yfinance price change
│   ├── summarizer.py    # Claude AI analysis (HTML output)
│   ├── renderer.py      # HTML email builder
│   └── emailer.py       # AgentMail sender
├── main.py              # Entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

## Run Schedule

The daily job is triggered by **GCP Cloud Scheduler** (not GitHub Actions). GitHub Actions handles CI and CD only — see `ci.yml` and `deploy.yml`.

| Run | Time | Flag | Trigger |
|-----|------|------|---------|
| Morning | 8 AM PT Mon–Fri | _(none)_ | Always runs (Cloud Scheduler) |
| Noon | 12 PM PT Mon–Fri | `--noon` | Only if S&P 500 moved ±0.5% from open |

The noon run saves API cost on quiet market days by checking `^GSPC` current vs open price before doing anything else.

## CI/CD (GitHub Actions)

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | Push / PR to `main` | Installs deps, runs `--test --no-ai` smoke test |
| `deploy.yml` | Push to `main` (CD not yet wired) | Build & deploy to Cloud Run via `cloudbuild.yaml` — GCP auth TODO |

### GitHub Secrets (stored encrypted, never in code)

| Secret | Description |
|--------|-------------|
| `AGENTMAIL_API_KEY` | [AgentMail API key](https://agentmail.to) — used for sending email |
| `RECIPIENTS` | Comma-separated recipient emails |
| `ANTHROPIC_API_KEY` | [Anthropic API key](https://console.anthropic.com/settings/keys) |
| `BRAVE_API_KEY` | [Brave Search API key](https://api.search.brave.com) (free tier: 2,000 req/month) |

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
# Fill in your credentials
```

### 3. Run locally

```bash
# Send live email
python main.py

# Test mode — renders HTML to stdout, no email sent
python main.py --test

# Skip AI analysis (faster, for debugging)
python main.py --no-ai

# Noon conditional run — only sends if S&P 500 moved ±0.5% from open
python main.py --noon
```

## Email Design

- **Espresso brown header** (`#1a0c08 → #3b1a0e`) with `☕ Market Espresso` title
- **Index scoreboard**: S&P 500 and TSX shown with current price + ▲/▼ change % in Georgia serif
- Per-stock section with:
  - Color-coded ticker badge + **current price and change % pill** (🟢 up / 🔴 down)
  - Currency label (USD or CAD)
  - AI analysis box: theme, significance, outlook (~100 words)
  - Top 3 news links with source, date, and description
- Subject line: `☕ Market Espresso — Mar 06, 2026`
- Powered by Brave Search + Claude AI

## Deployment (GCP)

Runs as a **Cloud Run Job** on GCP (`agentlens-489006`, region: `us-west1`).

### Build & deploy
```bash
gcloud builds submit --config cloudbuild.yaml . \
  --project=agentlens-489006 \
  --substitutions=COMMIT_SHA=$(git rev-parse HEAD)
```
This builds the Docker image, pushes it to Artifact Registry, and updates the Cloud Run Job in one step.
`COMMIT_SHA` must be passed explicitly for manual submits — it's only auto-set when triggered from a GitHub push.

### Cloud Run Jobs (one-time setup)

Two separate Cloud Run Jobs are required — one for the morning run (no args) and one for the noon run (`--noon`). `cloudbuild.yaml` updates both jobs on every deploy.

```bash
# Morning job (created automatically by first deploy, or manually):
gcloud run jobs create stocknews \
  --image=us-west1-docker.pkg.dev/agentlens-489006/voicebuddy/stocknews:latest \
  --region=us-west1 --project=agentlens-489006

# Noon job — must be created separately with --noon arg:
gcloud run jobs create stocknews-noon \
  --image=us-west1-docker.pkg.dev/agentlens-489006/voicebuddy/stocknews:latest \
  --args='--noon' \
  --region=us-west1 --project=agentlens-489006
```

### Cloud Scheduler (one-time setup)

```bash
# Morning — always runs:
gcloud scheduler jobs create http stocknews-daily \
  --schedule="0 8 * * 1-5" --time-zone="America/Los_Angeles" \
  --uri="https://us-west1-run.googleapis.com/v2/projects/agentlens-489006/locations/us-west1/jobs/stocknews:run" \
  --http-method=POST --oauth-service-account-email=<SA_EMAIL> \
  --location=us-west1 --project=agentlens-489006

# Noon — triggers stocknews-noon job (which has --noon baked in):
gcloud scheduler jobs create http stocknews-noon \
  --schedule="0 12 * * 1-5" --time-zone="America/Los_Angeles" \
  --uri="https://us-west1-run.googleapis.com/v2/projects/agentlens-489006/locations/us-west1/jobs/stocknews-noon:run" \
  --http-method=POST --oauth-service-account-email=<SA_EMAIL> \
  --location=us-west1 --project=agentlens-489006
```

> **Note:** The noon scheduler must point to `stocknews-noon:run`, NOT `stocknews:run`. The `--noon` flag is baked into the `stocknews-noon` Cloud Run Job; passing it via scheduler message body overrides is fragile and was the source of a bug where the noon job always sent regardless of market movement.

### Secrets
```bash
# Apply secrets to both jobs:
for JOB in stocknews stocknews-noon; do
  gcloud run jobs update $JOB \
    --region=us-west1 \
    --update-secrets=RECIPIENTS=RECIPIENTS:latest,AGENTMAIL_API_KEY=AGENTMAIL_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,BRAVE_API_KEY=BRAVE_API_KEY:latest
done
```

### Check status & logs
```bash
# Job status
gcloud run jobs describe stocknews --region=us-west1

# Recent executions
gcloud run jobs executions list --job=stocknews --region=us-west1

# Logs from latest execution
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="stocknews"' \
  --project=agentlens-489006 --limit=50 --format="table(timestamp,textPayload)"
```

### Image cleanup
Artifact Registry is configured to auto-delete images older than 2 days, keeping at minimum the most recent version. Policy file: `infra/cleanup-policy.json`.

To reapply:
```bash
gcloud artifacts repositories set-cleanup-policies voicebuddy \
  --project=agentlens-489006 \
  --location=us-west1 \
  --policy=infra/cleanup-policy.json \
  --no-dry-run
```

## PR Workflow

All changes go through pull requests — direct commits to `main` are blocked.

1. Changes are made on a feature branch
2. A PR is opened with a description of what changed
3. CI must pass (smoke test)
4. Owner approves → merges
