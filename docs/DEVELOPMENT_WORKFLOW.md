# Development Workflow: Types → Tests → Architecture → Implementation

**For every new feature, follow this exact order to ensure quality and maintainability.**

---

## The Iron Rule: Test-First Development

**NO FEATURE SHIPS WITHOUT TESTS.**

For every new feature:
1. ✅ Define types first
2. ✅ Write failing tests
3. ✅ Document architecture (ADR if significant)
4. ✅ Implement to pass tests
5. ✅ Refactor for quality

---

## Step 1: Define Types

**Before writing any code, define your types.**

### Request Types

Located in: `/workspace/types/request_types.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class CreateCampaignRequest(BaseModel):
    """Request to create a new campaign"""
    client_id: str = Field(..., description="Unique client identifier")
    campaign_type: str = Field(..., description="Type of campaign (awareness, conversions, etc.)")
    budget: float = Field(..., gt=0, description="Campaign budget in USD")
    objectives: list[str] = Field(..., min_items=1, description="Campaign objectives")
```

### Response Types

Located in: `/workspace/types/response_types.py`

```python
from pydantic import BaseModel
from typing import Optional

class CreateCampaignResponse(BaseModel):
    """Response after creating a campaign"""
    campaign_id: str
    status: str
    message: str
    estimated_completion_date: Optional[str] = None
```

### Component Types

Located in: `/workspace/types/component_types.py`

```python
from pydantic import BaseModel
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    COMPLETED = "completed"

class AgentComponent(BaseModel):
    """Represents an agent in the system"""
    agent_id: str
    agent_type: str
    status: AgentStatus
    last_execution_time_ms: float
```

### Database Types

Located in: `/workspace/types/database_types.py`

```python
from typing import Optional
from datetime import datetime

class CampaignRecord:
    """Database record for a campaign"""
    campaign_id: str
    client_id: str
    campaign_type: str
    budget: float
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
```

---

## Step 2: Write Tests FIRST

**Write the test before implementing the feature.**

### Test File Naming Convention

```
tests/
├── unit/
│   ├── test_agent_tracking_system.py
│   ├── test_client_guidance_system.py
│   └── test_rate_limiter.py
├── integration/
│   ├── test_campaign_workflow.py
│   └── test_agent_handoffs.py
└── e2e/
    └── test_full_campaign.py
```

### Test Structure

```python
import pytest
from agent_tracking_system import AgentTracker, AgentType, CampaignType

class TestAgentTracker:
    """Test suite for AgentTracker"""
    
    def test_start_campaign_creates_record(self):
        """GIVEN a new campaign request
           WHEN start_campaign is called
           THEN a campaign record is created with correct data
        """
        # Arrange
        tracker = AgentTracker()
        
        # Act
        campaign_id = tracker.start_campaign(
            campaign_id="test_123",
            campaign_type=CampaignType.AWARENESS,
            client_id="client_456",
            client_name="Test Client",
            budget=1000.0,
            objectives=["Increase brand awareness"],
        )
        
        # Assert
        assert campaign_id == "test_123"
        report = tracker.get_campaign_report(campaign_id)
        assert report["client_name"] == "Test Client"
        assert report["budget"] == 1000.0
        assert report["status"] == "active"
    
    def test_track_agent_execution_updates_metrics(self):
        """GIVEN an active campaign
           WHEN an agent executes
           THEN metrics are recorded accurately
        """
        # Arrange
        tracker = AgentTracker()
        tracker.start_campaign(
            campaign_id="test_123",
            campaign_type=CampaignType.AWARENESS,
            client_id="client_456",
            client_name="Test Client",
            budget=1000.0,
            objectives=["Test"],
        )
        
        # Act
        tracker.track_agent_execution(
            campaign_id="test_123",
            agent_type=AgentType.RESEARCH,
            execution_time_ms=1500.0,
            success=True,
            output_quality=0.92,
            api_calls=3,
            api_cost=0.05,
        )
        
        # Assert
        report = tracker.get_campaign_report("test_123")
        agent_perf = report["agent_performance"]["research"]
        assert agent_perf["executions"] == 1
        assert agent_perf["success_rate"] == 1.0
        assert agent_perf["avg_quality"] == 0.92
        assert agent_perf["api_cost"] == 0.05
```

### Test Coverage Requirements

