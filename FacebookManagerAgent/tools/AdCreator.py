import os
from pathlib import Path

from agency_swarm.tools import BaseTool
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.exceptions import FacebookRequestError
from pydantic import Field

from dotenv import load_dotenv
from workflow_state import get_state_value, set_state_value
try:
    from ..facebook_auth import get_required_env, initialize_business_sdk
except ImportError:
    import sys

    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import get_required_env, initialize_business_sdk

load_dotenv()

class AdCreator(BaseTool):
    """
    Enables scheduling and posting of ads on Facebook with optimal timing and audience targeting.
    """
    name: str = Field(..., description='Headline of the ad.')
    link: str = Field(
        ..., description="The URL to which the ad will direct the user."
    )

    def _resolve_image_path(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.is_absolute():
            project_root = Path(__file__).resolve().parents[2]
            path = project_root / path
        return str(path.resolve())

    def run(self):
        try:
            initialize_business_sdk()
            ad_account_id = get_required_env("FACEBOOK_AD_ACCOUNT_ID")
            image_path = self._shared_state.get('image_path') or get_state_value("image_path")
            ad_set_id = self._shared_state.get('ad_set_id') or get_state_value("ad_set_id")
            campaign_id = self._shared_state.get('campaign_id') or get_state_value("campaign_id")
            ad_copy = self._shared_state.get('ad_copy') or get_state_value("ad_copy")
            ad_headline = self._shared_state.get('ad_headline') or get_state_value("ad_headline")

            if not image_path:
                raise ValueError('Please tell Image Creator agent to generate an image first.')
            if not ad_set_id:
                raise ValueError('Ad set ID not found. Please use AdSetCreator tool first.')
            if not campaign_id:
                raise ValueError('Campaign ID not found. Please use AdCampaignStarter tool first.')
            if not ad_copy:
                raise ValueError('Please use AdCopyGenerator tool to generate ad copy first.')

            resolved_image_path = self._resolve_image_path(image_path)
            if not os.path.exists(resolved_image_path):
                raise ValueError(f'Image file does not exist: {resolved_image_path}')

            image = AdImage(parent_id=ad_account_id)
            image[AdImage.Field.filename] = resolved_image_path
            image.remote_create()

            creative = AdCreative(parent_id=ad_account_id)
            creative[AdCreative.Field.object_story_spec] = {
                'page_id': get_required_env("FACEBOOK_PAGE_ID"),
                'link_data': {
                    'image_hash': image.get_hash(),
                    "call_to_action": {'type': 'LEARN_MORE'},
                    'link': self.link,
                    "name": ad_headline,
                    "message": ad_copy,
                }
            }
            creative.remote_create()

            ad = Ad(parent_id=ad_account_id)
            ad[Ad.Field.name] = self.name
            ad[Ad.Field.adset_id] = ad_set_id
            ad[Ad.Field.creative] = {"creative_id": creative["id"]}
            ad.remote_create(params={
                'status': Ad.Status.paused,
            })
            set_state_value("ad_id", ad["id"])

            return f"Ad created successfully with ID: {ad['id']}"
        except FacebookRequestError as e:
            return (
                f"Error creating ad: {e.api_error_message()} "
                f"(code={e.api_error_code()}, subcode={e.api_error_subcode()}, "
                f"type={e.api_error_type()})"
            )

if __name__ == "__main__":
    import os
    tool = AdCreator(name="Test Creative 2", link="https://www.example.com")
    # Set required shared_state values with actual test data
    tool._shared_state.set('image_path', os.path.abspath('image.png'))
    tool._shared_state.set('ad_set_id', '6867670805634')  # From AdSetCreator test
    tool._shared_state.set('ad_copy', 'Join the sustainable style revolution without breaking the bank. Look good, feel good!')
    tool._shared_state.set('ad_headline', 'Eco-Friendly Fashion for Less!')
    tool._shared_state.set('campaign_id', '6867670459634')  # From AdCampaignStarter test
    print(tool.run())
