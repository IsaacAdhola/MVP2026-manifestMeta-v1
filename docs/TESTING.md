# Testing

This project follows a test-led workflow. Tests live under `tests/` and are grouped by how much of the system they exercise and what they require to run.

## Layout

```
tests/
├── conftest.py          # puts repo root on sys.path; auto-skips OpenAI tests when no key
├── unit/                # pure Python tool logic; no network, no API key
│   ├── test_campaign_ops.py
│   └── test_agent_handoff_and_state.py
├── guardrails/          # governance invariants (see docs/GUARDRAILS.md)
│   └── test_guardrails.py
└── smoke/               # agency import / startup / conversation (requires OPENAI_API_KEY)
    ├── test_agency_import.py
    ├── test_agency_startup.py
    └── test_conversation.py
```

## Running

Offline (no secrets required):

```bash
pytest tests/unit tests/guardrails
```

Full suite (requires `OPENAI_API_KEY`, plus `FACEBOOK_*` / `SCRAPE_CREATORS_API_KEY` for the
Facebook and research paths):

```bash
pytest
```

Tests marked `requires_openai` are automatically skipped when `OPENAI_API_KEY` is not set, so the
offline suite always runs cleanly. See `pytest.ini` for the marker definition.

## What each group covers

- `unit/` — CampaignOps tools (scheduler, post tracker, budget manager, dashboard) and the
  shared-state / handoff helpers. These validate deterministic tool logic and file-based state.
- `guardrails/` — asserts the governance invariants that must never regress: paid-object creation
  defaults to paused, and the agency communication graph never allows the CEO to reach Media
  Operations directly (paid publishing is reachable only through Client Approval). See
  [GUARDRAILS.md](GUARDRAILS.md).
- `smoke/` — imports and initializes the full 9-agent agency, verifies the Gradio startup path, and
  runs a scripted client conversation. These require a valid `OPENAI_API_KEY` because agent
  initialization talks to OpenAI.

## Environments

Runs default to the `staging` safety profile (`MANIFEST_AI_ENV=staging`), which blocks live external
mutations (Facebook publishing / activation). See [STAGING.md](STAGING.md) and
[GO-LIVE-RUNBOOK.md](GO-LIVE-RUNBOOK.md) for how production go-live differs.

## History

This document is the current, consolidated testing guide. The earlier ad-hoc, per-tool test logs
(`TEST_RESULTS.md`, `FINAL_TEST_RESULTS.md`, `AGENCY_TEST_RESULTS.md`, `TESTING_SUMMARY.md`) are
retained at the repository root for historical reference. Note that some of those historical files
contain credentials from the original prototype; those credentials should be rotated and are not used
by the current test suite.
