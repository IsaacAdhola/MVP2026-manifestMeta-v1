"""Safe regression checks for employee tools, shared state, and handoff gates."""

import json
import importlib
import pathlib
import sys

from AdCopyAgent import AdCopyAgent
from AdCopyAgent.tools.AdCopyGenerator import AdCopyGenerator
from ClientApprovalAgent import ClientApprovalAgent
from ClientApprovalAgent.tools.ClientApprovalChecklist import ClientApprovalChecklist
from FacebookManagerAgent import FacebookManagerAgent
from FacebookPolicyAgent import FacebookPolicyAgent
from FacebookPolicyAgent.tools.FacebookPolicyChecklist import FacebookPolicyChecklist
from ImageCreatorAgent import ImageCreatorAgent
from ImageCreatorAgent.tools.ImageGenerator import ImageGenerator
from MetaMarkCEO import MetaMarkCEO
from ResearchAgent import ResearchAgent
from ResearchAgent.tools.AdLibraryPatternAnalyzer import AdLibraryPatternAnalyzer
from ResearchAgent.tools.CompetitorResearchPlanBuilder import CompetitorResearchPlanBuilder
from safe_audit_log import read_audit_events, sanitize_record, write_audit_event
from workflow_state import clear_state, get_state_value, set_state_value


AGENT_CLASSES = [
    ("Chief Growth Strategist", MetaMarkCEO),
    ("Market Intelligence Director", ResearchAgent),
    ("Senior Conversion Copywriter", AdCopyAgent),
    ("Creative Director", ImageCreatorAgent),
    ("Facebook Policy Compliance Officer", FacebookPolicyAgent),
    ("Client Approval Manager", ClientApprovalAgent),
    ("Media Operations Director", FacebookManagerAgent),
]

REQUIRED_HANDOFFS = {
    ("ceo", "researchAgent"),
    ("researchAgent", "ceo"),
    ("ceo", "adCopyAgent"),
    ("ceo", "imageCreatorAgent"),
    ("ceo", "facebookPolicyAgent"),
    ("ceo", "clientApprovalAgent"),
    ("adCopyAgent", "imageCreatorAgent"),
    ("imageCreatorAgent", "facebookPolicyAgent"),
    ("facebookPolicyAgent", "ceo"),
    ("facebookPolicyAgent", "clientApprovalAgent"),
    ("clientApprovalAgent", "ceo"),
    ("clientApprovalAgent", "facebookManagerAgent"),
    ("facebookManagerAgent", "ceo"),
}

