"""
Response Type Definitions
All outgoing response models for the MetaMarkAgency system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateCampaignResponse(BaseModel):
    """Response after creating a campaign"""
    campaign_id: str = Field(..., description="Unique campaign identifier")
    status: str = Field(..., description="Campaign status")
    message: str = Field(..., description="Human-readable status message")
    estimated_completion_date: Optional[str] = Field(None, description="ISO 8601 date string")
    agents_assigned: List[str] = Field(default_factory=list, description="Agents assigned to campaign")


class TrackAgentExecutionResponse(BaseModel):
    """Response after tracking agent execution"""
    success: bool = Field(..., description="Whether tracking succeeded")
    message: str = Field(..., description="Status message")
    metrics_updated: bool = Field(..., description="Whether metrics were updated")


class CampaignReportResponse(BaseModel):
    """Comprehensive campaign report"""
    campaign_id: str
    client_name: str
    campaign_type: str
    status: str
    duration: str
    budget: float
    actual_spend: float
    agents_used: List[str]
    agent_performance: Dict[str, Any]
    frameworks: Dict[str, str]
    performance_metrics: Dict[str, Any]
    client_satisfaction: Optional[float]


class RecommendationResponse(BaseModel):
    """Single campaign recommendation"""
    campaign_type: str = Field(..., description="Recommended campaign type")
    priority: int = Field(..., description="Priority (1 = highest)")
    reasoning: str = Field(..., description="Why this campaign is recommended")
    budget_recommendation: Dict[str, float] = Field(..., description="Min/max budget")
    expected_outcomes: List[str] = Field(..., description="Expected results")
    timeline: str = Field(..., description="Expected timeline")
    best_practices: List[str] = Field(..., description="Best practices for this campaign")


class GetRecommendationsResponse(BaseModel):
    """Response with campaign recommendations"""
    client_id: str
    recommendations: List[RecommendationResponse]
    questionnaire_completed: bool
    generated_at: str  # ISO 8601 timestamp


class AgencyAnalyticsResponse(BaseModel):
    """Agency-wide analytics"""
    total_campaigns: int
    completed_campaigns: int
    active_campaigns: int
    total_revenue: float
    avg_client_satisfaction: float
    agent_performance: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
