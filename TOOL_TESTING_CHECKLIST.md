# MetaMarkAgency Tool Testing - Action Checklist

Use this checklist to track your progress through fixing tool issues.

---

## Phase 1: Environment Setup (Priority: CRITICAL)

### Configure API Credentials
- [ ] Create `.env` file in `/workspace`
- [ ] Add `OPENAI_API_KEY` (unblocks 2 tools)
- [ ] Add `FACEBOOK_ACCESS_TOKEN` (unblocks 8 tools)
- [ ] Add `FACEBOOK_APP_ID` (unblocks 8 tools)
- [ ] Add `FACEBOOK_APP_SECRET` (unblocks 8 tools)
- [ ] Add `FACEBOOK_PAGE_ID` (unblocks 8 tools)
- [ ] Add `SCRAPE_CREATORS_API_KEY` (unblocks 5 tools)
- [ ] Optional: Add `META_AD_LIBRARY_ACCESS_TOKEN` (fallback for 2 tools)

### Verify Setup
- [ ] Run `python3 test_all_tools.py` again
- [ ] Check that pass rate improves from 20.7% → 50%+
- [ ] Review any remaining failures
- [ ] Document any API setup issues

**Expected Outcome:** 15+ tools passing instead of 6

---

## Phase 2: Add Missing Test Blocks (Priority: HIGH)

### ImageCreatorAgent
- [ ] Add test block to `ImageSelector.py`
  - [ ] Import workflow_state
  - [ ] Create mock image options
  - [ ] Test selection logic
  - [ ] Verify output format

### FacebookManagerAgent
- [ ] Add test block to `CampaignLifecycle.py`
  - [ ] Test state transitions
  - [ ] Verify campaign status updates
  - [ ] Check error handling

### CampaignOpsAgent (4 tools)
- [ ] Add test block to `BudgetManager.py`
  - [ ] Test set_budget action
  - [ ] Test record_spend action
  - [ ] Test get_budget_status action
  - [ ] Test list_all_budgets action

- [ ] Add test block to `CampaignScheduler.py`
  - [ ] Test create_campaign action
  - [ ] Test add_post action
  - [ ] Test update_post_status action
  - [ ] Test list_campaigns action

- [ ] Add test block to `CampaignDashboard.py`
  - [ ] Test dashboard data retrieval
  - [ ] Verify metrics calculation
  - [ ] Check visualization output

- [ ] Add test block to `PostTracker.py`
  - [ ] Test post tracking
  - [ ] Verify status updates
  - [ ] Check performance metrics

### SearchVisibilityAgent
- [ ] Add test block to `KnowledgeDocumentLookup.py`
  - [ ] Test document retrieval
  - [ ] Verify search functionality
  - [ ] Check result formatting

### Verify Test Blocks
- [ ] Run `python3 test_all_tools.py` again
- [ ] Check that skipped count drops from 7 → 0
- [ ] Verify all new test blocks pass
- [ ] Fix any failing test blocks

**Expected Outcome:** 0 skipped tools, all 29 tools testable

---

## Phase 3: Implement Mock Modes (Priority: MEDIUM)

### High Priority Mock Modes
- [ ] Add mock mode to `AdCopyAgent/AdCopyGenerator.py`
  - [ ] Add mock_mode parameter
  - [ ] Implement _generate_mock_copy method
  - [ ] Update run method to check API key
  - [ ] Update test block to use mock mode
  - [ ] Test without API key

- [ ] Add mock mode to `ImageCreatorAgent/ImageGenerator.py`
  - [ ] Add mock_mode parameter
  - [ ] Implement _generate_mock_image method
  - [ ] Update run method to check API key
  - [ ] Update test block to use mock mode
  - [ ] Test without API key

### Medium Priority Mock Modes
- [ ] Add environment validation to `FacebookManagerAgent/AdCreator.py`
  - [ ] Create validate_facebook_env function
  - [ ] Check for missing variables
  - [ ] Return helpful error message
  - [ ] Test without credentials

- [ ] Add environment validation to `FacebookManagerAgent/AdSetCreator.py`
  - [ ] Use shared validation function
  - [ ] Test error handling
  - [ ] Verify error message quality

- [ ] Add environment validation to `FacebookManagerAgent/FacebookPagePostPublisher.py`
  - [ ] Use shared validation function
  - [ ] Test error handling
  - [ ] Add helpful setup instructions

### Create Shared Helpers
- [ ] Create `env_validator.py` module
  - [ ] Add validate_env_vars function
  - [ ] Add get_missing_vars function
  - [ ] Add format_error_message function
  - [ ] Test validation logic

- [ ] Update tools to use shared validator
  - [ ] AdCopyGenerator
  - [ ] ImageGenerator
  - [ ] All FacebookManagerAgent tools

### Verify Mock Modes
- [ ] Test all mock modes without API credentials
- [ ] Verify mock responses match real response format
- [ ] Check that independence scores improve
- [ ] Update documentation

**Expected Outcome:** All tools testable without API credentials

