# MetaMarkAgency Tool Testing Report

**Generated:** 2026-09-14 22:59:09

## Executive Summary

- **Total Tools Tested:** 29
- **Passed:** 6 (20.7%)
- **Failed:** 9 (31.0%)
- **Needs Configuration:** 7 (24.1%)
- **Skipped:** 7 (24.1%)
- **Average Independence Score:** 5.3/10

## Tool Status Overview

| Agent | Tool | Status | Independence | Dependencies |
|-------|------|--------|--------------|--------------|
| AdCopyAgent | AdCopyGenerator | ❌ FAIL | 4/10 | OPENAI_API_KEY, Shared State |
| ClientApprovalAgent | ClientApprovalChecklist | ✅ PASS | 10/10 | None |
| FacebookManagerAgent | AdCampaignStarter | ⚠️ NEEDS_CONFIG | 5/10 | Facebook API, Shared State |
| FacebookManagerAgent | AdCreator | ❌ FAIL | 3/10 | Facebook API, Shared State |
| FacebookManagerAgent | AdPerformanceMonitor | ❌ FAIL | 5/10 | Facebook API |
| FacebookManagerAgent | AdSetCreator | ❌ FAIL | 3/10 | Facebook API, Shared State |
| FacebookManagerAgent | FacebookPagePostPublisher | ❌ FAIL | 3/10 | Facebook API, Shared State |
| FacebookManagerAgent | FacebookPhotoPostPublisher | ❌ FAIL | 5/10 | Shared State |
| FacebookManagerAgent | FacebookTokenDiagnostics | ⚠️ NEEDS_CONFIG | 7/10 | Facebook API |
| FacebookPolicyAgent | FacebookPolicyChecklist | ✅ PASS | 10/10 | None |
| ImageCreatorAgent | ImageGenerator | ❌ FAIL | 4/10 | OPENAI_API_KEY, Shared State |
| ResearchAgent | AdLibraryPatternAnalyzer | ✅ PASS | 10/10 | None |
| ResearchAgent | CompetitorResearchPlanBuilder | ✅ PASS | 10/10 | None |
| ResearchAgent | MetaAdLibraryKeywordSearch | ❌ FAIL | 7/10 | None |
| ResearchAgent | MetaAdLibraryPageSearch | ❌ FAIL | 7/10 | None |
| ResearchAgent | ScrapeCreatorsFacebookAdDetails | ⚠️ NEEDS_CONFIG | 9/10 | None |
| ResearchAgent | ScrapeCreatorsFacebookAdSearch | ⚠️ NEEDS_CONFIG | 9/10 | None |
| ResearchAgent | ScrapeCreatorsFacebookAdTranscript | ⚠️ NEEDS_CONFIG | 9/10 | None |
| ResearchAgent | ScrapeCreatorsFacebookCompanyAds | ⚠️ NEEDS_CONFIG | 9/10 | None |
| ResearchAgent | ScrapeCreatorsFacebookCompanySearch | ⚠️ NEEDS_CONFIG | 9/10 | None |
| SearchVisibilityAgent | ContentVisibilityChecklist | ✅ PASS | 8/10 | Shared State |
| SearchVisibilityAgent | SearchVisibilityBriefBuilder | ✅ PASS | 8/10 | Shared State |

## Detailed Test Results by Agent

### AdCopyAgent

**Status:** 0/1 tools passing


#### AdCopyGenerator

- **Status:** FAIL
- **Independence Score:** 4/10
- **Execution Time:** 2.05s
- **Dependencies:** OPENAI_API_KEY, Shared State
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
{"error": "Copy generation failed: AuthenticationError"}

