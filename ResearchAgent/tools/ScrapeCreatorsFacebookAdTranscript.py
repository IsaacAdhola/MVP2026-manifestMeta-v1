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


class ScrapeCreatorsFacebookAdTranscript(BaseTool):
    """
    Gets a transcript for a Facebook Ad Library video ad by ad ID or URL.
    """

    id: str | None = Field(
        default=None,
        description="Facebook Ad Library video ad ID.",
    )
    url: str | None = Field(
        default=None,
        description="Facebook Ad Library URL for a video ad.",
    )

    def run(self):
        if not self.id and not self.url:
            raise ValueError("Either id or url is required.")

        return scrape_creators_get(
            "/v1/facebook/adLibrary/ad/transcript",
            {
                "id": self.id,
                "url": self.url,
            },
        )


if __name__ == "__main__":
    import json

    tool = ScrapeCreatorsFacebookAdTranscript(id="1020359190509080")
    print(json.dumps(tool.run(), ensure_ascii=True))
