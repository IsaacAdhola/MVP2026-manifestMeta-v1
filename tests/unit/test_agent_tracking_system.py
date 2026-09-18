#!/usr/bin/env python3
"""
Unit Tests for Agent Tracking System
Following TDD: Types → Tests → Architecture → Implementation

Test Coverage:
- Campaign creation and tracking
- Agent execution metrics
- Framework usage tracking
- Client approval tracking
- Campaign completion
- Report generation
"""

import pytest
from agent_tracking_system import (
    AgentTracker,
    AgentType,
    CampaignType,
    get_tracker,
)


class TestAgentTracker:
    """Test suite for AgentTracker core functionality"""
    
    def test_start_campaign_creates_record(self):
        """
        GIVEN a new campaign request
        WHEN start_campaign is called
        THEN a campaign record is created with correct data
        """
        # Arrange
        tracker = AgentTracker()
        
        # Act
        campaign_id = tracker.start_campaign(
            campaign_id="test_campaign_001",
            campaign_type=CampaignType.AWARENESS,
            client_id="client_456",
            client_name="Test Client Inc",
            budget=1000.0,
            objectives=["Increase brand awareness", "Drive traffic"],
        )
        
        # Assert
        assert campaign_id == "test_campaign_001"
        report = tracker.get_campaign_report(campaign_id)
        assert report["client_name"] == "Test Client Inc"
        assert report["budget"] == 1000.0
        assert report["status"] == "active"
        assert report["campaign_type"] == "awareness"
        assert "Increase brand awareness" in report.get("objectives", [])
    
    def test_track_agent_execution_updates_metrics(self):
        """
        GIVEN an active campaign
        WHEN an agent executes successfully
        THEN metrics are recorded accurately
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_campaign_002",
            campaign_type=CampaignType.CONVERSIONS,
            client_id="client_789",
            client_name="E-commerce Co",
            budget=2000.0,
            objectives=["Drive sales"],
        )
        
        # Act
        tracker.track_agent_execution(
            campaign_id="test_campaign_002",
            agent_type=AgentType.RESEARCH,
            execution_time_ms=1500.0,
            success=True,
            output_quality=0.92,
            api_calls=3,
            api_cost=0.05,
        )
        
        # Assert
        report = tracker.get_campaign_report("test_campaign_002")
        assert "research" in report["agents_used"]
        
        agent_perf = report["agent_performance"]["research"]
        assert agent_perf["executions"] == 1
        assert agent_perf["success_rate"] == 1.0
        assert agent_perf["avg_quality"] == 0.92
        assert agent_perf["api_cost"] == 0.05
    
    def test_track_agent_execution_handles_failure(self):
        """
        GIVEN an active campaign
        WHEN an agent execution fails
        THEN failure is recorded with error message
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_campaign_003",
            campaign_type=CampaignType.LEADS,
            client_id="client_999",
            client_name="Lead Gen LLC",
            budget=500.0,
            objectives=["Generate qualified leads"],
        )
        
        # Act
        tracker.track_agent_execution(
            campaign_id="test_campaign_003",
            agent_type=AgentType.AD_COPY,
            execution_time_ms=800.0,
            success=False,
            error_message="API rate limit exceeded",
        )
        
        # Assert
        report = tracker.get_campaign_report("test_campaign_003")
        agent_perf = report["agent_performance"]["ad_copy"]
        assert agent_perf["success_rate"] == 0.0
        assert agent_perf["executions"] == 1
    
    def test_track_multiple_agents_in_campaign(self):
        """
        GIVEN an active campaign
        WHEN multiple agents execute
        THEN all agents are tracked separately
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_campaign_004",
            campaign_type=CampaignType.PRODUCT_LAUNCH,
            client_id="client_111",
            client_name="Product Co",
            budget=5000.0,
            objectives=["Launch new product"],
        )
        
        # Act - Multiple agents execute
        tracker.track_agent_execution(
            campaign_id="test_campaign_004",
            agent_type=AgentType.RESEARCH,
            execution_time_ms=1000.0,
            success=True,
            output_quality=0.85,
        )
        
        tracker.track_agent_execution(
            campaign_id="test_campaign_004",
            agent_type=AgentType.AD_COPY,
            execution_time_ms=1200.0,
            success=True,
            output_quality=0.90,
        )
        
        tracker.track_agent_execution(
            campaign_id="test_campaign_004",
            agent_type=AgentType.IMAGE_CREATOR,
            execution_time_ms=2000.0,
            success=True,
            output_quality=0.95,
        )
        
        # Assert
        report = tracker.get_campaign_report("test_campaign_004")
        assert len(report["agents_used"]) == 3
        assert "research" in report["agents_used"]
        assert "ad_copy" in report["agents_used"]
        assert "image_creator" in report["agents_used"]
        
        # Check individual agent performance
        assert report["agent_performance"]["research"]["avg_quality"] == 0.85
        assert report["agent_performance"]["ad_copy"]["avg_quality"] == 0.90
        assert report["agent_performance"]["image_creator"]["avg_quality"] == 0.95
    
    def test_track_framework_usage(self):
        """
        GIVEN an active campaign
        WHEN frameworks are used
        THEN framework versions are recorded
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_campaign_005",
            campaign_type=CampaignType.TRAFFIC,
            client_id="client_222",
            client_name="Traffic Inc",
            budget=750.0,
            objectives=["Drive website traffic"],
        )
        
        # Act
        tracker.track_framework_usage(
            campaign_id="test_campaign_005",
            framework_name="openai",
            version="2.44.0",
            usage_type="gpt4_completion",
        )
        
        tracker.track_framework_usage(
            campaign_id="test_campaign_005",
            framework_name="facebook-sdk",
            version="15.0.0",
            usage_type="ad_posting",
        )
        
        # Assert
        report = tracker.get_campaign_report("test_campaign_005")
        assert "openai" in report["frameworks"]
        assert report["frameworks"]["openai"] == "2.44.0"
        assert "facebook-sdk" in report["frameworks"]
        assert report["frameworks"]["facebook-sdk"] == "15.0.0"
    
    def test_track_client_approval(self):
        """
        GIVEN an agent output
        WHEN client approves or rejects
        THEN approval rate is tracked
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_campaign_006",
            campaign_type=CampaignType.ENGAGEMENT,
            client_id="client_333",
            client_name="Engagement Co",
            budget=1200.0,
            objectives=["Increase engagement"],
        )
        
        # First execution
        tracker.track_agent_execution(
            campaign_id="test_campaign_006",
            agent_type=AgentType.AD_COPY,
            execution_time_ms=1000.0,
            success=True,
        )
        
        # Act - Client approves
        tracker.track_client_approval(
            campaign_id="test_campaign_006",
            agent_type=AgentType.AD_COPY,
            approved=True,
            revisions_requested=0,
        )
        
        # Second execution
        tracker.track_agent_execution(
            campaign_id="test_campaign_006",
            agent_type=AgentType.AD_COPY,
            execution_time_ms=1000.0,
            success=True,
        )
        
        # Act - Client rejects and requests revisions
        tracker.track_client_approval(
            campaign_id="test_campaign_006",
            agent_type=AgentType.AD_COPY,
            approved=False,
            revisions_requested=2,
        )
        
        # Assert
        report = tracker.get_campaign_report("test_campaign_006")
        agent_perf = report["agent_performance"]["ad_copy"]
        assert agent_perf["approval_rate"] == 0.5  # 1 approved, 1 rejected
    
    def test_complete_campaign(self):
        """
        GIVEN an active campaign
        WHEN campaign is completed
        THEN final metrics are recorded
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_campaign_007",
            campaign_type=CampaignType.SEASONAL,
            client_id="client_444",
            client_name="Seasonal Shop",
            budget=3000.0,
            objectives=["Holiday sales"],
        )
        
        # Act
        tracker.complete_campaign(
            campaign_id="test_campaign_007",
            actual_spend=2800.0,
            performance_metrics={
                "impressions": 50000,
                "clicks": 2500,
                "conversions": 125,
                "ctr": 0.05,
                "cpa": 22.40,
            },
            client_satisfaction=8.5,
        )
        
        # Assert
        report = tracker.get_campaign_report("test_campaign_007")
        assert report["status"] == "completed"
        assert report["actual_spend"] == 2800.0
        assert report["client_satisfaction"] == 8.5
        assert report["performance_metrics"]["conversions"] == 125
    
    def test_get_agency_analytics(self):
        """
        GIVEN multiple campaigns
        WHEN get_agency_analytics is called
        THEN aggregate metrics are returned
        """
        # Arrange
        tracker = AgentTracker()
        
        # Campaign 1
        tracker.start_campaign(
            campaign_id="analytics_001",
            campaign_type=CampaignType.AWARENESS,
            client_id="client_a",
            client_name="Client A",
            budget=1000.0,
            objectives=["Awareness"],
        )
        tracker.complete_campaign(
            campaign_id="analytics_001",
            actual_spend=950.0,
            performance_metrics={},
            client_satisfaction=8.0,
        )
        
        # Campaign 2
        tracker.start_campaign(
            campaign_id="analytics_002",
            campaign_type=CampaignType.CONVERSIONS,
            client_id="client_b",
            client_name="Client B",
            budget=2000.0,
            objectives=["Sales"],
        )
        tracker.complete_campaign(
            campaign_id="analytics_002",
            actual_spend=1900.0,
            performance_metrics={},
            client_satisfaction=9.0,
        )
        
        # Campaign 3 (active)
        tracker.start_campaign(
            campaign_id="analytics_003",
            campaign_type=CampaignType.TRAFFIC,
            client_id="client_c",
            client_name="Client C",
            budget=1500.0,
            objectives=["Traffic"],
        )
        
        # Act
        analytics = tracker.get_agency_analytics()
        
        # Assert
        assert analytics["total_campaigns"] >= 3
        assert analytics["completed_campaigns"] >= 2
        assert analytics["active_campaigns"] >= 1
        assert analytics["total_revenue"] >= 2850.0  # 950 + 1900
        assert 8.0 <= analytics["avg_client_satisfaction"] <= 9.0


def test_get_tracker_singleton():
    """
    GIVEN the module-level get_tracker function
    WHEN called multiple times
    THEN returns same instance
    """
    # Act
    tracker1 = get_tracker()
    tracker2 = get_tracker()
    
    # Assert
    assert tracker1 is tracker2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
