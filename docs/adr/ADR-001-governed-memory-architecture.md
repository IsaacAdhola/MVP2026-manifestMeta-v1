# ADR-001: Governed Shared Memory Architecture

**Status:** Accepted  
**Date:** 2026-09-16  
**Decision Makers:** Development Team, CTO  
**Technical Story:** Investor requirement for memory isolation

---

## Context

The original MetaMarkAgency used a single shared state file (`workflow_state.py`) for all agents and campaigns. This created several problems:

1. **Data Leakage Risk:** Campaign A data could accidentally leak to Campaign B
2. **No Access Control:** All agents could read/write any data
3. **No Audit Trail:** No way to know who wrote what or when
4. **GDPR Non-Compliance:** No automatic data deletion mechanism
5. **Scaling Issues:** Single file became bottleneck

We needed an enterprise-grade memory system that:
- Prevents cross-campaign data leakage
- Provides role-based access control
- Tracks provenance (who, when, why)
- Supports GDPR-compliant deletion
- Scales horizontally

## Decision

**We will implement a 3-tier governed shared memory architecture based on the 2026 arXiv paper "Governed Shared Memory for Multi-Agent LLM Systems" (2606.24535v1).**

**Three memory scopes:**

1. **GLOBAL:** Organization-level, readable by all agents
   - Example: Company name, brand guidelines, global policies
   
2. **WORKFLOW:** Campaign-level, readable by agents in that campaign
   - Example: Target audience, campaign goals, research data
   
3. **AGENT_PRIVATE:** Agent-level, readable only by that specific agent
   - Example: Draft iterations, internal state, work-in-progress

**Key Features:**
- Permission matrix controls read/write/delete access per agent per scope
- Temporal supersession: newer facts automatically invalidate older ones
- Provenance tracking: every record includes creator, timestamp, source, confidence
- Namespace isolation: `{workflow_id}/{agent_id}` pattern prevents collisions
- Automatic cleanup: `cleanup_workflow()` deletes all campaign data (GDPR)

## Consequences

### Positive
- **Zero data leakage** between campaigns (enterprise requirement)
- **GDPR compliant** with automatic deletion
- **Full audit trail** for SOC2 compliance
- **Backward compatible** (old `workflow_state.py` interface still works)
- **Scalable** (separate files per workflow)

### Negative
- **Slightly more complex** API (3 scopes instead of 1)
- **Storage overhead** (~5MB per campaign for metadata)
- **Migration needed** for advanced features (though not required)

### Neutral
- Agents must explicitly choose scope when writing
- Requires developer education on when to use each scope

## Alternatives Considered

### Alternative 1: Single Shared State with Namespacing
**Pros:**
- Simpler implementation
- No API changes needed

**Cons:**
- No access control
- No provenance tracking
- Still vulnerable to leakage bugs

**Why not chosen:** Doesn't meet enterprise security requirements

### Alternative 2: Separate Database per Campaign
**Pros:**
- Complete isolation
- Easy to scale

**Cons:**
- Infrastructure overhead (need database server)
- More complex deployment
- Overkill for current scale

**Why not chosen:** Over-engineered for MVP, can add later if needed

### Alternative 3: Redis/External Cache
**Pros:**
- Fast access
- Battle-tested

**Cons:**
- Adds infrastructure dependency
- Complicates self-hosting
- Not needed for current throughput

**Why not chosen:** Want zero-dependency deployment option

## Implementation Notes

**Files:**
- `governed_memory.py` - Core implementation (418 lines)
- `test_new_systems.py` - Test coverage (9/9 passing)
- `INTEGRATION_GUIDE.md` - Developer documentation

**Storage Layout:**
```
.governed_memory/
├── global.json (organization data)
├── workflows/
│   ├── campaign_123.json
│   └── campaign_456.json
└── agents/
    ├── campaign_123_research_agent.json
    └── campaign_123_copywriter.json
```

**Backward Compatibility:**
```python
# Old code (still works)
from workflow_state import set_state_value, get_state_value

# New code (opt-in)
from governed_memory import GovernedMemory, MemoryScope
memory = GovernedMemory()
memory.set(key, value, MemoryScope.WORKFLOW, workflow_id="123")
```

**Migration Path:**
1. Phase 1: Deploy alongside existing `workflow_state.py` (no changes needed)
2. Phase 2: Add governed memory to new agents
3. Phase 3: Migrate existing agents over 4-6 weeks
4. Phase 4: Deprecate `workflow_state.py` (optional, keep for simplicity)

## References

- arXiv paper: https://arxiv.org/abs/2606.24535v1 (Governed Shared Memory for Multi-Agent LLM Systems)
- Implementation: `/workspace/governed_memory.py`
- Tests: `/workspace/test_new_systems.py`
- Integration guide: `/workspace/INTEGRATION_GUIDE.md`
- Related: ADR-002 (Access Control), ADR-003 (GDPR Compliance)

---

**Last Updated:** 2026-09-16  
**Reviewed By:** Development Team, Security Team, Legal Team (GDPR)
