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


class CommentReplyDrafts(BaseTool):
    """
    Writes three on-brand reply options for a comment, DM, or review.
    """

    incoming_message: str = Field(..., description="The public comment, DM, or review text.")
    brand_voice: str = Field(default="warm, classy, human", description="Brand voice.")
    business_context: str = Field(default="", description="What the business is.")

    def run(self):
        try:
            drafts = llm_text(
                MODEL_GROK,
                "You are Manifest AI's Community Manager. Write like a real person. No guarantees.",
                (
                    f"Business: {self.business_context}\nVoice: {self.brand_voice}\n"
                    f"Incoming message:\n{self.incoming_message}\n\n"
                    "Write three reply options in this format:\n"
                    "Option 1:\nAd Copy: [reply]\nRationale: [one sentence]\n"
                    "(repeat for 2 and 3). Keep replies short."
                ),
                max_tokens=800,
            )
            set_state_value("community_reply_drafts", drafts)
            return drafts
        except Exception as exc:
            log_error("Community Manager", exc, location="CommentReplyDrafts.run")
            return json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
