from agency_swarm.tools import BaseTool
from pydantic import Field

import os
import sys

_NESTED = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOT = os.path.dirname(_NESTED)
for _path in (_NESTED, _ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from claims_ledger import evaluate_and_store, parse_claim_records, reuse_results_to_concerns
from safe_audit_log import write_audit_event
from workflow_state import get_media_package, set_state_value


SENSITIVE_ATTRIBUTE_TERMS = {
    "addiction",
    "adhd",
    "anxiety",
    "bankrupt",
    "cancer",
    "debt",
    "depressed",
    "diabetes",
    "disabled",
    "ethnicity",
    "fat",
    "financial hardship",
    "gender identity",
    "medical condition",
    "overweight",
    "race",
    "religion",
    "sexual orientation",
    "single mom",
    "single parent",
}

UNSUPPORTED_CLAIM_TERMS = {
    "100% guaranteed",
    "guaranteed results",
    "instant results",
    "make money fast",
    "no risk",
    "risk free",
    "you will get rich",
}

REGULATED_CATEGORY_TERMS = {
    "alcohol",
    "casino",
    "credit",
    "crypto",
    "dating",
    "employment",
    "gambling",
    "healthcare",
    "housing",
    "insurance",
    "loan",
    "political",
    "supplement",
    "weight loss",
}


class FacebookPolicyChecklist(BaseTool):
    """
    Reviews drafted Facebook post or ad materials for common Meta policy risks before publishing.
    """

    caption_or_body: str = Field(
        default="",
        description="Final caption, ad body, or primary text to review.",
    )
    headline: str = Field(default="", description="Final ad or post headline to review.")
    call_to_action: str = Field(default="", description="Call to action text.")
    image_description: str = Field(
        default="",
        description="Brief description of the image or visual creative.",
    )
    destination_link: str = Field(
        default="",
        description="Landing page or destination URL, if one is used.",
    )
    audience_or_targeting: str = Field(
        default="",
        description="Audience, targeting, geography, demographic, or placement notes.",
    )
    campaign_type: str = Field(
        default="facebook_page_post",
        description="facebook_page_post, scheduled_post, or paid_meta_ad.",
    )
    client_approved: bool = Field(
        default=False,
        description="Whether the client authorized this post/ad to move toward publishing.",
    )
    claims_json: str = Field(
        default="",
        description=(
            "JSON list of claim records covering the caption AND the picture. "
            "Each record needs claim type (puffery, fact, regulated), source for facts, "
            "founder proof for regulated claims, review-by date for facts, image claims, "
            "and live placements when the line is already live."
        ),
    )
    image_reviewed: bool = Field(
        default=False,
        description=(
            "True when the picture was reviewed on the same record as the caption "
            "(star badge, before-and-after, baked-in text), not caption-only."
        ),
    )
    as_of_date: str = Field(
        default="",
        description="ISO date for stale-fact checks. Leave empty to use today (UTC).",
    )

    def _contains_any(self, text: str, terms: set[str]) -> list[str]:
        normalized = text.lower()
        return sorted(term for term in terms if term in normalized)

    def run(self):
        pkg = get_media_package()
        caption = (self.caption_or_body or pkg.get("ad_copy") or "").strip()
        headline = (self.headline or pkg.get("ad_headline") or "").strip()
        destination = (self.destination_link or pkg.get("destination_link") or "").strip()
        audience = (self.audience_or_targeting or pkg.get("geography") or "").strip()
        review_text = " ".join(
            [
                caption,
                headline,
                self.call_to_action,
                self.image_description,
                audience,
            ]
        )

        concerns: list[dict[str, str]] = []

        sensitive_matches = self._contains_any(review_text, SENSITIVE_ATTRIBUTE_TERMS)
        if sensitive_matches:
            concerns.append(
                {
                    "severity": "revise",
                    "area": "sensitive_attributes",
                    "reason": (
                        "Content may directly or indirectly reference sensitive personal attributes: "
                        + ", ".join(sensitive_matches)
                    ),
                    "required_fix": (
                        "Rewrite to focus on the offer or general situation without implying the viewer has a protected trait."
                    ),
                }
            )

        claim_matches = self._contains_any(review_text, UNSUPPORTED_CLAIM_TERMS)
        if claim_matches:
            concerns.append(
                {
                    "severity": "revise",
                    "area": "unsupported_or_exaggerated_claims",
                    "reason": "Content includes high-risk guarantee or outcome language: " + ", ".join(claim_matches),
                    "required_fix": "Soften the claim or add substantiation before approval.",
                }
            )

        regulated_matches = self._contains_any(review_text, REGULATED_CATEGORY_TERMS)
        if regulated_matches:
            concerns.append(
                {
                    "severity": "blocked",
                    "area": "regulated_category",
                    "reason": "Content appears related to a regulated category: " + ", ".join(regulated_matches),
                    "required_fix": (
                        "Escalate for client/legal/platform clarification before Media Operations proceeds."
                    ),
                }
            )

        if "http://" in destination.lower():
            concerns.append(
                {
                    "severity": "revise",
                    "area": "destination_link",
                    "reason": "Destination link uses insecure HTTP.",
                    "required_fix": "Use a secure HTTPS destination link before publishing.",
                }
            )

        if not self.client_approved:
            concerns.append(
                {
                    "severity": "revise",
                    "area": "client_authorization",
                    "reason": "Client approval has not been confirmed.",
                    "required_fix": "Confirm client approval before publishing or scheduling.",
                }
            )

        claims_payload: object = self.claims_json
        if self.claims_json.strip():
            records = parse_claim_records(self.claims_json)
            if self.image_reviewed:
                for record in records:
                    record.image_reviewed = True
            claims_payload = [item.model_dump(mode="json") for item in records]
        ledger = evaluate_and_store(
            claims_payload,
            image_description=self.image_description,
            as_of=self.as_of_date or None,
        )
        concerns.extend(reuse_results_to_concerns(ledger.get("results") or []))

        outcome = "approved"
        if any(item["severity"] == "blocked" for item in concerns):
            outcome = "blocked"
        elif concerns:
            outcome = "revise"

        result = {
            "outcome": outcome,
            "campaign_type": self.campaign_type,
            "concerns": concerns,
            "claims_ledger": ledger,
            "reference": "FacebookPolicyAgent/files/facebook_policy_reference_file-Xn42Zik8DqZd4Y9MNsxrJp.md",
            "next_step": self._next_step(outcome),
        }
        set_state_value("policy_outcome", outcome)
        set_state_value(
            "policy_review",
            {
                "outcome": outcome,
                "concern_count": len(concerns),
                "claims_ledger_outcome": ledger.get("outcome"),
            },
        )
        write_audit_event(
            event_type="facebook_policy_review",
            actor="Facebook Policy Compliance Officer",
            outcome=outcome,
            details={
                "campaign_type": self.campaign_type,
                "concern_areas": [concern["area"] for concern in concerns],
                "concern_count": len(concerns),
            },
        )
        return result

    def _next_step(self, outcome: str) -> str:
        if outcome == "approved":
            return "Send approval status and execution constraints to Media Operations Director."
        if outcome == "revise":
            return "Return concerns to the Chief Growth Strategist so the correct specialist can revise."
        return "Block publishing until client, legal, or platform clarification is complete."


if __name__ == "__main__":
    tool = FacebookPolicyChecklist(
        caption_or_body="Book a consultation to improve your marketing workflow.",
        headline="Grow with clearer automation",
        call_to_action="Book Now",
        destination_link="https://example.com",
        audience_or_targeting="Small business owners in the United States",
        campaign_type="facebook_page_post",
        client_approved=True,
    )
    print(tool.run())
