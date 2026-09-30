"""Persist Agency Swarm v1 message lists per Slack conversation.

`conversation_id` is the Slack thread timestamp. Each Slack thread is its own
conversation: load if found, otherwise start empty.

Staging (`ENVIRONMENT=staging`, project `manifest-ai-meta`) writes Firestore
collection `slack_threads`. Development uses local JSON. Production is refused.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import firebase_adapter

logger = logging.getLogger(__name__)

THREADS_COLLECTION = "slack_threads"
THREADS_DIR = Path(__file__).resolve().parent / ".slack_threads"
MAX_CONVERSATION_ID_LENGTH = 256
_UNSAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")
_BLOCKED_ENVIRONMENTS = frozenset({"production", "prod"})


def _normalize_conversation_id(conversation_id: str | None) -> str:
    raw = str(conversation_id or "").strip()
    if not raw:
        return ""
    safe = _UNSAFE_ID.sub("_", raw)
    return safe[:MAX_CONVERSATION_ID_LENGTH]


def _is_production() -> bool:
    return firebase_adapter.is_production_environment()


def _as_thread_list(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("threads"), list):
        return payload["threads"]
    return []


def _local_path(conversation_id: str) -> Path:
    return THREADS_DIR / f"{conversation_id}.json"


def _read_local(conversation_id: str) -> list[Any]:
    path = _local_path(conversation_id)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.error("Local thread file was unreadable for conversation %s", conversation_id)
        return []
    return _as_thread_list(payload)


def _write_local(conversation_id: str, threads: list[Any]) -> None:
    THREADS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"conversation_id": conversation_id, "threads": threads}
    _local_path(conversation_id).write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, default=str),
        encoding="utf-8",
    )


def init_thread_store() -> None:
    """Initialize staging Firestore when configured; always ensure local fallback dir."""
    firebase_adapter.initialize_firebase()
    if not _is_production():
        THREADS_DIR.mkdir(parents=True, exist_ok=True)


def get_threads(conversation_id: str) -> list[Any]:
    """Load saved v1 message list for a Slack thread. Empty list starts a new conversation."""
    cid = _normalize_conversation_id(conversation_id)
    if not cid:
        return []
    if _is_production():
        logger.error("Thread store refused to read in production")
        return []
    init_thread_store()
    remote = firebase_adapter.load_document(THREADS_COLLECTION, cid)
    if remote is not None:
        threads = _as_thread_list(remote)
        if threads:
            return threads
    return _read_local(cid)


def save_threads(conversation_id: str, threads: list[Any] | None) -> None:
    """Persist the v1 message list for a Slack thread after a turn."""
    cid = _normalize_conversation_id(conversation_id)
    if not cid:
        logger.error("Thread store refused to save without conversation_id")
        return
    if _is_production():
        logger.error("Thread store refused to write in production")
        return
    payload = list(threads or [])
    init_thread_store()
    _write_local(cid, payload)
    firebase_adapter.save_document(
        THREADS_COLLECTION,
        cid,
        {"conversation_id": cid, "threads": payload},
    )
