# Integration Guide: New Enterprise Features

## Overview

We've integrated three major enterprise-grade systems into MetaMarkAgency:

1. **Governed Shared Memory** - 3-tier memory with access control
2. **Rate Limiting & Cost Control** - Budget caps and API throttling
3. **API Version Monitoring** - Safe upgrade testing

All changes are **100% backward compatible**. Existing code continues to work without modification.

---

## 1. Governed Shared Memory

### Quick Start (Backward Compatible)

Your existing code still works:

```python
from workflow_state import set_state_value, get_state_value

set_state_value("campaign_name", "Summer Sale")
name = get_state_value("campaign_name")
```

### New Features - Three-Tier Scoping

```python
from governed_memory import GovernedMemory, MemoryScope

memory = GovernedMemory()

# GLOBAL scope - readable by all agents
memory.set("company_name", "MetaMarkAgency", MemoryScope.GLOBAL)

# WORKFLOW scope - campaign-level (default)
memory.set("target_audience", "25-34 professionals", 
           MemoryScope.WORKFLOW, workflow_id="summer_sale_2026")

# AGENT_PRIVATE scope - only this agent
memory.set("draft_count", 5, MemoryScope.AGENT_PRIVATE,
           workflow_id="summer_sale_2026", agent_id="copywriter")
```

### Provenance Tracking

Track who created data, when, and with what confidence:

```python
memory.set(
    "competitor_insights",
    "Nike focusing on Gen Z athletes",
    MemoryScope.WORKFLOW,
    workflow_id="campaign_123",
    created_by="ResearchAgent",
    source="Meta Ad Library API",
    confidence=0.95
)

# Retrieve with full metadata
provenance = memory.get_with_provenance("competitor_insights", 
                                        MemoryScope.WORKFLOW, 
                                        workflow_id="campaign_123")
print(provenance["created_by"])  # "ResearchAgent"
print(provenance["source"])       # "Meta Ad Library API"
print(provenance["confidence"])   # 0.95
```

### Temporal Supersession

Newer facts automatically invalidate older ones:

```python
# Initial fact
memory.set("meeting_time", "2 PM", MemoryScope.WORKFLOW, workflow_id="test")

# Update (supersede)
memory.set("meeting_time", "3 PM", MemoryScope.WORKFLOW, 
           workflow_id="test", supersedes_key="meeting_time")

# Only returns "3 PM" (old value invalidated)
result = memory.get("meeting_time", MemoryScope.WORKFLOW, workflow_id="test")
```

### GDPR Compliance

Automatically delete campaign data after completion:

```python
# When campaign completes
memory.cleanup_workflow("summer_sale_2026")
# All workflow and agent-private data for this campaign is deleted
```

---

## 2. Rate Limiting & Cost Control

### Basic Usage - Record API Calls

```python
from rate_limiter import record_api_request, APIProvider

# Record a request
record_api_request(
    APIProvider.OPENAI,
    "gpt4_completion",
    campaign_id="summer_sale",
    estimated_cost=0.01
)
```

### Set Campaign Budgets

```python
from rate_limiter import set_campaign_budget, get_rate_limiter

# Set $500 budget with 75% alert threshold
set_campaign_budget("summer_sale", 500.0)

# Check status
limiter = get_rate_limiter()
status = limiter.get_campaign_budget_status("summer_sale")
print(f"Spent: ${status['spent']:.2f} / ${status['budget']:.2f}")
print(f"Status: {status['status']}")  # OK, WARNING, or CRITICAL
```

### Integration in Tools

Example: `ImageGenerator.py` with rate limiting

```python
from rate_limiter import (
    get_rate_limiter, 
    APIProvider, 
    RateLimitError, 
    BudgetExceededError
)

def run(self):
    limiter = get_rate_limiter()
    
    # Check rate limit before calling API
    try:
        limiter.wait_if_needed(APIProvider.OPENAI, max_wait_seconds=60)
    except RateLimitError as e:
        return f"Rate limit exceeded: {e}"
    
    # Make API call
    try:
        image = openai.images.generate(...)
    except Exception as e:
        return f"Error: {e}"
    
    # Record the request for tracking
    try:
        limiter.record_request(
            APIProvider.OPENAI,
            "dalle3_image",
            campaign_id=self.campaign_id,
            estimated_cost=0.06  # DALL-E 3 cost
        )
    except BudgetExceededError as e:
        return f"Budget exceeded: {e}"
    
    return image.url
```

