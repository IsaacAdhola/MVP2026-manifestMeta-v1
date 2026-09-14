# ADR-0001: Multi-agent Agency Swarm architecture

- Status: Accepted
- Date: 2026-09-14
- Deciders: Manifest AI team

## Context

Manifest AI plans and executes Meta marketing campaigns end to end: intake, research, copy, creative,
policy compliance, client approval, publishing, and tracking. These are distinct skills with
different tools, knowledge, and risk profiles. A single monolithic agent would blur responsibilities
and make it impossible to gate the high-risk publishing step.

## Decision

We will implement the system as an Agency Swarm agency of nine specialist agents with an explicit,
directional communication graph defined in [`agency.py`](../../agency.py):

- Chief Growth Strategist (`MetaMarkCEO`) is the only client-facing agent and the orchestrator.
- Market Intelligence Director, Search & Answer Visibility Director, Senior Conversion Copywriter,
  Creative Director, Facebook Policy Compliance Officer, Client Approval Manager, Media Operations
  Director, and Campaign Operations Director run as background delegations.

Each agent follows one identical package layout (`__init__.py`, `<Agent>.py`, `instructions.md`,
`schemas/`, `tools/`, plus optional `lib/`, `files/`, `knowledge/`). See ADR-0002 for the guardrails
embedded in the communication graph.

## Consequences

- Positive: clear separation of responsibilities; each stage owns its tools and instructions; the
  topology itself encodes policy (see ADR-0002).
- Positive: uniform agent structure makes agents easy to add, test, and reason about.
- Negative: multi-agent handoffs add latency and token cost versus a single agent.
- Enforcement: the required communication edges are asserted in `tests/guardrails/` alongside the
  governance invariants.

## Alternatives considered

- Single general-purpose agent — rejected: cannot enforce a hard gate before publishing and mixes
  unrelated tools/knowledge.
- Two agents (planner + executor) — rejected: too coarse to separate policy review from client
  approval, which must be independent gates.
