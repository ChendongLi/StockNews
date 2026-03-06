# CLAUDE.md — StockNews Project Instructions

## Git Workflow (mandatory)

- **Always branch before making changes.** Never commit directly to `main`.
- Branch naming: `feat/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- After commits on the branch, open a PR against `main` via `gh pr create`.
- Keep `main` clean — reset any accidental direct commits before branching.

## Project Context

- Runs as a Cloud Run Job on GCP (project: `agentlens-489006`, region: `us-west1`)
- Sends daily stock news digest emails via AgentMail
- Primary schedule: 8 AM PT Mon–Fri
- Noon run uses `--noon` flag (only fires if S&P 500 moved ±0.5% from open)
