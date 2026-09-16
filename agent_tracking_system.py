"""
Agent & Framework Tracking System
Tracks agent usage, performance, and campaign outcomes for both agency and client visibility.
Provides analytics for optimization and client reporting.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from governed_memory import GovernedMemory, MemoryScope
from safe_audit_log import write_audit_event


class AgentType(Enum):
    """Types of agents in the system"""
    CEO = "ceo"
    RESEARCH = "research"
    AD_COPY = "ad_copy"
    IMAGE_CREATOR = "image_creator"
    FACEBOOK_POLICY = "facebook_policy"
    CAMPAIGN_OPS = "campaign_ops"
    CLIENT_APPROVAL = "client_approval"
    FACEBOOK_MANAGER = "facebook_manager"
    SEARCH_VISIBILITY = "search_visibility"


class CampaignType(Enum):
    """Types of campaigns supported"""
    AWARENESS = "awareness"  # Brand awareness
    TRAFFIC = "traffic"  # Drive website traffic
    ENGAGEMENT = "engagement"  # Social engagement
    LEADS = "leads"  # Lead generation
    CONVERSIONS = "conversions"  # Sales/conversions
    RETARGETING = "retargeting"  # Retargeting existing audience
    SEASONAL = "seasonal"  # Holiday/seasonal campaigns
    PRODUCT_LAUNCH = "product_launch"  # New product launches


class AgentMetric(Enum):
    """Metrics tracked per agent"""
    EXECUTION_TIME = "execution_time_ms"
    SUCCESS_RATE = "success_rate"
    ERROR_COUNT = "error_count"
    OUTPUT_QUALITY = "output_quality"  # 0-1 score
    API_CALLS = "api_calls"
    API_COST = "api_cost_usd"
    APPROVAL_RATE = "approval_rate"  # For client-facing outputs
    REVISIONS_NEEDED = "revisions_needed"


_TRACKING_DIR = Path(__file__).resolve().parent / ".agent_tracking"
_TRACKING_DIR.mkdir(exist_ok=True)


class AgentTracker:
    """
    Tracks agent performance, framework usage, and campaign outcomes.
    Provides visibility for both agency (optimization) and clients (reporting).
    """
    
    def __init__(self):
        self._campaign_file = _TRACKING_DIR / "campaigns.json"
        self._agent_metrics_file = _TRACKING_DIR / "agent_metrics.json"
        self._framework_usage_file = _TRACKING_DIR / "framework_usage.json"
        
        self._campaigns: dict[str, dict[str, Any]] = {}
        self._agent_metrics: dict[str, dict[str, Any]] = {}
        self._framework_usage: dict[str, dict[str, Any]] = {}
        
        self._load_state()
        self.memory = GovernedMemory()
    
    def _load_state(self) -> None:
        """Load tracking data from disk"""
        if self._campaign_file.exists():
            try:
                self._campaigns = json.loads(self._campaign_file.read_text(encoding="utf-8"))
            except Exception:
                self._campaigns = {}
        
        if self._agent_metrics_file.exists():
            try:
                self._agent_metrics = json.loads(self._agent_metrics_file.read_text(encoding="utf-8"))
            except Exception:
                self._agent_metrics = {}
        
        if self._framework_usage_file.exists():
            try:
                self._framework_usage = json.loads(self._framework_usage_file.read_text(encoding="utf-8"))
            except Exception:
                self._framework_usage = {}
    
    def _save_state(self) -> None:
        """Save tracking data to disk"""
        self._campaign_file.write_text(
            json.dumps(self._campaigns, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
        self._agent_metrics_file.write_text(
            json.dumps(self._agent_metrics, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
        self._framework_usage_file.write_text(
            json.dumps(self._framework_usage, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
    
    def start_campaign(
        self,
        campaign_id: str,
        campaign_type: CampaignType,
        client_id: str,
        client_name: str,
        budget: float,
        objectives: list[str],
    ) -> str:
        """Start tracking a new campaign"""
        self._campaigns[campaign_id] = {
            "campaign_id": campaign_id,
            "campaign_type": campaign_type.value,
            "client_id": client_id,
            "client_name": client_name,
            "budget": budget,
            "objectives": objectives,
            "status": "active",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "agents_used": [],
            "framework_versions": {},
            "performance_metrics": {},
            "client_satisfaction": None,
        }
        
        # Store in governed memory for agent access
        self.memory.set(
            f"campaign_{campaign_id}_metadata",
            self._campaigns[campaign_id],
            MemoryScope.WORKFLOW,
            workflow_id=campaign_id,
            created_by="tracking_system",
            source="campaign_tracking",
        )
        
        self._save_state()
        
        write_audit_event(
            event_type="campaign_started",
            actor="tracking_system",
            outcome="success",
            details={
                "campaign_id": campaign_id,
                "campaign_type": campaign_type.value,
                "client_id": client_id,
            },
        )
        
        return campaign_id
    
    def track_agent_execution(
        self,
        campaign_id: str,
        agent_type: AgentType,
        execution_time_ms: float,
        success: bool,
        output_quality: Optional[float] = None,
        api_calls: int = 0,
        api_cost: float = 0.0,
        error_message: Optional[str] = None,
    ) -> None:
        """Track a single agent execution"""
        # Update campaign agent usage
        if campaign_id in self._campaigns:
            if agent_type.value not in self._campaigns[campaign_id]["agents_used"]:
                self._campaigns[campaign_id]["agents_used"].append(agent_type.value)
        
        # Update agent metrics
        agent_key = f"{campaign_id}_{agent_type.value}"
        if agent_key not in self._agent_metrics:
            self._agent_metrics[agent_key] = {
                "campaign_id": campaign_id,
                "agent_type": agent_type.value,
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time_ms": 0.0,
                "avg_time_ms": 0.0,
                "total_api_calls": 0,
                "total_api_cost": 0.0,
                "quality_scores": [],
                "avg_quality": 0.0,
                "errors": [],
            }
        
        metrics = self._agent_metrics[agent_key]
        metrics["total_executions"] += 1
        
        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
            if error_message:
                metrics["errors"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": error_message,
                })
        
        metrics["total_time_ms"] += execution_time_ms
        metrics["avg_time_ms"] = metrics["total_time_ms"] / metrics["total_executions"]
        
        metrics["total_api_calls"] += api_calls
        metrics["total_api_cost"] += api_cost
        
        if output_quality is not None:
            metrics["quality_scores"].append(output_quality)
            metrics["avg_quality"] = sum(metrics["quality_scores"]) / len(metrics["quality_scores"])
        
        self._save_state()
        
        write_audit_event(
            event_type="agent_execution_tracked",
            actor=agent_type.value,
            outcome="success" if success else "error",
            details={
                "campaign_id": campaign_id,
                "execution_time_ms": execution_time_ms,
                "api_cost": api_cost,
            },
        )
    
    def track_framework_usage(
        self,
        campaign_id: str,
        framework_name: str,
        version: str,
        usage_type: str,
    ) -> None:
        """Track framework/library usage for debugging and upgrades"""
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id]["framework_versions"][framework_name] = version
        
        usage_key = f"{campaign_id}_{framework_name}"
        if usage_key not in self._framework_usage:
            self._framework_usage[usage_key] = {
                "campaign_id": campaign_id,
                "framework_name": framework_name,
                "version": version,
                "usage_types": [],
                "first_used": datetime.now(timezone.utc).isoformat(),
            }
        
        if usage_type not in self._framework_usage[usage_key]["usage_types"]:
            self._framework_usage[usage_key]["usage_types"].append(usage_type)
        
        self._save_state()
    
    def track_client_approval(
        self,
        campaign_id: str,
        agent_type: AgentType,
        approved: bool,
        revisions_requested: int = 0,
        feedback: Optional[str] = None,
    ) -> None:
        """Track client approval decisions for agent output quality"""
        agent_key = f"{campaign_id}_{agent_type.value}"
        
        if agent_key in self._agent_metrics:
            metrics = self._agent_metrics[agent_key]
            
            if "approvals" not in metrics:
                metrics["approvals"] = 0
                metrics["rejections"] = 0
                metrics["total_revisions"] = 0
                metrics["approval_rate"] = 0.0
            
            if approved:
                metrics["approvals"] += 1
            else:
                metrics["rejections"] += 1
            
            metrics["total_revisions"] += revisions_requested
            total_decisions = metrics["approvals"] + metrics["rejections"]
            metrics["approval_rate"] = metrics["approvals"] / total_decisions
            
            self._save_state()
    
    def complete_campaign(
        self,
        campaign_id: str,
        actual_spend: float,
        performance_metrics: dict[str, Any],
        client_satisfaction: float,
    ) -> None:
        """Mark campaign as complete and record final metrics"""
        if campaign_id in self._campaigns:
            campaign = self._campaigns[campaign_id]
            campaign["status"] = "completed"
            campaign["completed_at"] = datetime.now(timezone.utc).isoformat()
            campaign["actual_spend"] = actual_spend
            campaign["performance_metrics"] = performance_metrics
            campaign["client_satisfaction"] = client_satisfaction
            
            self._save_state()
            
            write_audit_event(
                event_type="campaign_completed",
                actor="tracking_system",
                outcome="success",
                details={
                    "campaign_id": campaign_id,
                    "actual_spend": actual_spend,
                    "client_satisfaction": client_satisfaction,
                },
            )
    
    def get_campaign_report(self, campaign_id: str) -> dict[str, Any]:
        """Generate comprehensive campaign report for client"""
        if campaign_id not in self._campaigns:
            return {"error": "Campaign not found"}
        
        campaign = self._campaigns[campaign_id]
        
        # Aggregate agent metrics
        agent_summary = {}
        for agent_key, metrics in self._agent_metrics.items():
            if metrics["campaign_id"] == campaign_id:
                agent_type = metrics["agent_type"]
                agent_summary[agent_type] = {
                    "executions": metrics["total_executions"],
                    "success_rate": (
                        metrics["successful_executions"] / metrics["total_executions"]
                        if metrics["total_executions"] > 0 else 0
                    ),
                    "avg_quality": metrics.get("avg_quality", 0.0),
                    "approval_rate": metrics.get("approval_rate", 0.0),
                    "api_cost": metrics["total_api_cost"],
                }
        
        return {
            "campaign_id": campaign_id,
            "client_name": campaign["client_name"],
            "campaign_type": campaign["campaign_type"],
            "status": campaign["status"],
            "duration": (
                campaign["completed_at"] if campaign["completed_at"]
                else datetime.now(timezone.utc).isoformat()
            ),
            "budget": campaign["budget"],
            "actual_spend": campaign.get("actual_spend", 0.0),
            "agents_used": campaign["agents_used"],
            "agent_performance": agent_summary,
            "frameworks": campaign["framework_versions"],
            "performance_metrics": campaign.get("performance_metrics", {}),
            "client_satisfaction": campaign.get("client_satisfaction"),
        }
    
    def get_agency_analytics(self) -> dict[str, Any]:
        """Generate agency-wide analytics for internal optimization"""
        total_campaigns = len(self._campaigns)
        completed_campaigns = sum(
            1 for c in self._campaigns.values() if c["status"] == "completed"
        )
        
        total_revenue = sum(
            c.get("actual_spend", 0.0) for c in self._campaigns.values()
        )
        
        avg_satisfaction = (
            sum(
                c.get("client_satisfaction", 0.0)
                for c in self._campaigns.values()
                if c.get("client_satisfaction")
            ) / completed_campaigns
            if completed_campaigns > 0 else 0.0
        )
        
        # Agent performance aggregation
        agent_performance = {}
        for agent_type in AgentType:
            agent_metrics = [
                m for m in self._agent_metrics.values()
                if m["agent_type"] == agent_type.value
            ]
            
            if agent_metrics:
                total_execs = sum(m["total_executions"] for m in agent_metrics)
                total_success = sum(m["successful_executions"] for m in agent_metrics)
                
                agent_performance[agent_type.value] = {
                    "total_executions": total_execs,
                    "success_rate": total_success / total_execs if total_execs > 0 else 0,
                    "avg_quality": (
                        sum(m.get("avg_quality", 0.0) for m in agent_metrics) / len(agent_metrics)
                    ),
                    "total_cost": sum(m["total_api_cost"] for m in agent_metrics),
                }
        
        return {
            "total_campaigns": total_campaigns,
            "completed_campaigns": completed_campaigns,
            "active_campaigns": total_campaigns - completed_campaigns,
            "total_revenue": total_revenue,
            "avg_client_satisfaction": avg_satisfaction,
            "agent_performance": agent_performance,
        }


# Global tracker instance
_tracker = AgentTracker()


def get_tracker() -> AgentTracker:
    """Get global tracker instance"""
    return _tracker


__all__ = [
    "AgentTracker",
    "AgentType",
    "CampaignType",
    "AgentMetric",
    "get_tracker",
]
