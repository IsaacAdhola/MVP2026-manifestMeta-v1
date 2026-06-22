from agency_swarm.tools import BaseTool
from pydantic import Field

from safe_audit_log import write_audit_event


class ClientApprovalChecklist(BaseTool):
    """
    Verifies that the client has approved the final campaign package before media execution.
    """

    selected_copy_approved: bool = Field(
        default=False,
        description="Whether the client approved the selected headline, caption, body copy, and CTA.",
    )
    selected_image_approved: bool = Field(
        default=False,
        description="Whether the client approved the selected image or confirmed no image is needed.",
    )
    schedule_approved: bool = Field(
        default=False,
        description="Whether the client approved the posting/scheduling date, time, and timezone.",
    )
    budget_and_targeting_approved: bool = Field(
        default=True,
        description="Whether the client approved budget, targeting, objective, and geography. Use true for organic posts where these do not apply.",
    )
    destination_link_approved: bool = Field(
        default=True,
        description="Whether the client approved the destination link. Use true when no link is needed.",
    )
    policy_approved: bool = Field(
        default=False,
        description="Whether the Facebook Policy Compliance Officer returned approved.",
    )
    final_client_authorization: bool = Field(
        default=False,
        description="Whether the client gave final authorization to publish, schedule, or create the campaign.",
    )
    approval_notes: str = Field(
        default="",
        description="Client-safe approval notes, excluding secrets, internal tools, file paths, and API details.",
    )

    def run(self):
        required_checks = {
            "selected_copy_approved": self.selected_copy_approved,
            "selected_image_approved": self.selected_image_approved,
            "schedule_approved": self.schedule_approved,
            "budget_and_targeting_approved": self.budget_and_targeting_approved,
            "destination_link_approved": self.destination_link_approved,
            "policy_approved": self.policy_approved,
            "final_client_authorization": self.final_client_authorization,
        }
        missing = [name for name, approved in required_checks.items() if not approved]
        outcome = "approved" if not missing else "revise"

        result = {
            "outcome": outcome,
            "approved_for_media_operations": outcome == "approved",
            "missing_approvals": missing,
            "approval_notes": self.approval_notes,
            "next_step": (
                "Send the approved final package to Media Operations Director."
                if outcome == "approved"
                else "Return missing approval items to the Chief Growth Strategist before media execution."
            ),
        }
        write_audit_event(
            event_type="client_approval_review",
            actor="Client Approval Manager",
            outcome=outcome,
            details={
                "approved_for_media_operations": result["approved_for_media_operations"],
                "missing_approvals": missing,
                "approval_notes": self.approval_notes,
            },
        )
        return result


if __name__ == "__main__":
    tool = ClientApprovalChecklist(
        selected_copy_approved=True,
        selected_image_approved=True,
        schedule_approved=True,
        budget_and_targeting_approved=True,
        destination_link_approved=True,
        policy_approved=True,
        final_client_authorization=True,
        approval_notes="Client approved final organic Facebook post package.",
    )
    print(tool.run())
