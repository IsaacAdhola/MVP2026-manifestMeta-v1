import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from error_logger import log_error
from workflow_state import set_state_value


class ClientBriefRecorder(BaseTool):
    """
    Locks the client intake brief into workflow state so specialists receive one clean package.
    """

    business: str = Field(..., description="What the business sells or offers.")
    campaign_goal: str = Field(..., description="Campaign goal.")
    target_customer: str = Field(default="", description="Audience if known.")
    geography: str = Field(default="", description="City, region, or country.")
    campaign_type: str = Field(
        default="",
        description="paid or organic. Leave empty if the client has not confirmed.",
    )
    platform: str = Field(
        default="",
        description="facebook, instagram, or both. Leave empty if unknown.",
    )
    budget: str = Field(default="", description="Budget notes for paid campaigns.")
    go_live: str = Field(default="", description="Schedule, date, time, timezone, or post now.")
    destination_link: str = Field(
        default="",
        description="Landing page or destination URL for paid ads.",
    )
    brand_notes: str = Field(default="", description="Tone, visual preferences, or things to avoid.")

    def run(self):
        try:
            brief = {
                "business": self.business,
                "campaign_goal": self.campaign_goal,
                "target_customer": self.target_customer,
                "geography": self.geography,
                "campaign_type": self.campaign_type,
                "platform": self.platform,
                "budget": self.budget,
                "go_live": self.go_live,
                "destination_link": self.destination_link,
                "brand_notes": self.brand_notes,
            }
            set_state_value("client_brief", brief)
            if self.destination_link:
                set_state_value("destination_link", self.destination_link)
            set_state_value("handoff_status", "intake_recorded")
            missing = [
                name
                for name, value in (
                    ("campaign_type", self.campaign_type),
                    ("platform", self.platform),
                )
                if not str(value).strip()
            ]
            return {
                "status": "recorded",
                "brief": brief,
                "still_needed_before_execution": missing,
            }
        except Exception as exc:
            log_error("Chief Growth Strategist", exc, location="ClientBriefRecorder.run")
            return f"Brief recording failed: {type(exc).__name__}: {exc}"
