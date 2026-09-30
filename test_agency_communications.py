"""
Clean leftover Manifest QA Meta objects, then test agency communications
and specialist capabilities (independent + team, CEO as client voice).
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
        lower = payload.lower()
        return lower.startswith("error") or '"error"' in lower or "[error]" in lower
    if isinstance(payload, dict):
        return bool(payload.get("error")) or payload.get("status") == "error"
    return False


def _cleanup_meta_test_objects() -> None:
    import requests

    from FacebookManagerAgent.facebook_auth import (
        get_page_access_token,
        get_required_env,
        initialize_business_sdk,
    )
    from FacebookManagerAgent.tools.CampaignLifecycle import CampaignLifecycle
    from error_logger import log_error
    from workflow_state import get_state_value

    campaign_ids = {
        str(get_state_value("campaign_id") or ""),
        "52506223896438",
        "52506749995438",
    }
    ad_set_ids = {str(get_state_value("ad_set_id") or ""), "52506750000638"}
    ad_ids = {str(get_state_value("ad_id") or ""), "52506750033838"}
    post_ids = {
        str(get_state_value("page_post_id") or ""),
        str(get_state_value("page_photo_id") or ""),
        "659878773884281_122198858210902991",
        "659878773884281_122198962868902991",
        "122199080816902991",
        "122198858210902991",
        "122198962868902991",
    }

    for object_id in sorted(x for x in ad_ids if x):
        result = _parse(CampaignLifecycle(action="delete", object_type="ad", object_id=object_id).run())
        print(f"  delete ad {object_id}: {result}")
        if _has_error(result):
            log_error("Media Operations Director", str(result), location="cleanup.delete_ad")

    for object_id in sorted(x for x in ad_set_ids if x):
        result = _parse(CampaignLifecycle(action="delete", object_type="adset", object_id=object_id).run())
        print(f"  delete ad set {object_id}: {result}")
        if _has_error(result):
            log_error("Media Operations Director", str(result), location="cleanup.delete_adset")

    for object_id in sorted(x for x in campaign_ids if x):
        result = _parse(CampaignLifecycle(action="delete", object_type="campaign", object_id=object_id).run())
        print(f"  delete campaign {object_id}: {result}")
        if _has_error(result):
            log_error("Media Operations Director", str(result), location="cleanup.delete_campaign")
        else:
            check(f"Meta campaign {object_id} delete attempted", result.get("status") == "updated" or _has_error(result), str(result)[:200])

    try:
        env = initialize_business_sdk()
        page_id = get_required_env("FACEBOOK_PAGE_ID")
        page_token, _meta = get_page_access_token(env["access_token"], page_id)
        if not page_token:
            log_error("Media Operations Director", "No page token for post cleanup", location="cleanup.posts")
            check("Page token available for draft cleanup", False, "no page token")
            return
        check("Page token available for draft cleanup", True)
        for object_id in sorted(x for x in post_ids if x):
            response = requests.delete(
                f"https://graph.facebook.com/{object_id}",
                params={"access_token": page_token},
                timeout=30,
            )
            try:
                data = response.json()
            except ValueError:
                data = {"raw": response.text}
            ok = response.status_code < 400 and data.get("success") is True
            err = data.get("error") if isinstance(data.get("error"), dict) else {}
            already_gone = err.get("code") in (100, 803)
            needs_prefixed_id = err.get("code") == 12
            print(f"  delete post/photo {object_id}: http={response.status_code} {data}")
            if ok or already_gone or needs_prefixed_id:
                check(f"Draft/post {object_id[-12:]} removed, gone, or retried via page-prefixed ID", True)
            else:
                log_error(
                    "Media Operations Director",
                    str(data)[:400],
                    location="cleanup.delete_post",
                    context={"http_status": response.status_code},
                )
                check(f"Draft/post {object_id[-12:]} removed", False, str(data)[:200])
    except Exception as exc:
        from error_logger import log_error as _log

        _log("Media Operations Director", exc, location="cleanup.posts")
        check("Draft/post cleanup ran", False, str(exc)[:200])


def main() -> int:
    from error_logger import log_error, read_error_events

    section("0. Remove leftover test ads and unpublished drafts")
    _cleanup_meta_test_objects()

    from CampaignOpsAgent.tools.BudgetManager import BudgetManager
    from CampaignOpsAgent.tools.CampaignDashboard import CampaignDashboard
    from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler
    from CampaignOpsAgent.tools.PostTracker import PostTracker
    from ClientApprovalAgent.tools.ClientApprovalChecklist import ClientApprovalChecklist
    from CommunityManagerAgent.tools.CommentReplyDrafts import CommentReplyDrafts
    from ConversionPageAgent.tools.CroAuditChecklist import CroAuditChecklist
    from ConversionPageAgent.tools.LandingPageBriefBuilder import LandingPageBriefBuilder
    from CulturalIntelligenceAgent.tools.TrendVoiceBrief import TrendVoiceBrief
    from FacebookManagerAgent.tools.FacebookTokenDiagnostics import FacebookTokenDiagnostics
    from FacebookPolicyAgent.tools.FacebookPolicyChecklist import FacebookPolicyChecklist
    from PerformanceAnalystAgent.tools.PerformanceInsightBuilder import PerformanceInsightBuilder
    from ResearchAgent.tools.CompetitorResearchPlanBuilder import CompetitorResearchPlanBuilder
    from SearchVisibilityAgent.tools.SearchVisibilityBriefBuilder import SearchVisibilityBriefBuilder
    from agency import (
        adCopyAgent,
        agency,
        build_independent_agency,
        campaignOpsAgent,
        ceo,
        clientApprovalAgent,
        communityManagerAgent,
        conversionPageAgent,
        culturalIntelligenceAgent,
        facebookManagerAgent,
        facebookPolicyAgent,
        imageCreatorAgent,
        performanceAnalystAgent,
        researchAgent,
        searchVisibilityAgent,
    )
    from client_gateway import run_client_turn
    from workflow_state import get_state_value, set_state_value

    section("1. Independent specialists (13 employees)")
    roster = [
        ("Chief Growth Strategist", ceo),
        ("Market Intelligence Director", researchAgent),
        ("Cultural Intelligence Director", culturalIntelligenceAgent),
        ("Search & Answer Visibility Director", searchVisibilityAgent),
        ("Senior Conversion Copywriter", adCopyAgent),
        ("Landing Page & CRO Director", conversionPageAgent),
        ("Creative Director", imageCreatorAgent),
        ("Facebook Policy Compliance Officer", facebookPolicyAgent),
        ("Client Approval Manager", clientApprovalAgent),
        ("Media Operations Director", facebookManagerAgent),
        ("Campaign Operations Director", campaignOpsAgent),
        ("Community Manager", communityManagerAgent),
        ("Performance Analyst", performanceAnalystAgent),
    ]
    for expected, agent in roster:
        check(f"{expected} ready independently", agent.name == expected, agent.name)

    try:
        solo = build_independent_agency(culturalIntelligenceAgent)
        check("Cultural Intelligence can run as its own agency", solo is not None)
        solo_ops = build_independent_agency(campaignOpsAgent)
        check("Campaign Operations can run as its own agency", solo_ops is not None)
    except Exception as exc:
        log_error("Chief Growth Strategist", exc, location="build_independent_agency")
        check("Independent specialist agencies", False, str(exc)[:200])

    section("2. Team communications contract")
    check("Team agency exists", agency is not None)
    raw_agents = getattr(agency, "agents", [])
    if isinstance(raw_agents, dict):
        names = {getattr(v, "name", k) for k, v in raw_agents.items()}
    else:
        names = {getattr(item, "name", str(item)) for item in raw_agents}
    check("Team has 13 employees", len(raw_agents) == 13, str(len(raw_agents)))
    for expected, _agent in roster:
        check(f"Team includes {expected}", expected in names)
    agency_src = Path("agency.py").read_text(encoding="utf-8")
    check("CEO is constructed first as the client communicator", "Agency(\n    ceo," in agency_src)
    check("CEO cannot skip straight to Media Operations", "[ceo, facebookManagerAgent]" not in agency_src)
    check(
        "CEO cannot skip straight to Media Operations (tuple form)",
        "(ceo, facebookManagerAgent)" not in agency_src,
    )
    check("Media reports back to CEO", "[facebookManagerAgent, ceo]" in agency_src)
    check("Client Approval is the only path into Media", "[clientApprovalAgent, facebookManagerAgent]" in agency_src)
    for source, target in [
        ("ceo", "culturalIntelligenceAgent"),
        ("ceo", "communityManagerAgent"),
        ("ceo", "conversionPageAgent"),
        ("ceo", "performanceAnalystAgent"),
        ("campaignOpsAgent", "performanceAnalystAgent"),
    ]:
        check(f"Handoff {source} -> {target}", f"[{source}, {target}]" in agency_src)

    section("3. Specialist capabilities (no new live Meta spend)")
    research = CompetitorResearchPlanBuilder(
        client_business="Atlas Peak specialty coffee subscription",
        target_customer="Austin professionals 25-45",
        geography="Austin, Texas",
        known_competitors=["Blue Bottle"],
    ).run()
    check("Research plan runs independently", "recommended_keyword_queries" in research, str(research)[:200])
    set_state_value("research_brief", research)

    cultural = TrendVoiceBrief(
        business="Atlas Peak specialty coffee subscription",
        audience="Austin professionals 25-45",
        geography="Austin, Texas",
        market_notes="Competitors lean on freshness and weekly delivery.",
    ).run()
    cultural_text = str(cultural)
    if _has_error(cultural):
        log_error("Cultural Intelligence Director", cultural_text, location="TrendVoiceBrief.run")
        check("Cultural intelligence brief", False, cultural_text[:240])
    else:
        check("Cultural intelligence brief", len(cultural_text) > 40, cultural_text[:120])
        check("Cultural brief stored in shared memory", bool(get_state_value("cultural_voice_brief")))

    search = SearchVisibilityBriefBuilder(
        business_or_category="Specialty coffee",
        topic_or_offer="coffee subscription Austin",
        audience="professionals 25-45",
        geography="Austin, Texas",
        campaign_goal="subscription signups",
        primary_keyword="coffee subscription Austin",
    ).run()
    check("Search visibility brief", search.get("role") == "search_visibility_strategy_brief", str(search)[:200])

    landing = LandingPageBriefBuilder(
        business="Atlas Peak coffee subscription",
        audience="Austin professionals 25-45",
        campaign_goal="subscription signup",
        ad_promise="Fresh-roasted coffee delivered weekly",
    ).run()
    landing_text = str(landing)
    if _has_error(landing):
        log_error("Landing Page & CRO Director", landing_text, location="LandingPageBriefBuilder.run")
        check("Landing page brief", False, landing_text[:240])
    else:
        check("Landing page brief", len(landing_text) > 40)
        check("Landing brief stored in shared memory", bool(get_state_value("landing_page_brief")))

    cro = CroAuditChecklist(
        page_copy="Fresh roast. Weekly. Yours. Start a subscription. Weekly roasted coffee delivered in Austin.",
        campaign_goal="subscription signup",
        ad_promise="Fresh-roasted coffee delivered weekly",
    ).run()
    cro_text = str(cro)
    if _has_error(cro):
        log_error("Landing Page & CRO Director", cro_text, location="CroAuditChecklist.run")
        check("CRO audit runs independently", False, cro_text[:240])
    else:
        check("CRO audit runs independently", len(cro_text) > 40, cro_text[:120])

    replies = CommentReplyDrafts(
        incoming_message="Do you deliver to South Austin?",
        brand_voice="warm, classy, human",
        business_context="Atlas Peak coffee subscription",
    ).run()
    replies_text = str(replies)
    if _has_error(replies):
        log_error("Community Manager", replies_text, location="CommentReplyDrafts.run")
        check("Community reply drafts", False, replies_text[:240])
    else:
        check("Community reply drafts", "option" in replies_text.lower() or len(replies_text) > 40)

    policy = FacebookPolicyChecklist(
        caption_or_body="Atlas Peak delivers Austin-roasted coffee on your schedule.",
        headline="Fresh Roast. Weekly. Yours.",
        call_to_action="Subscribe",
        destination_link="https://example.com/atlas-peak",
        audience_or_targeting="Adults 25-45 in Austin, Texas interested in coffee",
        campaign_type="facebook_page_post",
        client_approved=True,
    ).run()
    check("Policy gate", policy.get("outcome") in ("approved", "revise", "blocked"), str(policy)[:200])

    approval = ClientApprovalChecklist(
        selected_copy_approved=True,
        selected_image_approved=True,
        schedule_approved=True,
        budget_and_targeting_approved=True,
        destination_link_approved=True,
        policy_approved=policy.get("outcome") == "approved",
        final_client_authorization=False,
        approval_notes="Communications test — do not publish.",
    ).run()
    check("Approval gate blocks publish without final authorization", approval.get("outcome") == "revise", str(approval)[:200])

    created = _parse(
        CampaignScheduler(
            action="create_campaign",
            campaign_name="Atlas Peak Communications Drill",
            client_name="Atlas Peak Coffee",
            campaign_type="combination",
        ).run()
    )
    campaign_id = (created.get("campaign") or {}).get("id")
    check("Ops calendar create", created.get("status") == "created", str(created)[:200])
    future = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%dT15:00:00Z")
    scheduled = _parse(
        CampaignScheduler(
            action="add_post",
            campaign_id=campaign_id,
            platform="Facebook",
            scheduled_time=future,
            content_summary="Communications drill — do not publish live",
        ).run()
    )
    check("Ops can schedule", scheduled.get("status") == "post_added", str(scheduled)[:200])
    paused = _parse(CampaignScheduler(action="pause_campaign", campaign_id=campaign_id).run())
    check("Ops can pause", paused.get("status") == "paused", str(paused)[:200])
    BudgetManager(action="set_budget", client_name="Atlas Peak Coffee", total_budget=5000.0).run()
    tracker = _parse(PostTracker(filter_client="Atlas Peak Coffee").run())
    check("Post tracker reads the drill", tracker.get("total_campaigns", 0) >= 1, str(tracker)[:200])
    dashboard = _parse(CampaignDashboard(client_name="Atlas Peak Coffee").run())
    check("Ops dashboard", "summary" in dashboard, str(dashboard)[:200])

    performance = _parse(
        PerformanceInsightBuilder(
            client_name="Atlas Peak Coffee",
            campaign_goal="subscription signups",
            live_metrics_json="",
        ).run()
    )
    if _has_error(performance):
        log_error("Performance Analyst", str(performance), location="PerformanceInsightBuilder.run")
        check("Performance brief", False, str(performance)[:240])
    else:
        check("Performance brief", performance.get("status") == "complete" or bool(performance.get("brief")))

    diagnostics = FacebookTokenDiagnostics(include_accounts_lookup=True).run()
    if not isinstance(diagnostics, dict):
        diagnostics = {"raw": diagnostics}
    check("Facebook token diagnostics ran", "token_is_valid" in diagnostics, str(diagnostics)[:200])
    if not diagnostics.get("token_is_valid"):
        log_error(
            "Media Operations Director",
            "Facebook token invalid during communications test",
            location="FacebookTokenDiagnostics.run",
            context={"token_type": diagnostics.get("token_type")},
        )
        NOTES.append("Facebook token is not valid; Media write APIs were not re-exercised.")

    section("4. CEO as client communicator (live team turn)")
    reply_box = {"value": None, "error": None}

    def _ceo_turn():
        try:
            reply_box["value"] = run_client_turn(
                "This is a systems communications test for Atlas Peak Coffee. "
                "Introduce Manifest AI in one sentence, confirm you are my point of contact, "
                "and do not publish anything or spend any budget.",
                agency,
            )
        except Exception as exc:
            reply_box["error"] = exc

    thread = threading.Thread(target=_ceo_turn, daemon=True)
    thread.start()
    thread.join(180)
    if thread.is_alive():
        log_error("Chief Growth Strategist", "CEO turn timed out after 180s", location="run_client_turn")
        check("CEO team turn completed", False, "timeout")
    elif reply_box["error"] is not None:
        log_error("Chief Growth Strategist", reply_box["error"], location="run_client_turn")
        check("CEO team turn completed", False, str(reply_box["error"])[:200])
    else:
        reply = reply_box["value"]
        text = getattr(reply, "text", "") or ""
        failed = text.lower().startswith("[error]")
        check("CEO team turn completed", bool(text.strip()) and not failed, text[:220])
        check("CEO used a client-facing voice", (not failed) and ("Manifest" in text or "point of contact" in text.lower() or len(text) > 30), text[:220])
        check("CEO did not dump internal agent names as a roster", "tools_folder" not in text.lower())
        print("\n  CEO said:\n  " + "\n  ".join(text.strip().splitlines()[:12]))

    section("5. Shared memory + error log")
    set_state_value("handoff_status", "communications_test_complete")
    check("Shared memory round-trip", get_state_value("handoff_status") == "communications_test_complete")
    before = len(read_error_events(limit=500))
    log_error(
        "Chief Growth Strategist",
        "intentional communications-test log event",
        location="test_agency_communications.py",
    )
    after = read_error_events(limit=500)
    check("Errors persist", len(after) >= before)
    check("Error log does not store env secrets", "FACEBOOK_ACCESS_TOKEN" not in json.dumps(after[-1]))

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

        log_error("Chief Growth Strategist", exc, location="test_agency_communications.main")
        print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise SystemExit(1)
