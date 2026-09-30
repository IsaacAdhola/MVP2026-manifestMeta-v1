import json
import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_NESTED = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOT = os.path.dirname(_NESTED)
for _path in (_NESTED, _ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from claims_ledger import execute_pause_list, pause_plan_for_claim


class PauseClaimPlacements(BaseTool):
    """
    Lists live posts and ads that used a claims-ledger line so Media can pause
    those IDs only. Records IDs; does not spend ad budget. Graph pause is never
    auto-run — CampaignLifecycle stays a separate founder-gated Media step.
    Optional execute_ops_pause updates the local CampaignScheduler pause list.
    """

    claim_id: str = Field(..., description="Claims-ledger claim_id whose live placements should be paused.")
    execute_ops_pause: bool = Field(
        default=False,
        description=(
            "If true, pause matching CampaignScheduler posts/campaigns locally. "
            "Default false: return the pause list only."
        ),
    )

    def run(self):
        claim_id = (self.claim_id or "").strip()
        if not claim_id:
            return json.dumps({"error": "claim_id is required"})
        if self.execute_ops_pause:
            result = execute_pause_list(
                claim_id,
                execute_ops_pause=True,
                execute_media_pause=False,
            )
        else:
            result = pause_plan_for_claim(claim_id)
        return json.dumps(result, ensure_ascii=True)


if __name__ == "__main__":
    from claims_ledger import save_ledger
    from manifest_types.component_types import ClaimRecord, ClaimType
    from workflow_state import clear_state

    clear_state()
    save_ledger(
        [
            ClaimRecord(
                claim_id="demo-pause",
                line="Best coffee in town",
                claim_type=ClaimType.PUFFERY,
            )
        ]
    )
    print(PauseClaimPlacements(claim_id="demo-pause", execute_ops_pause=False).run())
