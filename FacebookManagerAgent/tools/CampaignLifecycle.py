import json
import os
import sys
from typing import Optional

_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign
from facebook_business.exceptions import FacebookRequestError
from pydantic import Field

from workflow_state import get_state_value, set_state_value

try:
    from ..facebook_auth import initialize_business_sdk
except ImportError:
    import sys

    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import initialize_business_sdk

from error_logger import log_error

load_dotenv()

_STATUS_MAP = {
    "pause": "PAUSED",
    "paused": "PAUSED",
    "activate": "ACTIVE",
    "active": "ACTIVE",
    "archive": "ARCHIVED",
    "archived": "ARCHIVED",
}


class CampaignLifecycle(BaseTool):
    """
    Pause, activate, archive, or inspect a Meta campaign, ad set, or ad.
    Defaults to the campaign ID stored in shared workflow state.
    """

    action: str = Field(
        ...,
        description=(
            "What to do: 'pause', 'activate', 'archive', or 'get_status'."
        ),
    )
    campaign_id: Optional[str] = Field(
        default=None,
        description="Meta campaign ID. Defaults to shared-state campaign_id.",
    )
    object_type: str = Field(
        default="campaign",
        description="Which Meta object to update: 'campaign', 'adset', or 'ad'.",
    )
    object_id: Optional[str] = Field(
        default=None,
        description="Explicit ad set or ad ID. Defaults to shared-state ad_set_id or ad_id.",
    )

    def run(self):
        actor = "Media Operations Director"
        try:
            initialize_business_sdk()
            object_type = (self.object_type or "campaign").strip().lower()
            action = (self.action or "").strip().lower()
            object_id = self._resolve_id(object_type)
            if not object_id:
                message = f"No {object_type} ID found. Create the object first or pass object_id."
                log_error(actor, message, location="CampaignLifecycle.run", context={"action": action})
                return json.dumps({"error": message, "object_type": object_type})

            if action == "get_status":
                payload = self._read_status(object_type, object_id)
                set_state_value("campaign_status", str(payload.get("status") or "").lower())
                return json.dumps({"status": "ok", "object": payload}, ensure_ascii=True)

            target_status = _STATUS_MAP.get(action)
            if not target_status:
                message = f"Unknown action '{self.action}'. Use pause, activate, archive, or get_status."
                log_error(actor, message, location="CampaignLifecycle.run")
                return json.dumps({"error": message})

            self._update_status(object_type, object_id, target_status)
            if object_type == "campaign":
                set_state_value("campaign_status", target_status.lower())
            return json.dumps(
                {
                    "status": "updated",
                    "object_type": object_type,
                    "object_id": object_id,
                    "new_status": target_status,
                },
                ensure_ascii=True,
            )
        except FacebookRequestError as exc:
            log_error(
                actor,
                exc,
                location="CampaignLifecycle.run",
                context={
                    "api_error_code": exc.api_error_code(),
                    "api_error_subcode": exc.api_error_subcode(),
                },
            )
            return json.dumps(
                {
                    "error": exc.api_error_message(),
                    "code": exc.api_error_code(),
                    "subcode": exc.api_error_subcode(),
                }
            )
        except Exception as exc:
            log_error(actor, exc, location="CampaignLifecycle.run")
            return json.dumps({"error": str(exc)[:300]})

    def _resolve_id(self, object_type: str) -> str:
        if self.object_id:
            return str(self.object_id).strip()
        if object_type == "campaign":
            return str(self.campaign_id or get_state_value("campaign_id") or "").strip()
        if object_type == "adset":
            return str(get_state_value("ad_set_id") or "").strip()
        if object_type == "ad":
            return str(get_state_value("ad_id") or "").strip()
        return ""

    def _read_status(self, object_type: str, object_id: str) -> dict:
        fields = ["id", "name", "status", "effective_status"]
        extra = {
            "campaign": ["objective", "daily_budget"],
            "adset": ["daily_budget", "campaign_id"],
            "ad": ["adset_id", "campaign_id"],
        }
        if object_type == "campaign":
            obj = Campaign(object_id)
        elif object_type == "adset":
            obj = AdSet(object_id)
        else:
            obj = Ad(object_id)
        obj.api_get(fields=fields + extra.get(object_type, []))
        if hasattr(obj, "export_all_data"):
            return obj.export_all_data()
        return {key: obj.get(key) for key in fields}

    def _update_status(self, object_type: str, object_id: str, status: str) -> None:
        if object_type == "campaign":
            Campaign(object_id).api_update(params={Campaign.Field.status: status})
            return
        if object_type == "adset":
            AdSet(object_id).api_update(params={AdSet.Field.status: status})
            return
        Ad(object_id).api_update(params={Ad.Field.status: status})
