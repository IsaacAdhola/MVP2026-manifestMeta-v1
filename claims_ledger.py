"""Claims ledger persistence and pause-list helpers.

Extends the Facebook Policy review — not a second claims system.
Records live post/ad/campaign IDs so Media/Ops can pause those and only those.
Does not call Graph or spend ad budget unless a caller injects a media runner.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

_NESTED = Path(__file__).resolve().parent
_ROOT = _NESTED.parent
for _path in (str(_NESTED), str(_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from manifest_types.component_types import (
    CLAIMS_LEDGER_OUTCOME_BLOCKED,
    CLAIMS_LEDGER_OUTCOME_KEY,
    CLAIMS_LEDGER_OUTCOME_PASS,
    CLAIMS_LEDGER_STATE_KEY,
    CLAIM_BLOCK_CAPTION_ONLY,
    OPS_PAUSE_CAMPAIGN_ACTION,
    OPS_PAUSE_POST_ACTION,
    OPS_POST_STATUS_PAUSED,
    PAUSE_ACTION,
    PAUSE_OBJECT_AD,
    PAUSE_OBJECT_CAMPAIGN,
    ClaimRecord,
    ClaimReuseResult,
    LivePlacement,
    evaluate_claim_records,
    ledger_is_blocked,
)
from workflow_state import get_state_value, set_state_value

MediaPauseRunner = Callable[[str, str, str], Any]


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def parse_as_of(value: str | date | None) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = (value or "").strip()
    if not text:
        return utc_today()
    return date.fromisoformat(text[:10])


def _as_claim_dicts(raw: Any) -> list[dict[str, Any]]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    raise ValueError("claims must be a JSON object, list, or empty")


def parse_claim_records(raw: Any) -> list[ClaimRecord]:
    records: list[ClaimRecord] = []
    for item in _as_claim_dicts(raw):
        payload = dict(item)
        payload.setdefault("claim_id", str(uuid4()))
        records.append(ClaimRecord.model_validate(payload))
    return records


def load_ledger() -> list[dict[str, Any]]:
    stored = get_state_value(CLAIMS_LEDGER_STATE_KEY) or []
    return stored if isinstance(stored, list) else []


def save_ledger(records: list[ClaimRecord] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for item in records:
        if isinstance(item, ClaimRecord):
            payload.append(item.model_dump(mode="json"))
        else:
            payload.append(item)
    set_state_value(CLAIMS_LEDGER_STATE_KEY, payload)
    return payload


def upsert_records(records: list[ClaimRecord]) -> list[dict[str, Any]]:
    by_id = {item.get("claim_id"): item for item in load_ledger() if isinstance(item, dict)}
    for record in records:
        by_id[record.claim_id] = record.model_dump(mode="json")
    payload = list(by_id.values())
    set_state_value(CLAIMS_LEDGER_STATE_KEY, payload)
    return payload


def evaluate_and_store(
    raw_claims: Any,
    *,
    image_description: str = "",
    as_of: str | date | None = None,
) -> dict[str, Any]:
    records = parse_claim_records(raw_claims)
    checked_on = parse_as_of(as_of)
    results = evaluate_claim_records(
        records,
        as_of=checked_on,
        image_description=image_description,
    )
    if records:
        upsert_records(records)
    blocked = ledger_is_blocked(results)
    outcome = CLAIMS_LEDGER_OUTCOME_BLOCKED if blocked else CLAIMS_LEDGER_OUTCOME_PASS
    set_state_value(CLAIMS_LEDGER_OUTCOME_KEY, outcome)
    return {
        "outcome": outcome,
        "as_of": checked_on.isoformat(),
        "results": [item.model_dump() for item in results],
        "records": [record.model_dump(mode="json") for record in records],
    }


def record_live_placement(
    claim_id: str,
    *,
    post_id: str | None = None,
    ad_id: str | None = None,
    campaign_id: str | None = None,
) -> dict[str, Any]:
    placement = LivePlacement(post_id=post_id or None, ad_id=ad_id or None, campaign_id=campaign_id or None)
    stored = load_ledger()
    found = False
    for item in stored:
        if item.get("claim_id") != claim_id:
            continue
        found = True
        placements = item.get("live_placements") or item.get("pause_list") or []
        dumped = placement.model_dump(mode="json")
        if dumped not in placements:
            placements.append(dumped)
        item["live_placements"] = placements
    if not found:
        raise ValueError(f"Claim '{claim_id}' is not on the ledger")
    set_state_value(CLAIMS_LEDGER_STATE_KEY, stored)
    return {"claim_id": claim_id, "live_placements": next(
        item.get("live_placements") for item in stored if item.get("claim_id") == claim_id
    )}


def attach_current_media_ids_to_ledger() -> list[str]:
    """After Media writes IDs to state, attach them to every current ledger line."""
    post_id = str(get_state_value("page_post_id") or "").strip()
    ad_id = str(get_state_value("ad_id") or "").strip()
    campaign_id = str(get_state_value("campaign_id") or "").strip()
    if not (post_id or ad_id or campaign_id):
        return []
    stored = load_ledger()
    touched: list[str] = []
    placement = LivePlacement(
        post_id=post_id or None,
        ad_id=ad_id or None,
        campaign_id=campaign_id or None,
    ).model_dump(mode="json")
    for item in stored:
        claim_id = str(item.get("claim_id") or "")
        placements = item.get("live_placements") or []
        if placement not in placements:
            placements.append(placement)
            item["live_placements"] = placements
        if claim_id:
            touched.append(claim_id)
    if stored:
        set_state_value(CLAIMS_LEDGER_STATE_KEY, stored)
    return touched


def pause_plan_for_claim(claim_id: str) -> dict[str, Any]:
    stored = load_ledger()
    record = next((item for item in stored if item.get("claim_id") == claim_id), None)
    if record is None:
        return {"error": f"Claim '{claim_id}' is not on the ledger", "claim_id": claim_id}
    placements = record.get("live_placements") or record.get("pause_list") or []
    post_ids: list[str] = []
    ad_ids: list[str] = []
    campaign_ids: list[str] = []
    media_actions: list[dict[str, str]] = []
    ops_actions: list[dict[str, str]] = []
    for raw in placements:
        post_id = str((raw or {}).get("post_id") or "").strip()
        ad_id = str((raw or {}).get("ad_id") or "").strip()
        campaign_id = str((raw or {}).get("campaign_id") or "").strip()
        if post_id and post_id not in post_ids:
            post_ids.append(post_id)
        if ad_id and ad_id not in ad_ids:
            ad_ids.append(ad_id)
            media_actions.append(
                {
                    "tool": "CampaignLifecycle",
                    "action": PAUSE_ACTION,
                    "object_type": PAUSE_OBJECT_AD,
                    "object_id": ad_id,
                }
            )
        if campaign_id and campaign_id not in campaign_ids:
            campaign_ids.append(campaign_id)
        if post_id and campaign_id:
            ops_actions.append(
                {
                    "tool": "CampaignScheduler",
                    "action": OPS_PAUSE_POST_ACTION,
                    "campaign_id": campaign_id,
                    "post_id": post_id,
                    "new_status": OPS_POST_STATUS_PAUSED,
                }
            )
        elif campaign_id and not ad_id and not post_id:
            ops_actions.append(
                {
                    "tool": "CampaignScheduler",
                    "action": OPS_PAUSE_CAMPAIGN_ACTION,
                    "campaign_id": campaign_id,
                }
            )
        if campaign_id and not ad_id:
            media_actions.append(
                {
                    "tool": "CampaignLifecycle",
                    "action": PAUSE_ACTION,
                    "object_type": PAUSE_OBJECT_CAMPAIGN,
                    "object_id": campaign_id,
                }
            )
    return {
        "claim_id": claim_id,
        "line": record.get("line") or "",
        "post_ids": post_ids,
        "ad_ids": ad_ids,
        "campaign_ids": campaign_ids,
        "pause_list": placements,
        "media_actions": media_actions,
        "ops_actions": ops_actions,
        "note": (
            "IDs only until execute_ops_pause or an injected media runner. "
            "Do not spend ad budget. CampaignLifecycle is listed for Media, not auto-run."
        ),
    }


def execute_pause_list(
    claim_id: str,
    *,
    execute_ops_pause: bool = False,
    execute_media_pause: bool = False,
    media_pause_runner: Optional[MediaPauseRunner] = None,
) -> dict[str, Any]:
    """Pause those recorded IDs. Graph/Media runs only when a runner is injected."""
    plan = pause_plan_for_claim(claim_id)
    if plan.get("error"):
        return plan
    ops_results: list[Any] = []
    media_results: list[Any] = []
    if execute_ops_pause:
        from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler

        for action in plan["ops_actions"]:
            if action["action"] == OPS_PAUSE_CAMPAIGN_ACTION:
                ops_results.append(
                    json.loads(
                        CampaignScheduler(
                            action=OPS_PAUSE_CAMPAIGN_ACTION,
                            campaign_id=action["campaign_id"],
                        ).run()
                    )
                )
            elif action["action"] == OPS_PAUSE_POST_ACTION:
                ops_results.append(
                    json.loads(
                        CampaignScheduler(
                            action=OPS_PAUSE_POST_ACTION,
                            campaign_id=action["campaign_id"],
                            post_id=action["post_id"],
                            new_status=OPS_POST_STATUS_PAUSED,
                        ).run()
                    )
                )
    if execute_media_pause and media_pause_runner is not None:
        for action in plan["media_actions"]:
            media_results.append(
                media_pause_runner(
                    action["action"],
                    action["object_type"],
                    action["object_id"],
                )
            )
    elif execute_media_pause:
        media_results.append(
            {
                "skipped": True,
                "reason": "No media runner injected; Graph pause not auto-run.",
            }
        )
    plan["ops_results"] = ops_results
    plan["media_results"] = media_results
    plan["executed_ops"] = bool(execute_ops_pause)
    plan["executed_media"] = bool(execute_media_pause and media_pause_runner is not None)
    return plan


def reuse_results_to_concerns(results: list[ClaimReuseResult] | list[dict[str, Any]]) -> list[dict[str, str]]:
    from manifest_types.component_types import POLICY_AREA_CAPTION_ONLY, POLICY_AREA_CLAIMS_LEDGER

    concerns: list[dict[str, str]] = []
    for item in results:
        payload = item.model_dump() if isinstance(item, ClaimReuseResult) else item
        if payload.get("can_reuse", True):
            continue
        blockers = payload.get("blockers") or []
        area = (
            POLICY_AREA_CAPTION_ONLY
            if CLAIM_BLOCK_CAPTION_ONLY in blockers
            else POLICY_AREA_CLAIMS_LEDGER
        )
        concerns.append(
            {
                "severity": "blocked",
                "area": area,
                "reason": (
                    "A line on the claims record cannot be reused: "
                    + ", ".join(blockers)
                    + f" (claim {payload.get('claim_id')})"
                ),
                "required_fix": (
                    "Cover the picture on the same record, add a source for facts, "
                    "add founder proof for regulated claims, or refresh the review-by date."
                ),
            }
        )
    return concerns
