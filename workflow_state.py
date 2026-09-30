import json
import re
from pathlib import Path
from typing import Any

from firebase_adapter import load_workflow_state, save_workflow_state

_STATE_FILE = Path(__file__).resolve().parent / ".workflow_state.json"

COUNTRY_CODES = (
    ("united kingdom", "GB"),
    ("great britain", "GB"),
    ("united states", "US"),
    ("australia", "AU"),
    ("canada", "CA"),
    ("germany", "DE"),
    ("france", "FR"),
    ("mexico", "MX"),
    ("india", "IN"),
    ("ireland", "IE"),
    ("usa", "US"),
    ("u.s.", "US"),
    ("uk", "GB"),
)


def _read_local_state() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {}
    try:
        payload = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_local_state(data: dict[str, Any]) -> None:
    _STATE_FILE.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def _read_state() -> dict[str, Any]:
    local = _read_local_state()
    if local:
        return local
    remote = load_workflow_state()
    if not remote:
        return {}
    _write_local_state(remote)
    return remote


def _write_state(data: dict[str, Any]) -> None:
    _write_local_state(data)
    save_workflow_state(data)


def set_state_value(key: str, value: Any) -> None:
    data = _read_state()
    data[key] = value
    _write_state(data)


def get_state_value(key: str, default: Any = None) -> Any:
    return _read_state().get(key, default)


def merge_state(updates: dict[str, Any]) -> dict[str, Any]:
    data = _read_state()
    data.update(updates)
    _write_state(data)
    return data


def clear_state() -> None:
    _write_state({})


STALE_DEMO_MARKERS = (
    "atlas peak",
    "fresh coffee, roasted weekly",
    "specialty coffee subscription",
    "atlas peak coffee",
    "coffee subscription austin",
)

EXCLUDE_STALE_HINTS = (
    "do not reuse",
    "don't reuse",
    "do not use",
    "don't use",
    "not atlas peak",
    "not coffee",
    "no leftover",
    "never substitute",
    "instead of atlas",
)


def _message_excludes_stale_demo(message: str) -> bool:
    text = (message or "").lower()
    return any(hint in text for hint in EXCLUDE_STALE_HINTS)

CREATIVE_SUBJECT_KEYS = (
    "ad_copy",
    "ad_headline",
    "ad_copy_options",
    "image_options",
    "image_path",
    "client_brief",
    "research_brief",
    "market_research_brief",
    "cultural_voice_brief",
    "search_visibility_brief",
    "landing_page_brief",
    "cro_audit",
    "community_reply_drafts",
    "performance_brief",
    "selected_image_option",
    "claims_ledger",
    "claims_ledger_outcome",
)

LEFTOVER_EXECUTION_KEYS = (
    "campaign_id",
    "ad_set_id",
    "ad_id",
    "page_post_id",
    "page_photo_id",
    "campaign_status",
)


def _value_looks_like_stale_demo(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        blob = value.lower()
    else:
        blob = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in blob for marker in STALE_DEMO_MARKERS)


def isolate_stale_demo_state(client_message: str = "") -> list[str]:
    """Drop leftover coffee-demo fixtures when this turn is a different client request."""
    message = (client_message or "").lower()
    matched_markers = [marker for marker in STALE_DEMO_MARKERS if marker in message]
    excludes_stale = _message_excludes_stale_demo(message)
    data = _read_state()
    if matched_markers and not excludes_stale:
        return []
    removed: list[str] = []
    for key in CREATIVE_SUBJECT_KEYS:
        if key in data and _value_looks_like_stale_demo(data[key]):
            del data[key]
            removed.append(key)
    if removed:
        for key in ("image_options", "image_path", "selected_image_option"):
            if key in data and key not in removed:
                del data[key]
                removed.append(key)
        for key in LEFTOVER_EXECUTION_KEYS:
            if key in data:
                del data[key]
                removed.append(key)
        _write_state(data)
    return removed


