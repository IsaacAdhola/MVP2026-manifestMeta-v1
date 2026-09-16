# ADR-004: Staging Environment Strategy (Firebase)

**Status:** Proposed  
**Date:** 2026-09-16  
**Decision Makers:** Development Team, User  
**Technical Story:** User requirement - "DO NOT connect AI agents to production database!"

---

## Context

**CRITICAL USER REQUIREMENT:** *"!!!DO NOT connect AI agents to production database!!! Instead create 'a stage environment' we can use firebase."*

**Problem:**
- AI agents currently write to local JSON files
- No staging environment for testing
- Risk of agents corrupting production data
- No separation between dev/staging/production
- Cannot safely test new agent behaviors

**Requirements:**
1. **NEVER** connect AI agents directly to production database
2. Create staging environment (user suggests Firebase)
3. Safe testing of agent behaviors before production
4. Easy to reset/clean staging data
5. Low cost (Firebase free tier: 1GB storage, 10GB bandwidth)

---

## Decision

**We will use Firebase as staging environment for AI agent testing. Production will remain file-based or use separate database that agents CANNOT access directly.**

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│ DEVELOPMENT (Local)                             │
│ - JSON files (.agent_tracking/, .governed_memory)│
│ - No API keys required for basic testing       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ STAGING (Firebase)                              │
│ - Firestore for campaign data                  │
│ - AI agents write here for testing             │
│ - Can be reset anytime                         │
│ - Separate Firebase project                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ PRODUCTION (Protected)                          │
│ - AI agents WRITE to queue/staging             │
│ - Human approval before production             │
│ - Read-only for agents (if needed)             │
│ - Production DB isolated                       │
└─────────────────────────────────────────────────┘
```

**Firebase Setup:**
```
metaark-agency-staging/         # Staging project
├── Firestore Collections
│   ├── campaigns/              # Campaign metadata
│   ├── agent_executions/       # Agent tracking
│   ├── recommendations/        # Client guidance
│   └── audit_logs/            # All events
└── Firebase Rules
    └── Allow all writes (staging only)

metamark-agency-production/     # Production project (future)
├── Firestore Collections
│   └── Same structure
└── Firebase Rules
    └── NO direct agent writes
    └── Only via Cloud Functions with approval
```

---

## Consequences

### Positive
- **Safety** - AI agents can NEVER corrupt production
- **Easy reset** - Delete staging project, recreate in minutes
- **Free** - Firebase free tier sufficient for testing
- **Real-time** - See agent writes immediately in Firebase console
- **Cloud-based** - Multiple developers can test simultaneously
- **Audit trail** - Firebase automatically logs all operations

### Negative
- **Requires setup** - User must create Firebase project and provide credentials
- **Internet required** - Unlike local JSON files
- **API limits** - Free tier has quotas (1GB storage, 50K reads/day)

### Neutral
- Need environment variable: `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS`
- Staging costs ~$0-5/month if we exceed free tier

---

## Alternatives Considered

### Alternative 1: Local SQLite Database
**Pros:**
- No internet required
- Zero cost
- Fast

**Cons:**
- Still on same machine as production code
- Risk of pointing to wrong database
- No cloud access for team

**Why not chosen:** Doesn't provide cloud staging, user suggested Firebase

### Alternative 2: Docker Container with Postgres
**Pros:**
- Complete isolation
- Production-like environment
- No vendor lock-in

**Cons:**
- Requires Docker knowledge
- More setup complexity
- Not suggested by user

**Why not chosen:** User specifically suggested Firebase

### Alternative 3: Separate PostgreSQL Database
**Pros:**
- Production-like
- Relational queries

**Cons:**
- Still requires database server
- More expensive than Firebase free tier
- User said "DO NOT connect to production database" - any DB is risky

**Why not chosen:** User wants staging, not another database

---

## Implementation Plan

### Phase 1: Setup (Requires User Action)

**USER TODO:**
1. Create Firebase project: `metamark-agency-staging`
2. Enable Firestore
3. Get service account credentials JSON
4. Add to `.env`:
   ```
   ENVIRONMENT=staging
   FIREBASE_PROJECT_ID=metamark-agency-staging
   FIREBASE_CREDENTIALS_PATH=./firebase-staging-key.json
   ```

### Phase 2: Create Firebase Adapter

**NEW FILE:** `firebase_adapter.py`
```python
from firebase_admin import firestore, initialize_app

