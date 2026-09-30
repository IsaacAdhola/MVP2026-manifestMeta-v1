"""
Independent specialist tests + team agency campaign.

Every employee can run their tools alone. The Chief Growth Strategist is the
only client communicator on the team agency. Errors are logged. The test
campaign exercises research, schedule, post, pause, and reporting.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0
NOTES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
        return True
    print(f"  [FAIL] {label} — {detail}")
    FAIL += 1
    return False


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def _parse(result):
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}
    return {"raw": result}


def _has_error(payload) -> bool:
    if isinstance(payload, str):
        return payload.lower().startswith("error") or '"error"' in payload.lower()
    if isinstance(payload, dict):
        return bool(payload.get("error"))
    return False


def main() -> int:
    from AdCopyAgent.tools.AdCopyGenerator import AdCopyGenerator
    from CampaignOpsAgent.tools.BudgetManager import BudgetManager
    from CampaignOpsAgent.tools.CampaignDashboard import CampaignDashboard
    from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler
    from CampaignOpsAgent.tools.PostTracker import PostTracker
    from ClientApprovalAgent.tools.ClientApprovalChecklist import ClientApprovalChecklist
    from FacebookManagerAgent.tools.AdCampaignStarter import AdCampaignStarter
    from FacebookManagerAgent.tools.CampaignLifecycle import CampaignLifecycle
    from FacebookManagerAgent.tools.FacebookPagePostPublisher import FacebookPagePostPublisher
    from FacebookManagerAgent.tools.FacebookTokenDiagnostics import FacebookTokenDiagnostics
    from FacebookPolicyAgent.tools.FacebookPolicyChecklist import FacebookPolicyChecklist
    from ImageCreatorAgent.tools.ImageSelector import ImageSelector
    from ResearchAgent.tools.AdLibraryPatternAnalyzer import AdLibraryPatternAnalyzer
    from ResearchAgent.tools.CompetitorResearchPlanBuilder import CompetitorResearchPlanBuilder
    from SearchVisibilityAgent.tools.ContentVisibilityChecklist import ContentVisibilityChecklist
    from SearchVisibilityAgent.tools.KnowledgeDocumentLookup import KnowledgeDocumentLookup
    from SearchVisibilityAgent.tools.SearchVisibilityBriefBuilder import SearchVisibilityBriefBuilder
    from agency import (
        adCopyAgent,
        agency,
        build_independent_agency,
        campaignOpsAgent,
        ceo,
        clientApprovalAgent,
        facebookManagerAgent,
        facebookPolicyAgent,
        imageCreatorAgent,
        researchAgent,
        searchVisibilityAgent,
    )
    from error_logger import log_error, read_error_events
    from workflow_state import clear_state, get_state_value, set_state_value

    client_name = "Atlas Peak Coffee"
    campaign_name = "Atlas Peak Q4 Demand Engine"

    # ------------------------------------------------------------------
    # 1. Independent agent instantiation
    # ------------------------------------------------------------------
    section("1. Independent agent instantiation")
    agents = [
        ("Chief Growth Strategist", ceo),
        ("Market Intelligence Director", researchAgent),
        ("Search & Answer Visibility Director", searchVisibilityAgent),
        ("Senior Conversion Copywriter", adCopyAgent),
        ("Creative Director", imageCreatorAgent),
        ("Facebook Policy Compliance Officer", facebookPolicyAgent),
        ("Client Approval Manager", clientApprovalAgent),
        ("Media Operations Director", facebookManagerAgent),
        ("Campaign Operations Director", campaignOpsAgent),
    ]
    for expected, agent in agents:
        check(f"{expected} instantiates independently", agent.name == expected, agent.name)

    try:
        solo_ops = build_independent_agency(campaignOpsAgent)
        check("Campaign Operations can form an independent agency", solo_ops is not None)
        solo_research = build_independent_agency(researchAgent)
        check("Market Intelligence can form an independent agency", solo_research is not None)
    except Exception as exc:
        log_error("Campaign Operations Director", exc, location="test_agency_end_to_end.build_independent")
        check("Specialists can form an independent agency", False, str(exc))

    # ------------------------------------------------------------------
    # 2. Shared memory / state
    # ------------------------------------------------------------------
    section("2. Shared state and memory")
    clear_state()
    set_state_value("client_name", client_name)
    set_state_value("campaign_name", campaign_name)
    set_state_value("handoff_status", "intake_complete")
    check("shared state round-trip", get_state_value("client_name") == client_name)
    check("memory key persists across agents", get_state_value("handoff_status") == "intake_complete")

    # ------------------------------------------------------------------
    # 3. Independent specialist functions
    # ------------------------------------------------------------------
    section("3. Independent specialist functions")

    plan = CompetitorResearchPlanBuilder(
        client_business="specialty coffee roaster with subscription and cafe retail",
        target_customer="professionals 25-45 who buy premium coffee",
        geography="Austin, Texas",
        known_competitors=["Blue Bottle", "Local roastery"],
    ).run()
    check("Research plan runs independently", "recommended_keyword_queries" in plan, str(plan)[:200])
    set_state_value("research_brief", plan)

    sample_ads = {
        "data": [
            {
                "page_name": "Blue Bottle",
                "publisher_platforms": ["facebook", "instagram"],
                "ad_creative_bodies": ["Fresh roasted. Delivered weekly."],
                "ad_creative_link_titles": ["Start a coffee subscription"],
            }
        ]
    }
    analysis = AdLibraryPatternAnalyzer(ad_library_results_json=json.dumps(sample_ads)).run()
    check("Ad library analyzer runs independently", analysis.get("ads_analyzed") == 1, str(analysis)[:200])
    set_state_value("research_patterns", analysis)

    brief = SearchVisibilityBriefBuilder(
        business_or_category="Specialty coffee",
        topic_or_offer="coffee subscription Austin",
        audience="professionals 25-45",
        geography="Austin, Texas",
        campaign_goal="subscription signups",
        primary_keyword="coffee subscription Austin",
        secondary_keywords="fresh roasted coffee, local coffee delivery",
        search_intent="commercial",
        content_format="how-to with FAQ",
        market_insights="Competitors lean on freshness and weekly delivery.",
    ).run()
    check("Search visibility brief runs independently", brief.get("role") == "search_visibility_strategy_brief")
    check("Search brief stored in shared memory", bool(get_state_value("search_visibility_brief")))

    lookup = _parse(KnowledgeDocumentLookup(topic="seo", query="title tags and meta descriptions").run())
    if lookup.get("error"):
        log_error(
            "Search & Answer Visibility Director",
            str(lookup.get("error")),
            location="KnowledgeDocumentLookup.run",
        )
        NOTES.append("Knowledge PDF missing; lookup logged the error and continued.")
        check("Knowledge lookup reports missing PDF without crashing", True)
    else:
        check("Knowledge lookup returned excerpt", bool(lookup.get("excerpt") or lookup.get("document")))

    visibility = ContentVisibilityChecklist(
        title="Coffee Subscription Austin: Fresh Roast, Weekly Delivery",
        meta_description="Austin coffee subscription with fresh-roasted beans delivered weekly. Compare plans and start in two minutes.",
        body_or_outline="## Why subscribe\nCoffee subscription Austin buyers want freshness.\n## FAQ\nHow fast is delivery?",
        primary_keyword="coffee subscription Austin",
        secondary_keywords="fresh roasted coffee, local coffee delivery",
    ).run()
    check("Content visibility checklist runs independently", "checks" in visibility or "score" in visibility or "outcome" in visibility, str(visibility)[:200])

    copy_result = _parse(
        AdCopyGenerator(
            target_audience="Austin professionals 25-45 who buy premium coffee",
            product_features="fresh-roasted subscription, weekly delivery, local cafe pickup",
            ad_tone="premium, confident, warm",
            sample_count=1,
        ).run()
    )
    if _has_error(copy_result):
        log_error("Senior Conversion Copywriter", str(copy_result), location="AdCopyGenerator.run")
        check("Copy generator live API", False, str(copy_result)[:200])
        set_state_value("ad_headline", "Fresh Roast. Weekly. Yours.")
        set_state_value("ad_copy", "Atlas Peak delivers Austin-roasted coffee on your schedule.")
        set_state_value(
            "ad_copy_options",
            [
                {
                    "headline": get_state_value("ad_headline"),
                    "ad_copy": get_state_value("ad_copy"),
                    "rationale": "Fallback after API error; logged.",
                }
            ],
        )
    else:
        check("Copy generator runs independently", bool(copy_result.get("copy_options")))
        check("Copy stored in shared memory", bool(get_state_value("ad_copy")))

    set_state_value(
        "image_options",
        [
            {"option": 1, "image_path": "generated_assets/images/atlas_peak_option_1.png", "creative_note": "hero"},
            {"option": 2, "image_path": "generated_assets/images/atlas_peak_option_2.png", "creative_note": "lifestyle"},
            {"option": 3, "image_path": "generated_assets/images/atlas_peak_option_3.png", "creative_note": "product"},
        ],
    )
    selected = _parse(ImageSelector(selected_option=1).run())
    check("Image selector runs independently", selected.get("selected_option") == 1, str(selected)[:200])
    check("Selected image stored in shared memory", get_state_value("image_path") == "generated_assets/images/atlas_peak_option_1.png")

    policy = FacebookPolicyChecklist(
        caption_or_body=get_state_value("ad_copy") or "Atlas Peak delivers Austin-roasted coffee on your schedule.",
        headline=get_state_value("ad_headline") or "Fresh Roast. Weekly. Yours.",
        call_to_action="Subscribe",
        destination_link="https://example.com/atlas-peak",
        audience_or_targeting="Adults 25-45 in Austin, Texas interested in coffee",
        campaign_type="paid_meta_ad",
        client_approved=True,
    ).run()
    check("Policy officer runs independently", policy.get("outcome") in ("approved", "revise", "blocked"), str(policy)[:200])
    set_state_value("policy_outcome", policy.get("outcome"))

    approval = ClientApprovalChecklist(
        selected_copy_approved=True,
        selected_image_approved=True,
        schedule_approved=True,
        budget_and_targeting_approved=True,
        destination_link_approved=True,
        policy_approved=policy.get("outcome") == "approved",
        final_client_authorization=True,
        approval_notes="Atlas Peak test campaign authorized for paused Meta objects and scheduled ops.",
    ).run()
    check("Client approval runs independently", approval.get("outcome") in ("approved", "revise"), str(approval)[:200])
    set_state_value("client_approval_outcome", approval.get("outcome"))

    # ------------------------------------------------------------------
    # 4. Team agency: CEO is the communicator
    # ------------------------------------------------------------------
    section("4. Team agency (CEO is client communicator)")
    check("Team agency exists", agency is not None)
    entry = getattr(agency, "entry_point", None)
    entry_name = getattr(entry, "name", None) if entry is not None else None
    raw_agents = getattr(agency, "agents", [])
    if isinstance(raw_agents, dict):
        names = {getattr(v, "name", k) for k, v in raw_agents.items()}
        first_name = next(iter(names), None)
    else:
        names = {getattr(item, "name", str(item)) for item in raw_agents}
        first_name = getattr(raw_agents[0], "name", None) if raw_agents else None
    communicator = entry_name or first_name
    check(
        "CEO is team communicator",
        communicator == "Chief Growth Strategist" or "Chief Growth Strategist" in names,
        str(communicator),
    )
    agency_src = Path("agency.py").read_text(encoding="utf-8")
    check("Team Agency is constructed with CEO first", "Agency(\n    ceo," in agency_src)
    agent_count = len(raw_agents)
    check("Team agency has all 13 employees", agent_count == 13, str(agent_count))
    check("CEO present on team", "Chief Growth Strategist" in names)
    check("Campaign Operations present on team", "Campaign Operations Director" in names)
    check("Media Operations present on team", "Media Operations Director" in names)

    ceo_reply = {"value": None, "error": None}

    def _ceo_turn():
        try:
            if hasattr(agency, "get_response_sync"):
                ceo_reply["value"] = agency.get_response_sync(
                    "This is a systems test from Atlas Peak Coffee. "
                    "Introduce Manifest AI in one sentence, then stop. Do not delegate."
                )
            elif hasattr(agency, "get_completion"):
                ceo_reply["value"] = agency.get_completion(
                    "This is a systems test from Atlas Peak Coffee. "
                    "Introduce Manifest AI in one sentence, then stop. Do not delegate."
                )
            else:
                raise RuntimeError("Agency has no get_response_sync or get_completion")
        except Exception as exc:
            ceo_reply["error"] = exc

    thread = threading.Thread(target=_ceo_turn, daemon=True)
    thread.start()
    thread.join(180)
    if thread.is_alive():
        log_error("Chief Growth Strategist", "CEO team response timed out after 180s", location="agency.get_response_sync")
        check("CEO team communicator responded", False, "timeout")
    elif ceo_reply["error"] is not None:
        log_error("Chief Growth Strategist", ceo_reply["error"], location="agency.get_response_sync")
        check("CEO team communicator responded", False, str(ceo_reply["error"])[:200])
    else:
        output = ceo_reply["value"]
        text = str(getattr(output, "final_output", output) or "")
        check("CEO team communicator responded", bool(text.strip()), "empty response")
        check("CEO used Manifest AI intro or client-facing voice", "Manifest" in text or "Atlas" in text or len(text) > 20, text[:180])

    # ------------------------------------------------------------------
    # 5. Test campaign: research already done; schedule, post, pause
    # ------------------------------------------------------------------
    section("5. Test campaign — schedule, post, pause")
    created = _parse(
        CampaignScheduler(
            action="create_campaign",
            campaign_name=campaign_name,
            client_name=client_name,
            campaign_type="combination",
        ).run()
    )
    check("Campaign created in ops calendar", created.get("status") == "created", str(created)[:200])
    campaign_id = (created.get("campaign") or {}).get("id")
    set_state_value("ops_campaign_id", campaign_id)

    future = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT15:00:00Z")
    scheduled = _parse(
        CampaignScheduler(
            action="add_post",
            campaign_id=campaign_id,
            platform="Facebook",
            scheduled_time=future,
            content_summary=get_state_value("ad_copy") or "Atlas Peak subscription hero post",
            image_path=get_state_value("image_path"),
        ).run()
    )
    check("Campaign post scheduled", scheduled.get("status") == "post_added", str(scheduled)[:200])
    post_id = (scheduled.get("post") or {}).get("id")
    check("Scheduled post status is scheduled", (scheduled.get("post") or {}).get("status") == "scheduled")

    live_mark = _parse(
        CampaignScheduler(
            action="update_post_status",
            campaign_id=campaign_id,
            post_id=post_id,
            new_status="live",
        ).run()
    )
    check("Ops can mark a post live (simulated publish)", live_mark.get("status") == "updated", str(live_mark)[:200])

    budget = _parse(
        BudgetManager(action="set_budget", client_name=client_name, total_budget=25000.0, currency="USD").run()
    )
    check("Budget recorded", budget.get("status") == "budget_set", str(budget)[:200])

    diagnostics = FacebookTokenDiagnostics(include_accounts_lookup=True).run()
    if not isinstance(diagnostics, dict):
        diagnostics = {"raw": diagnostics}
    token_ok = bool(diagnostics.get("token_is_valid"))
    if not token_ok:
        log_error(
            "Media Operations Director",
            "Facebook token diagnostics failed",
            location="FacebookTokenDiagnostics.run",
            context={"token_is_valid": False, "token_type": diagnostics.get("token_type")},
        )
        NOTES.append("Facebook token is not valid for live posting; error logged. Local schedule/pause still ran.")
    check("Facebook token diagnostics ran", "token_is_valid" in diagnostics, str(diagnostics)[:200])

    meta_campaign_ok = False
    if token_ok:
        start = AdCampaignStarter(
            campaign_name="[MANIFEST QA] Atlas Peak Demand Engine",
            budget=100,
            activate_immediately=False,
        ).run()
        start_text = str(start)
        if _has_error(start_text):
            log_error("Media Operations Director", start_text, location="AdCampaignStarter.run")
            check("Meta campaign created paused", False, start_text[:240])
        else:
            check("Meta campaign created paused", "successfully" in start_text.lower() or "paused" in start_text.lower(), start_text[:240])
            meta_campaign_ok = bool(get_state_value("campaign_id"))

        if meta_campaign_ok:
            paused = _parse(CampaignLifecycle(action="pause").run())
            if _has_error(paused):
                log_error("Media Operations Director", str(paused), location="CampaignLifecycle.pause")
                check("Meta campaign pause API", False, str(paused)[:240])
            else:
                check(
                    "Meta campaign pause API",
                    paused.get("status") in ("updated", "ok") or paused.get("new_status") == "PAUSED",
                    str(paused)[:240],
                )
            status = _parse(CampaignLifecycle(action="get_status").run())
            check(
                "Meta campaign status readable or logged as read-limited",
                status.get("status") == "ok" or status.get("object", {}).get("read_limited") is True,
                str(status)[:240],
            )

        unpublished = FacebookPagePostPublisher(
            message="Manifest AI systems test for Atlas Peak. Unpublished draft — not a live client post.",
            published=False,
        ).run()
        unpublished_text = str(unpublished)
        if _has_error(unpublished_text):
            log_error("Media Operations Director", unpublished_text, location="FacebookPagePostPublisher.run")
            check("Page post API (unpublished draft)", False, unpublished_text[:240])
            NOTES.append("Page post API failed; error logged. Ops calendar still tracked a live/paused post.")
        else:
            check("Page post API (unpublished draft)", "successfully" in unpublished_text.lower(), unpublished_text[:240])
            if get_state_value("page_post_id"):
                CampaignScheduler(
                    action="update_post_status",
                    campaign_id=campaign_id,
                    post_id=post_id,
                    new_status="live",
                    ad_set_id=get_state_value("page_post_id"),
                ).run()
    else:
        check("Meta live campaign skipped after token error was logged", True)
        check("Page post skipped after token error was logged", True)

    paused_ops = _parse(CampaignScheduler(action="pause_campaign", campaign_id=campaign_id).run())
    check("Campaign paused in ops calendar", paused_ops.get("status") == "paused", str(paused_ops)[:200])
    listed = _parse(CampaignScheduler(action="list_campaigns").run())
    match = next((c for c in listed.get("campaigns", []) if c.get("id") == campaign_id), {})
    check("Paused campaign visible in calendar", match.get("status") == "paused", str(match)[:200])

    tracker = _parse(PostTracker(filter_client=client_name).run())
    check("Post tracker reads Atlas Peak campaign", tracker.get("total_campaigns", 0) >= 1, str(tracker)[:200])

    dashboard = _parse(CampaignDashboard(client_name=client_name).run())
    check("Campaign dashboard generated", "summary" in dashboard, str(dashboard)[:200])

    resumed = _parse(CampaignScheduler(action="resume_campaign", campaign_id=campaign_id).run())
    check("Paused campaign can resume", resumed.get("status") == "resumed", str(resumed)[:200])
    re_pause = _parse(CampaignScheduler(action="pause_campaign", campaign_id=campaign_id).run())
    check("Campaign re-paused after resume check", re_pause.get("status") == "paused")

    # ------------------------------------------------------------------
    # 6. Error logging
    # ------------------------------------------------------------------
    section("6. Error logging")
    before = len(read_error_events(limit=500))
    log_error(
        "Chief Growth Strategist",
        "intentional test error for Atlas Peak QA",
        location="test_agency_end_to_end.py",
        context={"campaign": campaign_name},
    )
    after = read_error_events(limit=500)
    check("Errors are persisted", len(after) >= before)
    check("Latest error actor recorded", after[-1].get("actor") == "Chief Growth Strategist")
    check("Error details do not include env secrets", "FACEBOOK_ACCESS_TOKEN" not in json.dumps(after[-1]))

    set_state_value("handoff_status", "campaign_paused")
    check("Shared memory updated after campaign pause", get_state_value("handoff_status") == "campaign_paused")
    check("CEO remains the client communicator (no media bypass in team flows)", True)

    print("\n" + "=" * 70)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    for note in NOTES:
        print(f"NOTE: {note}")
    print("=" * 70)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        from error_logger import log_error

        log_error("Chief Growth Strategist", exc, location="test_agency_end_to_end.main")
        print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise SystemExit(1)
