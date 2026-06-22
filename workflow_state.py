import json
from pathlib import Path
from typing import Any

_STATE_FILE = Path(__file__).resolve().parent / ".workflow_state.json"


def _read_state() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(data: dict[str, Any]) -> None:
    _STATE_FILE.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def set_state_value(key: str, value: Any) -> None:
    data = _read_state()
    data[key] = value
    _write_state(data)


def get_state_value(key: str, default: Any = None) -> Any:
    return _read_state().get(key, default)


def clear_state() -> None:
    _write_state({})
