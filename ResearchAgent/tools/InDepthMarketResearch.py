"""Single-call in-depth market research brief for the Market Intelligence Director."""

from __future__ import annotations

import json
import os
from typing import Any

import openai
from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

from error_logger import log_error
from workflow_state import set_state_value

load_dotenv()

try:
    from .CompetitorResearchPlanBuilder import CompetitorResearchPlanBuilder
    from .AdLibraryPatternAnalyzer import AdLibraryPatternAnalyzer
except ImportError:
    from CompetitorResearchPlanBuilder import CompetitorResearchPlanBuilder
    from AdLibraryPatternAnalyzer import AdLibraryPatternAnalyzer


def _try_live_ads(query: str, country: str) -> dict[str, Any]:
    sources: list[str] = []
    payload: dict[str, Any] | None = None

    scrape_key = (os.getenv("SCRAPE_CREATORS_API_KEY") or "").strip()
    if scrape_key:
        try:
            from ..scrape_creators_api import scrape_creators_get
        except ImportError:
            from scrape_creators_api import scrape_creators_get
        try:
            result = scrape_creators_get(
                "/v1/facebook/adLibrary/search/ads",
                {
                    "query": query,
                    "country": country if len(country) == 2 else "US",
                    "status": "ACTIVE",
                    "trim": True,
                },
            )
            if isinstance(result, dict) and result.get("ok") is not False and not result.get("error"):
                payload = result
                sources.append("scrape_creators_ad_library")
        except Exception as exc:
            log_error(
                "Market Intelligence Director",
                exc,
                location="InDepthMarketResearch._try_live_ads.scrape_creators",
            )

    if payload is None:
        try:
            from ..ad_library_api import graph_get, json_list
        except ImportError:
            from ad_library_api import graph_get, json_list
        try:
            result = graph_get(
                "ads_archive",
                {
                    "search_terms": query,
                    "ad_reached_countries": json_list(["US"]),
                    "ad_type": "ALL",
                    "active_status": "ACTIVE",
                    "limit": 15,
                    "fields": ",".join(
                        [
                            "id",
                            "page_name",
                            "ad_creative_bodies",
                            "ad_creative_link_titles",
                            "publisher_platforms",
                        ]
                    ),
                },
            )
            if isinstance(result, dict) and result.get("ok") is not False and not result.get("error"):
                payload = result
                sources.append("meta_ads_archive")
            elif isinstance(result, dict) and result.get("error"):
                err = result.get("error") if isinstance(result.get("error"), dict) else {}
                log_error(
                    "Market Intelligence Director",
                    f"ads_archive blocked (code={err.get('code')}, subcode={err.get('error_subcode')})",
                    location="InDepthMarketResearch._try_live_ads",
                    context={
                        "code": err.get("code"),
                        "subcode": err.get("error_subcode"),
                        "http_status": result.get("http_status"),
                    },
                )
        except Exception as exc:
            log_error(
                "Market Intelligence Director",
                exc,
                location="InDepthMarketResearch._try_live_ads",
            )

    return {"sources": sources, "payload": payload or {}}


class InDepthMarketResearch(BaseTool):
    """
    Completes in-depth market research in one pass: research plan, live ad-library
    lookup when credentials exist, pattern analysis, and a client-ready strategy brief.
    Always returns a finished brief. Never stall or report a fake delay.
    """

    client_business: str = Field(..., description="Business, offer, and category.")
    campaign_goal: str = Field(..., description="Campaign goal such as awareness or bookings.")
    target_customer: str = Field(
        default="local customers",
        description="Target customer description if known.",
    )
    geography: str = Field(
        default="United States",
        description="City, region, or country to research.",
    )
    campaign_type: str = Field(
        default="organic",
        description="organic or paid.",
    )
    known_competitors: list[str] = Field(
        default_factory=list,
        description="Competitor names if the client provided any.",
    )

    def run(self):
        actor = "Market Intelligence Director"
        try:
            plan = CompetitorResearchPlanBuilder(
                client_business=self.client_business,
                target_customer=self.target_customer,
                geography=self.geography,
                known_competitors=self.known_competitors,
            ).run()

            queries = list(plan.get("recommended_keyword_queries") or [])
            if self.client_business and self.client_business not in queries:
                queries.insert(0, self.client_business)
            live_sources: list[str] = []
            live_ads: dict[str, Any] = {}
            analysis: dict[str, Any] = {}
            country = "US"
            geo = (self.geography or "").upper()
            if len(self.geography.strip()) == 2:
                country = self.geography.strip().upper()

            for query in queries[:3]:
                live = _try_live_ads(str(query), country)
                live_sources.extend(live.get("sources") or [])
                payload = live.get("payload") or {}
                ads = payload.get("data") or payload.get("searchResults") or payload.get("results")
                if ads:
                    live_ads = payload
                    break

            if live_ads:
                analysis = AdLibraryPatternAnalyzer(
                    ad_library_results_json=json.dumps(live_ads),
                    client_business_context=self.client_business,
                ).run()

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            synthesis_prompt = (
                "Write an in-depth market research brief for a premium marketing agency. "
                "Separate FACTS found in live ad data from STRATEGIC recommendations. "
                "If live ads are empty, say so clearly and still deliver a rigorous category, "
                "audience, competitor-set, messaging, and creative brief from the client inputs. "
                "Do not invent specific competitor ad claims, metrics, or quotes. "
                "Do not mention internal tools or APIs.\n\n"
                f"Business: {self.client_business}\n"
                f"Goal: {self.campaign_goal}\n"
                f"Audience: {self.target_customer}\n"
                f"Geography: {self.geography}\n"
                f"Campaign type: {self.campaign_type}\n"
                f"Known competitors: {self.known_competitors}\n"
                f"Research plan: {json.dumps(plan, ensure_ascii=True)}\n"
                f"Live ad sources: {live_sources or ['none']}\n"
                f"Live ad pattern analysis: {json.dumps(analysis, ensure_ascii=True)[:4000]}\n"
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are Manifest AI's Market Intelligence Director.",
                    },
                    {"role": "user", "content": synthesis_prompt},
                ],
                temperature=0.4,
                max_tokens=1400,
            )
            brief = (response.choices[0].message.content or "").strip()
            package = {
                "status": "complete",
                "live_ad_sources": live_sources,
                "ads_analyzed": analysis.get("ads_analyzed", 0) if isinstance(analysis, dict) else 0,
                "research_plan": plan,
                "pattern_analysis": analysis,
                "brief": brief,
                "recommended_copy_angle": (
                    analysis.get("opportunity_notes")
                    if isinstance(analysis, dict)
                    else None
                ),
            }
            set_state_value("market_research_brief", package)
            set_state_value("pending_client_research", True)
            return json.dumps(package, ensure_ascii=False)
        except Exception as exc:
            log_error(actor, exc, location="InDepthMarketResearch.run")
            return json.dumps(
                {
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "next_action": "Retry InDepthMarketResearch with the same brief. Do not tell the client research is delayed.",
                }
            )
