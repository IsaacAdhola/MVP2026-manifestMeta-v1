from agency_swarm.tools import BaseTool
from pydantic import Field


class CompetitorResearchPlanBuilder(BaseTool):
    """
    Builds a structured Meta Ad Library research plan from the client's business details.
    """

    client_business: str = Field(
        ..., description="Description of the client's business, offer, and category."
    )
    target_customer: str = Field(
        ..., description="Description of the client's target customers."
    )
    geography: str = Field(
        default="United States",
        description="Primary market geography to research.",
    )
    known_competitors: list[str] = Field(
        default_factory=list,
        description="Known competitor names, if the client provided any.",
    )

    def run(self):
        base_terms = [
            term.strip()
            for term in self.client_business.replace("/", " ").replace(",", " ").split()
            if len(term.strip()) > 3
        ]
        customer_terms = [
            term.strip()
            for term in self.target_customer.replace("/", " ").replace(",", " ").split()
            if len(term.strip()) > 3
        ]
        unique_terms = []
        for term in base_terms + customer_terms:
            normalized = term.lower()
            if normalized not in unique_terms:
                unique_terms.append(normalized)

        keyword_queries = []
        if self.known_competitors:
            keyword_queries.extend(self.known_competitors)
        keyword_queries.extend(unique_terms[:8])

        return {
            "client_business": self.client_business,
            "target_customer": self.target_customer,
            "geography": self.geography,
            "known_competitors": self.known_competitors,
            "recommended_keyword_queries": keyword_queries,
            "recommended_steps": [
                "Search known competitor names first.",
                "Search category and offer keywords next.",
                "Collect active ads and repeated messages.",
                "Analyze hooks, offers, platforms, and creative themes.",
                "Report factual competitor patterns separately from recommendations.",
            ],
        }


if __name__ == "__main__":
    tool = CompetitorResearchPlanBuilder(
        client_business="local AI automation agency for small businesses",
        target_customer="small business owners who need leads and better marketing",
        known_competitors=["Example Competitor"],
    )
    print(tool.run())