```

### CampaignOpsAgent

**Status:** 0/0 tools passing


### ClientApprovalAgent

**Status:** 1/1 tools passing


#### ClientApprovalChecklist

- **Status:** PASS
- **Independence Score:** 10/10
- **Execution Time:** 1.49s
- **Dependencies:** None
- **Notes:**
  - Tool executed successfully

**Output:**
```
{'outcome': 'approved', 'approved_for_media_operations': True, 'missing_approvals': [], 'approval_notes': 'Client approved final organic Facebook post package.', 'next_step': 'Send the approved final package to Media Operations Director.'}

```

### FacebookManagerAgent

**Status:** 0/7 tools passing


#### AdCampaignStarter

- **Status:** NEEDS_CONFIG
- **Independence Score:** 5/10
- **Execution Time:** 1.48s
- **Dependencies:** Facebook API, Shared State
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/FacebookManagerAgent/tools/AdCampaignStarter.py", line 73, in <module>
    print(tool.run())
          ^^^^^^^^^^
  File "/workspace/FacebookManagerAgent/tools/AdCampaignStarter.py", line 36, in run
    initialize_business_sdk()
  File "/workspace/FacebookManagerAgent/facebook_auth.py", line 19, in initialize_business_sdk
    token = (access_token or get_required_env("FACEBOOK_ACCESS_TOKEN")).strip()
                             ^^^^^^^^^^^^^... (truncated)
```

#### AdCreator

- **Status:** FAIL
- **Independence Score:** 3/10
- **Execution Time:** 1.45s
- **Dependencies:** Facebook API, Shared State
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
Error creating ad: Missing FACEBOOK_ACCESS_TOKEN in environment.

```

#### AdPerformanceMonitor

- **Status:** FAIL
- **Independence Score:** 5/10
- **Execution Time:** 1.47s
- **Dependencies:** Facebook API
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
Error accessing ad performance metrics: Missing FACEBOOK_ACCESS_TOKEN in environment.

```

#### AdSetCreator

- **Status:** FAIL
- **Independence Score:** 3/10
- **Execution Time:** 1.48s
- **Dependencies:** Facebook API, Shared State
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
Error creating ad set: Missing FACEBOOK_ACCESS_TOKEN in environment.

```

#### FacebookPagePostPublisher

- **Status:** FAIL
- **Independence Score:** 3/10
- **Execution Time:** 1.45s
- **Dependencies:** Facebook API, Shared State
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
Error publishing page post: Missing FACEBOOK_PAGE_ID in environment.

```

#### FacebookPhotoPostPublisher

- **Status:** FAIL
- **Independence Score:** 5/10
- **Execution Time:** 1.41s
- **Dependencies:** Shared State
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
Error publishing photo post: Missing FACEBOOK_PAGE_ID in environment.

```

#### FacebookTokenDiagnostics

- **Status:** NEEDS_CONFIG
- **Independence Score:** 7/10
- **Execution Time:** 1.43s
- **Dependencies:** Facebook API
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/FacebookManagerAgent/tools/FacebookTokenDiagnostics.py", line 115, in <module>
    print(tool.run())
          ^^^^^^^^^^
  File "/workspace/FacebookManagerAgent/tools/FacebookTokenDiagnostics.py", line 39, in run
    app_id = self._env("FACEBOOK_APP_ID")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/FacebookManagerAgent/tools/FacebookTokenDiagnostics.py", line 25, in _env
    raise ValueError(f"Missing {key} in environment.")
... (truncated)
```

### FacebookPolicyAgent

**Status:** 1/1 tools passing


#### FacebookPolicyChecklist

- **Status:** PASS
- **Independence Score:** 10/10
- **Execution Time:** 1.53s
- **Dependencies:** None
- **Notes:**
  - Tool executed successfully

**Output:**
```
{'outcome': 'approved', 'campaign_type': 'facebook_page_post', 'concerns': [], 'reference': 'FacebookPolicyAgent/files/facebook_policy_reference_file-Xn42Zik8DqZd4Y9MNsxrJp.md', 'next_step': 'Send approval status and execution constraints to Media Operations Director.'}

```

### ImageCreatorAgent

