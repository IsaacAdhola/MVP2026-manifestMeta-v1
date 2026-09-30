"""Claims ledger: policy gate, caption-only failure, pause-list helper."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

NESTED = Path(__file__).resolve().parent
ROOT = NESTED.parent
for _path in (str(NESTED), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler
from FacebookPolicyAgent.tools.FacebookPolicyChecklist import FacebookPolicyChecklist
from FacebookManagerAgent.tools.PauseClaimPlacements import PauseClaimPlacements
from claims_ledger import (
    attach_current_media_ids_to_ledger,
    execute_pause_list,
    record_live_placement,
    save_ledger,
)
from manifest_types.component_types import (
    CLAIM_BLOCK_CAPTION_ONLY,
    CLAIM_BLOCK_FACT_EXPIRED,
    CLAIM_BLOCK_FACT_NO_SOURCE,
    CLAIM_BLOCK_REGULATED_NO_PROOF,
    CLAIMS_LEDGER_STATE_KEY,
    ClaimRecord,
    ClaimType,
)
from workflow_state import clear_state, get_state_value, set_state_value

AS_OF = "2026-09-30"


def _safe_policy(**overrides):
    payload = {
        "caption_or_body": "Book a consultation to improve your marketing workflow.",
        "headline": "Grow with clearer automation",
        "call_to_action": "Book Now",
        "destination_link": "https://example.com",
        "audience_or_targeting": "Small business owners in the United States",
        "campaign_type": "facebook_page_post",
        "client_approved": True,
        "as_of_date": AS_OF,
    }
    payload.update(overrides)
    return FacebookPolicyChecklist(**payload).run()


def test_existing_caption_sample_still_approves_without_visual_claims() -> None:
    clear_state()
    result = _safe_policy()
    assert result["outcome"] == "approved"
    assert get_state_value("policy_outcome") == "approved"


def test_puffery_passes_without_source() -> None:
    clear_state()
    result = _safe_policy(
        caption_or_body="Best coffee in town",
        headline="Best coffee in town",
        claims_json=json.dumps(
            [
                {
                    "claim_id": "puffery-1",
                    "line": "Best coffee in town",
                    "claim_type": "puffery",
                }
            ]
        ),
    )
    assert result["outcome"] == "approved"
    blockers = []
    for item in result["claims_ledger"]["results"]:
        blockers.extend(item.get("blockers") or [])
    assert blockers == []


def test_fact_without_source_is_blocked() -> None:
    clear_state()
    result = _safe_policy(
        caption_or_body="4.9 stars",
        headline="4.9 stars",
        claims_json=json.dumps(
            [
                {
                    "claim_id": "fact-1",
                    "line": "4.9 stars",
                    "claim_type": "fact",
                    "review_by": "2026-12-31",
                }
            ]
        ),
    )
    assert result["outcome"] == "blocked"
    assert any(
        CLAIM_BLOCK_FACT_NO_SOURCE in (item.get("blockers") or [])
        for item in result["claims_ledger"]["results"]
    )


def test_expired_fact_cannot_be_reused() -> None:
    clear_state()
    result = _safe_policy(
        caption_or_body="50% off this week",
        headline="50% off",
        claims_json=json.dumps(
            [
                {
                    "claim_id": "offer-1",
                    "line": "50% off this week",
                    "claim_type": "fact",
                    "source": "Founder promo sheet",
                    "review_by": "2026-08-01",
                    "stale_category": "offer",
                }
            ]
        ),
    )
    assert result["outcome"] == "blocked"
    assert any(
        CLAIM_BLOCK_FACT_EXPIRED in (item.get("blockers") or [])
        for item in result["claims_ledger"]["results"]
    )


def test_regulated_without_founder_proof_is_blocked() -> None:
    clear_state()
    result = _safe_policy(
        caption_or_body="Cures pain",
        headline="Cures pain",
        claims_json=json.dumps(
            [
                {
                    "claim_id": "reg-1",
                    "line": "Cures pain",
                    "claim_type": "regulated",
                }
            ]
        ),
    )
    assert result["outcome"] == "blocked"
    assert any(
        CLAIM_BLOCK_REGULATED_NO_PROOF in (item.get("blockers") or [])
        for item in result["claims_ledger"]["results"]
    )


def test_caption_only_fails_when_picture_has_star_badge() -> None:
    clear_state()
    result = _safe_policy(
        caption_or_body="Best coffee in town",
        headline="Best coffee in town",
        image_description="Gold star badge, before-and-after, text baked into the picture",
        claims_json=json.dumps(
            [
                {
                    "claim_id": "caption-only-1",
                    "line": "Best coffee in town",
                    "claim_type": "puffery",
                    "image_reviewed": False,
                }
            ]
        ),
    )
    assert result["outcome"] == "blocked"
    assert any(
        CLAIM_BLOCK_CAPTION_ONLY in (item.get("blockers") or [])
        for item in result["claims_ledger"]["results"]
    )


def test_same_record_covers_image_when_reviewed() -> None:
    clear_state()
    result = _safe_policy(
        caption_or_body="4.9 stars",
        headline="4.9 stars",
        image_description="Gold star badge with 4.9 baked into the picture",
        image_reviewed=True,
        claims_json=json.dumps(
            [
                {
                    "claim_id": "image-ok",
                    "line": "4.9 stars",
                    "claim_type": "fact",
                    "source": "Google Business Profile 2026-09-01",
                    "review_by": "2026-12-31",
                    "image_claims": [
                        {
                            "kind": "star_badge",
                            "description": "Gold 4.9 star badge in the corner",
                        },
                        {
                            "kind": "baked_in_text",
                            "description": "4.9 painted on the cup",
                        },
                    ],
                }
            ]
        ),
    )
    assert result["outcome"] == "approved"
    stored = get_state_value(CLAIMS_LEDGER_STATE_KEY) or []
    assert stored[0]["image_reviewed"] is True
    assert len(stored[0]["image_claims"]) == 2


def test_pause_list_records_ids_and_ops_pauses_only_those() -> None:
    clear_state()
    save_ledger(
        [
            ClaimRecord(
                claim_id="pause-line",
                line="4.9 stars",
                claim_type=ClaimType.FACT,
                source="Google rating",
                review_by=date(2026, 12, 31),
            )
        ]
    )
    created = json.loads(
        CampaignScheduler(
            action="create_campaign",
            campaign_name="Claims pause drill",
            client_name="Claims Ledger Test",
            campaign_type="organic_facebook",
        ).run()
    )
    campaign_id = created["campaign"]["id"]
    posted = json.loads(
        CampaignScheduler(
            action="add_post",
            campaign_id=campaign_id,
            platform="Facebook",
            scheduled_time="2026-10-01T15:00:00Z",
            content_summary="Line used 4.9 stars",
        ).run()
    )
    post_id = posted["post"]["id"]
    record_live_placement(
        "pause-line",
        post_id=post_id,
        ad_id="ad_pause_only",
        campaign_id=campaign_id,
    )
    listed = json.loads(PauseClaimPlacements(claim_id="pause-line").run())
    assert listed["post_ids"] == [post_id]
    assert listed["ad_ids"] == ["ad_pause_only"]
    assert listed["campaign_ids"] == [campaign_id]
    assert listed.get("executed_ops") in (None, False)

    media_calls: list[tuple[str, str, str]] = []

    def _fake_media(action: str, object_type: str, object_id: str) -> dict:
        media_calls.append((action, object_type, object_id))
        return {"status": "updated", "object_id": object_id}

    executed = execute_pause_list(
        "pause-line",
        execute_ops_pause=True,
        execute_media_pause=True,
        media_pause_runner=_fake_media,
    )
    assert executed["executed_ops"] is True
    assert executed["executed_media"] is True
    assert media_calls == [("pause", "ad", "ad_pause_only")]
    posts = json.loads(CampaignScheduler(action="list_posts", campaign_id=campaign_id).run())["posts"]
    target = next(item for item in posts if item["id"] == post_id)
    assert target["status"] == "paused"
    other = json.loads(
        CampaignScheduler(
            action="create_campaign",
            campaign_name="Unrelated campaign",
            client_name="Claims Ledger Test",
            campaign_type="organic_facebook",
        ).run()
    )
    other_id = other["campaign"]["id"]
    listed_all = json.loads(CampaignScheduler(action="list_campaigns").run())["campaigns"]
    other_row = next(item for item in listed_all if item["id"] == other_id)
    assert other_row["status"] != "paused"


def test_attach_media_ids_records_pause_list_without_graph() -> None:
    clear_state()
    save_ledger(
        [
            ClaimRecord(
                claim_id="live-line",
                line="Best coffee in town",
                claim_type=ClaimType.PUFFERY,
            )
        ]
    )
    set_state_value("page_post_id", "post_live_1")
    set_state_value("ad_id", "ad_live_1")
    set_state_value("campaign_id", "camp_live_1")
    touched = attach_current_media_ids_to_ledger()
    assert touched == ["live-line"]
    stored = get_state_value(CLAIMS_LEDGER_STATE_KEY)[0]
    placement = stored["live_placements"][0]
    assert placement["post_id"] == "post_live_1"
    assert placement["ad_id"] == "ad_live_1"
    assert placement["campaign_id"] == "camp_live_1"
