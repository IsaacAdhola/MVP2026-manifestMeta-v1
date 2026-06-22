import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_AUDIT_DIR = Path(__file__).resolve().parent / "audit_logs"
_AUDIT_FILE = _AUDIT_DIR / "manifest_ai_audit.jsonl"

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(token|secret|password|api[_-]?key|authorization|access[_-]?token|app[_-]?secret|payload|prompt|raw|path|\.env)",
    re.IGNORECASE,
)
_FILE_PATH_PATTERN = re.compile(r"([A-Za-z]:\\[^\s]+|/[^\s]+)")


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_record(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:20]]
    if isinstance(value, str):
        value = _FILE_PATH_PATTERN.sub("[REDACTED_PATH]", value)
        if len(value) > 500:
            return value[:497] + "..."
        return value
    return value


def sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in record.items():
        safe_key = str(key)
        if _SENSITIVE_KEY_PATTERN.search(safe_key):
            continue
        else:
            sanitized[safe_key] = _sanitize_value(value)
    return sanitized


def write_audit_event(event_type: str, actor: str, outcome: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    _AUDIT_DIR.mkdir(exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor": actor,
        "outcome": outcome,
        "details": sanitize_record(details or {}),
    }
    with _AUDIT_FILE.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(event, ensure_ascii=True) + "\n")
    return event


def read_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    if not _AUDIT_FILE.exists():
        return []
    lines = _AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = []
    for line in lines[-max(1, min(limit, 500)):]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


if __name__ == "__main__":
    event = write_audit_event(
        event_type="self_test",
        actor="safe_audit_log",
        outcome="ok",
        details={
            "campaign_name": "Example Campaign",
            "access_token": "should_not_be_logged",
            "image_path": "C:\\secret\\image.png",
            "note": "Safe audit event created.",
        },
    )
    print(event)
