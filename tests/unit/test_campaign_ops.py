"""Pytest suite for CampaignOpsAgent tools and agent wiring.

Covers CampaignScheduler, PostTracker, BudgetManager, CampaignDashboard, agent instantiation, and the
shared workflow-state round-trip. Pure Python logic and local file state only: no network, no API key.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from CampaignOpsAgent import CampaignOpsAgent
from CampaignOpsAgent.tools.BudgetManager import BudgetManager
from CampaignOpsAgent.tools.CampaignDashboard import CampaignDashboard
from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler
from CampaignOpsAgent.tools.PostTracker import PostTracker
from workflow_state import get_state_value, set_state_value

_ROOT = Path(__file__).resolve().parents[2]


def _reset_campaign_data():
    data = _ROOT / "campaign_data"
    for name in ("schedule.json", "budgets.json"):
        path = data / name
        if path.exists():
            path.unlink()


def test_campaign_ops_suite():
    _reset_campaign_data()
    failures = []

    def check(label, condition, detail=""):
        if not condition:
            failures.append(f"{label} — {detail}")

    # 1. CampaignScheduler
    r = json.loads(CampaignScheduler(action="create_campaign",
        campaign_name="Summer Launch 2026", client_name="AcmeCorp").run())
    check("create_campaign returns status=created", r.get("status") == "created", r)
    campaign_id = r["campaign"]["id"]
    check("campaign has a UUID id", len(campaign_id) == 36, campaign_id)

    future_time = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT10:00:00Z")
    r = json.loads(CampaignScheduler(action="add_post", campaign_id=campaign_id,
        platform="Facebook", scheduled_time=future_time,
        content_summary="Summer sale hero post").run())
    check("add_post returns status=post_added", r.get("status") == "post_added", r)
    post_id_1 = r["post"]["id"]
    check("post status defaults to scheduled", r["post"]["status"] == "scheduled")

    r = json.loads(CampaignScheduler(action="add_post", campaign_id=campaign_id,
        platform="Instagram", scheduled_time="2026-05-01T08:00:00Z",
        content_summary="Early teaser post").run())
    post_id_2 = r["post"]["id"]
    check("second post added successfully", r.get("status") == "post_added")

    r = json.loads(CampaignScheduler(action="update_post_status", campaign_id=campaign_id,
        post_id=post_id_2, new_status="live").run())
    check("update_post_status returns updated", r.get("status") == "updated")
    check("actual_live_time is set when going live", r["post"]["actual_live_time"] is not None)

    r = json.loads(CampaignScheduler(action="list_campaigns").run())
    check("list_campaigns returns at least 1", len(r["campaigns"]) >= 1)

    r = json.loads(CampaignScheduler(action="list_posts", campaign_id=campaign_id).run())
    check("list_posts returns 2 posts", len(r["posts"]) == 2)

    # 2. PostTracker
    r = json.loads(PostTracker().run())
    check("PostTracker runs with no filter", "campaigns" in r)
    check("totals.live >= 1", r["totals"].get("live", 0) >= 1)
    check("totals.scheduled >= 1", r["totals"].get("scheduled", 0) >= 1)

    r = json.loads(PostTracker(filter_client="AcmeCorp").run())
    check("filter_client=AcmeCorp returns 1 campaign", r["total_campaigns"] == 1)
    check("overdue correctly 0 after marking past post live", r["totals"].get("overdue", 0) == 0)

    r = json.loads(PostTracker(filter_status="live").run())
    check("filter_status=live returns only live posts",
          all(p["status"] == "live" for c in r["campaigns"] for p in c["posts"]))

    # 3. BudgetManager
    r = json.loads(BudgetManager(action="set_budget", client_name="AcmeCorp",
        total_budget=50000.00, currency="USD").run())
    check("set_budget returns budget_set", r.get("status") == "budget_set")
    check("remaining equals total when no spend", r["remaining"] == 50000.00)

    r = json.loads(BudgetManager(action="record_spend", client_name="AcmeCorp",
        campaign_id=campaign_id, post_id=post_id_2, spend_amount=1250.00).run())
    check("record_spend returns spend_recorded", r.get("status") == "spend_recorded")
    check("total_spent updated correctly", r["total_spent"] == 1250.00)
    check("remaining updated correctly", r["remaining"] == 48750.00)
    check("pct_used is 2.5%", r["pct_used"] == 2.5)
    check("no alert at 2.5% spend", "alert" not in r)

    r = json.loads(BudgetManager(action="record_spend", client_name="AcmeCorp",
        spend_amount=40000.00).run())
    check("alert fires at >75% spend", "alert" in r)
    check("alert says WARNING or CRITICAL", "WARNING" in r.get("alert", "") or "CRITICAL" in r.get("alert", ""))

    r = json.loads(BudgetManager(action="get_budget_status", client_name="AcmeCorp").run())
    check("get_budget_status returns spend_log", "spend_log" in r)
    check("spend_log has 2 entries", len(r["spend_log"]) == 2)

    r = json.loads(BudgetManager(action="list_all_budgets").run())
    check("list_all_budgets returns budgets list", "budgets" in r)
    check("AcmeCorp present in list", any(b["client"] == "AcmeCorp" for b in r["budgets"]))

    # 4. CampaignDashboard
    r = json.loads(CampaignDashboard(client_name="AcmeCorp", include_spend_log=True).run())
    check("dashboard generates summary", "summary" in r)
    check("summary.total_campaigns >= 1", r["summary"]["total_campaigns"] >= 1)
    check("summary.posts_live >= 1", r["summary"]["posts_live"] >= 1)
    check("budget section present", "budget" in r)
    check("budget health is WARNING or CRITICAL (>75% spent)",
          r["budget"].get("budget_health") in ("WARNING", "CRITICAL"))
    check("spend_log present when include_spend_log=True", "spend_log" in r["budget"])
    check("alerts list present", isinstance(r["alerts"], list))

    r = json.loads(CampaignDashboard().run())
    check("agency-wide dashboard has all_clients", "all_clients" in r["budget"])

    # 5. Agent wiring
    agent = CampaignOpsAgent()
    check("agent name is Campaign Operations Director", agent.name == "Campaign Operations Director")

    # 6. Shared state handoff
    set_state_value("test_campaign_id", campaign_id)
    check("workflow_state set/get round-trip", get_state_value("test_campaign_id") == campaign_id)

    assert not failures, "CampaignOps checks failed:\n" + "\n".join(failures)
