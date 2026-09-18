"""
Example: Integrating new enterprise features into existing agents
This shows how to upgrade ResearchAgent with governed memory and rate limiting
"""

from governed_memory import GovernedMemory, MemoryScope
from rate_limiter import get_rate_limiter, APIProvider, record_api_request, BudgetExceededError
from safe_audit_log import write_audit_event


class EnhancedResearchAgent:
    """
    Enhanced version of ResearchAgent with:
    - Governed memory (3-tier scoping)
    - Rate limiting and cost control
    - Provenance tracking
    """
    
    def __init__(self, campaign_id: str, agent_id: str = "research_agent"):
        self.campaign_id = campaign_id
        self.agent_id = agent_id
        self.memory = GovernedMemory()
        self.limiter = get_rate_limiter()
    
    def research_competitors(self, industry: str, budget_usd: float = 100.0):
        """
        Research competitors with rate limiting and cost tracking.
        """
        # Set campaign budget
        self.limiter.set_campaign_budget(self.campaign_id, budget_usd, alert_threshold_pct=75.0)
        
        # Store campaign info in WORKFLOW scope (visible to all agents in this campaign)
        self.memory.set(
            "research_industry",
            industry,
            MemoryScope.WORKFLOW,
            workflow_id=self.campaign_id,
            created_by=self.agent_id,
            source="user_input",
            confidence=1.0
        )
        
        # Store private work state in AGENT_PRIVATE scope
        self.memory.set(
            "research_status",
            "in_progress",
            MemoryScope.AGENT_PRIVATE,
            workflow_id=self.campaign_id,
            agent_id=self.agent_id,
        )
        
        try:
            # Check rate limit before API call
            self.limiter.wait_if_needed(APIProvider.META_AD_LIBRARY, max_wait_seconds=60)
            
            # Simulate API call
            insights = self._call_meta_ad_library(industry)
            
            # Record the API request
            record_api_request(
                APIProvider.META_AD_LIBRARY,
                "competitor_research",
                campaign_id=self.campaign_id,
                estimated_cost=0.0  # Free API
            )
            
            # Store insights with full provenance
            self.memory.set(
                "competitor_insights",
                insights,
                MemoryScope.WORKFLOW,
                workflow_id=self.campaign_id,
                created_by=self.agent_id,
                source="Meta Ad Library API",
                confidence=0.92
            )
            
            # Update status
            self.memory.set(
                "research_status",
                "completed",
                MemoryScope.AGENT_PRIVATE,
                workflow_id=self.campaign_id,
                agent_id=self.agent_id,
                supersedes_key="research_status"  # Invalidate old status
            )
            
            write_audit_event(
                event_type="research_completed",
                actor=self.agent_id,
                outcome="success",
                details={"campaign_id": self.campaign_id, "insights_count": len(insights)}
            )
            
            return insights
            
        except BudgetExceededError as e:
            write_audit_event(
                event_type="research_blocked",
                actor=self.agent_id,
                outcome="budget_exceeded",
                details={"campaign_id": self.campaign_id, "error": str(e)}
            )
            raise
    
    def _call_meta_ad_library(self, industry: str):
        """Simulate Meta Ad Library API call"""
        return {
            "top_competitors": ["Competitor A", "Competitor B", "Competitor C"],
            "trending_keywords": ["keyword1", "keyword2", "keyword3"],
            "avg_engagement": 2.5,
            "recommended_budget": 1500.0
        }
    
    def get_insights_with_provenance(self):
        """
        Retrieve insights with full metadata for transparency.
        """
        provenance = self.memory.get_with_provenance(
            "competitor_insights",
            MemoryScope.WORKFLOW,
            workflow_id=self.campaign_id
        )
        
        if provenance:
            return {
                "data": provenance["value"],
                "created_by": provenance["created_by"],
                "source": provenance["source"],
                "confidence": provenance["confidence"],
                "created_at": provenance["created_at"]
            }
        return None
    
    def cleanup_campaign(self):
        """
        GDPR-compliant cleanup after campaign completion.
        Deletes all workflow and agent-private data.
        """
        self.memory.cleanup_workflow(self.campaign_id)
        
        write_audit_event(
            event_type="campaign_cleanup",
            actor=self.agent_id,
            outcome="success",
            details={"campaign_id": self.campaign_id}
        )


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("EXAMPLE: Enhanced Research Agent with Enterprise Features")
    print("=" * 70)
    print()
    
    # Create agent
    agent = EnhancedResearchAgent(campaign_id="demo_campaign_2026")
    
    # Research competitors
    print("[1] Researching competitors...")
    insights = agent.research_competitors("sportswear", budget_usd=100.0)
    print(f"✅ Found {len(insights['top_competitors'])} competitors")
    print()
    
    # Get insights with provenance
    print("[2] Retrieving insights with provenance...")
    result = agent.get_insights_with_provenance()
    print(f"✅ Created by: {result['created_by']}")
    print(f"✅ Source: {result['source']}")
    print(f"✅ Confidence: {result['confidence']}")
    print(f"✅ Timestamp: {result['created_at']}")
    print()
    
    # Check budget status
    print("[3] Checking budget status...")
    status = agent.limiter.get_campaign_budget_status("demo_campaign_2026")
    print(f"✅ Budget: ${status['budget']:.2f}")
    print(f"✅ Spent: ${status['spent']:.2f}")
    print(f"✅ Remaining: ${status['remaining']:.2f}")
    print(f"✅ Status: {status['status']}")
    print()
    
    # Cleanup (GDPR)
    print("[4] Cleaning up campaign data (GDPR compliance)...")
    agent.cleanup_campaign()
    print("✅ All campaign data deleted")
    print()
    
    print("=" * 70)
    print("✅ Example completed successfully!")
    print("=" * 70)
