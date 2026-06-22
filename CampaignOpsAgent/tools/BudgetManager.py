from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import json

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BUDGET_FILE = _PROJECT_ROOT / "campaign_data" / "budgets.json"
_SCHEDULE_FILE = _PROJECT_ROOT / "campaign_data" / "schedule.json"


def _load_budgets() -> dict:
    if _BUDGET_FILE.exists():
        return json.loads(_BUDGET_FILE.read_text(encoding="utf-8"))
    return {"clients": {}}


def _save_budgets(data: dict) -> None:
    _BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    _BUDGET_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_schedule() -> dict:
    if _SCHEDULE_FILE.exists():
        return json.loads(_SCHEDULE_FILE.read_text(encoding="utf-8"))
    return {"campaigns": []}


class BudgetManager(BaseTool):
    """
    Manages client ad budgets and tracks spend per post/campaign.
    Actions: set_budget, record_spend, get_budget_status, list_all_budgets.
    """

    action: str = Field(
        ...,
        description=(
            "What to do: "
            "'set_budget' — set or update a client's total campaign budget; "
            "'record_spend' — log the actual cost of a post once it runs; "
            "'get_budget_status' — get remaining budget and spend breakdown for a client; "
            "'list_all_budgets' — overview of all client budgets."
        ),
    )
    client_name: Optional[str] = Field(None, description="Client name this budget belongs to.")
    campaign_id: Optional[str] = Field(None, description="Campaign ID the spend is associated with.")
    post_id: Optional[str] = Field(None, description="Post ID the spend is associated with (for record_spend).")
    total_budget: Optional[float] = Field(None, description="Total budget amount in USD (for set_budget).")
    currency: Optional[str] = Field("USD", description="Currency code, default USD.")
    spend_amount: Optional[float] = Field(None, description="Actual dollar amount spent on this post (for record_spend).")
    notes: Optional[str] = Field(None, description="Optional notes about this budget entry or spend.")

    def run(self) -> str:
        data = _load_budgets()
        now = datetime.now(timezone.utc).isoformat()

        if self.action == "list_all_budgets":
            overview = []
            for client, info in data["clients"].items():
                overview.append({
                    "client": info.get("display_name", client),
                    "total_budget": info.get("total_budget", 0),
                    "currency": info.get("currency", "USD"),
                    "total_spent": info.get("total_spent", 0),
                    "remaining": info.get("total_budget", 0) - info.get("total_spent", 0),
                    "pct_used": round(
                        (info.get("total_spent", 0) / info["total_budget"] * 100)
                        if info.get("total_budget", 0) > 0 else 0,
                        1,
                    ),
                })
            return json.dumps({"budgets": overview}, indent=2)

        if not self.client_name:
            return json.dumps({"error": "client_name is required for this action."})

        client_key = self.client_name.strip().lower()

        if self.action == "set_budget":
            if self.total_budget is None:
                return json.dumps({"error": "total_budget is required for set_budget."})
            existing = data["clients"].get(client_key, {})
            data["clients"][client_key] = {
                "display_name": self.client_name,
                "total_budget": self.total_budget,
                "currency": self.currency or "USD",
                "total_spent": existing.get("total_spent", 0.0),
                "spend_log": existing.get("spend_log", []),
                "set_at": now,
                "notes": self.notes,
            }
            _save_budgets(data)
            remaining = self.total_budget - data["clients"][client_key]["total_spent"]
            return json.dumps({
                "status": "budget_set",
                "client": self.client_name,
                "total_budget": self.total_budget,
                "currency": self.currency,
                "remaining": remaining,
            })

        client = data["clients"].get(client_key)
        if not client:
            return json.dumps({"error": f"No budget found for '{self.client_name}'. Use set_budget first."})

        if self.action == "record_spend":
            if self.spend_amount is None:
                return json.dumps({"error": "spend_amount is required for record_spend."})

            # Also update the cost on the post in schedule.json
            if self.campaign_id and self.post_id:
                sched = _load_schedule()
                for campaign in sched.get("campaigns", []):
                    if campaign["id"] == self.campaign_id:
                        for post in campaign.get("posts", []):
                            if post["id"] == self.post_id:
                                post["cost"] = self.spend_amount

                schedule_file = _PROJECT_ROOT / "campaign_data" / "schedule.json"
                schedule_file.write_text(json.dumps(sched, indent=2, ensure_ascii=False), encoding="utf-8")

            entry = {
                "campaign_id": self.campaign_id,
                "post_id": self.post_id,
                "amount": self.spend_amount,
                "currency": client.get("currency", "USD"),
                "recorded_at": now,
                "notes": self.notes,
            }
            client["spend_log"].append(entry)
            client["total_spent"] = round(client.get("total_spent", 0.0) + self.spend_amount, 2)
            remaining = round(client["total_budget"] - client["total_spent"], 2)

            alert = None
            pct_used = (client["total_spent"] / client["total_budget"] * 100) if client["total_budget"] > 0 else 0
            if pct_used >= 90:
                alert = f"ALERT: {client['display_name']} has used {pct_used:.1f}% of their budget."
            elif pct_used >= 75:
                alert = f"WARNING: {client['display_name']} has used {pct_used:.1f}% of their budget."

            _save_budgets(data)
            result = {
                "status": "spend_recorded",
                "client": self.client_name,
                "spend_recorded": self.spend_amount,
                "total_spent": client["total_spent"],
                "total_budget": client["total_budget"],
                "remaining": remaining,
                "pct_used": round(pct_used, 1),
            }
            if alert:
                result["alert"] = alert
            return json.dumps(result, indent=2)

        if self.action == "get_budget_status":
            total_spent = client.get("total_spent", 0.0)
            total_budget = client.get("total_budget", 0.0)
            remaining = round(total_budget - total_spent, 2)
            pct_used = round((total_spent / total_budget * 100) if total_budget > 0 else 0, 1)
            return json.dumps({
                "client": client.get("display_name", self.client_name),
                "currency": client.get("currency", "USD"),
                "total_budget": total_budget,
                "total_spent": total_spent,
                "remaining": remaining,
                "pct_used": pct_used,
                "spend_log": client.get("spend_log", []),
            }, indent=2)

        return json.dumps({"error": f"Unknown action '{self.action}'."})
