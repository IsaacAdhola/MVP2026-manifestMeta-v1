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


class ScrapeCreatorsFacebookAdDetails(BaseTool):
    """
    Gets detailed information for a single Facebook Ad Library ad by ad ID or URL.
    """

    id: str | None = Field(
        default=None,
        description="Facebook Ad Library ad ID.",
    )
    url: str | None = Field(
        default=None,
        description="Facebook Ad Library URL, such as https://www.facebook.com/ads/library?id=...",
    )
    trim: bool = Field(
        default=True,
        description="Whether to request a trimmed response.",
    )

    def run(self):
        if not self.id and not self.url:
            raise ValueError("Either id or url is required.")

        return scrape_creators_get(
            "/v1/facebook/adLibrary/ad",
            {
                "id": self.id,
                "url": self.url,
                "trim": self.trim,
            },
        )


if __name__ == "__main__":
    import json

    tool = ScrapeCreatorsFacebookAdDetails(id="702369045530963", trim=True)
    print(json.dumps(tool.run(), ensure_ascii=True))
