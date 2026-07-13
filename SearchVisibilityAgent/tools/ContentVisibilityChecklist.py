from agency_swarm.tools import BaseTool
from pydantic import Field

from safe_audit_log import write_audit_event
from workflow_state import get_state_value, set_state_value


class ContentVisibilityChecklist(BaseTool):
    """
    Scores a content draft against high-level SEO / AEO / GEO criteria.
    This is a lightweight scaffold — the agent must still consult knowledge files
    in files/ for depth before issuing final revision guidance.
    """

    title: str = Field(default="", description="Draft SEO title or H1.")
    meta_description: str = Field(default="", description="Draft meta description.")
    body_or_outline: str = Field(
        ...,
        description="Full draft body, outline, or structured sections to score.",
    )
    primary_keyword: str = Field(default="", description="Target primary keyword.")
    secondary_keywords: str = Field(
        default="",
        description="Comma-separated secondary keywords to check for natural presence.",
    )
    content_type: str = Field(
        default="seo_blog",
        description="seo_blog, landing_page, faq_page, or social_to_search_package.",
    )

    def _has(self, haystack: str, needle: str) -> bool:
        if not needle.strip():
            return False
        return needle.strip().lower() in haystack.lower()

    def run(self):
        text = " ".join([self.title, self.meta_description, self.body_or_outline])
        secondary = [
            item.strip()
            for item in (self.secondary_keywords or "").split(",")
            if item.strip()
        ]
        brief = get_state_value("search_visibility_brief") or {}
        if not self.primary_keyword and isinstance(brief, dict):
            self.primary_keyword = (
                (brief.get("seo") or {}).get("primary_keyword") or ""
            )

        checks = []

        # SEO (high-level)
        seo_title_kw = self._has(self.title, self.primary_keyword) if self.primary_keyword else False
        checks.append(
            {
                "pillar": "seo",
                "criterion": "primary_keyword_in_title",
                "pass": seo_title_kw,
                "note": "Primary keyword should appear naturally in the title when provided.",
            }
        )
        seo_body_kw = self._has(self.body_or_outline, self.primary_keyword) if self.primary_keyword else False
        checks.append(
            {
                "pillar": "seo",
                "criterion": "primary_keyword_in_body",
                "pass": seo_body_kw,
                "note": "Primary keyword should appear in the opening and body without stuffing.",
            }
        )
        has_headers = any(token in self.body_or_outline for token in ("##", "H2", "H3", "# "))
        checks.append(
            {
                "pillar": "seo",
                "criterion": "structured_headers",
                "pass": has_headers or len(self.body_or_outline.split()) < 80,
                "note": "Long-form drafts should use clear H2/H3 structure.",
            }
        )
        has_meta = 50 <= len(self.meta_description) <= 170 if self.meta_description else False
        checks.append(
            {
                "pillar": "seo",
                "criterion": "meta_description_present",
                "pass": has_meta,
                "note": "Meta description ideally 140–160 characters and keyword-aware.",
            }
        )
        secondary_hits = sum(1 for kw in secondary if self._has(text, kw))
        checks.append(
            {
                "pillar": "seo",
                "criterion": "secondary_keywords_present",
                "pass": (secondary_hits >= min(2, len(secondary))) if secondary else True,
                "note": f"Secondary keyword hits: {secondary_hits}/{len(secondary) or 0}.",
            }
        )

        # AEO (high-level)
        early = self.body_or_outline[:400].lower()
        answer_first = any(
            phrase in early
            for phrase in ("is ", "are ", "means ", "refers to", "in short", "the answer")
        ) or ("?" in self.title and len(self.body_or_outline) > 100)
        checks.append(
            {
                "pillar": "aeo",
                "criterion": "answer_ready_opening",
                "pass": answer_first or "faq" in self.body_or_outline.lower(),
                "note": "Lead with a clear, direct answer when the query is question-shaped.",
            }
        )
        has_faq = "faq" in self.body_or_outline.lower() or self.body_or_outline.count("?") >= 2
        checks.append(
            {
                "pillar": "aeo",
                "criterion": "faq_or_question_blocks",
                "pass": has_faq,
                "note": "Include FAQ or explicit Q&A blocks for answer-engine capture.",
            }
        )

        # GEO (high-level)
        has_takeaways = any(
            token in self.body_or_outline.lower()
            for token in ("key takeaway", "summary", "in summary", "bottom line", "tl;dr")
        )
        checks.append(
            {
                "pillar": "geo",
                "criterion": "structured_takeaways",
                "pass": has_takeaways or has_headers,
                "note": "Clear takeaways help generative engines cite and summarize accurately.",
            }
        )
        avoids_hype = not any(
            phrase in text.lower()
            for phrase in ("guaranteed #1", "rank #1 overnight", "dominate google instantly")
        )
        checks.append(
            {
                "pillar": "geo",
                "criterion": "citation_safe_claims",
                "pass": avoids_hype,
                "note": "Avoid unverifiable ranking guarantees that hurt trust and citability.",
            }
        )

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = round((passed / total) * 100) if total else 0
        outcome = "ready" if score >= 80 else ("revise" if score >= 50 else "rework")

        result = {
            "outcome": outcome,
            "score": score,
            "passed": passed,
            "total": total,
            "content_type": self.content_type,
            "checks": checks,
            "revision_guidance": (
                "Return specific revision notes to the Senior Conversion Copywriter. "
                "Consult files/ PDFs via File Search for depth — this checklist is not a substitute."
            ),
            "knowledge_reminder": (
                "Use Search_Engine_Optimization.pdf, "
                "answer_engine_optimization_holtschulte_202508.pdf, and GEO.pdf."
            ),
        }

        set_state_value("content_visibility_checklist", result)
        write_audit_event(
            event_type="content_visibility_checklist",
            actor="Search & Answer Visibility Director",
            outcome=outcome,
            details={
                "score": score,
                "passed": passed,
                "total": total,
                "content_type": self.content_type,
            },
        )
        return result


if __name__ == "__main__":
    tool = ContentVisibilityChecklist(
        title="First-Time Botox: What to Expect Before Your Appointment",
        meta_description="Learn what to expect from a first botox consultation, recovery basics, and how to prepare — book with a trusted North Dallas med spa.",
        body_or_outline=(
            "## What is a first botox appointment?\n"
            "In short, a first visit is a consultation plus a treatment plan.\n"
            "## FAQ\n"
            "### Does botox hurt?\n"
            "Most patients feel only mild discomfort.\n"
            "## Key takeaways\n"
            "- Consult first\n- Set realistic goals\n"
        ),
        primary_keyword="first time botox",
        secondary_keywords="botox consultation, botox recovery",
    )
    print(tool.run())