**Minimum coverage per feature:**
- Unit tests: 80%+
- Integration tests: Key workflows
- E2E tests: Happy path + critical failures

---

## Step 3: Document Architecture (ADRs)

**For significant decisions, create an ADR.**

### When to Write an ADR

Write an ADR if:
- ✅ Introduces new pattern or architecture
- ✅ Breaks backward compatibility
- ✅ Impacts multiple components
- ✅ Security, compliance, or data model changes
- ✅ Third-party dependency added
- ✅ Performance trade-offs

Do NOT write an ADR for:
- ❌ Bug fixes
- ❌ Trivial refactors
- ❌ UI copy changes
- ❌ Adding one field to existing model

### ADR Numbering

```
docs/adr/
├── ADR-001-governed-memory-architecture.md
├── ADR-002-rate-limiting-strategy.md
├── ADR-003-gdpr-compliance-approach.md
└── ADR-004-agent-tracking-system.md
```

### Quick ADR Creation

```bash
# Use the template
cp docs/ADR_TEMPLATE.md docs/adr/ADR-NNN-your-feature.md

# Fill in:
# - Context: Why is this needed?
# - Decision: What are we doing?
# - Consequences: What are the impacts?
# - Alternatives: What else did we consider?
```

---

## Step 4: Implement to Pass Tests

**Now write the minimum code to make tests pass.**

### Implementation Checklist

- [ ] Types defined (request, response, component, database)
- [ ] Tests written (unit, integration, e2e)
- [ ] ADR created (if significant change)
- [ ] Implementation written
- [ ] All tests passing
- [ ] No hardcoded credentials
- [ ] Input validation added
- [ ] Error handling implemented
- [ ] Audit logging added (for sensitive operations)
- [ ] Documentation updated

---

## Step 5: Refactor for Quality

**Make it work, then make it right.**

### Refactoring Checklist

- [ ] Remove duplication (DRY principle)
- [ ] Extract complex logic to functions
- [ ] Add descriptive variable names
- [ ] Remove dead code
- [ ] Optimize hot paths (if needed)
- [ ] Add inline documentation for non-obvious logic
- [ ] Run linter (`ruff check .`)
- [ ] Run type checker (`mypy .`)

---

## Complete Example: Adding Campaign Tracking

### 1. Define Types

```python
# types/request_types.py
class TrackAgentExecutionRequest(BaseModel):
    campaign_id: str
    agent_type: str
    execution_time_ms: float
    success: bool
    output_quality: Optional[float] = None
```

### 2. Write Tests

```python
# tests/unit/test_agent_tracking_system.py
def test_track_agent_execution_updates_metrics():
    # Test code here (see above)
    pass
```

### 3. Document Architecture

```markdown
# ADR-004: Agent Tracking System
(See ADR template above)
```

### 4. Implement

```python
# agent_tracking_system.py
def track_agent_execution(self, ...):
    # Implementation here
    pass
```

### 5. Refactor

```python
# Extract helper function
def _calculate_average_quality(scores: list[float]) -> float:
    return sum(scores) / len(scores) if scores else 0.0
```

---

## Continuous Quality Checks

### Before Every Commit

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check .

# Run type checker
mypy .

# Check coverage
pytest --cov=. --cov-report=html
```

### Before Every PR

```bash
# Full test suite
pytest tests/ -v --cov=. --cov-report=term-missing

# Check ADRs are up to date
ls docs/adr/*.md

# Verify no secrets in code
git diff main | grep -i "api_key\|secret\|token\|password"
```

---

## Summary: The Golden Path

```
Feature Request
    ↓
Define Types (request, response, component, database)
    ↓
Write Failing Tests (unit → integration → e2e)
    ↓
Create ADR (if significant architectural change)
    ↓
Implement Minimum Code to Pass Tests
    ↓
Refactor for Quality
    ↓
Run Quality Checks (pytest, ruff, mypy)
    ↓
Create PR
    ↓
Code Review
    ↓
Merge
```

**Never skip a step. Quality is not negotiable.** ✅

---

## Resources

- ADR Template: `/workspace/docs/ADR_TEMPLATE.md`
- Type Definitions: `/workspace/types/`
- Test Examples: `/workspace/tests/`
- Integration Guide: `/workspace/INTEGRATION_GUIDE.md`

---

**Questions? See `/workspace/docs/FAQ.md` or ask the team.** 