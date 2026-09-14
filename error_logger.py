"""Frontend-safe error logger for Manifest AI tools, APIs, and agency runs."""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from safe_audit_log import sanitize_record, write_audit_event

_ERROR_DIR = Path(__file__).resolve().parent / "audit_logs"
_ERROR_FILE = _ERROR_DIR / "errors.jsonl"


def log_error(
    actor: str,
    error: BaseException | str,
    *,
    location: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a sanitized error to errors.jsonl and the shared audit log."""
    if isinstance(error, BaseException):
        error_type = type(error).__name__
        error_message = str(error)[:500]
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))[-1500:]
    else:
        error_type = "ToolError"
        error_message = str(error)[:500]
        tb = ""

    details = sanitize_record(
        {
            "location": location,
            "error_type": error_type,
            "error_message": error_message,
            **(context or {}),
        }
    )
    if tb:
        details["traceback_tail"] = sanitize_record({"tb": tb}).get("tb", "")[:1500]

    _ERROR_DIR.mkdir(exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "outcome": "error",
        "details": details,
    }
    with _ERROR_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")

    write_audit_event(
        event_type="error",
        actor=actor,
        outcome="error",
        details=details,
    )
    return record


def read_error_events(limit: int = 50) -> list[dict[str, Any]]:
    if not _ERROR_FILE.exists():
        return []
    lines = _ERROR_FILE.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = []
    for line in lines[-max(1, min(limit, 500)) :]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
