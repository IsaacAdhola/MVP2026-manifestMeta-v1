"""
Database Type Definitions
Data models for persistence layer.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class CampaignRecord:
    """Database record for a campaign"""
    campaign_id: str
    client_id: str
    client_name: str
    campaign_type: str
    budget: float
    status: str
    objectives: List[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    actual_spend: float = 0.0
    agents_used: List[str] = None
    framework_versions: Dict[str, str] = None
    performance_metrics: Dict[str, Any] = None
    client_satisfaction: Optional[float] = None
    
    def __post_init__(self):
        if self.agents_used is None:
            self.agents_used = []
        if self.framework_versions is None:
            self.framework_versions = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}


@dataclass
class AgentMetricsRecord:
    """Database record for agent metrics"""
    campaign_id: str
    agent_type: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    total_api_calls: int = 0
    total_api_cost: float = 0.0
    quality_scores: List[float] = None
    avg_quality: float = 0.0
    errors: List[Dict[str, Any]] = None
    approvals: int = 0
    rejections: int = 0
    total_revisions: int = 0
    approval_rate: float = 0.0
    
    def __post_init__(self):
        if self.quality_scores is None:
            self.quality_scores = []
        if self.errors is None:
            self.errors = []


@dataclass
class FrameworkUsageRecord:
    """Database record for framework usage tracking"""
    campaign_id: str
    framework_name: str
    version: str
    usage_types: List[str]
    first_used: datetime
    
    def __post_init__(self):
        if self.usage_types is None:
            self.usage_types = []


@dataclass
class ClientGuidanceRecord:
    """Database record for client guidance history"""
    client_id: str
    timestamp: datetime
    goal: str
    industry: str
    business_stage: str
    budget: float
    recommendations: List[Dict[str, Any]]
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class CompetitorRecord:
    """Database record for competitor intelligence"""
    competitor_id: str
    name: str
    url: str
    focus: str
    target: str
    pricing_model: str
    estimated_price_range: str
    features: List[Dict[str, Any]]
    pricing_history: List[Dict[str, Any]]
    last_updated: datetime
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.pricing_history is None:
            self.pricing_history = []
