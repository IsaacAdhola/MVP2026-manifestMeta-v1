from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import json

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SCHEDULE_FILE = _PROJECT_ROOT / "campaign_data" / "schedule.json"


def _load() -> dict:
    if _SCHEDULE_FILE.exists():
        return json.loads(_SCHEDULE_FILE.read_text(encoding="utf-8"))
    return {"campaigns": []}


class PostTracker(BaseTool):
    """
    Queries the live post tracker.
    Returns counts of live, scheduled, completed, and overdue posts
    across all campaigns or for a specific client/campaign.
    Also flags any posts that are overdue (scheduled time has passed but still not live).
    """

    filter_client: Optional[str] = Field(
        None, description="Filter results to a specific client name. Leave blank for all clients."
    )
    filter_campaign_id: Optional[str] = Field(
        None, description="Filter results to a specific campaign ID."
    )
    filter_status: Optional[str] = Field(
        None,
        description="Filter by post status: 'scheduled', 'live', 'completed', 'paused', 'cancelled'. Leave blank for all.",
    )

    def run(self) -> str:
        data = _load()
        now = datetime.now(timezone.utc)

        campaigns = data.get("campaigns", [])
        if self.filter_client:
            campaigns = [c for c in campaigns if self.filter_client.lower() in c.get("client", "").lower()]
        if self.filter_campaign_id:
            campaigns = [c for c in campaigns if c["id"] == self.filter_campaign_id]

        summary = {
            "generated_at": now.isoformat(),
            "total_campaigns": len(campaigns),
            "totals": {"scheduled": 0, "live": 0, "completed": 0, "paused": 0, "cancelled": 0, "overdue": 0},
            "campaigns": [],
        }

        for campaign in campaigns:
            posts = campaign.get("posts", [])
            if self.filter_status:
                posts_view = [p for p in posts if p["status"] == self.filter_status]
            else:
                posts_view = posts

            overdue = []
            for p in posts:
                if p["status"] == "scheduled" and p.get("scheduled_time"):
                    try:
                        sched = datetime.fromisoformat(p["scheduled_time"].replace("Z", "+00:00"))
                        if sched < now:
                            overdue.append(p["id"])
                            summary["totals"]["overdue"] += 1
                    except ValueError:
                        pass
                summary["totals"][p["status"]] = summary["totals"].get(p["status"], 0) + 1

            campaign_entry = {
                "id": campaign["id"],
                "name": campaign["name"],
                "client": campaign["client"],
                "post_counts": {
                    "total": len(posts),
                    "scheduled": sum(1 for p in posts if p["status"] == "scheduled"),
                    "live": sum(1 for p in posts if p["status"] == "live"),
                    "completed": sum(1 for p in posts if p["status"] == "completed"),
                    "overdue_ids": overdue,
                },
                "posts": [
                    {
                        "id": p["id"],
                        "platform": p.get("platform"),
                        "scheduled_time": p.get("scheduled_time"),
                        "actual_live_time": p.get("actual_live_time"),
                        "status": p.get("status"),
                        "content_summary": p.get("content_summary"),
                        "cost": p.get("cost"),
                    }
                    for p in posts_view
                ],
            }
            summary["campaigns"].append(campaign_entry)

        return json.dumps(summary, indent=2, ensure_ascii=False)
