# MetaMarkAgency Tool Testing - Quick Reference

## Test Results At-a-Glance

```
✅ PASSING (6 tools):
├── ResearchAgent
│   ├── AdLibraryPatternAnalyzer
│   └── CompetitorResearchPlanBuilder
├── FacebookPolicyAgent
│   └── FacebookPolicyChecklist
├── ClientApprovalAgent
│   └── ClientApprovalChecklist
└── SearchVisibilityAgent
    ├── ContentVisibilityChecklist
    └── SearchVisibilityBriefBuilder

❌ FAILING (9 tools):
├── AdCopyAgent
│   └── AdCopyGenerator (missing OPENAI_API_KEY)
├── ImageCreatorAgent
│   └── ImageGenerator (missing OPENAI_API_KEY)
└── FacebookManagerAgent
    ├── AdCreator (missing Facebook credentials)
    ├── AdPerformanceMonitor (missing Facebook credentials)
    ├── AdSetCreator (missing Facebook credentials)
    ├── FacebookPagePostPublisher (missing Facebook credentials)
    ├── FacebookPhotoPostPublisher (missing Facebook credentials)
└── ResearchAgent
    ├── MetaAdLibraryKeywordSearch (missing token - OK, fallback tool)
    └── MetaAdLibraryPageSearch (missing token - OK, fallback tool)

⚠️ NEEDS CONFIG (7 tools):
├── FacebookManagerAgent
│   ├── AdCampaignStarter (missing Facebook credentials)
│   └── FacebookTokenDiagnostics (missing Facebook credentials)
└── ResearchAgent (Scrape Creators tools)
    ├── ScrapeCreatorsFacebookAdDetails
    ├── ScrapeCreatorsFacebookAdSearch
    ├── ScrapeCreatorsFacebookAdTranscript
    ├── ScrapeCreatorsFacebookCompanyAds
    └── ScrapeCreatorsFacebookCompanySearch

⏭️ SKIPPED (7 tools - missing test blocks):
├── ImageCreatorAgent
│   └── ImageSelector
├── FacebookManagerAgent
│   └── CampaignLifecycle
├── CampaignOpsAgent
│   ├── BudgetManager
│   ├── CampaignDashboard
│   ├── CampaignScheduler
│   └── PostTracker
└── SearchVisibilityAgent
    └── KnowledgeDocumentLookup
```

## Environment Setup Checklist

- [ ] Create `.env` file in `/workspace`
- [ ] Add OPENAI_API_KEY (for 2 tools)
- [ ] Add Facebook API credentials (for 8 tools)
- [ ] Add SCRAPE_CREATORS_API_KEY (for 5 tools)
- [ ] Optional: Add META_AD_LIBRARY_ACCESS_TOKEN (for 2 fallback tools)
- [ ] Run test again: `python3 test_all_tools.py`

## Required Environment Variables

### Critical (Blocks 17 tools)
```bash
OPENAI_API_KEY=sk-...                    # AdCopy & Image generation
FACEBOOK_ACCESS_TOKEN=EAA...             # All Facebook operations
FACEBOOK_APP_ID=123456789                # Facebook app credentials
FACEBOOK_APP_SECRET=abc123...            # Facebook app secret
FACEBOOK_PAGE_ID=987654321               # Target Facebook page
SCRAPE_CREATORS_API_KEY=sc_...           # Ad research tools
```

### Optional (Fallback tools)
```bash
META_AD_LIBRARY_ACCESS_TOKEN=...         # Direct Meta Ad Library access
```

## Run Tests

```bash
# Full test suite
cd /workspace
python3 test_all_tools.py

# Test individual tool
cd /workspace
python3 AdCopyAgent/tools/AdCopyGenerator.py

# Test with proper Python path (if needed)
PYTHONPATH=/workspace python3 AdCopyAgent/tools/AdCopyGenerator.py
```

## Common Issues & Fixes

### Issue: ModuleNotFoundError for error_logger, workflow_state, safe_audit_log
**Fix:** Run with PYTHONPATH set to workspace root
```bash
PYTHONPATH=/workspace python3 path/to/tool.py
```

### Issue: OPENAI_API_KEY missing
**Fix:** Add to `.env` file or export
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Issue: Facebook API errors
**Fix:** Ensure all 4 Facebook variables are set:
- FACEBOOK_ACCESS_TOKEN
- FACEBOOK_APP_ID
- FACEBOOK_APP_SECRET
- FACEBOOK_PAGE_ID

### Issue: Tool has no test block
**Fix:** Add test block to tool file:
```python
if __name__ == "__main__":
    tool = ToolName(param="test")
    print(tool.run())
```

## Tool Independence Scores

| Score | Count | Meaning |
|-------|-------|---------|
| 10/10 | 6 | Perfect - No external dependencies |
| 8-9/10 | 7 | High - Minimal dependencies |
| 7/10 | 3 | Medium - Some API dependencies |
| 4-6/10 | 6 | Low - Multiple dependencies |
| 3/10 | 3 | Very Low - Heavy API coupling |

## Next Actions

1. **Immediate:** Configure environment variables in `.env`
2. **Short-term:** Add test blocks to 7 skipped tools
3. **Medium-term:** Add mock modes to low-independence tools
4. **Long-term:** Implement retry logic and rate limiting

## Files Generated

- `TOOL_TEST_RESULTS.md` - Full detailed test report with outputs/errors
- `TOOL_TEST_ANALYSIS.md` - Comprehensive analysis with recommendations
- `TOOL_TEST_QUICKREF.md` - This quick reference (you are here)
- `.env.example` - Template for environment variables

## Contact Points

- **Test Script:** `/workspace/test_all_tools.py`
- **Shared Modules:** `/workspace/{error_logger,workflow_state,safe_audit_log}.py`
- **Audit Logs:** `/workspace/audit_logs/`
- **Generated Assets:** `/workspace/generated_assets/`
- **Campaign Data:** `/workspace/campaign_data/`
