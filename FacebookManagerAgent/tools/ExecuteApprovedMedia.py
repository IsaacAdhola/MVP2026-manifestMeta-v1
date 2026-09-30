import json
import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from error_logger import log_error
from claims_ledger import attach_current_media_ids_to_ledger
from workflow_state import (
    get_media_package,
    is_paid_campaign,
    missing_for_organic,
    missing_for_paid,
    set_state_value,
)

from FacebookManagerAgent.tools.AdCampaignStarter import AdCampaignStarter
from FacebookManagerAgent.tools.AdCreator import AdCreator
from FacebookManagerAgent.tools.AdSetCreator import AdSetCreator
from FacebookManagerAgent.tools.FacebookPagePostPublisher import FacebookPagePostPublisher
from FacebookManagerAgent.tools.FacebookPhotoPostPublisher import FacebookPhotoPostPublisher


class ExecuteApprovedMedia(BaseTool):
    """
    Publishes an organic Facebook photo post or builds a paused paid Meta campaign
    from shared workflow state. Use this after policy and client approval.
    """

    execution_path: str = Field(
        default="",
        description="organic or paid. Leave empty to use the locked client brief.",
    )
    destination_link: str = Field(
        default="",
        description="Landing page URL for paid ads. Uses shared state when empty.",
    )
    published: bool = Field(
        default=True,
        description="For organic posts: publish now. Set false for a draft/unpublished photo.",
    )
    activate_immediately: bool = Field(
        default=False,
        description="For paid campaigns: set true only with explicit client go-live. Default stays paused.",
    )

    def run(self):
        actor = "Media Operations Director"
        try:
            pkg = get_media_package()
            path = (self.execution_path or "").strip().lower()
            if not path:
                path = "paid" if is_paid_campaign(pkg) else "organic"

            if path in {"paid", "paid_meta_ad", "meta_ad"}:
                missing = missing_for_paid(pkg)
                if missing:
                    return (
                        "Paid campaign cannot start. Missing from shared state: "
                        + ", ".join(missing)
                    )
                return self._run_paid(pkg)
            missing = missing_for_organic(pkg)
            if missing:
                return (
                    "Organic Facebook post cannot start. Missing from shared state: "
                    + ", ".join(missing)
                )
            return self._run_organic(pkg)
        except Exception as exc:
            log_error(actor, exc, location="ExecuteApprovedMedia.run")
            return f"Error executing media: {type(exc).__name__}: {exc}"

    def _run_organic(self, pkg: dict) -> str:
        message = pkg["ad_copy"]
        image_path = pkg["image_path"]
        result = FacebookPhotoPostPublisher(
            message=message,
            image_path=image_path,
            published=self.published,
        ).run()
        set_state_value("handoff_status", "organic_executed")
        set_state_value("last_media_result", result)
        attach_current_media_ids_to_ledger()
        return result

    def _run_paid(self, pkg: dict) -> str:
        link = (self.destination_link or pkg["destination_link"]).strip()
        if link:
            set_state_value("destination_link", link)
        budget = pkg["daily_budget_cents"]
        name = (pkg.get("business") or "Manifest AI")[:60] + " campaign"
        steps = []
        if not pkg.get("campaign_id"):
            steps.append(
                AdCampaignStarter(
                    campaign_name=name,
                    budget=budget,
                    activate_immediately=self.activate_immediately,
                ).run()
            )
        steps.append(
            AdSetCreator(
                name=f"{name} ad set",
                budget=budget,
                activate_immediately=self.activate_immediately,
            ).run()
        )
        headline = pkg.get("ad_headline") or name
        steps.append(
            AdCreator(
                name=headline[:80],
                link=link,
            ).run()
        )
        combined = " | ".join(str(item) for item in steps)
        set_state_value("handoff_status", "paid_campaign_built")
        set_state_value("last_media_result", combined)
        attach_current_media_ids_to_ledger()
        return combined
