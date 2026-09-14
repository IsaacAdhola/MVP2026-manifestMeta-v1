# ADR-0004: Cloud Agent environment and secrets

- Status: Accepted
- Date: 2026-09-14
- Deciders: Manifest AI team

## Context

The project runs both locally and in Cursor Cloud Agents. Agent initialization talks to OpenAI (the
agency cannot import without `OPENAI_API_KEY`), and the execution/research stages need Facebook and
ScrapeCreators credentials. We need a reproducible environment definition and a safe way to supply
secrets without committing them.

## Decision

We will define the environment in [`.cursor/environment.json`](../../.cursor/environment.json):

- `install` installs `requirements.txt` plus the web/UI runtime dependencies the apps need but that
  are not pinned in `requirements.txt` (`fastapi`, `uvicorn[standard]`, `websockets`, `gradio`,
  `pytest`).
- `ports` exposes `7860` (Gradio) and `8000` (web bridge).
- Servers are not auto-started, because agent initialization can create OpenAI vector stores at
  import time and we do not want to incur that on every boot.

Secrets are supplied via environment variables / the Cloud Agent Secrets panel and read with
`os.getenv(...)`; they are never committed. `.env` is git-ignored and `.env.example` documents the
required names. `OPENAI_API_KEY` is required; `FACEBOOK_*` and `SCRAPE_CREATORS_API_KEY` are optional
and only needed for the execution and live-research stages.

## Consequences

- Positive: a fresh Cloud Agent (or local checkout) reaches a runnable state with one install step.
- Positive: secrets stay out of the repo and out of the sanitized audit log (see ADR-0003).
- Negative: running the apps end to end is blocked until `OPENAI_API_KEY` is provided.
- Enforcement: OpenAI-dependent tests are marked `requires_openai` and auto-skip when the key is
  absent, so the offline suite stays green.

## Alternatives considered

- Auto-starting the servers in `terminals` — rejected: would create OpenAI vector stores on every
  boot, incurring cost and clutter.
- Committing a `.env` with placeholder values only — rejected in favor of `.env.example`, so a real
  `.env` is never at risk of being committed.
