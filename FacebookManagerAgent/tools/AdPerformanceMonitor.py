import json
import os
import sys

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List
from facebook_business.adobjects.ad import Ad
from facebook_business.exceptions import FacebookRequestError

from dotenv import load_dotenv

try:
    from ..facebook_auth import initialize_business_sdk
except ImportError:
    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import initialize_business_sdk

load_dotenv()


class AdPerformanceMonitor(BaseTool):
    """
    Monitors ad performance on Facebook and returns metrics such as impressions,
    clicks, and spend for the specified ad ID. Returns a JSON string with the
    insights data or an error message.
    """

    ad_id: str = Field(
        ..., description="The ID of the ad to monitor."
    )
    fields: List[str] = Field(
        default=["impressions", "clicks", "spend"],
        description="The insight fields to retrieve from the Facebook ad.",
    )

    def run(self):
        try:
            initialize_business_sdk()
            ad = Ad(self.ad_id)
            params = {"date_preset": "maximum"}
            insights = ad.get_insights(fields=self.fields, params=params)
            records = [dict(row) for row in insights] if insights else []
            return json.dumps({"ad_id": self.ad_id, "insights": records}, ensure_ascii=False)
        except FacebookRequestError as e:
            return (
                f"Error accessing ad performance metrics: {e.api_error_message()} "
                f"(code={e.api_error_code()}, subcode={e.api_error_subcode()})"
            )


if __name__ == "__main__":
    tool = AdPerformanceMonitor(ad_id="23853583733130117")
    print(tool.run())