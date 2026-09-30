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


class CroAuditChecklist(BaseTool):
    """
    Audits existing landing-page copy for conversion leaks.
    """

    page_copy: str = Field(..., description="Existing page copy or transcript.")
    campaign_goal: str = Field(default="leads", description="Intended conversion.")
    ad_promise: str = Field(default="", description="Ad promise to check message match.")

    def run(self):
        try:
            audit = llm_text(
                MODEL_CLAUDE,
                "You are a CRO auditor. Be blunt. Do not invent missing proof.",
                (
                    f"Goal: {self.campaign_goal}\nAd promise: {self.ad_promise or 'none'}\n\n"
                    f"Page copy:\n{self.page_copy}\n\n"
                    "Score message match, CTA clarity, proof, friction, and trust. "
                    "Give the top 5 fixes in priority order."
                ),
            )
            set_state_value("cro_audit", audit)
            return audit
        except Exception as exc:
            log_error("Landing Page & CRO Director", exc, location="CroAuditChecklist.run")
            return json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
