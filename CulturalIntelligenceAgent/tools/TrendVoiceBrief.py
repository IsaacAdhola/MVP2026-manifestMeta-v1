import json
import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from error_logger import log_error
from model_router import MODEL_GROK, llm_text
from workflow_state import set_state_value


class TrendVoiceBrief(BaseTool):
    """
    Builds a cultural voice and angle brief for copy and creative.
    """

    business: str = Field(..., description="Business and offer.")
    audience: str = Field(..., description="Target audience.")
    geography: str = Field(default="", description="Market geography.")
    market_notes: str = Field(default="", description="Facts from market research, if any.")

    def run(self):
        try:
            brief = llm_text(
                MODEL_GROK,
                "You are Manifest AI's Cultural Intelligence Director. Be specific. No fake competitor quotes.",
                (
                    f"Business: {self.business}\nAudience: {self.audience}\n"
                    f"Geography: {self.geography}\nMarket notes: {self.market_notes or 'none'}\n\n"
                    "Deliver: how this audience talks, one sharp campaign angle, "
                    "words to use, words to avoid, and a classy vs. generic contrast."
                ),
            )
            set_state_value("cultural_voice_brief", brief)
            return brief
        except Exception as exc:
            log_error("Cultural Intelligence Director", exc, location="TrendVoiceBrief.run")
            return json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
