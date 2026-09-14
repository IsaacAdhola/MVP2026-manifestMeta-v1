# Staging vs Production

Manifest AI runs under one of two environment profiles, selected by the `MANIFEST_AI_ENV`
environment variable and implemented in [`config.py`](../config.py).

| Profile | `MANIFEST_AI_ENV` | Live Meta mutations | Use for |
| --- | --- | --- | --- |
| Staging (default) | unset or `staging` | Blocked | Demos, local dev, tests, investor walkthroughs |
| Production | `production` | Allowed (still gated) | Real client go-live |

If `MANIFEST_AI_ENV` is unset or set to any unrecognized value, the profile resolves to `staging`.
This is deliberate: the system fails safe, never fails open.

## What staging blocks

In staging, tools that would perform a live external mutation on Meta short-circuit at the top of
`run()` and return a `[BLOCKED - staging] ...` notice without making any network call:

- `AdCampaignStarter` — creating a campaign
- `AdSetCreator` — creating an ad set
- `AdCreator` — creating an ad
- `FacebookPagePostPublisher` — publishing a Page post
- `FacebookPhotoPostPublisher` — publishing a photo post

Read-only tools (`AdPerformanceMonitor`, `FacebookTokenDiagnostics`) are unaffected. This backstop is
independent of the tool arguments — even a call with `activate_immediately=True` is blocked in
staging.

## Relationship to the other guardrails

Staging is a runtime backstop that complements the structural guardrails described in
[GUARDRAILS.md](GUARDRAILS.md) and [ADR-0002](adr/0002-governance-guardrails.md):

1. Structural: no direct CEO -> Media path; paid objects default to paused.
2. Process: Policy + Approval gates must pass before execution.
3. Runtime (this doc): staging disables live mutations entirely.

All three must be satisfied for anything to go live, and staging must be switched off explicitly.

## Going to production

```bash
export MANIFEST_AI_ENV=production
```

Only do this once the required `FACEBOOK_*` credentials are configured and you intend to perform real
Meta operations. Follow [GO-LIVE-RUNBOOK.md](GO-LIVE-RUNBOOK.md) for the full go-live procedure. Even
in production, publishing remains subject to the approval gates and paused-by-default guardrails.

## Checking the active profile

```python
import config
config.current_env()          # 'staging' or 'production'
config.live_mutations_allowed()  # True only in production
```
