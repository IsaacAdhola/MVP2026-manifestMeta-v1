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


class ScrapeCreatorsFacebookAdSearch(BaseTool):
    """
    Searches the Facebook Ad Library by keyword using Scrape Creators.
    """

    query: str = Field(..., description="Keyword, offer, product, or competitor term to search.")
    sort_by: str = Field(
        default="total_impressions",
        description="Sort by total_impressions or relevancy_monthly_grouped.",
    )
    search_type: str = Field(
        default="keyword_unordered",
        description="keyword_unordered or keyword_exact_phrase.",
    )
    ad_type: str = Field(
        default="all",
        description="all or political_and_issue_ads.",
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
    start_date: str | None = Field(
        default=None,
        description="Optional impressions start date in YYYY-MM-DD format.",
    )
    end_date: str | None = Field(
        default=None,
        description="Optional impressions end date in YYYY-MM-DD format.",
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
        return scrape_creators_get(
            "/v1/facebook/adLibrary/search/ads",
            {
                "query": self.query,
                "sort_by": self.sort_by,
                "search_type": self.search_type,
                "ad_type": self.ad_type,
                "country": self.country,
                "status": self.status,
                "media_type": self.media_type,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "cursor": self.cursor,
                "trim": self.trim,
            },
        )


if __name__ == "__main__":
    import json

    tool = ScrapeCreatorsFacebookAdSearch(query="running", country="US", trim=True)
    print(json.dumps(tool.run(), ensure_ascii=True))
