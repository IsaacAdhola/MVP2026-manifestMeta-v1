# ADR-0002: Governance guardrails

- Status: Accepted
- Date: 2026-09-14
- Deciders: Manifest AI team

## Context

The agency can spend real ad budget and publish publicly to a brand's Facebook Page. Mistakes here
are expensive and hard to reverse. We need hard, structural guarantees — not just prompt
instructions — that nothing goes live without policy review and explicit client approval, and that
paid objects are never created already-spending.

## Decision

We will enforce three guardrails:

1. Paid-object creation defaults to paused. `AdCampaignStarter` and `AdSetCreator` expose
   `activate_immediately: bool = False`; when false the created Campaign/AdSet use
   `Status.paused`. Activation requires an explicit, client-approved opt-in.
2. Two independent gates precede execution. Stage 5 Facebook Policy Compliance Officer and Stage 6
   Client Approval Manager must both approve before Stage 7 Media Operations runs.
3. The communication graph has no direct CEO → Media edge. In [`agency.py`](../../agency.py),
   Media Operations Director is reachable only via `Client Approval Manager → Media Operations
   Director`, so publishing structurally cannot be triggered without passing the approval gate.

## Consequences

- Positive: go-live is a deliberate, gated action; the default state of any paid object is safe.
- Positive: guardrails are enforced by code structure, not by trusting model behavior.
- Negative: even harmless test runs require passing gates to reach publishing.
- Enforcement: `tests/guardrails/test_guardrails.py` asserts the paused defaults and the
  absence of a CEO → Media edge. See [../GUARDRAILS.md](../GUARDRAILS.md). Staging adds a second
  runtime backstop (ADR-0004 / STAGING) that blocks live mutations entirely.

## Alternatives considered

- Prompt-only guardrails ("please keep campaigns paused") — rejected: not verifiable and easy to
  regress.
- A single combined approval step — rejected: policy compliance and client sign-off are different
  concerns and must not be able to substitute for one another.