class FirebaseAdapter:
    def __init__(self):
        if os.getenv("ENVIRONMENT") == "staging":
            # Initialize Firebase
            initialize_app(credentials=...)
            self.db = firestore.client()
        else:
            # Use local JSON files
            self.db = None
    
    def save_campaign(self, campaign_data):
        if self.db:  # Firebase
            self.db.collection('campaigns').document(campaign_id).set(campaign_data)
        else:  # Local
            # Current JSON file logic
```

### Phase 3: Agent Integration

**MODIFY:** `agent_tracking_system.py`
```python
class AgentTracker:
    def __init__(self):
        # Check environment
        if os.getenv("ENVIRONMENT") == "staging":
            self.storage = FirebaseAdapter()
        else:
            self.storage = JSONAdapter()  # Current logic
```

### Phase 4: Testing

```bash
# Development (no Firebase needed)
ENVIRONMENT=development python agency.py

# Staging (writes to Firebase)
ENVIRONMENT=staging python agency.py

# Production (protected, agents can't write directly)
ENVIRONMENT=production python agency.py
```

---

## Production Protection Rules

**HARD RULES:**
1. ✅ AI agents NEVER have production database credentials
2. ✅ AI agents write to staging or approval queue
3. ✅ Human reviews before production deployment
4. ✅ Production writes go through Cloud Functions with auth
5. ✅ Agents can READ production (read-only token) if needed

**Firebase Rules (Staging):**
```javascript
// Staging: Allow everything (it's for testing!)
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: true;
    }
  }
}
```

**Firebase Rules (Production - Future):**
```javascript
// Production: NO direct writes from agents
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      // Agents can only read
      allow read: if request.auth != null;
      // Only Cloud Functions can write
      allow write: if request.auth.token.role == "admin";
    }
  }
}
```

---

## Cost Estimate

**Firebase Free Tier:**
- 1 GB storage
- 50,000 reads/day
- 20,000 writes/day
- 10 GB network egress/month

**Estimated Usage (Staging):**
- ~100 campaigns/month testing = ~10 MB
- ~1,000 agent executions/month = ~500 KB
- Well within free tier

**If exceed free tier:** ~$5-10/month

---

## Security Checklist

- [ ] User creates separate Firebase project for staging
- [ ] Service account has minimal permissions
- [ ] Credentials stored in `.env` (never in code)
- [ ] `.env` in `.gitignore` (never committed)
- [ ] Production Firebase project uses strict rules
- [ ] Agents NEVER have production credentials

---

## Questions for User

**BEFORE IMPLEMENTING, I NEED:**

1. **Do you want me to create the Firebase adapter now, or wait until you set up the Firebase project?**

2. **What data should go to Firebase staging?**
   - [ ] Campaign tracking data?
   - [ ] Agent execution metrics?
   - [ ] Client guidance recommendations?
   - [ ] All of the above?

3. **Do you already have a Firebase account, or should I provide setup instructions?**

4. **For production (future), do you want:**
   - [ ] Separate Firebase project?
   - [ ] Traditional database (PostgreSQL/MySQL)?
   - [ ] Keep JSON files (current)?

5. **Should staging environment be reset:**
   - [ ] Manually (when you want)?
   - [ ] Daily?
   - [ ] Weekly?

---

## References

- Firebase docs: https://firebase.google.com/docs/firestore
- Firebase free tier: https://firebase.google.com/pricing
- Related: ADR-002 (Agent Tracking), ADR-001 (Governed Memory)

---

**Last Updated:** 2026-09-16  
**Status:** AWAITING USER INPUT FOR FIREBASE CREDENTIALS  
**Reviewed By:** Development Team, User
