# Architecture

The project is organized as small single-purpose modules:

- `src/config.py`: Loads environment variables and sets up logging.
- `src/fetcher.py`: Pulls RSS headlines for each stock ticker.
- `src/summarizer.py`: Uses Anthropic API to summarize ticker news.
- `src/renderer.py`: Builds HTML email content.
- `src/emailer.py`: Sends email via SMTP.
- `src/app.py`: Orchestrates the full workflow.
- `main.py`: Thin entry point.

Data flow:

1. Load `.env` and runtime config.
2. Fetch RSS headlines per ticker.
3. Summarize each ticker's news.
4. Render one HTML digest.
5. Send email or print in test mode.
