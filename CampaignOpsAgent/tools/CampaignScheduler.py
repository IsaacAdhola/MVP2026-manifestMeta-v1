from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import json

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA_FILE = _PROJECT_ROOT / "campaign_data" / "schedule.json"


def _load() -> dict:
    if _DATA_FILE.exists():
        return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    return {"campaigns": []}


def _save(data: dict) -> None:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class CampaignScheduler(BaseTool):
    """
    Creates or updates a campaign entry in the schedule.
    Use this to set when a post should go live, on which platform,
    and attach any relevant content details.
    """

    action: str = Field(
        ...,
        description=(
            "What to do: 'create_campaign', 'add_post', 'update_post_status', 'list_campaigns', 'list_posts'."
        ),
    )
    campaign_name: Optional[str] = Field(None, description="Name of the campaign.")
    campaign_id: Optional[str] = Field(None, description="Existing campaign ID (for add_post / list_posts).")
    client_name: Optional[str] = Field(None, description="Client the campaign belongs to.")
    platform: Optional[str] = Field(None, description="Platform for the post: Facebook, Instagram, etc.")
    scheduled_time: Optional[str] = Field(
        None,
        description="ISO 8601 datetime for when the post should go live, e.g. '2026-07-01T10:00:00Z'.",
    )
    content_summary: Optional[str] = Field(None, description="Brief description of the post content.")
    image_path: Optional[str] = Field(None, description="Path to the approved image asset.")
    post_id: Optional[str] = Field(None, description="Post ID for status updates.")
    new_status: Optional[str] = Field(
        None,
        description="New status for update_post_status: 'scheduled', 'live', 'completed', 'paused', 'cancelled'.",
    )
    ad_set_id: Optional[str] = Field(None, description="Meta ad set ID once the post is live.")

    def run(self) -> str:
        data = _load()

        if self.action == "create_campaign":
            campaign = {
                "id": str(uuid4()),
                "name": self.campaign_name or "Unnamed Campaign",
                "client": self.client_name or "Unknown Client",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "posts": [],
            }
            data["campaigns"].append(campaign)
            _save(data)
            return json.dumps({"status": "created", "campaign": campaign})

        if self.action == "list_campaigns":
            summary = [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "client": c["client"],
                    "total_posts": len(c["posts"]),
                    "live_posts": sum(1 for p in c["posts"] if p["status"] == "live"),
                    "scheduled_posts": sum(1 for p in c["posts"] if p["status"] == "scheduled"),
                }
                for c in data["campaigns"]
            ]
            return json.dumps({"campaigns": summary})

        campaign = next((c for c in data["campaigns"] if c["id"] == self.campaign_id), None)
        if not campaign:
            return json.dumps({"error": f"Campaign '{self.campaign_id}' not found. Create it first."})

        if self.action == "add_post":
            post = {
                "id": str(uuid4()),
                "platform": self.platform or "Facebook",
                "scheduled_time": self.scheduled_time,
                "status": "scheduled",
                "content_summary": self.content_summary,
                "image_path": self.image_path,
                "ad_set_id": self.ad_set_id,
                "actual_live_time": None,
                "cost": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            campaign["posts"].append(post)
            _save(data)
            return json.dumps({"status": "post_added", "post": post})

        if self.action == "update_post_status":
            post = next((p for p in campaign["posts"] if p["id"] == self.post_id), None)
            if not post:
                return json.dumps({"error": f"Post '{self.post_id}' not found in campaign."})
            post["status"] = self.new_status
            if self.new_status == "live":
                post["actual_live_time"] = datetime.now(timezone.utc).isoformat()
            if self.ad_set_id:
                post["ad_set_id"] = self.ad_set_id
            _save(data)
            return json.dumps({"status": "updated", "post": post})

        if self.action == "list_posts":
            return json.dumps({"campaign": campaign["name"], "posts": campaign["posts"]})

        return json.dumps({"error": f"Unknown action '{self.action}'."})
