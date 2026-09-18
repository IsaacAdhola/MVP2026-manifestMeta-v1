"""
API Rate Limiting and Cost Control System
Prevents API quota exhaustion and unexpected costs.
"""

from __future__ import annotations

import json
import time
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from safe_audit_log import write_audit_event


class APIProvider(Enum):
    """Supported API providers"""
    OPENAI = "openai"
    FACEBOOK = "facebook"
    SCRAPE_CREATORS = "scrape_creators"
    META_AD_LIBRARY = "meta_ad_library"


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass


class BudgetExceededError(Exception):
    """Raised when budget cap is exceeded"""
    pass


_LIMITER_DIR = Path(__file__).resolve().parent / ".rate_limiter"
_LIMITER_DIR.mkdir(exist_ok=True)


class RateLimiter:
    """
    Rate limiter with exponential backoff and budget tracking.
    Prevents API quota exhaustion and cost overruns.
    """
    
    # Default rate limits (requests per minute)
    DEFAULT_LIMITS = {
        APIProvider.OPENAI: 50,  # Conservative for API tier 1
        APIProvider.FACEBOOK: 200,  # Graph API default
        APIProvider.SCRAPE_CREATORS: 60,  # Typical SaaS limit
        APIProvider.META_AD_LIBRARY: 60,  # Conservative
    }
    
    # Estimated costs per API call (USD)
    ESTIMATED_COSTS = {
        "openai_gpt4": 0.01,  # ~$0.01 per short completion
        "openai_dalle3": 0.06,  # $0.04-0.08 per image
        "facebook_post": 0.0,  # Free
        "facebook_ad": 0.0,  # Free (ad spend separate)
        "scrape_creators": 0.001,  # Typically included in subscription
        "meta_ad_library": 0.0,  # Free
    }
    
    def __init__(self):
        self._state_file = _LIMITER_DIR / "state.json"
        self._budget_file = _LIMITER_DIR / "budgets.json"
        
        # Request timestamps: provider -> deque of timestamps
        self._requests: dict[APIProvider, deque] = {
            provider: deque() for provider in APIProvider
        }
        
        # Budget tracking: campaign_id -> {budget, spent, alerts}
        self._budgets: dict[str, dict[str, Any]] = {}
        
        self._load_state()
    
    def _load_state(self) -> None:
        """Load rate limiter state from disk"""
        if self._budget_file.exists():
            try:
                self._budgets = json.loads(self._budget_file.read_text(encoding="utf-8"))
            except Exception:
                self._budgets = {}
    
    def _save_state(self) -> None:
        """Save budget state to disk"""
        self._budget_file.write_text(
            json.dumps(self._budgets, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
    
    def _cleanup_old_requests(self, provider: APIProvider, window_seconds: int = 60) -> None:
        """Remove requests older than the time window"""
        cutoff = time.time() - window_seconds
        while self._requests[provider] and self._requests[provider][0] < cutoff:
            self._requests[provider].popleft()
    
    def check_rate_limit(
        self,
        provider: APIProvider,
        max_per_minute: Optional[int] = None,
    ) -> bool:
        """
        Check if request would exceed rate limit.
        Returns True if allowed, False if would exceed limit.
        """
        limit = max_per_minute or self.DEFAULT_LIMITS.get(provider, 60)
        self._cleanup_old_requests(provider)
        return len(self._requests[provider]) < limit
    
    def wait_if_needed(
        self,
        provider: APIProvider,
        max_per_minute: Optional[int] = None,
        max_wait_seconds: int = 60,
    ) -> float:
        """
        Wait if necessary to respect rate limits.
        Returns the time waited in seconds.
        Raises RateLimitError if max_wait_seconds exceeded.
        """
        limit = max_per_minute or self.DEFAULT_LIMITS.get(provider, 60)
        self._cleanup_old_requests(provider)
        
        if len(self._requests[provider]) < limit:
            return 0.0
        
        # Calculate how long to wait
        oldest_request = self._requests[provider][0]
        wait_until = oldest_request + 60  # Wait until oldest request expires
        wait_time = wait_until - time.time()
        
        if wait_time > max_wait_seconds:
            write_audit_event(
                event_type="rate_limit_exceeded",
                actor="rate_limiter",
                outcome="blocked",
                details={
                    "provider": provider.value,
                    "current_requests": len(self._requests[provider]),
                    "limit": limit,
                    "wait_time_needed": wait_time,
                },
            )
            raise RateLimitError(
                f"{provider.value} rate limit exceeded. "
                f"Need to wait {wait_time:.1f}s (max: {max_wait_seconds}s)"
            )
        
        if wait_time > 0:
            time.sleep(wait_time)
            return wait_time
        
        return 0.0
    
    def record_request(
        self,
        provider: APIProvider,
        operation: str,
        campaign_id: Optional[str] = None,
        estimated_cost: Optional[float] = None,
    ) -> None:
        """
        Record an API request for rate limiting and cost tracking.
        """
        # Record timestamp for rate limiting
        self._requests[provider].append(time.time())
        
        # Track cost if campaign_id provided
        if campaign_id and estimated_cost:
            self._track_cost(campaign_id, operation, estimated_cost)
        
        # Audit log
        write_audit_event(
            event_type="api_request",
            actor=provider.value,
            outcome="recorded",
            details={
                "operation": operation,
                "campaign_id": campaign_id,
                "estimated_cost": estimated_cost,
            },
        )
    
    def set_campaign_budget(
        self,
        campaign_id: str,
        budget_usd: float,
        alert_threshold_pct: float = 75.0,
    ) -> None:
        """Set budget cap for a campaign"""
        self._budgets[campaign_id] = {
            "budget": budget_usd,
            "spent": 0.0,
            "alert_threshold_pct": alert_threshold_pct,
            "alerts_sent": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_state()
    
    def _track_cost(self, campaign_id: str, operation: str, cost: float) -> None:
        """Track cost against campaign budget"""
        if campaign_id not in self._budgets:
            # No budget set, just log
            return
        
        budget_info = self._budgets[campaign_id]
        budget_info["spent"] += cost
        
        pct_used = (budget_info["spent"] / budget_info["budget"]) * 100
        
        # Check for alert thresholds (check 75% first, then 90%)
        alert_threshold = budget_info["alert_threshold_pct"]
        if pct_used >= alert_threshold and f"{int(alert_threshold)}%" not in budget_info["alerts_sent"]:
            budget_info["alerts_sent"].append(f"{int(alert_threshold)}%")
            write_audit_event(
                event_type="budget_alert",
                actor="rate_limiter",
                outcome="warning",
                details={
                    "campaign_id": campaign_id,
                    "pct_used": pct_used,
                    "spent": budget_info["spent"],
                    "budget": budget_info["budget"],
                    "level": "WARNING",
                },
            )
        
        if pct_used >= 90 and "90%" not in budget_info["alerts_sent"]:
            budget_info["alerts_sent"].append("90%")
            write_audit_event(
                event_type="budget_alert",
                actor="rate_limiter",
                outcome="critical",
                details={
                    "campaign_id": campaign_id,
                    "pct_used": pct_used,
                    "spent": budget_info["spent"],
                    "budget": budget_info["budget"],
                    "level": "CRITICAL",
                },
            )
        
        # Hard stop at 100%
        if pct_used >= 100:
            self._save_state()
            raise BudgetExceededError(
                f"Campaign {campaign_id} has exceeded budget. "
                f"Spent: ${budget_info['spent']:.2f}, Budget: ${budget_info['budget']:.2f}"
            )
        
        self._save_state()
    
    def get_campaign_budget_status(self, campaign_id: str) -> dict[str, Any]:
        """Get current budget status for a campaign"""
        if campaign_id not in self._budgets:
            return {"error": "No budget set for this campaign"}
        
        budget_info = self._budgets[campaign_id]
        pct_used = (budget_info["spent"] / budget_info["budget"]) * 100
        remaining = budget_info["budget"] - budget_info["spent"]
        
        return {
            "campaign_id": campaign_id,
            "budget": budget_info["budget"],
            "spent": budget_info["spent"],
            "remaining": remaining,
            "pct_used": pct_used,
            "status": "OK" if pct_used < 75 else "WARNING" if pct_used < 90 else "CRITICAL",
            "alerts_sent": budget_info["alerts_sent"],
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter


# Convenience functions
def check_rate_limit(provider: APIProvider) -> bool:
    """Check if API request is allowed under rate limits"""
    return _rate_limiter.check_rate_limit(provider)


def record_api_request(
    provider: APIProvider,
    operation: str,
    campaign_id: Optional[str] = None,
    estimated_cost: Optional[float] = None,
) -> None:
    """Record an API request"""
    _rate_limiter.record_request(provider, operation, campaign_id, estimated_cost)


def set_campaign_budget(campaign_id: str, budget_usd: float) -> None:
    """Set budget cap for a campaign"""
    _rate_limiter.set_campaign_budget(campaign_id, budget_usd)


__all__ = [
    "RateLimiter",
    "APIProvider",
    "RateLimitError",
    "BudgetExceededError",
    "get_rate_limiter",
    "check_rate_limit",
    "record_api_request",
    "set_campaign_budget",
]