def get_brief() -> dict[str, Any]:
    brief = get_state_value("client_brief") or {}
    return brief if isinstance(brief, dict) else {}


def copy_context() -> str:
    brief = get_brief()
    parts = [
        f"Business: {brief.get('business') or ''}",
        f"Goal: {brief.get('campaign_goal') or ''}",
        f"Audience: {brief.get('target_customer') or ''}",
        f"Geography: {brief.get('geography') or ''}",
        f"Tone notes: {brief.get('brand_notes') or ''}",
        f"Campaign type: {brief.get('campaign_type') or ''}",
    ]
    research = get_state_value("market_research_brief")
    if research:
        parts.append(f"Research: {json.dumps(research, ensure_ascii=False)[:1800]}")
    culture = get_state_value("cultural_voice_brief")
    if culture:
        parts.append(f"Voice brief: {str(culture)[:1200]}")
    search = get_state_value("search_visibility_brief")
    if search:
        parts.append(f"Search brief: {json.dumps(search, ensure_ascii=False)[:1200]}")
    return "\n".join(parts)


def country_code_from_geography(geography: str | None = None) -> str:
    text = (geography or get_brief().get("geography") or "").lower()
    for needle, code in COUNTRY_CODES:
        if needle in text:
            return code
    return "US"


def budget_cents_from_brief() -> int:
    raw = str(get_brief().get("budget") or get_state_value("daily_budget_cents") or "")
    digits = re.findall(r"\d+", raw.replace(",", ""))
    if not digits:
        stored = get_state_value("daily_budget_cents")
        if isinstance(stored, int) and stored > 0:
            return stored
        return 1000
    amount = int(digits[0])
    if amount < 1000:
        return max(100, amount * 100)
    return amount


def get_media_package() -> dict[str, Any]:
    brief = get_brief()
    return {
        "business": brief.get("business") or "",
        "campaign_goal": brief.get("campaign_goal") or "",
        "campaign_type": (brief.get("campaign_type") or get_state_value("campaign_type") or "").lower(),
        "platform": (brief.get("platform") or "").lower(),
        "geography": brief.get("geography") or "",
        "budget": brief.get("budget") or "",
        "go_live": brief.get("go_live") or "",
        "destination_link": brief.get("destination_link") or get_state_value("destination_link") or "",
        "ad_copy": get_state_value("ad_copy") or "",
        "ad_headline": get_state_value("ad_headline") or "",
        "image_path": get_state_value("image_path") or "",
        "policy_outcome": get_state_value("policy_outcome") or "",
        "client_approval_outcome": get_state_value("client_approval_outcome") or "",
        "campaign_id": get_state_value("campaign_id") or "",
        "ad_set_id": get_state_value("ad_set_id") or "",
        "ad_id": get_state_value("ad_id") or "",
        "page_post_id": get_state_value("page_post_id") or "",
        "country_code": country_code_from_geography(brief.get("geography")),
        "daily_budget_cents": budget_cents_from_brief(),
    }


def missing_for_organic(package: dict[str, Any] | None = None) -> list[str]:
    pkg = package or get_media_package()
    missing = []
    if not pkg.get("ad_copy"):
        missing.append("ad_copy")
    if not pkg.get("image_path"):
        missing.append("image_path")
    if pkg.get("policy_outcome") != "approved":
        missing.append("policy_approved")
    if pkg.get("client_approval_outcome") != "approved":
        missing.append("client_authorization")
    return missing


def missing_for_paid(package: dict[str, Any] | None = None) -> list[str]:
    missing = missing_for_organic(package)
    pkg = package or get_media_package()
    if not pkg.get("destination_link"):
        missing.append("destination_link")
    return missing


def is_paid_campaign(package: dict[str, Any] | None = None) -> bool:
    pkg = package or get_media_package()
    campaign_type = pkg.get("campaign_type") or ""
    return "paid" in campaign_type or campaign_type in {"meta_ad", "boosted", "retargeting"}
