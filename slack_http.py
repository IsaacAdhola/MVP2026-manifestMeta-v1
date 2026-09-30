"""HTTP helpers for Slack Events API payloads."""

from __future__ import annotations

from typing import Any


def slack_url_challenge(payload: dict[str, Any]) -> str | None:
    if payload.get("type") == "url_verification":
        challenge = payload.get("challenge")
        return challenge if isinstance(challenge, str) else None
    return None


def summarize_slack_envelope(payload: dict[str, Any]) -> str:
    """Log-safe Slack envelope summary. Never includes tokens or message text."""
    kind = str(payload.get("type") or "unknown")
    event = payload.get("event")
    if not isinstance(event, dict):
        event = {}
    text = str(event.get("text") or payload.get("text") or "")
    return (
        f"type={kind} event={event.get('type') or ''} "
        f"channel_type={event.get('channel_type') or ''} "
        f"has_mention={str('<@' in text).lower()}"
    )