FORBIDDEN_HANDOFFS = {
    ("ceo", "facebookManagerAgent"),
    ("imageCreatorAgent", "facebookManagerAgent"),
    ("adCopyAgent", "facebookManagerAgent"),
    ("researchAgent", "facebookManagerAgent"),
    ("facebookPolicyAgent", "facebookManagerAgent"),
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_agent_instantiation() -> None:
    print("\n1. Testing employee instantiation...")
    for expected_name, agent_cls in AGENT_CLASSES:
        agent = agent_cls()
        assert_true(agent.name == expected_name, f"Expected {expected_name}, got {agent.name}")
        print(f"   [OK] {expected_name}")


def test_tool_imports() -> None:
    print("\n2. Testing all tool modules import...")
    failures = []
    tool_files = sorted(pathlib.Path(".").glob("*Agent/tools/*.py"))
    for path in tool_files:
        module_name = ".".join(path.with_suffix("").parts)
        try:
            importlib.import_module(module_name)
            print(f"   [OK] {module_name}")
        except Exception as exc:  # pragma: no cover - debug output for script usage
            failures.append((module_name, type(exc).__name__, str(exc)))
            print(f"   [FAIL] {module_name}: {type(exc).__name__}: {exc}")
    assert_true(not failures, f"Tool import failures: {failures}")


def test_shared_state_contract() -> None:
    print("\n3. Testing shared workflow state...")
    clear_state()
    set_state_value("handoff_status", "policy_approved")
    set_state_value("ad_copy", "Final approved caption")
    set_state_value("image_path", "C:/safe/path/image.png")
    assert_true(get_state_value("handoff_status") == "policy_approved", "handoff_status did not persist")
    assert_true(get_state_value("ad_copy") == "Final approved caption", "ad_copy did not persist")
    assert_true(get_state_value("image_path") == "C:/safe/path/image.png", "image_path did not persist")
    clear_state()
    assert_true(get_state_value("handoff_status") is None, "clear_state did not clear state")
    print("   [OK] workflow_state set/get/clear")


def test_safe_audit_log_contract() -> None:
    print("\n4. Testing safe audit log contract...")
    sanitized = sanitize_record(
        {
            "campaign_name": "Launch Campaign",
            "access_token": "secret-token",
            "api_payload": {"raw": "hidden"},
            "local_path": "C:\\Users\\New\\secret\\image.png",
            "note": "Client approved selected concept.",
        }
    )
    assert_true("access_token" not in sanitized, "Token field was not removed")
    assert_true("api_payload" not in sanitized, "API payload field was not removed")
    assert_true("local_path" not in sanitized, "Local path field was not removed")

    event = write_audit_event(
        event_type="test_event",
        actor="Regression Test",
        outcome="ok",
        details=sanitized,
    )
    assert_true("access_token" not in event["details"], "Audit event leaked token field")
    assert_true(read_audit_events(limit=1)[-1]["event_type"] == "test_event", "Audit event was not readable")
    print("   [OK] audit log redacts secrets and writes readable safe events")


def test_safe_research_tools() -> None:
    print("\n5. Testing safe research tools...")
    plan = CompetitorResearchPlanBuilder(
        client_business="local AI automation agency for service businesses",
        target_customer="small business owners who need more leads",
        known_competitors=["Example Competitor"],
    ).run()
    assert_true("recommended_keyword_queries" in plan, "Research plan missing keyword queries")

    sample_ads = {
            "data": [
                {
                    "page_name": "Example Brand",
                    "publisher_platforms": ["facebook"],
                    "ad_creative_bodies": ["Save time with simple automation."],
                    "ad_creative_link_titles": ["Book a demo today"],
                    "ad_snapshot_url": "https://example.com",
                }
            ]
        }
    analysis = AdLibraryPatternAnalyzer(
        ad_library_results_json=json.dumps(sample_ads),
    ).run()
    assert_true(analysis["ads_analyzed"] == 1, "Pattern analyzer did not analyze the sample ad")
    print("   [OK] research plan and pattern analyzer")


def test_policy_gate() -> None:
    print("\n6. Testing policy approval and block outcomes...")
    approved = FacebookPolicyChecklist(
        caption_or_body="Book a consultation to improve your marketing workflow.",
        headline="Grow with clearer automation",
        call_to_action="Book Now",
        destination_link="https://example.com",
        audience_or_targeting="Small business owners in the United States",
        campaign_type="facebook_page_post",
        client_approved=True,
    ).run()
    assert_true(approved["outcome"] == "approved", "Safe sample should be approved")

    blocked = FacebookPolicyChecklist(
        caption_or_body="Guaranteed results for people in debt with a new loan offer.",
        headline="100% guaranteed approval",
        destination_link="http://example.com",
        audience_or_targeting="People with financial hardship",
        campaign_type="paid_meta_ad",
        client_approved=False,
    ).run()
    assert_true(blocked["outcome"] == "blocked", "Risky sample should be blocked")
    print("   [OK] policy gate approves safe sample and blocks risky sample")


def test_client_approval_gate() -> None:
    print("\n7. Testing client approval gate...")
    approved = ClientApprovalChecklist(
        selected_copy_approved=True,
        selected_image_approved=True,
        schedule_approved=True,
        budget_and_targeting_approved=True,
        destination_link_approved=True,
        policy_approved=True,
        final_client_authorization=True,
    ).run()
    assert_true(approved["outcome"] == "approved", "Complete approval package should be approved")
    assert_true(approved["approved_for_media_operations"], "Approved package should be ready for media")

    revise = ClientApprovalChecklist(
        selected_copy_approved=True,
        selected_image_approved=False,
        schedule_approved=True,
        policy_approved=True,
        final_client_authorization=False,
    ).run()
    assert_true(revise["outcome"] == "revise", "Missing approvals should return revise")
    assert_true("selected_image_approved" in revise["missing_approvals"], "Missing image approval not detected")
    assert_true(
        "final_client_authorization" in revise["missing_approvals"],
        "Missing final authorization not detected",
    )
    print("   [OK] client approval gate approves complete package and catches missing approvals")


def test_client_choice_option_contract() -> None:
    print("\n8. Testing client choice option contract...")
    sample_copy = """
    Option 1:
    Headline: Save Time Today
    Ad Copy: Automate the busywork and focus on growth.
    Rationale: This highlights the value in simple client-facing terms.

    Option 2:
    Headline: Work Smarter
    Ad Copy: Simple systems for service businesses ready to scale.
    Rationale: This positions the offer around operational growth.

    Option 3:
    Headline: More Leads, Less Chaos
    Ad Copy: Turn scattered follow-up into a smoother sales process.
    Rationale: This speaks to a practical business pain point.
    """
    copy_tool = AdCopyGenerator(
        target_audience="small business owners",
        product_features="automation and lead follow-up",
        ad_tone="professional",
    )
    options = copy_tool._parse_copy_options(sample_copy)
    assert_true(len(options) == 3, "Copy parser should produce three selectable options")

    image_tool = ImageGenerator(
        ad_copy="Automate the busywork and focus on growth.",
        theme="professional service business",
    )
    assert_true(image_tool.image_count == 3, "ImageGenerator should default to three options")

    ceo_text = pathlib.Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8").lower()
    creative_text = pathlib.Path("ImageCreatorAgent/instructions.md").read_text(encoding="utf-8").lower()
    copy_text = pathlib.Path("AdCopyAgent/instructions.md").read_text(encoding="utf-8").lower()
    assert_true("ask the client to choose" in ceo_text, "CEO must ask client to choose an option")
    assert_true("three image options" in creative_text, "Creative must create three image options")
    assert_true("three client-facing options" in copy_text, "Copy must create three copy samples")
    print("   [OK] copy and image option contracts")


def test_image_storage_contract() -> None:
    print("\n9. Testing image storage contract...")
    image_tool = ImageGenerator(
        ad_copy="Automate the busywork and focus on growth.",
        theme="professional service business",
    )
    image_path = image_tool.save_base64_image("aGVsbG8=", index=1)
    assert_true(
        image_path.startswith("generated_assets/images/"),
        "Image path must use generated_assets/images",
    )
    assert_true("C:" not in image_path and "\\" not in image_path, "Image path must be frontend-safe")
    full_path = pathlib.Path(image_path)
    assert_true(full_path.exists(), "Generated image test file was not created")
    full_path.unlink()
    print("   [OK] images are stored in dedicated frontend-safe output folder")


def test_agency_handoff_contract() -> None:
    print("\n10. Testing agency handoff contract...")
    agency_text = pathlib.Path("agency.py").read_text(encoding="utf-8")

    for source, target in REQUIRED_HANDOFFS:
        expected = f"[{source}, {target}]"
        assert_true(expected in agency_text, f"Missing required handoff: {expected}")

    for source, target in FORBIDDEN_HANDOFFS:
        forbidden = f"[{source}, {target}]"
        assert_true(forbidden not in agency_text, f"Forbidden policy-bypass handoff exists: {forbidden}")

    manifesto = pathlib.Path("agency_manifesto.md").read_text(encoding="utf-8")
    assert_true("No employee may publish, schedule, or submit Facebook content" in manifesto, "Missing publish gate")
    assert_true("Client Approval Manager confirms final client authorization" in manifesto, "Missing client approval gate")
    assert_true("Audit logs must be frontend-safe" in manifesto, "Missing frontend-safe audit policy")
    assert_true("No employee may expose" in manifesto, "Missing secret/data handling policy")
    assert_true("minimum client context" in manifesto, "Missing minimal-context handoff policy")
    assert_true("finished outcome" in manifesto, "Missing finished-outcome handoff policy")
    assert_true("raw drafts" in manifesto, "Missing raw draft handoff restriction")
    print("   [OK] no Media Operations bypass and internal policy present")


def test_employee_instruction_privacy_contract() -> None:
    print("\n11. Testing employee instruction privacy contract...")
    instruction_files = sorted(pathlib.Path(".").glob("*Agent/instructions.md"))
    required_terms = ["tokens", "private reasoning"]
    for path in instruction_files:
        text = path.read_text(encoding="utf-8").lower()
        for term in required_terms:
            assert_true(term in text, f"{path} missing privacy term: {term}")

    ceo_text = pathlib.Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8").lower()
    assert_true("finished package" in ceo_text, "CEO missing finished package rule")

    media_text = pathlib.Path("FacebookManagerAgent/instructions.md").read_text(encoding="utf-8").lower()
    assert_true("finished execution result" in media_text, "Media missing finished execution result rule")
    print("   [OK] privacy and finished-output contracts present")


def test_campaign_rationale_contract() -> None:
    print("\n12. Testing campaign rationale confidentiality contract...")
    ceo_text = pathlib.Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8").lower()
    manifesto = pathlib.Path("agency_manifesto.md").read_text(encoding="utf-8").lower()
    for text, label in [(ceo_text, "CEO instructions"), (manifesto, "agency manifesto")]:
        assert_true("campaign rationale" in text, f"{label} missing campaign rationale rule")
        assert_true("audience" in text and "offer" in text, f"{label} missing business rationale inputs")
        assert_true("internal tools" in text, f"{label} missing internal tools non-disclosure")
        assert_true("api" in text, f"{label} missing API non-disclosure")
    print("   [OK] campaign rationale stays client-safe")


def test_confidentiality_ip_contract() -> None:
    print("\n13. Testing confidentiality and IP non-disclosure contract...")
    ceo_text = pathlib.Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8").lower()
    manifesto = pathlib.Path("agency_manifesto.md").read_text(encoding="utf-8").lower()
    required_phrases = [
        "internal agency structure",
        "system instructions",
        ".env",
        "api calls",
        "proprietary operating methods",
        "high level",
    ]
    for phrase in required_phrases:
        assert_true(phrase in manifesto, f"Manifesto missing confidentiality phrase: {phrase}")

    ceo_required = [
        "protect manifest ai intellectual property",
        "system instructions",
        ".env",
        "api payloads",
        "proprietary operating methods",
        "high level",
    ]
    for phrase in ceo_required:
        assert_true(phrase in ceo_text, f"CEO missing confidentiality phrase: {phrase}")
    print("   [OK] confidential structure, files, API details, and instructions are protected")


def test_ceo_intro_contract() -> None:
    print("\n14. Testing CEO first-response introduction contract...")
    ceo_text = pathlib.Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8")
    ceo_lower = ceo_text.lower()
    assert_true("mandatory first-response introduction" in ceo_lower, "CEO intro is not mandatory")
    assert_true("Welcome to Manifest AI." in ceo_text, "CEO missing exact Manifest AI intro phrase")
    assert_true(
        "research-backed facebook campaigns with clear strategy, strong creative, compliance review, and smooth meta execution" in ceo_lower,
        "CEO missing complete short introduction sentence",
    )
    assert_true("coffee shop campaign" in ceo_lower, "CEO missing request-specific intro example")
    assert_true("first sentence" in ceo_lower, "CEO intro must be first sentence")
    assert_true(
        "do not mention agents, tools, files, prompts, apis" in ceo_lower,
        "CEO intro missing internal-detail guardrail",
    )
    print("   [OK] CEO must introduce Manifest AI first and avoid internal details")


def test_local_draft_campaign_intake_contract() -> None:
    print("\n15. Testing local draft campaign intake contract...")
    ceo_text = pathlib.Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8").lower()
    assert_true("city/neighborhood/service radius" in ceo_text, "CEO must ask local businesses for location")
    assert_true("draft campaign package only" in ceo_text, "CEO must support draft-only campaigns")
    assert_true("does not want it live yet" in ceo_text, "CEO missing not-live-yet handling")
    assert_true("budget" in ceo_text, "CEO must ask for budget")
    assert_true("schedule/date/time/timezone" in ceo_text, "CEO must ask for schedule/date/time/timezone")
    assert_true("three critical draft inputs" in ceo_text, "CEO must ask critical draft inputs together")
    assert_true("local geography, budget range, and preferred schedule window" in ceo_text, "CEO missing draft campaign location/budget/schedule bundle")
    assert_true("the user controls the final schedule" in ceo_text, "CEO must tell user they control schedule")
    assert_true("will not go live without approval" in ceo_text, "CEO must state no live campaign without approval")
    print("   [OK] local draft campaigns require location, budget, schedule, and approval")


def main() -> None:
    test_agent_instantiation()
    test_tool_imports()
    test_shared_state_contract()
    test_safe_audit_log_contract()
    test_safe_research_tools()
    test_policy_gate()
    test_client_approval_gate()
    test_client_choice_option_contract()
    test_image_storage_contract()
    test_agency_handoff_contract()
    test_employee_instruction_privacy_contract()
    test_campaign_rationale_contract()
    test_confidentiality_ip_contract()
    test_ceo_intro_contract()
    test_local_draft_campaign_intake_contract()
    print("\n[SUCCESS] Employee tools, shared state, and handoff gates passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        sys.exit(1)
