"""Slack-safe formatting. No tokens, no internal tool names."""

from __future__ import annotations

import re
from typing import Any

MENTION = re.compile(r"<@([A-Z0-9]+)>\s*")
IMAGE_MD = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
BOLD_MD = re.compile(r"\*\*(.+?)\*\*")
MAX_SLACK_CHARS = 3500


def strip_bot_mention(text: str, bot_user_id: str | None = None) -> str:
    raw = text or ""
    if bot_user_id:
        raw = re.sub(rf"<@{re.escape(bot_user_id)}>\s*", "", raw, flags=re.IGNORECASE)
    return MENTION.sub("", raw, count=1).strip()


def should_ignore_slack_event(event: dict[str, Any]) -> bool:
    if event.get("bot_id") or event.get("subtype") in {
        "bot_message",
        "message_changed",
        "message_deleted",
        "message_replied",
    }:
        return True
    if event.get("user") and event.get("user") == event.get("bot_id"):
        return True
    return False


def markdown_to_slack(text: str) -> tuple[str, list[str]]:
    """Convert CEO markdown to Slack mrkdwn and pull local image paths."""
    paths: list[str] = []

    def _keep_path(match: re.Match[str]) -> str:
        path = match.group(2).strip()
        if path:
            paths.append(path)
        option = match.group(1).strip() or "image"
        return f"*{option}*"

    converted = IMAGE_MD.sub(_keep_path, text or "")
    converted = BOLD_MD.sub(r"*\1*", converted)
    converted = converted.replace("\n\n\n", "\n\n").strip()
    return converted, paths


def chunk_text(text: str, limit: int = MAX_SLACK_CHARS) -> list[str]:
    body = (text or "").strip()
    if not body:
        return []
    if len(body) <= limit:
        return [body]
    chunks: list[str] = []
    remaining = body
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return chunks


def option_buttons(kind: str) -> dict[str, Any]:
    label = "Choose a copy option" if kind == "copy" else "Choose an image option"
    return {
        "text": label,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{label}.* Tap one and the team will continue."},
            },
            {
                "type": "actions",
                "block_id": f"manifest_{kind}_choice",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": f"Option {index}"},
                        "action_id": f"pick_{kind}_{index}",
                        "value": f"Option {index}",
                    }
                    for index in (1, 2, 3)
                ],
            },
        ],
    }
