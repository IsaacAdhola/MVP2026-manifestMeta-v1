from agency_swarm.tools import BaseTool
from pydantic import Field

from safe_audit_log import write_audit_event


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

    def _contains_any(self, text: str, terms: set[str]) -> list[str]:
        normalized = text.lower()
        return sorted(term for term in terms if term in normalized)

    def run(self):
        review_text = " ".join(
            [
                self.caption_or_body,
                self.headline,
                self.call_to_action,
                self.image_description,
                self.audience_or_targeting,
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

        if "http://" in self.destination_link.lower():
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

        outcome = "approved"
        if any(item["severity"] == "blocked" for item in concerns):
            outcome = "blocked"
        elif concerns:
            outcome = "revise"

        result = {
            "outcome": outcome,
            "campaign_type": self.campaign_type,
            "concerns": concerns,
            "reference": "FacebookPolicyAgent/files/facebook_policy_reference_file-Xn42Zik8DqZd4Y9MNsxrJp.md",
            "next_step": self._next_step(outcome),
        }
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
