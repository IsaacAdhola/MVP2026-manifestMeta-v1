from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional

from safe_audit_log import write_audit_event
from workflow_state import set_state_value


class SearchVisibilityBriefBuilder(BaseTool):
    """
    Builds a structured SEO / AEO / GEO strategy brief from confirmed campaign inputs.
    Persist the brief for handoff to the Chief Growth Strategist or Senior Conversion Copywriter.
    The agent should still consult knowledge files in files/ for depth before finalizing recommendations.
    """

    business_or_category: str = Field(..., description="Client business name or category.")
    topic_or_offer: str = Field(..., description="Primary topic, product, or offer to optimize for.")
    audience: str = Field(default="", description="Target audience summary.")
    geography: str = Field(default="", description="Geography or market if relevant.")
    campaign_goal: str = Field(
        default="",
        description="Business goal: leads, bookings, awareness, traffic, authority, etc.",
    )
    primary_keyword: str = Field(default="", description="Proposed primary keyword if already known.")
    secondary_keywords: str = Field(
        default="",
        description="Comma-separated secondary / LSI keywords if already known.",
    )
    search_intent: str = Field(
        default="",
        description="informational, navigational, commercial, transactional, or mixed.",
    )
    market_insights: str = Field(
        default="",
        description="Relevant findings from Market Intelligence (gaps, questions, competitor themes).",
    )
    content_format: str = Field(
        default="",
        description="Recommended format: how-to, listicle, comparison, pillar, FAQ-led, case study, etc.",
    )

    def run(self):
        secondary = [
            item.strip()
            for item in (self.secondary_keywords or "").split(",")
            if item.strip()
        ]

        brief = {
            "role": "search_visibility_strategy_brief",
            "business_or_category": self.business_or_category,
            "topic_or_offer": self.topic_or_offer,
            "audience": self.audience,
            "geography": self.geography,
            "campaign_goal": self.campaign_goal,
            "seo": {
                "primary_keyword": self.primary_keyword,
                "secondary_keywords": secondary,
                "search_intent": self.search_intent,
                "content_format": self.content_format,
                "on_page_notes": (
                    "Consult Search_Engine_Optimization.pdf for title/meta, header, "
                    "and keyword placement standards before locking the brief."
                ),
            },
            "aeo": {
                "answer_first_opening": True,
                "faq_recommended": True,
                "direct_answer_blocks": True,
                "notes": (
                    "Consult answer_engine_optimization_holtschulte_202508.pdf for "
                    "answer-engine patterns and citation-friendly structure."
                ),
            },
            "geo": {
                "citation_friendly_claims": True,
                "clear_entity_context": True,
                "structured_takeaways": True,
                "notes": (
                    "Consult GEO.pdf for generative-engine visibility tactics "
                    "before finalizing GEO checklist items."
                ),
            },
            "market_insights": self.market_insights,
            "handoff": (
                "Pass this finished strategy package to the Chief Growth Strategist "
                "or Senior Conversion Copywriter. Do not include private reasoning, "
                "tokens, or raw tool dumps."
            ),
            "knowledge_reminder": "Search files/ PDFs via File Search; do not invent contradicting rules.",
        }

        set_state_value("search_visibility_brief", brief)
        write_audit_event(
            event_type="search_visibility_brief_built",
            actor="Search & Answer Visibility Director",
            outcome="brief_ready",
            details={
                "business_or_category": self.business_or_category,
                "has_primary_keyword": bool(self.primary_keyword),
                "secondary_keyword_count": len(secondary),
                "content_format": self.content_format or "unspecified",
            },
        )
        return brief


if __name__ == "__main__":
    tool = SearchVisibilityBriefBuilder(
        business_or_category="Med spa",
        topic_or_offer="Botox for first-time patients",
        audience="Women 30-55 in North Dallas",
        geography="Plano, Frisco, Allen",
        campaign_goal="booked consultations",
        primary_keyword="first time botox what to expect",
        secondary_keywords="botox consultation, botox recovery, med spa near me",
        search_intent="informational",
        content_format="how-to with FAQ",
    )
    print(tool.run())
