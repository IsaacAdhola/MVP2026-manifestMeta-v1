from agency_swarm.tools import BaseTool
from pydantic import Field

try:
    from ..scrape_creators_api import scrape_creators_get
except ImportError:
    import os
    import sys

    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from scrape_creators_api import scrape_creators_get


class ScrapeCreatorsFacebookCompanyAds(BaseTool):
    """
    Gets Facebook Ad Library ads for a specific company by page ID or company name.
    """

    pageId: str | None = Field(
        default=None,
        description="Facebook Ad Library page ID from company search.",
    )
    companyName: str | None = Field(
        default=None,
        description="Company name to search if pageId is not known.",
    )
    country: str = Field(
        default="ALL",
        description="Two-letter country code, or ALL.",
    )
    status: str = Field(
        default="ACTIVE",
        description="ALL, ACTIVE, or INACTIVE.",
    )
    media_type: str = Field(
        default="ALL",
        description="ALL, IMAGE, VIDEO, MEME, IMAGE_AND_MEME, or NONE.",
    )
    language: str | None = Field(
        default=None,
        description="Optional two-letter language code, such as EN, ES, or FR.",
    )
    sort_by: str = Field(
        default="total_impressions",
        description="Sort by total_impressions or relevancy_monthly_grouped.",
    )
    start_date: str | None = Field(
        default=None,
        description="Optional start date in YYYY-MM-DD format.",
    )
    end_date: str | None = Field(
        default=None,
        description="Optional end date in YYYY-MM-DD format.",
    )
    cursor: str | None = Field(
        default=None,
        description="Optional cursor for pagination.",
    )
    trim: bool = Field(
        default=True,
        description="Whether to request a trimmed response.",
    )

    def run(self):
        if not self.pageId and not self.companyName:
            raise ValueError("Either pageId or companyName is required.")

        return scrape_creators_get(
            "/v1/facebook/adLibrary/company/ads",
            {
                "pageId": self.pageId,
                "companyName": self.companyName,
                "country": self.country,
                "status": self.status,
                "media_type": self.media_type,
                "language": self.language,
                "sort_by": self.sort_by,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "cursor": self.cursor,
                "trim": self.trim,
            },
        )


if __name__ == "__main__":
    import json

    tool = ScrapeCreatorsFacebookCompanyAds(companyName="Nike", country="US", trim=True)
    print(json.dumps(tool.run(), ensure_ascii=True))
