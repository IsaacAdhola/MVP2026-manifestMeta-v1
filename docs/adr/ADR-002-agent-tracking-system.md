# ADR-002: Agent Tracking System for Campaign Analytics

**Status:** Accepted  
**Date:** 2026-09-16  
**Decision Makers:** Development Team  
**Technical Story:** User requirement for tracking agents and frameworks on both agency and client side

---

## Context

User requirement: *"How can we ensure that we can track our agents and frameworks as the clients use them on our side and theirs all types of campaigns?"*

**Problem:**
- No visibility into which agents execute for each campaign
- No tracking of execution time, quality, or costs
- Can't provide clients with reports on what was done
- Can't optimize agent performance across campaigns
- Can't track framework versions for debugging

**Requirements:**
1. Track all 9 agents across 8 campaign types
2. Record metrics: execution time, success rate, quality, API costs
3. Track framework versions (OpenAI, Facebook SDK, etc.)
4. Provide client-facing reports (what happened, results)
5. Provide agency analytics (revenue, agent performance)
6. Integrate with governed memory for agent access

---

## Decision

**We will implement a comprehensive agent tracking system (`agent_tracking_system.py`) that records all agent executions, framework usage, and campaign outcomes.**

**Architecture:**
```
AgentTracker
├── Campaign Management
│   ├── start_campaign()
│   ├── complete_campaign()
│   └── get_campaign_report() [CLIENT VIEW]
├── Execution Tracking
│   ├── track_agent_execution()
│   ├── track_framework_usage()
│   └── track_client_approval()
└── Analytics
    └── get_agency_analytics() [AGENCY VIEW]
```

**Data Storage:**
```
.agent_tracking/
├── campaigns.json           # All campaign metadata
├── agent_metrics.json       # Per-agent performance
└── framework_usage.json     # Framework versions used
```

**Integration Points:**
- Governed Memory: Campaign metadata stored in WORKFLOW scope
- Audit Logging: All tracking events logged
- Rate Limiter: API costs recorded

---

## Consequences

### Positive
- **Full visibility** into agent performance across all campaigns
- **Client transparency** - detailed reports of what was done
- **Optimization data** - identify slow/low-quality agents
- **Debugging support** - know which framework versions were used
- **Revenue tracking** - total spend across all campaigns
- **Quality metrics** - approval rates, revision counts

### Negative
- **Storage overhead** - ~1-2MB per campaign for all metrics
- **Performance impact** - Small (~5ms) per agent execution for tracking
- **Manual integration** - Agents must call `track_agent_execution()`

### Neutral
- Requires agents to pass campaign_id to tracking calls
- Framework tracking is opt-in (agents must call it)

---

## Alternatives Considered

### Alternative 1: Use External Analytics Service (e.g., Mixpanel, Segment)
**Pros:**
- Professional UI for analytics
- Real-time dashboards
- No storage management

**Cons:**
- Monthly cost ($100-500/month)
- Data leaves our infrastructure (compliance risk)
- Requires internet connection (blocks self-hosting)
- Vendor lock-in

**Why not chosen:** Conflicts with self-hosting requirement, adds cost, compliance issues

### Alternative 2: Database (PostgreSQL)
**Pros:**
- Relational queries
- Scales to millions of records
- ACID guarantees

**Cons:**
- Infrastructure requirement (not zero-dependency)
- Complicates deployment
- Overkill for current scale (hundreds of campaigns)

**Why not chosen:** User explicitly said "DO NOT connect to production database" - JSON files sufficient for now

### Alternative 3: No Tracking (Manual Reports)
**Pros:**
- Zero code overhead
- No storage needed

**Cons:**
- No visibility
- Can't optimize
- Can't answer client questions

**Why not chosen:** User explicitly requested tracking

---

## Implementation Notes

**Core Classes:**
```python
class AgentTracker:
    def start_campaign(campaign_id, campaign_type, client_id, budget, objectives)
    def track_agent_execution(campaign_id, agent_type, time_ms, success, quality, cost)
    def track_framework_usage(campaign_id, framework_name, version, usage_type)
    def track_client_approval(campaign_id, agent_type, approved, revisions)
    def complete_campaign(campaign_id, actual_spend, metrics, satisfaction)
    def get_campaign_report(campaign_id) -> dict  # For clients
    def get_agency_analytics() -> dict  # For agency
```

**Metrics Tracked Per Agent:**
- Total executions
- Success/failure counts
- Average execution time
- Quality scores (0-1)
- API calls and costs
- Client approval rate
- Revisions requested

**Integration Example:**
```python
# In ResearchAgent.run()
start_time = time.time()
try:
    result = self.do_research()
    success = True
    quality = self.evaluate_quality(result)
except Exception as e:
    success = False
    quality = 0.0
finally:
    execution_time = (time.time() - start_time) * 1000
    tracker.track_agent_execution(
        campaign_id=self.campaign_id,
        agent_type=AgentType.RESEARCH,
        execution_time_ms=execution_time,
        success=success,
        output_quality=quality,
        api_calls=self.api_calls,
        api_cost=self.api_cost,
    )
```

**Storage Format (JSON):**
```json
{
  "campaign_123": {
    "campaign_id": "campaign_123",
    "client_name": "Coffee Shop",
    "campaign_type": "conversions",
    "budget": 1000.0,
    "agents_used": ["research", "ad_copy", "image_creator"],
    "framework_versions": {"openai": "2.44.0"},
    "performance_metrics": {...}
  }
}
```

---

## Migration Plan

**Phase 1 (Week 1):**
- Deploy tracking system alongside existing code
- No agent changes required yet

**Phase 2 (Week 2-3):**
- Add tracking calls to CEO agent (orchestrator)
- Test with 2-3 pilot campaigns

**Phase 3 (Week 4-6):**
- Add tracking to all 9 agents
- Verify data quality

**Phase 4 (Week 7+):**
- Launch client-facing reports
- Use analytics for optimization

---

## Testing Strategy

**Unit Tests:** `tests/unit/test_agent_tracking_system.py`
- Campaign creation
- Agent execution tracking (success and failure)
- Multiple agents in one campaign
- Framework usage tracking
- Client approval tracking
- Campaign completion
- Analytics aggregation

**Integration Tests:**
- Full campaign workflow with tracking
- Governed memory integration
- Audit log integration

---

## References

- Implementation: `/workspace/agent_tracking_system.py`
- Tests: `/workspace/tests/unit/test_agent_tracking_system.py`
- Types: `/workspace/types/component_types.py` (AgentComponent, CampaignComponent)
- Related: ADR-001 (Governed Memory), ADR-003 (Client Guidance)

---

**Last Updated:** 2026-09-16  
**Reviewed By:** Development Team
