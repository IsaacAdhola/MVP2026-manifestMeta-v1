import json
import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from CampaignOpsAgent.tools.CampaignDashboard import CampaignDashboard
from error_logger import log_error
from model_router import MODEL_CLAUDE, llm_text
from workflow_state import set_state_value


class PerformanceInsightBuilder(BaseTool):
    """
    Builds a client-safe performance brief from operations data and optional live metrics.
    """

    client_name: str = Field(..., description="Client name used in campaign ops records.")
    campaign_goal: str = Field(default="", description="Stated campaign goal.")
    live_metrics_json: str = Field(
        default="",
        description="Optional JSON or notes from Ads Manager. Leave empty if unavailable.",
    )

    def run(self):
        try:
            dashboard = CampaignDashboard(client_name=self.client_name).run()
            brief = llm_text(
                MODEL_CLAUDE,
                "You are Manifest AI's Performance Analyst. Be precise. Never invent metrics.",
                (
                    f"Client: {self.client_name}\nGoal: {self.campaign_goal}\n\n"
                    f"Operations dashboard JSON:\n{dashboard}\n\n"
                    f"Live metrics (may be empty):\n{self.live_metrics_json or 'none'}\n\n"
                    "Write a performance brief with: what happened, budget health, "
                    "risks, and 3 recommended next actions. Label missing data as unknown."
                ),
            )
            package = {"client_name": self.client_name, "brief": brief, "dashboard": dashboard}
            try:
                package["dashboard"] = json.loads(dashboard)
            except Exception:
                package["dashboard"] = dashboard
            set_state_value("performance_brief", package)
            return json.dumps({"status": "complete", "brief": brief}, ensure_ascii=False)
        except Exception as exc:
            log_error("Performance Analyst", exc, location="PerformanceInsightBuilder.run")
            return json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