**Status:** 0/1 tools passing


#### ImageGenerator

- **Status:** FAIL
- **Independence Score:** 4/10
- **Execution Time:** 1.83s
- **Dependencies:** OPENAI_API_KEY, Shared State
- **Notes:**
  - Tool execution failed

**Error:**
```
Traceback (most recent call last):
  File "/workspace/ImageCreatorAgent/tools/ImageGenerator.py", line 216, in <module>
    result = tool.run()
             ^^^^^^^^^^
  File "/workspace/ImageCreatorAgent/tools/ImageGenerator.py", line 173, in run
    option = self._generate_single(client, prompt, index)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/ImageCreatorAgent/tools/ImageGenerator.py", line 88, in _generate_single
    response = client.images.generate(
     ... (truncated)
```

### ResearchAgent

**Status:** 2/9 tools passing


#### AdLibraryPatternAnalyzer

- **Status:** PASS
- **Independence Score:** 10/10
- **Execution Time:** 1.61s
- **Dependencies:** None
- **Notes:**
  - Tool executed successfully

**Output:**
```
{'ads_analyzed': 1, 'top_pages': [('Example Brand', 1)], 'top_platforms': [('facebook', 1), ('instagram', 1)], 'repeated_words': [('save', 1), ('time', 1), ('with', 1), ('simple', 1), ('automation', 1), ('book', 1), ('demo', 1), ('today', 1)], 'examples': [{'page_name': 'Example Brand', 'ad_snapshot_url': 'https://example.com', 'sample_body': ['Save time with simple automation.'], 'sample_title': ['Book a demo today'], 'ad_archive_id': None, 'display_format': None, 'cta_text': None}], 'client_bu... (truncated)
```

#### CompetitorResearchPlanBuilder

- **Status:** PASS
- **Independence Score:** 10/10
- **Execution Time:** 1.49s
- **Dependencies:** None
- **Notes:**
  - Tool executed successfully

**Output:**
```
{'client_business': 'local AI automation agency for small businesses', 'target_customer': 'small business owners who need leads and better marketing', 'geography': 'United States', 'known_competitors': ['Example Competitor'], 'recommended_keyword_queries': ['Example Competitor', 'local', 'automation', 'agency', 'small', 'businesses', 'business', 'owners', 'need'], 'recommended_steps': ['Search known competitor names first.', 'Search category and offer keywords next.', 'Collect active ads and rep... (truncated)
```

#### MetaAdLibraryKeywordSearch

- **Status:** FAIL
- **Independence Score:** 7/10
- **Execution Time:** 1.54s
- **Dependencies:** None
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
{"ok": false, "error": "Missing Meta Ad Library token. Set META_AD_LIBRARY_ACCESS_TOKEN or Facebook_ad_library_tolken in environment.", "next_action": "Set META_AD_LIBRARY_ACCESS_TOKEN only if direct Meta Ad Library fallback access is needed. Use Scrape Creators tools as the primary path."}

```

#### MetaAdLibraryPageSearch

- **Status:** FAIL
- **Independence Score:** 7/10
- **Execution Time:** 1.48s
- **Dependencies:** None
- **Notes:**
  - Tool ran but returned error in output

**Output:**
```
{"ok": false, "error": "Missing Meta Ad Library token. Set META_AD_LIBRARY_ACCESS_TOKEN or Facebook_ad_library_tolken in environment.", "next_action": "Set META_AD_LIBRARY_ACCESS_TOKEN only if direct Meta Ad Library fallback access is needed. Use Scrape Creators tools as the primary path."}

```

#### ScrapeCreatorsFacebookAdDetails

- **Status:** NEEDS_CONFIG
- **Independence Score:** 9/10
- **Execution Time:** 1.47s
- **Dependencies:** None
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookAdDetails.py", line 52, in <module>
    print(json.dumps(tool.run(), ensure_ascii=True))
                     ^^^^^^^^^^
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookAdDetails.py", line 38, in run
    return scrape_creators_get(
           ^^^^^^^^^^^^^^^^^^^^
  File "/workspace/ResearchAgent/scrape_creators_api.py", line 34, in scrape_creators_get
    headers={"x-api-key": get_api_key... (truncated)
```

