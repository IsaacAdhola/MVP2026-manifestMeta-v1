"""Classify whether Slack should run the CEO swarm.

Clients talk only to the Chief Growth Strategist. Humans may chat among
themselves. The bot stays silent unless the latest message is feedback or
a real request for the agency.
"""

from __future__ import annotations

import json
import os
import re

from model_router import MODEL_GPT, llm_text

OPTION_CHOICE = re.compile(r"^option\s*[123]\b", re.IGNORECASE)
WORK_HINTS = re.compile(
    r"\b(image|images|photo|photos|facebook|instagram|campaign|ad|ads|"
    r"copy|headline|budget|post|posts|research|approve|approval|"
    r"option|creative|landing|blog|seo|hello|hi|hey|start)\b",
    re.IGNORECASE,
)
ACK_ONLY = re.compile(
    r"^(ok|okay|k|thanks|thank you|ty|thx|got it|cool|lol|lmao|nice)[.!\s]*$",
    re.IGNORECASE,
)
CEO_NAME_PREFIX = re.compile(
    r"^@?(?:manifest(?:est)?(?:\s+meta)?(?:\s+(?:ai|ceo))?|manifest\s+ai)\b[:,]?\s*",
    re.IGNORECASE,
)

CLASSIFIER_SYSTEM = """You decide whether Manifest AI's Chief Growth Strategist should reply in Slack.

Reply YES only when the latest human message is directed at the agency/CEO AND contains real work:
- campaign feedback, copy or image choice, approvals, answers to CEO questions
- a new request for research, ads, posts, strategy, or creative
- an @mention that actually asks Manifest AI to do something

Reply NO when:
- humans are talking among themselves
- acknowledgements only: ok, thanks, lol, got it, thumbs up, emoji
- empty or near-empty @mentions with no request
- channel noise, small talk, messages not for the CEO

Return a single JSON object: {"reply": true} or {"reply": false}
No other text."""


def _has_letters(text: str) -> bool:
    return any(char.isalnum() for char in text)


def _parse_decision(raw: str) -> bool:
    body = (raw or "").strip()
    if not body:
        return False
    try:
        data = json.loads(body)
        if isinstance(data, dict) and "reply" in data:
            return bool(data["reply"])
    except json.JSONDecodeError:
        pass
    token = body.split()[0].strip(".,:;\"'").lower()
    if token in {"yes", "true", "reply"}:
        return True
    if token in {"no", "false", "silent"}:
        return False
    return False


def _classifier_model() -> str:
    return (os.getenv("AGENT_MODEL_NAME") or "").strip() or MODEL_GPT


def normalize_client_text(text: str) -> str:
    """Strip leftover CEO display-name prefixes after Slack mention markup is gone."""
    cleaned = (text or "").strip()
    cleaned = CEO_NAME_PREFIX.sub("", cleaned, count=1).strip()
    return cleaned


def _is_direct_client(channel_type: str | None, mentioned: bool) -> bool:
    kind = (channel_type or "").strip().lower()
    return mentioned or kind in {"im", "mpim"}


def should_reply_to_client(
    text: str,
    *,
    channel_type: str | None = None,
    mentioned: bool = False,
    source: str = "message",
) -> bool:
    """Return True only when the CEO should run a client turn."""
    cleaned = normalize_client_text(text)
    if source == "action":
        return True
    if OPTION_CHOICE.match(cleaned):
        return True
    if not cleaned or not _has_letters(cleaned):
        return False

    directed = _is_direct_client(channel_type, mentioned)
    if ACK_ONLY.match(cleaned):
        return False
    if directed:
        return True
    if WORK_HINTS.search(cleaned):
        return True
    kind = (channel_type or "").strip().lower() or "unknown"
    user = (
        f"channel_type: {kind}\n"
        f"mentioned: {str(mentioned).lower()}\n"
        f"message: {cleaned}"
    )
    try:
        raw = llm_text(
            _classifier_model(),
            CLASSIFIER_SYSTEM,
            user,
            max_tokens=40,
            temperature=0.0,
        )
    except Exception:
        return False
    return _parse_decision(raw)
