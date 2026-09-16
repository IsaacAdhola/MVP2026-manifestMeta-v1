"""
Request Type Definitions
All incoming request models for the MetaMarkAgency system.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class CampaignTypeEnum(str, Enum):
    """Valid campaign types"""
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEADS = "leads"
    CONVERSIONS = "conversions"
    RETARGETING = "retargeting"
    SEASONAL = "seasonal"
    PRODUCT_LAUNCH = "product_launch"


class CreateCampaignRequest(BaseModel):
    """Request to create a new marketing campaign"""
    client_id: str = Field(..., description="Unique client identifier")
    client_name: str = Field(..., min_length=1, description="Client company name")
    campaign_type: CampaignTypeEnum = Field(..., description="Type of campaign")
    budget: float = Field(..., gt=0, le=1000000, description="Campaign budget in USD")
    objectives: List[str] = Field(..., min_items=1, max_items=5, description="Campaign objectives")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    
    @validator("budget")
    def budget_must_be_reasonable(cls, v):
        if v < 50:
            raise ValueError("Minimum budget is $50")
        return v


class TrackAgentExecutionRequest(BaseModel):
    """Request to track an agent's execution metrics"""
    campaign_id: str = Field(..., description="Campaign identifier")
    agent_type: str = Field(..., description="Type of agent that executed")
    execution_time_ms: float = Field(..., gt=0, description="Execution time in milliseconds")
    success: bool = Field(..., description="Whether execution succeeded")
    output_quality: Optional[float] = Field(None, ge=0, le=1, description="Output quality score (0-1)")
    api_calls: int = Field(default=0, ge=0, description="Number of API calls made")
    api_cost: float = Field(default=0.0, ge=0, description="Cost of API calls in USD")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ClientApprovalRequest(BaseModel):
    """Request to record client approval decision"""
    campaign_id: str = Field(..., description="Campaign identifier")
    agent_type: str = Field(..., description="Agent that produced the output")
    approved: bool = Field(..., description="Whether client approved")
    revisions_requested: int = Field(default=0, ge=0, description="Number of revisions requested")
    feedback: Optional[str] = Field(None, description="Client feedback")


class GetRecommendationsRequest(BaseModel):
    """Request for campaign recommendations"""
    client_id: str = Field(..., description="Client identifier")
    goal: str = Field(..., description="Primary goal (e.g., 'grow_brand_awareness')")
    industry: str = Field(..., description="Industry vertical")
    business_stage: str = Field(..., description="Business maturity stage")
    monthly_budget: float = Field(..., gt=0, description="Monthly marketing budget in USD")
    current_audience_size: int = Field(default=0, ge=0, description="Current followers/customers")
    has_existing_customers: bool = Field(default=False, description="Whether they have customers to retarget")


class CompleteCampaignRequest(BaseModel):
    """Request to mark campaign as complete"""
    campaign_id: str = Field(..., description="Campaign identifier")
    actual_spend: float = Field(..., ge=0, description="Actual amount spent")
    performance_metrics: dict = Field(..., description="Campaign performance data")
    client_satisfaction: float = Field(..., ge=0, le=10, description="Client satisfaction score (0-10)")
