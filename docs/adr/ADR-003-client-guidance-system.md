# ADR-003: Client Guidance System for Campaign Recommendations

**Status:** Accepted  
**Date:** 2026-09-16  
**Decision Makers:** Development Team  
**Technical Story:** User requirement for helping clients who don't know what ads to run

---

## Context

User requirement: *"Most times the client when they start they may not know what types of ads to run."*

**Problem:**
- Clients are confused about which campaign type to choose
- No guidance based on their specific situation
- Leads to poor campaign choices and wasted budget
- Increases support burden (clients asking "what should I run?")
- Reduces conversion from trial to paid

**Requirements:**
1. Recommend campaigns based on client context (goal, industry, stage, budget)
2. Provide reasoning for recommendations
3. Give expected outcomes and timelines
4. Include best practices
5. Prioritize recommendations (most important first)

---

## Decision

**We will implement an intelligent recommendation engine (`client_guidance_system.py`) that analyzes client context and provides prioritized campaign strategies.**

**Architecture:**
```
ClientGuidanceSystem
├── Recommendation Engine
│   ├── get_recommendations() -> List[CampaignRecommendation]
│   └── RECOMMENDATION_RULES (goal x stage -> campaigns)
├── Onboarding
│   └── generate_onboarding_questionnaire()
└── History Tracking
    └── Save all recommendations for learning
```

**Input Factors:**
1. **Client Goal:** grow_brand, get_customers, launch_product, etc.
2. **Industry:** ecommerce, saas, local_business, restaurant, etc.
3. **Business Stage:** startup, growing, established, enterprise
4. **Monthly Budget:** Numeric value
5. **Audience Size:** Current followers/customers
6. **Existing Customers:** Boolean

**Output:**
```python
[
  CampaignRecommendation(
    campaign_type=CONVERSIONS,
    priority=1,
    reasoning="Growing restaurants see best results...",
    budget_recommendation=(600, 700),
    expected_outcomes=["50-100 conversions", "ROI: 2-4x"],
    timeline="3-4 weeks for data",
    best_practices=["Install Pixel", "Create urgency", ...]
  ),
  ...
]
```

---

## Consequences

### Positive
- **Reduced confusion** - Clients know what to run
- **Better outcomes** - Right campaign for their situation
- **Lower support burden** - Self-service recommendations
- **Higher conversion** - Confident clients convert to paid
- **Data-driven** - Recommendations based on rules + history

### Negative
- **Rule maintenance** - Must update rules as we learn
- **Not ML-based** - Rules, not predictive models (for now)
- **Limited personalization** - Same rules for similar clients

### Neutral
- Recommendations are suggestions, not guarantees
- Clients can ignore and choose their own campaigns

---

## Alternatives Considered

### Alternative 1: Machine Learning Recommendation Model
**Pros:**
- Learns from actual outcomes
- Personalized predictions
- Gets better over time

**Cons:**
- Requires 1000+ campaigns to train
- Complex infrastructure (model serving)
- Hard to explain reasoning to clients
- Takes 3-6 months to build

**Why not chosen:** Not enough data yet, need MVP now

### Alternative 2: Manual Sales Call
**Pros:**
- Human understanding
- Can ask clarifying questions
- Build relationship

**Cons:**
- Doesn't scale
- Requires sales team
- Slow (days to schedule)
- Expensive ($100+ per call)

**Why not chosen:** Want self-service, user wants automation

### Alternative 3: Static FAQ/Guide
**Pros:**
- Simple to implement
- Zero code

**Cons:**
- Not personalized
- Clients must read and interpret
- No budget allocation
- No prioritization

**Why not chosen:** Too generic, doesn't solve "I don't know" problem

---

## Implementation Notes

**Recommendation Rules:**
```python
RECOMMENDATION_RULES = {
    ClientGoal.GET_CUSTOMERS: {
        "startup": [
            (CampaignType.TRAFFIC, "Drive qualified traffic to landing page"),
            (CampaignType.LEADS, "Build email list for nurturing"),
        ],
        "growing": [
            (CampaignType.CONVERSIONS, "Direct conversion campaigns"),
            (CampaignType.RETARGETING, "Convert warm leads"),
        ],
        ...
    }
}
```

**Budget Allocation Logic:**
- Priority 1 gets 60-70% of budget
- Priority 2 gets 30-40% of budget
- If has_existing_customers, add retargeting campaign

**Industry Adjustments:**
```python
industry_notes = {
    Industry.ECOMMERCE: "Visual ads and retargeting work best",
    Industry.SAAS: "Educate audience before conversion",
    Industry.RESTAURANT: "Food photography and limited-time offers",
    ...
}
```

**Onboarding Flow:**
```
1. Show questionnaire (6 questions)
2. Client answers
3. Generate recommendations
4. Client reviews and selects
5. Create campaign with guidance context
```

---

## Testing Strategy

**Unit Tests:**
- Recommendations for each goal x stage combination
- Budget allocation logic
- Industry adjustments
- Expected outcomes generation

**Integration Tests:**
- Full onboarding flow
- History tracking
- Edge cases (zero budget, no audience, etc.)

**Manual Testing:**
- Real client personas (coffee shop, SaaS startup, etc.)
- Validate recommendations make sense

---

## Future Enhancements

**Phase 2 (3-6 months):**
- Track recommendation → campaign outcome
- A/B test different recommendation strategies
- Add confidence scores based on historical success

**Phase 3 (6-12 months):**
- ML model trained on actual outcomes
- Personalized recommendations based on similar clients
- Multi-objective optimization (awareness + conversions)

---

## References

- Implementation: `/workspace/client_guidance_system.py`
- Types: `/workspace/types/request_types.py` (GetRecommendationsRequest)
- Related: ADR-002 (Agent Tracking - will track recommendation success)

---

**Last Updated:** 2026-09-16  
**Reviewed By:** Development Team
