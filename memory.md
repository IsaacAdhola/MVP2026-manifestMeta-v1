# 🧠 MetaMarkAgency Memory

**Purpose:** Record key decisions, lessons learned, and architectural insights so they're never forgotten.

**Last Updated:** 2026-09-16

---

## Key Architectural Decisions

### 1. Governed Shared Memory (2026-09-16)
**Decision:** 3-tier memory architecture (GLOBAL, WORKFLOW, AGENT_PRIVATE)  
**Why:** Prevent data leakage between campaigns, GDPR compliance  
**Reference:** ADR-001  
**Lesson:** Backward compatibility is critical - kept old `workflow_state.py` interface

### 2. Agent Tracking System (2026-09-16)
**Decision:** Track all agent executions, costs, and quality per campaign  
**Why:** Need visibility for both agency (optimization) and clients (transparency)  
**Reference:** ADR-002  
**Lesson:** JSON files sufficient for now, don't over-engineer with database

### 3. Client Guidance System (2026-09-16)
**Decision:** Rule-based recommendation engine (not ML yet)  
**Why:** Clients don't know what campaigns to run, need guidance  
**Reference:** ADR-003  
**Lesson:** Start with rules, collect data, build ML later when we have 1000+ campaigns

### 4. Staging Environment Strategy (2026-09-16)
**Decision:** Firebase for staging, NEVER connect agents to production DB  
**Why:** User requirement - safety first  
**Reference:** ADR-004  
**Status:** AWAITING USER - Need Firebase credentials before implementation  
**Critical Rule:** ❌ NO PRODUCTION DB ACCESS FOR AGENTS ❌

---

## Critical Rules (NEVER FORGET)

### 1. Database Safety
- ❌ AI agents NEVER write to production database
- ✅ Agents write to staging (Firebase)
- ✅ Human approval before production
- ✅ Separate projects: `metamark-staging` vs `metamark-production`

### 2. Ask, Don't Guess
**Before doing these, ASK user:**
- Getting API keys
- Connecting services
- Creating accounts
- Deploying anything
- Installing dependencies

### 3. No Broken Windows
**Zero tolerance for:**
- Failing tests
- Linter warnings
- Hardcoded credentials
- Commented-out code
- Unused imports

**Pre-commit checklist:**
```bash
pytest tests/ -v    # Must pass
ruff check .        # Must be clean
mypy .              # Must type-check
```

### 4. Document Everything
**For every significant change:**
- Create ADR in `docs/adr/`
- Update this `memory.md`
- Update `heartbeat.md`
- Follow TDD workflow

### 5. PDR Process
**When creating Product Requirements Document:**
- ASK questions until clear
- Don't assume
- Document assumptions
- Get user confirmation

---

## Lessons Learned

### Testing
- **TDD saves time** - Write test first, implement to pass, refactor
- **Types catch bugs** - Pydantic validation prevents runtime errors
- **Integration tests needed** - Unit tests alone miss interaction bugs

### Architecture
- **Start simple** - JSON files beat databases for MVP
- **Backward compatible** - Keep old interfaces while adding new features
- **Self-documenting** - Good types and names reduce comment needs

### User Requirements
- **Listen to constraints** - "No production DB" shaped entire staging strategy
- **Ask, don't assume** - Better to ask than implement wrong thing
- **Document rules** - Critical requirements go in `.cursorrules` to never forget

---

## Technical Debt

### Immediate (Fix Now)
1. ~~Add pytest to requirements.txt~~ (pending)
2. ~~Document all architectural decisions in ADRs~~ ✅ DONE
3. Create Firebase adapter (waiting for user credentials)

### Short-term (Next 2-4 weeks)
1. Migrate agents to use tracking system
2. Test client guidance with real clients
3. Set up CI/CD pipeline

### Long-term (3+ months)
1. ML-based recommendations (need 1000+ campaigns)
2. Real-time dashboard (when scale requires it)
3. Multi-language support

---

## What We Built

### Phase 1: Infrastructure (Week 1)
- Governed memory with 3 scopes
- Rate limiting and budget control
- API version monitoring
- Competitive intelligence
- Marketing materials
- Complete test suite (9/9 passing)

### Phase 2: Tracking & TDD (Week 1)
- Agent tracking system (512 lines)
- Client guidance system (476 lines)
- Complete type system (425 lines)
- ADR framework with 4 ADRs
- TDD workflow documentation
- Comprehensive unit tests (268 lines)

**Total:** 5,992 lines of production code + documentation

---

## Known Issues

### Blockers
1. **Firebase setup needed** - Waiting for user to create project and provide credentials
2. **Pytest not in requirements** - Need to add

### Non-Blockers
1. ML recommendations - Don't have enough data yet
2. Real-time dashboard - Current reports sufficient
3. Multi-language - English only for MVP

---

## Future Enhancements

### Phase 3 (Next sprint)
- [ ] Firebase adapter implementation (after user provides creds)
- [ ] CI/CD pipeline setup
- [ ] Integration tests for full workflows

### Phase 4 (3-6 months)
- [ ] ML recommendation engine (when data available)
- [ ] Real-time analytics dashboard
- [ ] A/B testing framework

### Phase 5 (6-12 months)
- [ ] Multi-language support
- [ ] Advanced optimization (multi-objective)
- [ ] Predictive budget recommendations

---

## Questions for Next Session

1. **Firebase:** Do you have credentials, or should I provide setup guide?
2. **Staging data:** What should go to Firebase? (campaigns, metrics, all?)
3. **Production strategy:** What DB do you want for production? (Firebase, PostgreSQL, keep JSON?)
4. **Reset frequency:** How often reset staging? (manual, daily, weekly?)

---

**Remember:** This file is the team's memory. Update after every significant change!
