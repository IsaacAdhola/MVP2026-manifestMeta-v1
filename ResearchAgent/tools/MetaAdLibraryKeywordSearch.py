from agency_swarm.tools import BaseTool
from pydantic import Field

try:
    from ..ad_library_api import graph_get, json_list, normalize_list
except ImportError:
    import os
    import sys

    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from ad_library_api import graph_get, json_list, normalize_list


DEFAULT_FIELDS = [
    "id",
    "page_id",
    "page_name",
    "ad_creation_time",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "publisher_platforms",
]


class MetaAdLibraryKeywordSearch(BaseTool):
    """
    Searches Meta Ad Library ads by competitor, category, offer, or market keyword.
    """

    search_terms: str = Field(
        ..., description="Keyword, competitor name, category, or offer to search."
    )
    countries: list[str] = Field(
        default_factory=lambda: ["US"],
        description="Two-letter country codes to search, such as US, CA, GB.",
    )
    ad_type: str = Field(
        default="ALL",
        description="Meta Ad Library ad type. Use ALL unless a narrower type is required.",
    )
    active_status: str = Field(
        default="ACTIVE",
        description="ACTIVE, INACTIVE, or ALL.",
    )
    media_type: str = Field(
        default="ALL",
        description="ALL, IMAGE, VIDEO, or other Meta-supported media filters.",
    )
    limit: int = Field(
        default=25,
        description="Maximum number of ads to return.",
    )

    def run(self):
        countries = normalize_list(self.countries, ["US"])
        safe_limit = max(1, min(self.limit, 100))
        params = {
            "search_terms": self.search_terms,
            "ad_reached_countries": json_list(countries),
            "ad_type": self.ad_type,
            "active_status": self.active_status,
            "media_type": self.media_type,
            "limit": safe_limit,
            "fields": ",".join(DEFAULT_FIELDS),
        }
        try:
            return graph_get("ads_archive", params)
        except ValueError as exc:
            return {
                "ok": False,
                "error": str(exc),
                "next_action": (
                    "Set META_AD_LIBRARY_ACCESS_TOKEN only if direct Meta Ad Library "
                    "fallback access is needed. Use Scrape Creators tools as the primary path."
                ),
            }


if __name__ == "__main__":
    import json

    tool = MetaAdLibraryKeywordSearch(search_terms="coffee", limit=3)
    print(json.dumps(tool.run(), ensure_ascii=True))
