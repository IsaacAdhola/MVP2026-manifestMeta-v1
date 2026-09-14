# ADR-0003: File-based state and sanitized audit log

- Status: Accepted
- Date: 2026-09-14
- Deciders: Manifest AI team

## Context

The live web bridge ([`web_bridge.py`](../../web_bridge.py)) mirrors what the agency produces to a
browser UI in real time: copy options, creative options, gate outcomes, and execution objects. It
must do this without reaching into agent internals, tool payloads, prompts, or secrets, and without
changing agent behavior. We also need an inter-agent record of the two governance gates.

## Decision

We will use files written by the tools themselves as the single source of truth the bridge observes:

- `.workflow_state.json` (via [`workflow_state.py`](../../workflow_state.py)) holds structured
  campaign state: `ad_copy_options`, `image_options`, `image_path`, `campaign_id`, `ad_set_id`,
  `ad_id`, `page_post_id`, `page_photo_id`, etc. The bridge diffs this file and emits UI events.
- `audit_logs/manifest_ai_audit.jsonl` (via [`safe_audit_log.py`](../../safe_audit_log.py)) is an
  append-only JSONL log of inter-agent events, including the `facebook_policy_review` and
  `client_approval_review` gate outcomes.
- `campaign_data/schedule.json` and `campaign_data/budgets.json` hold CampaignOps tracking.

`safe_audit_log` sanitizes every record before writing: keys matching tokens/secrets/passwords/
api-keys/authorization/payload/prompt/raw/path are dropped, filesystem paths are replaced with
`[REDACTED_PATH]`, and long strings/lists are truncated. The bridge therefore never needs raw tool
internals.

## Consequences

- Positive: the UI and any observer are fully decoupled from agent internals; sensitive data cannot
  leak through the audit stream by construction.
- Positive: state is inspectable and diffable on disk, which aids debugging and testing.
- Negative: file polling adds a small latency; concurrent writers rely on append-only / last-write
  semantics rather than a transactional store.
- Enforcement: `safe_audit_log.sanitize_record` is covered by the unit/handoff tests.

## Alternatives considered

- In-memory event bus / direct callbacks from tools to the bridge — rejected: couples the UI to
  agent internals and risks leaking payloads.
- A database — rejected as overkill for the current single-process demo footprint; can supersede
  this ADR if multi-process durability becomes a requirement.
