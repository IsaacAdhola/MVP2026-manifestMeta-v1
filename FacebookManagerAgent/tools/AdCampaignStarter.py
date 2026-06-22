from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import facebook_business.exceptions
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign

from dotenv import load_dotenv
from workflow_state import set_state_value
try:
    from ..facebook_auth import get_required_env, initialize_business_sdk
except ImportError:
    import sys

    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import get_required_env, initialize_business_sdk

load_dotenv()

class AdCampaignStarter(BaseTool):
    """
    Tool for starting ad campaigns on Facebook.
    """

    campaign_name: str = Field(..., description='Name of the ad campaign.')
    budget: int = Field(..., description='Daily budget for the ad campaign in cents.')
    activate_immediately: bool = Field(
        default=False,
        description="Set true only when the client explicitly approved immediate go-live. Default keeps campaign paused.",
    )

    def run(self):
        initialize_business_sdk()
        ad_account_id = get_required_env("FACEBOOK_AD_ACCOUNT_ID")
        try:
            ad_account = AdAccount(ad_account_id)
            campaign_status = (
                Campaign.Status.active
                if self.activate_immediately
                else Campaign.Status.paused
            )
            params = {
                'name': self.campaign_name,
                'objective': "OUTCOME_LEADS",
                'status': campaign_status,
                'daily_budget': self.budget,
                'special_ad_categories': [],

            }
            campaign = ad_account.create_campaign(params=params)
            self._shared_state.set('campaign_id', campaign["id"])
            set_state_value("campaign_id", campaign["id"])
            return (
                f'Ad campaign {self.campaign_name} has been successfully started '
                f'with ID {campaign["id"]} in status {campaign_status}.'
            )
        except facebook_business.exceptions.FacebookRequestError as e:
            return f'Error starting ad campaign: {e}'

if __name__ == "__main__":
    tool = AdCampaignStarter(campaign_name="Test Campaign", budget=1000)
    print(tool.run())

