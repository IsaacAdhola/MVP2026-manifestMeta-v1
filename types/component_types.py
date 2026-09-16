"""
Component Type Definitions
Internal component models for the MetaMarkAgency system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    COMPLETED = "completed"
    PAUSED = "paused"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AgentComponent(BaseModel):
    """Represents an agent in the system"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent (ceo, research, etc.)")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status")
    last_execution_time_ms: float = Field(default=0.0, description="Last execution time")
    total_executions: int = Field(default=0, description="Total executions")
    success_rate: float = Field(default=0.0, ge=0, le=1, description="Success rate (0-1)")
    avg_quality: float = Field(default=0.0, ge=0, le=1, description="Average output quality")
    total_cost: float = Field(default=0.0, description="Total API cost in USD")


class CampaignComponent(BaseModel):
    """Represents a campaign in the system"""
    campaign_id: str
    client_id: str
    client_name: str
    campaign_type: str
    status: CampaignStatus
    budget: float
    actual_spend: float = Field(default=0.0)
    agents_used: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None


class MemoryRecord(BaseModel):
    """Represents a memory record in governed memory"""
    record_id: str
    key: str
    value: Any
    scope: str  # "global", "workflow", "agent_private"
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    created_by: str
    source: str
    confidence: float = Field(ge=0, le=1)
    created_at: str  # ISO 8601
    supersedes: Optional[str] = None
    valid_until: Optional[str] = None


class BudgetTracker(BaseModel):
    """Tracks budget for a campaign"""
    campaign_id: str
    budget: float
    spent: float = Field(default=0.0)
    remaining: float
    pct_used: float = Field(ge=0, le=100)
    status: str  # "OK", "WARNING", "CRITICAL"
    alerts_sent: List[str] = Field(default_factory=list)


class APIVersionInfo(BaseModel):
    """Information about an API version"""
    package: str
    current_version: str
    new_version: str
    status: str  # "detected", "testing", "approved", "deployed", "rejected"
    detected_at: str
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
