import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from error_logger import log_error
from workflow_state import get_state_value, set_state_value


class CopySelector(BaseTool):
    """
    Locks the client-selected copy option before creative or publishing.
    """

    selected_option: int = Field(..., description="1, 2, or 3.")

    def run(self):
        try:
            options = get_state_value("ad_copy_options") or []
            index = int(self.selected_option) - 1
            if index < 0 or index >= len(options):
                return f"Invalid copy option {self.selected_option}. Available: {len(options)}."
            selected = options[index]
            set_state_value("selected_copy_option", int(self.selected_option))
            set_state_value("ad_headline", selected.get("headline") or "")
            set_state_value("ad_copy", selected.get("ad_copy") or "")
            set_state_value("pending_client_copy", False)
            return {
                "status": "selected",
                "selected_option": int(self.selected_option),
                "headline": selected.get("headline"),
                "ad_copy": selected.get("ad_copy"),
            }
        except Exception as exc:
            log_error("Senior Conversion Copywriter", exc, location="CopySelector.run")
            return f"Copy selection failed: {type(exc).__name__}: {exc}"
