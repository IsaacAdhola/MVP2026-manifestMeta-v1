"""
Type Definitions for MetaMarkAgency

Centralized type definitions for:
- Request types (incoming API/function calls)
- Response types (outgoing API/function returns)  
- Component types (internal system components)
- Database types (persistence layer)

Usage:
    from types.request_types import CreateCampaignRequest
    from types.response_types import CreateCampaignResponse
    from types.component_types import AgentComponent
    from types.database_types import CampaignRecord
"""

# Request Types
from .request_types import (
    CampaignTypeEnum,
    CreateCampaignRequest,
    TrackAgentExecutionRequest,
    ClientApprovalRequest,
    GetRecommendationsRequest,
    CompleteCampaignRequest,
)

# Response Types
from .response_types import (
    CreateCampaignResponse,
    TrackAgentExecutionResponse,
    CampaignReportResponse,
    RecommendationResponse,
    GetRecommendationsResponse,
    AgencyAnalyticsResponse,
    ErrorResponse,
)

# Component Types
from .component_types import (
    AgentStatus,
    CampaignStatus,
    AgentComponent,
    CampaignComponent,
    MemoryRecord,
    BudgetTracker,
    APIVersionInfo,
)

# Database Types
from .database_types import (
    CampaignRecord,
    AgentMetricsRecord,
    FrameworkUsageRecord,
    ClientGuidanceRecord,
    CompetitorRecord,
)

__all__ = [
    # Request Types
    "CampaignTypeEnum",
    "CreateCampaignRequest",
    "TrackAgentExecutionRequest",
    "ClientApprovalRequest",
    "GetRecommendationsRequest",
    "CompleteCampaignRequest",
    
    # Response Types
    "CreateCampaignResponse",
    "TrackAgentExecutionResponse",
    "CampaignReportResponse",
    "RecommendationResponse",
    "GetRecommendationsResponse",
    "AgencyAnalyticsResponse",
    "ErrorResponse",
    
    # Component Types
    "AgentStatus",
    "CampaignStatus",
    "AgentComponent",
    "CampaignComponent",
    "MemoryRecord",
    "BudgetTracker",
    "APIVersionInfo",
    
    # Database Types
    "CampaignRecord",
    "AgentMetricsRecord",
    "FrameworkUsageRecord",
    "ClientGuidanceRecord",
    "CompetitorRecord",
]
