"""Runtime environment profile for Manifest AI.

The ``MANIFEST_AI_ENV`` environment variable selects a safety profile:

- ``staging`` (default): live external mutations are blocked. Tools that would create or activate
  paid Meta objects or publish to a Facebook Page short-circuit with a clear notice and make no
  external changes. Safe for demos, local development, and automated tests.
- ``production``: external mutations are permitted. They remain governed by the agency's
  PAUSED-by-default guardrails and the Policy + Approval gates (see ``docs/GUARDRAILS.md``).

This is a runtime backstop that complements the structural guardrails in ``agency.py`` and the
paused-by-default tool arguments. See ``docs/STAGING.md`` and ADR-0004.
"""

from __future__ import annotations

import os

STAGING = "staging"
PRODUCTION = "production"
_VALID_ENVS = {STAGING, PRODUCTION}


def current_env() -> str:
    """Return the active environment profile, defaulting to ``staging``.

    Any unrecognized value falls back to ``staging`` (fail safe, never fail open).
    """
    raw = (os.getenv("MANIFEST_AI_ENV") or STAGING).strip().lower()
    return raw if raw in _VALID_ENVS else STAGING


def is_production() -> bool:
    return current_env() == PRODUCTION


def is_staging() -> bool:
    return not is_production()


def live_mutations_allowed() -> bool:
    """True only in production. Live external (Meta) mutations require production."""
    return is_production()


def staging_block_notice(action: str) -> str:
    """Human-readable notice returned by a tool when a live mutation is blocked in staging."""
    env = current_env()
    return (
        f"[BLOCKED - {env}] '{action}' is a live external Meta operation and is disabled in the "
        f"'{env}' environment. No changes were made to Facebook/Meta. Set MANIFEST_AI_ENV=production "
        "to enable live operations (still subject to the approval gates and paused-by-default "
        "guardrails)."
    )
