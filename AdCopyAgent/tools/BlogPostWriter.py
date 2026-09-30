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

from copy_llm import complete_copy


class BlogPostWriter(BaseTool):
    """
    Writes one SEO blog draft from a Search Visibility brief and research inputs.
    """

    topic: str = Field(..., description="Blog topic or offer.")
    primary_keyword: str = Field(..., description="Primary SEO keyword.")
    secondary_keywords: str = Field(
        default="",
        description="Comma-separated secondary keywords.",
    )
    audience: str = Field(..., description="Target reader.")
    business_and_offer: str = Field(..., description="Client business and offer.")
    search_intent: str = Field(default="commercial", description="Search intent.")
    word_count: int = Field(default=900, description="Target word count, 600 to 2000.")

    def run(self):
        try:
            words = max(600, min(self.word_count, 2000))
            draft = complete_copy(
                "You are a senior SEO copywriter. Write for humans first. "
                "Do not fabricate statistics, citations, or named studies. "
                "Do not mention internal tools.",
                (
                    f"{copy_context()}\n\n"
                    f"Write one blog draft of about {words} words.\n"
                    f"Business: {self.business_and_offer}\n"
                    f"Audience: {self.audience}\n"
                    f"Topic: {self.topic}\n"
                    f"Primary keyword: {self.primary_keyword}\n"
                    f"Secondary keywords: {self.secondary_keywords}\n"
                    f"Intent: {self.search_intent}\n\n"
                    "Include: SEO title, meta description, H2/H3 structure, "
                    "keyword in title, first paragraph, and at least two headers, "
                    "internal/external link placeholders, image alt-text suggestions, "
                    "and a closing CTA."
                ),
                max_tokens=3500,
            )
            set_state_value("blog_draft", draft)
            set_state_value("ad_copy", draft[:500])
            set_state_value("ad_headline", self.primary_keyword)
            return draft
        except Exception as exc:
            log_error("Senior Conversion Copywriter", exc, location="BlogPostWriter.run")
            return f"Blog draft failed: {type(exc).__name__}: {exc}"
