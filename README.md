# Manifest AI

Standalone **Meta digital marketing company**. The founder talks to the CEO. Employees research, write, design, check policy, and execute on Facebook after explicit go-live.

This repository is the company operating system (**Agency Swarm v1.x**). Framework install, Learn More docs, and migration notes: `AGENCY_SWARM_SETUP.md` and `../docs/adr/ADR-011-agency-swarm-v1-framework.md`. Founders do not clone it. Founders sign the paid pilot and work in Slack. See `../SMB_ONBOARDING_GUIDE.md` and `../docs/commercial/PILOT_SOW_AND_INVOICE.md`.

**Company lock (ADR-010):** this Meta ads firm is Company One. Do not sell a seven-seat C-suite, $499 campaign packs, lead forms, lookalikes, or Instagram auto-publish. Honest scope lives in `agency_manifesto.md`.

### Company structure

- **CEO** — Chief Growth Strategist (only founder-facing voice)
- **Employees** — Market Intelligence, Cultural Intelligence, Search Visibility, Copy, Landing/CRO, Creative, Policy, Approval, Media Operations, Campaign Operations, Community, Performance

Paid execution today: **traffic** campaigns (website / link clicks / country geo), created paused. Organic: Facebook Page photo and text/link posts.

## Operator: Facebook App Setup

To let Media Operations post and build ads, set up a Facebook app and credentials. This is operator work, not founder onboarding.


1. **Create Your Facebook App**:
   - Visit the [Facebook for Developers](https://developers.facebook.com/) site and log in.
   - Click on "My Apps" and select "Create App".
   - Choose "Business" as your app type and provide a name for your app.
   - Follow the prompts to complete the app creation process.

2. **Add the Marketing API**:
   - In your app dashboard, find the "Add a Product" section and select "Marketing API".
   - Click "Set Up" to add the Marketing API to your app.

3. **Configure App Settings**:
   - Navigate to "Settings" > "Basic" in your app dashboard.
   - Note your "App ID" and "App Secret" for later use.
   - Add your app domain, privacy policy URL, and other required details.

4. **Obtain Access Token**:
   - Go to the [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/).
   - Select your app from the "Application" dropdown.
   - Click "Generate Access Token" and grant the necessary permissions for ad management.
   - Copy the generated access token for use in your agency setup.

5. **Update Environment File**:
   - Copy `.env.example` to `.env` and fill in your actual values, OR
   - Create an `.env` file in your project directory and add the required environment variables.

    ```env
    OPENAI_API_KEY=your_openai_api_key
    FACEBOOK_APP_ID=your_app_id
    FACEBOOK_APP_SECRET=your_app_secret
    FACEBOOK_ACCESS_TOKEN=your_access_token
    FACEBOOK_AD_ACCOUNT_ID=your_ad_account_id
    FACEBOOK_PAGE_ID=your_page_id
    ```
   
   **Important**: Variable names in `.env` must exactly match what the code expects. See `CONFIG_REFERENCE.md` for a complete mapping of variable names and their usage.

6. **Install Facebook Business SDK** (if required by your tools):
   - Run the following command to install the SDK:

   