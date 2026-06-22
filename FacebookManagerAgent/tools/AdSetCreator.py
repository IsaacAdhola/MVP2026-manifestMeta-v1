from datetime import datetime, timedelta, timezone

from agency_swarm.tools import BaseTool
from pydantic import Field
import facebook_business.exceptions
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet

from dotenv import load_dotenv
from workflow_state import get_state_value, set_state_value
try:
    from ..facebook_auth import get_required_env, initialize_business_sdk
except ImportError:
    import os
    import sys

    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import get_required_env, initialize_business_sdk

load_dotenv()

class AdSetCreator(BaseTool):
    """
    Tool for creating ad sets within a Facebook campaign.
    """
    name: str = Field(..., description='Name of the ad set.')
    budget: int = Field(..., description='Daily budget for the ad set in cents.')
    activate_immediately: bool = Field(
        default=False,
        description="Set true only when the client explicitly approved immediate go-live. Default keeps ad set paused.",
    )

    def run(self):
        try:
            initialize_business_sdk()
            ad_account_id = get_required_env("FACEBOOK_AD_ACCOUNT_ID")
            campaign_id = self._shared_state.get('campaign_id') or get_state_value("campaign_id")
            if not campaign_id:
                raise ValueError('Campaign ID not found. Please use AdCampaignStarter tool first.')

            ad_account = AdAccount(ad_account_id)
            ad_set_status = (
                AdSet.Status.active
                if self.activate_immediately
                else AdSet.Status.paused
            )
            params = {
                'campaign_id': campaign_id,
                'name': self.name,
                'targeting': {"geo_locations": {"countries": ["US"]}},
                'start_time': datetime.now(timezone.utc).isoformat(),
                'end_time': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                'status': ad_set_status,
                'daily_budget': self.budget,
                "billing_event": "IMPRESSIONS",
                'optimization_goal': "LINK_CLICKS",
                "bid_amount": "100",
            }
            ad_set = ad_account.create_ad_set(params=params)
            self._shared_state.set('ad_set_id', ad_set["id"])
            set_state_value("ad_set_id", ad_set["id"])
            return (
                f'Ad set {self.name} has been successfully created '
                f'with ID {ad_set["id"]} in status {ad_set_status}.'
            )
        except facebook_business.exceptions.FacebookRequestError as e:
            return f'Error creating ad set: {e}'

if __name__ == "__main__":
    tool = AdSetCreator(name="Test Ad Set", budget=1000)
    # Use the campaign_id from the last test (or update with actual campaign_id)
    tool._shared_state.set('campaign_id', '6867670459634')
    print(tool.run())
