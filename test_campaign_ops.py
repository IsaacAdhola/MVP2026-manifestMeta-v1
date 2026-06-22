"""
Test suite for CampaignOpsAgent tools and agency integration.
Tests: CampaignScheduler, PostTracker, BudgetManager, CampaignDashboard, agency import.
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))

# Clean slate — remove test data files before run
from pathlib import Path
_data = Path("campaign_data")
for f in ["schedule.json", "budgets.json"]:
    p = _data / f
    if p.exists():
        p.unlink()

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label} — {detail}")
        FAIL += 1

print("\n" + "="*60)
print("CAMPAIGN OPS AGENT — TOOL TESTS")
print("="*60)

# ─────────────────────────────────────────────────────────────────
# 1. CampaignScheduler
# ─────────────────────────────────────────────────────────────────
print("\n[1] CampaignScheduler")
from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler

# Create campaign
r = json.loads(CampaignScheduler(action="create_campaign",
    campaign_name="Summer Launch 2026", client_name="AcmeCorp").run())
check("create_campaign returns status=created", r.get("status") == "created", r)
campaign_id = r["campaign"]["id"]
check("campaign has a UUID id", len(campaign_id) == 36, campaign_id)

# Add post 1 (future — scheduled)
r = json.loads(CampaignScheduler(action="add_post", campaign_id=campaign_id,
    platform="Facebook", scheduled_time="2026-07-01T10:00:00Z",
    content_summary="Summer sale hero post").run())
check("add_post returns status=post_added", r.get("status") == "post_added", r)
post_id_1 = r["post"]["id"]
check("post status defaults to scheduled", r["post"]["status"] == "scheduled")

# Add post 2 (past date — will be overdue)
r = json.loads(CampaignScheduler(action="add_post", campaign_id=campaign_id,
    platform="Instagram", scheduled_time="2026-05-01T08:00:00Z",
    content_summary="Early teaser post").run())
post_id_2 = r["post"]["id"]
check("second post added successfully", r.get("status") == "post_added")

# Update post 2 to live
r = json.loads(CampaignScheduler(action="update_post_status", campaign_id=campaign_id,
    post_id=post_id_2, new_status="live").run())
check("update_post_status returns updated", r.get("status") == "updated")
check("actual_live_time is set when going live", r["post"]["actual_live_time"] is not None)

# List campaigns
r = json.loads(CampaignScheduler(action="list_campaigns").run())
check("list_campaigns returns at least 1", len(r["campaigns"]) >= 1)

# List posts
r = json.loads(CampaignScheduler(action="list_posts", campaign_id=campaign_id).run())
check("list_posts returns 2 posts", len(r["posts"]) == 2)

# ─────────────────────────────────────────────────────────────────
# 2. PostTracker
# ─────────────────────────────────────────────────────────────────
print("\n[2] PostTracker")
from CampaignOpsAgent.tools.PostTracker import PostTracker

r = json.loads(PostTracker().run())
check("PostTracker runs with no filter", "campaigns" in r)
check("totals.live >= 1", r["totals"].get("live", 0) >= 1)
check("totals.scheduled >= 1", r["totals"].get("scheduled", 0) >= 1)

# Filter by client
r = json.loads(PostTracker(filter_client="AcmeCorp").run())
check("filter_client=AcmeCorp returns 1 campaign", r["total_campaigns"] == 1)

# Overdue detection — post_id_1 is in the future, post_id_2 was set to live
# so no scheduled+past posts remain → overdue = 0
check("overdue correctly 0 after marking past post live", r["totals"].get("overdue", 0) == 0)

# Filter by status
r = json.loads(PostTracker(filter_status="live").run())
check("filter_status=live returns only live posts",
      all(p["status"] == "live" for c in r["campaigns"] for p in c["posts"]))

# ─────────────────────────────────────────────────────────────────
# 3. BudgetManager
# ─────────────────────────────────────────────────────────────────
print("\n[3] BudgetManager")
from CampaignOpsAgent.tools.BudgetManager import BudgetManager

# Set budget
r = json.loads(BudgetManager(action="set_budget", client_name="AcmeCorp",
    total_budget=50000.00, currency="USD").run())
check("set_budget returns budget_set", r.get("status") == "budget_set")
check("remaining equals total when no spend", r["remaining"] == 50000.00)

# Record spend
r = json.loads(BudgetManager(action="record_spend", client_name="AcmeCorp",
    campaign_id=campaign_id, post_id=post_id_2, spend_amount=1250.00).run())
check("record_spend returns spend_recorded", r.get("status") == "spend_recorded")
check("total_spent updated correctly", r["total_spent"] == 1250.00)
check("remaining updated correctly", r["remaining"] == 48750.00)
check("pct_used is 2.5%", r["pct_used"] == 2.5)
check("no alert at 2.5% spend", "alert" not in r)

# Trigger warning alert (record large spend)
r = json.loads(BudgetManager(action="record_spend", client_name="AcmeCorp",
    spend_amount=40000.00).run())
check("alert fires at >75% spend", "alert" in r)
check("alert says WARNING or CRITICAL", "WARNING" in r.get("alert","") or "CRITICAL" in r.get("alert",""))

# Get budget status
r = json.loads(BudgetManager(action="get_budget_status", client_name="AcmeCorp").run())
check("get_budget_status returns spend_log", "spend_log" in r)
check("spend_log has 2 entries", len(r["spend_log"]) == 2)

# List all budgets
r = json.loads(BudgetManager(action="list_all_budgets").run())
check("list_all_budgets returns budgets list", "budgets" in r)
check("AcmeCorp present in list", any(b["client"] == "AcmeCorp" for b in r["budgets"]))

# ─────────────────────────────────────────────────────────────────
# 4. CampaignDashboard
# ─────────────────────────────────────────────────────────────────
print("\n[4] CampaignDashboard")
from CampaignOpsAgent.tools.CampaignDashboard import CampaignDashboard

# Full dashboard for AcmeCorp
r = json.loads(CampaignDashboard(client_name="AcmeCorp", include_spend_log=True).run())
check("dashboard generates summary", "summary" in r)
check("summary.total_campaigns >= 1", r["summary"]["total_campaigns"] >= 1)
check("summary.posts_live >= 1", r["summary"]["posts_live"] >= 1)
check("budget section present", "budget" in r)
check("budget health is WARNING or CRITICAL (>75% spent)", 
      r["budget"].get("budget_health") in ("WARNING", "CRITICAL"))
check("spend_log present when include_spend_log=True", "spend_log" in r["budget"])
check("alerts list present", isinstance(r["alerts"], list))

# Agency-wide dashboard
r = json.loads(CampaignDashboard().run())
check("agency-wide dashboard has all_clients", "all_clients" in r["budget"])

# ─────────────────────────────────────────────────────────────────
# 5. Agency import — agent wiring check
# ─────────────────────────────────────────────────────────────────
print("\n[5] Agency Import & Agent Wiring")
try:
    from CampaignOpsAgent import CampaignOpsAgent
    agent = CampaignOpsAgent()
    check("CampaignOpsAgent imports and instantiates", True)
    check("agent name is Campaign Operations Director", agent.name == "Campaign Operations Director")
except Exception as e:
    check("CampaignOpsAgent imports and instantiates", False, str(e))

# Verify tools load from tools_folder
try:
    from CampaignOpsAgent.tools.CampaignScheduler import CampaignScheduler
    from CampaignOpsAgent.tools.PostTracker import PostTracker
    from CampaignOpsAgent.tools.BudgetManager import BudgetManager
    from CampaignOpsAgent.tools.CampaignDashboard import CampaignDashboard
    check("All 4 tools importable", True)
except Exception as e:
    check("All 4 tools importable", False, str(e))

# ─────────────────────────────────────────────────────────────────
# 6. State handoff — shared state read/write
# ─────────────────────────────────────────────────────────────────
print("\n[6] Shared State Handoff")
try:
    from workflow_state import set_state_value, get_state_value
    set_state_value("test_campaign_id", campaign_id)
    val = get_state_value("test_campaign_id")
    check("workflow_state set/get round-trip", val == campaign_id, f"got={val}")
except Exception as e:
    check("workflow_state set/get round-trip", False, str(e))

# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("="*60)
sys.exit(0 if FAIL == 0 else 1)