#### ScrapeCreatorsFacebookAdSearch

- **Status:** NEEDS_CONFIG
- **Independence Score:** 9/10
- **Execution Time:** 1.57s
- **Dependencies:** None
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookAdSearch.py", line 86, in <module>
    print(json.dumps(tool.run(), ensure_ascii=True))
                     ^^^^^^^^^^
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookAdSearch.py", line 64, in run
    return scrape_creators_get(
           ^^^^^^^^^^^^^^^^^^^^
  File "/workspace/ResearchAgent/scrape_creators_api.py", line 34, in scrape_creators_get
    headers={"x-api-key": get_api_key()... (truncated)
```

#### ScrapeCreatorsFacebookAdTranscript

- **Status:** NEEDS_CONFIG
- **Independence Score:** 9/10
- **Execution Time:** 1.59s
- **Dependencies:** None
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookAdTranscript.py", line 47, in <module>
    print(json.dumps(tool.run(), ensure_ascii=True))
                     ^^^^^^^^^^
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookAdTranscript.py", line 34, in run
    return scrape_creators_get(
           ^^^^^^^^^^^^^^^^^^^^
  File "/workspace/ResearchAgent/scrape_creators_api.py", line 34, in scrape_creators_get
    headers={"x-api-key": get_a... (truncated)
```

#### ScrapeCreatorsFacebookCompanyAds

- **Status:** NEEDS_CONFIG
- **Independence Score:** 9/10
- **Execution Time:** 1.53s
- **Dependencies:** None
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookCompanyAds.py", line 92, in <module>
    print(json.dumps(tool.run(), ensure_ascii=True))
                     ^^^^^^^^^^
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookCompanyAds.py", line 70, in run
    return scrape_creators_get(
           ^^^^^^^^^^^^^^^^^^^^
  File "/workspace/ResearchAgent/scrape_creators_api.py", line 34, in scrape_creators_get
    headers={"x-api-key": get_api_k... (truncated)
```

#### ScrapeCreatorsFacebookCompanySearch

- **Status:** NEEDS_CONFIG
- **Independence Score:** 9/10
- **Execution Time:** 1.50s
- **Dependencies:** None
- **Notes:**
  - Missing environment variables or configuration

**Error:**
```
Traceback (most recent call last):
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookCompanySearch.py", line 34, in <module>
    print(json.dumps(tool.run(), ensure_ascii=True))
                     ^^^^^^^^^^
  File "/workspace/ResearchAgent/tools/ScrapeCreatorsFacebookCompanySearch.py", line 24, in run
    return scrape_creators_get(
           ^^^^^^^^^^^^^^^^^^^^
  File "/workspace/ResearchAgent/scrape_creators_api.py", line 34, in scrape_creators_get
    headers={"x-api-key": get... (truncated)
```

### SearchVisibilityAgent

**Status:** 2/2 tools passing


#### ContentVisibilityChecklist

- **Status:** PASS
- **Independence Score:** 8/10
- **Execution Time:** 1.48s
- **Dependencies:** Shared State
- **Notes:**
  - Tool executed successfully

**Output:**
```
{'outcome': 'revise', 'score': 67, 'passed': 6, 'total': 9, 'content_type': 'seo_blog', 'checks': [{'pillar': 'seo', 'criterion': 'primary_keyword_in_title', 'pass': False, 'note': 'Primary keyword should appear naturally in the title when provided.'}, {'pillar': 'seo', 'criterion': 'primary_keyword_in_body', 'pass': False, 'note': 'Primary keyword should appear in the opening and body without stuffing.'}, {'pillar': 'seo', 'criterion': 'structured_headers', 'pass': True, 'note': 'Long-form draf... (truncated)
```

#### SearchVisibilityBriefBuilder

- **Status:** PASS
- **Independence Score:** 8/10
- **Execution Time:** 1.48s
- **Dependencies:** Shared State
- **Notes:**
  - Tool executed successfully

**Output:**
```
{'role': 'search_visibility_strategy_brief', 'business_or_category': 'Med spa', 'topic_or_offer': 'Botox for first-time patients', 'audience': 'Women 30-55 in North Dallas', 'geography': 'Plano, Frisco, Allen', 'campaign_goal': 'booked consultations', 'seo': {'primary_keyword': 'first time botox what to expect', 'secondary_keywords': ['botox consultation', 'botox recovery', 'med spa near me'], 'search_intent': 'informational', 'content_format': 'how-to with FAQ', 'on_page_notes': 'Consult Search... (truncated)
```

## Dependencies Analysis

| Dependency | Tool Count | Tools |
|------------|------------|-------|
| Shared State | 9 | AdCopyAgent/AdCopyGenerator, ImageCreatorAgent/ImageGenerator, FacebookManagerAgent/AdCampaignStarter... |
| Facebook API | 6 | FacebookManagerAgent/AdCampaignStarter, FacebookManagerAgent/AdCreator, FacebookManagerAgent/AdPerformanceMonitor... |
| OPENAI_API_KEY | 2 | AdCopyAgent/AdCopyGenerator, ImageCreatorAgent/ImageGenerator |

## Recommendations

### Configuration Required (7 tools)

1. **Environment Variables**: Ensure `.env` file contains:
   - `OPENAI_API_KEY` for OpenAI-dependent tools
   - `FACEBOOK_ACCESS_TOKEN`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `FACEBOOK_PAGE_ID` for Facebook API tools

2. **Missing Dependencies**: Run `pip install -r requirements.txt` if any import errors occurred

### Failed Tools (9 tools)

Tools that failed require investigation:
- **AdCopyAgent/AdCopyGenerator**: Tool ran but returned error in output
- **ImageCreatorAgent/ImageGenerator**: Tool execution failed
- **FacebookManagerAgent/AdCreator**: Tool ran but returned error in output
- **FacebookManagerAgent/AdPerformanceMonitor**: Tool ran but returned error in output
- **FacebookManagerAgent/AdSetCreator**: Tool ran but returned error in output
- **FacebookManagerAgent/FacebookPagePostPublisher**: Tool ran but returned error in output
- **FacebookManagerAgent/FacebookPhotoPostPublisher**: Tool ran but returned error in output
- **ResearchAgent/MetaAdLibraryKeywordSearch**: Tool ran but returned error in output
- **ResearchAgent/MetaAdLibraryPageSearch**: Tool ran but returned error in output

### Tool Independence Improvements

Tools with low independence scores (< 7/10):
- **FacebookManagerAgent/AdCreator** (3/10)
  - Dependencies: Facebook API, Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **FacebookManagerAgent/AdSetCreator** (3/10)
  - Dependencies: Facebook API, Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **FacebookManagerAgent/FacebookPagePostPublisher** (3/10)
  - Dependencies: Facebook API, Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **AdCopyAgent/AdCopyGenerator** (4/10)
  - Dependencies: OPENAI_API_KEY, Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **ImageCreatorAgent/ImageGenerator** (4/10)
  - Dependencies: OPENAI_API_KEY, Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **FacebookManagerAgent/AdCampaignStarter** (5/10)
  - Dependencies: Facebook API, Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **FacebookManagerAgent/AdPerformanceMonitor** (5/10)
  - Dependencies: Facebook API
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies
- **FacebookManagerAgent/FacebookPhotoPostPublisher** (5/10)
  - Dependencies: Shared State
  - Recommendation: Consider adding mock mode or better error handling for missing dependencies