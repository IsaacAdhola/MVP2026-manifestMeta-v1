import json
import re
from collections import Counter
from typing import Any

from agency_swarm.tools import BaseTool
from pydantic import Field


class AdLibraryPatternAnalyzer(BaseTool):
    """
    Analyzes Meta Ad Library search results for competitor ad patterns and themes.
    """

    ad_library_results_json: str = Field(
        ..., description="JSON string returned by a Meta Ad Library search tool."
    )
    client_business_context: str = Field(
        default="",
        description="Optional client business context to shape opportunity notes.",
    )

    def _flatten_text(self, values: Any) -> list[str]:
        if not values:
            return []
        if isinstance(values, list):
            return [str(value) for value in values if value]
        return [str(values)]

    def run(self):
        try:
            payload = json.loads(self.ad_library_results_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON input: {exc}") from exc

        ads = []
        if isinstance(payload, dict):
            ads = (
                payload.get("data")
                or payload.get("searchResults")
                or payload.get("results")
                or []
            )
        page_names = Counter()
        platforms = Counter()
        phrases = Counter()
        examples = []

        for ad in ads:
            snapshot = ad.get("snapshot") or {}
            page_name = ad.get("page_name") or ad.get("pageName") or snapshot.get("page_name")
            if page_name:
                page_names[page_name] += 1

            for platform in (
                ad.get("publisher_platforms")
                or ad.get("publisher_platform")
                or ad.get("publisherPlatform")
                or []
            ):
                platforms[str(platform)] += 1

            text_blocks = []
            text_blocks.extend(self._flatten_text(ad.get("ad_creative_bodies")))
            text_blocks.extend(self._flatten_text(ad.get("ad_creative_link_titles")))
            text_blocks.extend(self._flatten_text(ad.get("ad_creative_link_descriptions")))
            body = snapshot.get("body")
            if isinstance(body, dict):
                text_blocks.extend(self._flatten_text(body.get("text")))
            else:
                text_blocks.extend(self._flatten_text(body))
            text_blocks.extend(self._flatten_text(snapshot.get("title")))
            text_blocks.extend(self._flatten_text(snapshot.get("cta_text")))
            for card in snapshot.get("cards", []) or []:
                if isinstance(card, dict):
                    text_blocks.extend(self._flatten_text(card.get("body")))
                    text_blocks.extend(self._flatten_text(card.get("title")))

            for block in text_blocks:
                normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", block).lower()
                words = [word for word in normalized.split() if len(word) > 3]
                for word in words:
                    phrases[word] += 1

            if len(examples) < 5:
                examples.append(
                    {
                        "page_name": page_name,
                        "ad_snapshot_url": ad.get("ad_snapshot_url") or ad.get("url"),
                        "sample_body": self._flatten_text(ad.get("ad_creative_bodies"))[:1],
                        "sample_title": self._flatten_text(ad.get("ad_creative_link_titles"))[:1],
                        "ad_archive_id": ad.get("ad_archive_id") or ad.get("adArchiveID"),
                        "display_format": snapshot.get("display_format"),
                        "cta_text": snapshot.get("cta_text"),
                    }
                )

        return {
            "ads_analyzed": len(ads),
            "top_pages": page_names.most_common(10),
            "top_platforms": platforms.most_common(10),
            "repeated_words": phrases.most_common(25),
            "examples": examples,
            "client_business_context": self.client_business_context,
            "notes": [
                "Use examples as factual evidence from retrieved ads.",
                "Treat repeated words as signals, not performance proof.",
                "Review ad_snapshot_url links manually for visual creative details.",
            ],
        }


if __name__ == "__main__":
    sample = {
        "data": [
            {
                "page_name": "Example Brand",
                "publisher_platforms": ["facebook", "instagram"],
                "ad_creative_bodies": ["Save time with simple automation."],
                "ad_creative_link_titles": ["Book a demo today"],
                "ad_snapshot_url": "https://example.com",
            }
        ]
    }
    tool = AdLibraryPatternAnalyzer(ad_library_results_json=json.dumps(sample))
    print(tool.run())
