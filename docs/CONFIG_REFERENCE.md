# Configuration Reference

This document maps all environment variables used in the codebase, showing their names, where they're used, and what they're called in the code.

## Environment Variables Mapping

### OpenAI Configuration

| .env Variable Name | Code Variable Name | Used In | Purpose |
|-------------------|-------------------|---------|---------|
| `OPENAI_API_KEY` | `openai.api_key` | `ImageCreatorAgent/tools/ImageGenerator.py` | API key for OpenAI services (DALL-E, GPT) |

### Facebook Configuration

| .env Variable Name | Code Variable Name | Used In | Purpose |
|-------------------|-------------------|---------|---------|
| `FACEBOOK_APP_ID` | `app_id` | All Facebook tools: `AdCampaignStarter.py`, `AdSetCreator.py`, `AdCreator.py`, `AdPerformanceMonitor.py` | Facebook App ID for API authentication |
| `FACEBOOK_APP_SECRET` | `app_secret` | All Facebook tools: `AdCampaignStarter.py`, `AdSetCreator.py`, `AdCreator.py`, `AdPerformanceMonitor.py` | Facebook App Secret for API authentication |
| `FACEBOOK_ACCESS_TOKEN` | `access_token` | All Facebook tools: `AdCampaignStarter.py`, `AdSetCreator.py`, `AdCreator.py`, `AdPerformanceMonitor.py` | Facebook Access Token for API authorization |
| `FACEBOOK_AD_ACCOUNT_ID` | `ad_account_id` | All Facebook tools: `AdCampaignStarter.py`, `AdSetCreator.py`, `AdCreator.py`, `AdPerformanceMonitor.py` | Facebook Ad Account ID where campaigns are created |
| `FACEBOOK_PAGE_ID` | `page_id` (via `os.getenv()`) | `FacebookManagerAgent/tools/AdCreator.py` | Facebook Page ID where ads will be posted |

## Complete .env File Structure

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key

# Facebook API Configuration
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_AD_ACCOUNT_ID=your_ad_account_id
FACEBOOK_PAGE_ID=your_page_id
```

## Naming Convention

**Important**: All Facebook-related environment variables use the `FACEBOOK_` prefix in the `.env` file. This matches the codebase usage:

- ✅ `FACEBOOK_APP_ID` (correct - matches code)
- ❌ `FB_APP_ID` (incorrect - doesn't match code)
- ❌ `APP_ID` (incorrect - too generic)

## Code Usage Pattern

In the code, these variables are typically loaded like this:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Facebook credentials
access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
app_id = os.getenv('FACEBOOK_APP_ID')
app_secret = os.getenv('FACEBOOK_APP_SECRET')
ad_account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')
page_id = os.getenv('FACEBOOK_PAGE_ID')

# OpenAI credentials
openai.api_key = os.getenv("OPENAI_API_KEY")
```

## Quick Reference

**For Developers**: When you see `os.getenv('FACEBOOK_APP_ID')` in the code, it's looking for `FACEBOOK_APP_ID` in your `.env` file.

**Consistency Rule**: The name in `.env` must **exactly match** what's inside `os.getenv('...')` in the code.





