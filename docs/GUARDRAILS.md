# Guardrails

Manifest AI enforces a small set of governance invariants structurally (in code and topology), not
just through prompt instructions. Each invariant below is backed by a test in
`tests/guardrails/test_guardrails.py` so it cannot regress silently. The rationale is recorded in
[ADR-0002](adr/0002-governance-guardrails.md).

## Invariant 1 - Paid objects are created paused

Paid Meta objects must never be created already-spending.

- `FacebookManagerAgent/tools/AdCampaignStarter.py` and `AdSetCreator.py` expose
  `activate_immediately: bool = False`. When false, the Campaign / AdSet are created with
  `Status.paused`.
- Activation is an explicit, client-approved action, documented in
  [GO-LIVE-RUNBOOK.md](GO-LIVE-RUNBOOK.md).

Enforced by: assertions that both tools default `activate_immediately` to `False`.

## Invariant 2 - Two independent gates precede execution

Nothing reaches Stage 7 (Media Operations) without passing both:

- Stage 5 - Facebook Policy Compliance Officer (`FacebookPolicyAgent`)
- Stage 6 - Client Approval Manager (`ClientApprovalAgent`)

Gate outcomes (`facebook_policy_review`, `client_approval_review`) are written to the sanitized audit
log `audit_logs/manifest_ai_audit.jsonl`.

## Invariant 3 - No direct CEO to Media path

The communication graph in [`agency.py`](../agency.py) intentionally omits a CEO -> Media edge. Media
Operations is reachable only through the approval gate:

```mermaid
flowchart LR
    CEO[Chief Growth Strategist]
    Approval[Client Approval Manager]
    Media[Media Operations Director]
    CEO -->|delegates| Approval
    Approval -->|only path to publish| Media
    CEO -. no direct edge .-> Media
```

Enforced by: an assertion that `(ceo, facebookManagerAgent)` is not among the communication flows,
and that `(clientApprovalAgent, facebookManagerAgent)` is.

## Invariant 4 - Audit log is sanitized

`safe_audit_log.sanitize_record` ([`safe_audit_log.py`](../safe_audit_log.py)) drops keys matching
tokens / secrets / passwords / api-keys / authorization / payload / prompt / raw / path, replaces
filesystem paths with `[REDACTED_PATH]`, and truncates long values before anything is written. The
web bridge only ever reads this sanitized stream. See [ADR-0003](adr/0003-file-based-state-and-audit-log.md).

## Runtime backstop - staging profile

Beyond the structural guardrails above, the `staging` environment profile
(`MANIFEST_AI_ENV=staging`, the default) blocks live external mutations entirely at runtime — even if
a tool is called with `activate_immediately=True`. See [STAGING.md](STAGING.md) and
[ADR-0004](adr/0004-cloud-agent-environment-and-secrets.md).

## Running the checks

```bash
pytest tests/guardrails
```

These tests require no API key and must stay green on every change.