### Budget Alerts

Alerts are automatically logged to audit trail when:
- **75%** of budget spent (WARNING)
- **90%** of budget spent (CRITICAL)
- **100%** of budget spent (BLOCKED - raises BudgetExceededError)

---

## 3. API Version Monitoring

### Check for Updates

```python
from api_version_monitor import get_version_monitor

monitor = get_version_monitor()

# Check for package updates
updates = monitor.check_for_updates()
for package, info in updates.items():
    print(f"{package}: {info['current']} -> {info['latest']}")
```

### Detect and Test Upgrades

```python
# Detect new version
upgrade_id = monitor.detect_upgrade("openai", "2.44.0", "3.13.0")

# Run tests
monitor.record_test_result(upgrade_id, "unit_tests", True, {"tests": 40})
monitor.record_test_result(upgrade_id, "integration_tests", True, {"tests": 15})

# Check if should auto-upgrade
if monitor.should_auto_upgrade(upgrade_id):
    print("✅ Safe to auto-upgrade")
else:
    print("⚠️ Manual review required")

# Manually approve
monitor.approve_upgrade(upgrade_id, approved_by="CTO")
```

### Get Pending Upgrades

```python
pending = monitor.get_pending_upgrades()
for upgrade in pending:
    print(f"Package: {upgrade['package']}")
    print(f"Version: {upgrade['current_version']} -> {upgrade['new_version']}")
    print(f"Status: {upgrade['status']}")
    print(f"Tests: {len(upgrade['test_results'])} completed")
```

---

## 4. Security Improvements

All new systems integrate with existing security infrastructure:

- **Sanitization**: All memory values are sanitized via `safe_audit_log.py`
- **Audit Logging**: All operations logged to audit trail
- **Access Control**: Memory scopes prevent unauthorized data access
- **GDPR Compliance**: Automatic data deletion via `cleanup_workflow()`

---

## 5. Migration Path

### Phase 1: No Changes Required ✅
Your existing code continues to work. All new systems are opt-in.

### Phase 2: Add Rate Limiting (Recommended)
1. Add `record_api_request()` calls to all tools that call external APIs
2. Set campaign budgets when creating campaigns
3. Monitor audit logs for budget alerts

### Phase 3: Upgrade to Governed Memory (Optional)
1. Identify agents that need private memory
2. Switch from `set_state_value()` to `memory.set()` with appropriate scopes
3. Add provenance tracking for critical data
4. Implement `cleanup_workflow()` in campaign completion flow

### Phase 4: API Monitoring (Future)
1. Schedule weekly checks for API updates
2. Run automated tests on new versions
3. Review and approve upgrades

---

## 6. Example: Full Integration

```python
from governed_memory import GovernedMemory, MemoryScope
from rate_limiter import get_rate_limiter, APIProvider, record_api_request
from api_version_monitor import get_version_monitor

class ResearchAgent:
    def __init__(self, campaign_id: str):
        self.campaign_id = campaign_id
        self.memory = GovernedMemory()
        self.limiter = get_rate_limiter()
    
    def analyze_competitors(self):
        # Check rate limit
        self.limiter.wait_if_needed(APIProvider.META_AD_LIBRARY)
        
        # Call API
        results = self.call_meta_ad_library()
        
        # Record request
        record_api_request(
            APIProvider.META_AD_LIBRARY,
            "competitor_analysis",
            campaign_id=self.campaign_id,
            estimated_cost=0.0  # Free API
        )
        
        # Store with provenance
        self.memory.set(
            "competitor_insights",
            results,
            MemoryScope.WORKFLOW,
            workflow_id=self.campaign_id,
            created_by="ResearchAgent",
            source="Meta Ad Library API",
            confidence=0.95
        )
        
        return results
    
    def cleanup(self):
        # GDPR compliance - delete all campaign data
        self.memory.cleanup_workflow(self.campaign_id)
```

---

## 7. Testing

Run the comprehensive test suite:

```bash
python3 test_new_systems.py
```

Expected output: **✅ All tests passing**

---

## 8. Key Benefits

✅ **No Breaking Changes** - 100% backward compatible
✅ **Cost Control** - Prevent unexpected API bills
✅ **Security** - 3-tier memory prevents data leakage
✅ **Compliance** - GDPR-compliant data deletion
✅ **Quality** - Safe API upgrade testing
✅ **Auditability** - Full provenance tracking

---

## Questions?

See the comprehensive test file (`test_new_systems.py`) for more examples.
