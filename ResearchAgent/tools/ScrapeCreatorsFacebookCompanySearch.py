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


class ScrapeCreatorsFacebookCompanySearch(BaseTool):
    """
    Searches Facebook Ad Library companies by name and returns page IDs for competitor ad lookups.
    """

    query: str = Field(..., description="Company or competitor name to search for.")

    def run(self):
        return scrape_creators_get(
            "/v1/facebook/adLibrary/search/companies",
            {"query": self.query},
        )


if __name__ == "__main__":
    import json

    tool = ScrapeCreatorsFacebookCompanySearch(query="nike")
    print(json.dumps(tool.run(), ensure_ascii=True))