---

## Phase 4: Fix Specific Tool Issues (Priority: MEDIUM)

### AdCopyAgent
- [ ] Review AdCopyGenerator error handling
- [ ] Test with various input combinations
- [ ] Verify output format consistency
- [ ] Check shared state integration

### ImageCreatorAgent
- [ ] Review ImageGenerator image saving logic
- [ ] Test ImageSelector with mock state
- [ ] Verify file path resolution
- [ ] Check image option formatting

### FacebookManagerAgent
- [ ] Review all Facebook API error handling
- [ ] Test with invalid credentials
- [ ] Verify rate limiting logic
- [ ] Check shared state dependencies
- [ ] Test campaign workflow end-to-end

### ResearchAgent
- [ ] Document Scrape Creators API setup
- [ ] Test all 5 Scrape Creators tools
- [ ] Verify Meta Ad Library fallback
- [ ] Check pattern analyzer logic

### CampaignOpsAgent
- [ ] Test budget tracking accuracy
- [ ] Verify campaign scheduling logic
- [ ] Check dashboard data aggregation
- [ ] Test post tracking updates

**Expected Outcome:** All tools production-ready

---

## Phase 5: Documentation & Process (Priority: LOW)

### Update Documentation
- [ ] Document all API setup processes
- [ ] Create troubleshooting guide
- [ ] Add architecture diagrams
- [ ] Write tool usage examples
- [ ] Create video walkthroughs

### Improve Development Process
- [ ] Add pre-commit hooks for test blocks
- [ ] Create tool development template
- [ ] Add CI/CD for automated testing
- [ ] Set up monitoring dashboards
- [ ] Implement error tracking

### Knowledge Sharing
- [ ] Present findings to team
- [ ] Document lessons learned
- [ ] Create best practices guide
- [ ] Schedule code review sessions
- [ ] Plan ongoing improvements

**Expected Outcome:** Sustainable tool development process

---

## Testing Milestones

### Milestone 1: Basic Functionality ✅
- [x] All Python path issues resolved
- [x] Shared modules importable
- [x] Test framework working
- [x] 6/29 tools passing

### Milestone 2: Environment Configured
- [ ] All API credentials set
- [ ] 15+ tools passing
- [ ] All API-dependent tools tested
- [ ] No configuration errors

### Milestone 3: Complete Test Coverage
- [ ] All 29 tools have test blocks
- [ ] 0 skipped tools
- [ ] All tests runnable
- [ ] Clear pass/fail status

### Milestone 4: Mock Modes Implemented
- [ ] All API tools have mock modes
- [ ] Tests run without credentials
- [ ] Independence scores 7+
- [ ] Easy local testing

### Milestone 5: Production Ready
- [ ] 25+ tools passing
- [ ] Comprehensive error handling
- [ ] Full documentation
- [ ] Monitoring in place

---

## Quick Commands Reference

```bash
# Run full test suite
python3 test_all_tools.py

# Test individual tool
python3 AgentName/tools/ToolName.py

# Test with environment variables
PYTHONPATH=/workspace python3 AgentName/tools/ToolName.py

# Check environment setup
cat .env | grep -v "^#" | grep "="

# View test results
cat TOOL_TEST_RESULTS.md | less

# View quick reference
cat TOOL_TEST_QUICKREF.md
```

---

## Progress Tracking

| Phase | Tasks | Started | Completed | Status |
|-------|-------|---------|-----------|--------|
| Phase 1: Environment | 8 | [ ] | [ ] | Not Started |
| Phase 2: Test Blocks | 7 | [ ] | [ ] | Not Started |
| Phase 3: Mock Modes | 8 | [ ] | [ ] | Not Started |
| Phase 4: Fix Issues | 4 | [ ] | [ ] | Not Started |
| Phase 5: Documentation | 3 | [ ] | [ ] | Not Started |

---

## Notes & Issues

Use this space to track any issues or notes during implementation:

```
Date: _____________
Issue: ____________________________________________________________
Resolution: _______________________________________________________

Date: _____________
Issue: ____________________________________________________________
Resolution: _______________________________________________________

Date: _____________
Issue: ____________________________________________________________
Resolution: _______________________________________________________
```

---

## Success Criteria

### Phase 1 Complete When:
- ✅ `.env` file created with all credentials
- ✅ Test pass rate > 50%
- ✅ No NEEDS_CONFIG errors for configured APIs

### Phase 2 Complete When:
- ✅ All 7 skipped tools have test blocks
- ✅ All test blocks execute successfully
- ✅ Skipped count = 0

### Phase 3 Complete When:
- ✅ Mock modes implemented in 5+ tools
- ✅ All tools testable without credentials
- ✅ Average independence score > 7.0

### Phases 4-5 Complete When:
- ✅ Test pass rate > 85%
- ✅ All critical tools production-ready
- ✅ Documentation complete

---

**Last Updated:** September 14, 2026  
**Current Status:** Phase 1 Pending  
**Next Action:** Configure environment variables in `.env`
