from agency_swarm.tools import BaseTool
from pydantic import Field

from error_logger import log_error
from workflow_state import copy_context, get_state_value, set_state_value

import os
import sys

_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(_AGENT_DIR)
for path in (_ROOT, _AGENT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from copy_llm import complete_copy


class CopyReviser(BaseTool):
    """
    Revises selected copy from client feedback or policy required fixes.
    """

    revision_notes: str = Field(..., description="What to change.")
    current_copy: str = Field(
        default="",
        description="Copy to revise. If empty, uses the selected copy in workflow state.",
    )

    def run(self):
        try:
            source = (self.current_copy or get_state_value("ad_copy") or "").strip()
            if not source:
                return "No copy found to revise. Provide current_copy or generate copy first."
            revised = complete_copy(
                "Revise the copy. Keep facts intact. Do not add guarantees, "
                "fabricated stats, or internal tool names.",
                f"{copy_context()}\n\nRevision notes:\n{self.revision_notes}\n\nCopy:\n{source}",
                max_tokens=1200,
            )
            set_state_value("ad_copy", revised)
            set_state_value("pending_client_copy", True)
            return revised
        except Exception as exc:
            log_error("Senior Conversion Copywriter", exc, location="CopyReviser.run")
            return f"Copy revision failed: {type(exc).__name__}: {exc}"
