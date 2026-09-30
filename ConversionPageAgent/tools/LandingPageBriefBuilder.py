import json
import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from error_logger import log_error
from model_router import MODEL_CLAUDE, llm_text
from workflow_state import set_state_value


class LandingPageBriefBuilder(BaseTool):
    """
    Builds a conversion landing-page brief: headline, sections, proof, CTA, objections.
    """

    business: str = Field(..., description="Business and offer.")
    audience: str = Field(..., description="Who the page is for.")
    campaign_goal: str = Field(..., description="Lead, purchase, booking, or signup.")
    ad_promise: str = Field(default="", description="Promise used in the ad, if any.")

    def run(self):
        try:
            brief = llm_text(
                MODEL_CLAUDE,
                "You are Manifest AI's Landing Page & CRO Director. No fake proof.",
                (
                    f"Business: {self.business}\nAudience: {self.audience}\n"
                    f"Goal: {self.campaign_goal}\nAd promise: {self.ad_promise or 'none'}\n\n"
                    "Deliver: hero headline + subhead, offer block, 3 proof slots "
                    "(label as placeholders if proof was not provided), objection handling, "
                    "primary CTA, form fields, and a message-match note vs the ad promise."
                ),
            )
            set_state_value("landing_page_brief", brief)
            return brief
        except Exception as exc:
            log_error("Landing Page & CRO Director", exc, location="LandingPageBriefBuilder.run")
            return json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
