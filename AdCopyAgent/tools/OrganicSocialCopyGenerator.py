from agency_swarm.tools import BaseTool
from pydantic import Field

from error_logger import log_error
from workflow_state import copy_context, set_state_value

import os
import sys

_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(_AGENT_DIR)
for path in (_ROOT, _AGENT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from copy_llm import complete_copy, parse_copy_options


class OrganicSocialCopyGenerator(BaseTool):
    """
    Writes three organic social caption options for Facebook, Instagram, or LinkedIn.
    """

    platform: str = Field(
        default="facebook",
        description="facebook, instagram, or linkedin.",
    )
    audience: str = Field(..., description="Target audience.")
    offer_or_message: str = Field(..., description="What the post should communicate.")
    tone: str = Field(default="premium, warm, confident", description="Brand tone.")
    campaign_goal: str = Field(default="awareness", description="Post goal.")

    def run(self):
        try:
            platform = (self.platform or "facebook").strip().lower()
            text = complete_copy(
                "You are a senior social copywriter. Write three distinct organic "
                "caption options. No guarantees, no fabricated stats, no internal tools.",
                (
                    f"{copy_context()}\n\n"
                    f"Platform: {platform}\nAudience: {self.audience}\n"
                    f"Message: {self.offer_or_message}\nTone: {self.tone}\n"
                    f"Goal: {self.campaign_goal}\n\n"
                    "Use this exact format:\n"
                    "Option 1:\nHeadline: [short hook]\nAd Copy: [caption]\n"
                    "Rationale: [one sentence]\n"
                    "(repeat for Option 2 and Option 3)\n"
                    "Keep Facebook/LinkedIn captions under 400 characters. "
                    "Instagram captions may include a short hashtag line at the end."
                ),
                max_tokens=1200,
            )
            parsed = parse_copy_options(text)
            if parsed:
                set_state_value("ad_copy_options", parsed)
                set_state_value("ad_headline", parsed[0]["headline"])
                set_state_value("ad_copy", parsed[0]["ad_copy"])
                set_state_value("pending_client_copy", True)
            return text
        except Exception as exc:
            log_error("Senior Conversion Copywriter", exc, location="OrganicSocialCopyGenerator.run")
            return f"Organic copy generation failed: {type(exc).__name__}: {exc}"
