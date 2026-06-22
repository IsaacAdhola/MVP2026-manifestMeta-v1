from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import json

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SCHEDULE_FILE = _PROJECT_ROOT / "campaign_data" / "schedule.json"
_BUDGET_FILE = _PROJECT_ROOT / "campaign_data" / "budgets.json"


def _load(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


class CampaignDashboard(BaseTool):
    """
    Generates a comprehensive client-facing campaign dashboard.
    Shows all campaigns, post schedule, live status, budget health,
    spend to date, upcoming posts, and any alerts. This is the single
    source of truth a client sees for their entire account.
    """

    client_name: Optional[str] = Field(
        None,
        description="Filter dashboard to one client. Leave blank to show all clients (agency-wide view).",
    )
    include_spend_log: bool = Field(
        False,
        description="Set to true to include full line-by-line spend history in the report.",
    )

    def run(self) -> str:
        now = datetime.now(timezone.utc)
        schedule = _load(_SCHEDULE_FILE)
        budgets = _load(_BUDGET_FILE)

        campaigns = schedule.get("campaigns", [])
        if self.client_name:
            campaigns = [c for c in campaigns if self.client_name.lower() in c.get("client", "").lower()]

        client_key = self.client_name.strip().lower() if self.client_name else None

        # ── Aggregate post stats ──────────────────────────────────────────────
        all_posts = [p for c in campaigns for p in c.get("posts", [])]
        total_posts = len(all_posts)
        live_posts = [p for p in all_posts if p["status"] == "live"]
        scheduled_posts = [p for p in all_posts if p["status"] == "scheduled"]
        completed_posts = [p for p in all_posts if p["status"] == "completed"]
        overdue_posts = []
        for p in scheduled_posts:
            if p.get("scheduled_time"):
                try:
                    sched = datetime.fromisoformat(p["scheduled_time"].replace("Z", "+00:00"))
                    if sched < now:
                        overdue_posts.append(p)
                except ValueError:
                    pass

        # ── Upcoming (next 7 days) ────────────────────────────────────────────
        upcoming = []
        for p in scheduled_posts:
            if p.get("scheduled_time"):
                try:
                    sched = datetime.fromisoformat(p["scheduled_time"].replace("Z", "+00:00"))
                    delta = (sched - now).days
                    if 0 <= delta <= 7:
                        upcoming.append({
                            "post_id": p["id"],
                            "platform": p.get("platform"),
                            "scheduled_time": p["scheduled_time"],
                            "days_until_live": delta,
                            "content_summary": p.get("content_summary"),
                        })
                except ValueError:
                    pass
        upcoming.sort(key=lambda x: x["scheduled_time"])

        # ── Budget section ────────────────────────────────────────────────────
        budget_section = {}
        clients_data = budgets.get("clients", {})
        if client_key and client_key in clients_data:
            b = clients_data[client_key]
            total = b.get("total_budget", 0)
            spent = b.get("total_spent", 0)
            remaining = round(total - spent, 2)
            pct = round((spent / total * 100) if total > 0 else 0, 1)
            budget_section = {
                "total_budget": total,
                "currency": b.get("currency", "USD"),
                "total_spent": spent,
                "remaining": remaining,
                "pct_used": pct,
                "budget_health": (
                    "CRITICAL" if pct >= 90 else
                    "WARNING" if pct >= 75 else
                    "HEALTHY"
                ),
            }
            if self.include_spend_log:
                budget_section["spend_log"] = b.get("spend_log", [])
        elif not client_key:
            all_budgets = []
            for ck, b in clients_data.items():
                total = b.get("total_budget", 0)
                spent = b.get("total_spent", 0)
                pct = round((spent / total * 100) if total > 0 else 0, 1)
                all_budgets.append({
                    "client": b.get("display_name", ck),
                    "total_budget": total,
                    "currency": b.get("currency", "USD"),
                    "total_spent": spent,
                    "remaining": round(total - spent, 2),
                    "pct_used": pct,
                    "budget_health": (
                        "CRITICAL" if pct >= 90 else
                        "WARNING" if pct >= 75 else
                        "HEALTHY"
                    ),
                })
            budget_section = {"all_clients": all_budgets}

        # ── Alerts ───────────────────────────────────────────────────────────
        alerts = []
        if overdue_posts:
            alerts.append(f"{len(overdue_posts)} post(s) are overdue — scheduled time has passed but still not live.")
        if isinstance(budget_section, dict) and budget_section.get("budget_health") in ("CRITICAL", "WARNING"):
            alerts.append(f"Budget {budget_section['budget_health']}: {budget_section['pct_used']}% of budget used.")

        # ── Campaign breakdown ────────────────────────────────────────────────
        campaign_breakdown = []
        for c in campaigns:
            posts = c.get("posts", [])
            campaign_breakdown.append({
                "id": c["id"],
                "name": c["name"],
                "client": c["client"],
                "posts_total": len(posts),
                "posts_live": sum(1 for p in posts if p["status"] == "live"),
                "posts_scheduled": sum(1 for p in posts if p["status"] == "scheduled"),
                "posts_completed": sum(1 for p in posts if p["status"] == "completed"),
                "total_spend": sum(p.get("cost") or 0 for p in posts),
            })

        dashboard = {
            "dashboard_generated_at": now.isoformat(),
            "client_filter": self.client_name or "ALL CLIENTS",
            "summary": {
                "total_campaigns": len(campaigns),
                "total_posts": total_posts,
                "posts_live": len(live_posts),
                "posts_scheduled": len(scheduled_posts),
                "posts_completed": len(completed_posts),
                "posts_overdue": len(overdue_posts),
            },
            "alerts": alerts,
            "budget": budget_section,
            "upcoming_posts_next_7_days": upcoming,
            "campaigns": campaign_breakdown,
        }

        return json.dumps(dashboard, indent=2, ensure_ascii=False)
