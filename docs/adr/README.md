# Architecture Decision Records

This directory records significant architectural decisions for Manifest AI using lightweight
[MADR](https://adr.github.io/madr/)-style records.

## Why

This is an architecture-first project. Decisions that shape the system — the agent topology, the
governance guardrails, how state flows, how the environment is provisioned — are captured here so
they are reviewable, durable, and hard to erode accidentally. Where a decision is enforceable, it is
backed by a test under `tests/guardrails/`.

## Process

1. Copy [`0000-template.md`](0000-template.md) to `NNNN-short-title.md` using the next free number.
2. Fill in Context, Decision, and Consequences. Keep it short and concrete.
3. Set the Status (`Proposed`, `Accepted`, `Superseded by ADR-XXXX`, or `Deprecated`).
4. Open the ADR in the same pull request as the change it describes when possible.
5. Never edit an Accepted ADR's decision retroactively — supersede it with a new ADR and link both.

## Index

- [0001 - Multi-agent Agency Swarm architecture](0001-multi-agent-agency-swarm-architecture.md)
- [0002 - Governance guardrails](0002-governance-guardrails.md)
- [0003 - File-based state and sanitized audit log](0003-file-based-state-and-audit-log.md)
- [0004 - Cloud Agent environment and secrets](0004-cloud-agent-environment-and-secrets.md)
