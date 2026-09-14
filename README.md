# Manifest AI (ManifestMeta)

Manifest AI is an architecture-first, test-led multi-agent system built on the
[Agency Swarm](https://agency-swarm.ai) framework. A constellation of specialist agents plans and
executes Facebook / Meta marketing campaigns behind a single client-facing strategist, with
governance guardrails enforced at every stage.

## Agency structure

The agency is composed of nine agents wired into an eight-stage pipeline. Only the Chief Growth
Strategist talks to the client; every other agent runs as background delegation.

| Stage | Agent (`name=`) | Role |
| --- | --- | --- |
| 1 Intake | Chief Growth Strategist (`MetaMarkCEO`) | Client lead / orchestrator |
| 2 Research | Market Intelligence Director (`ResearchAgent`) | Competitor + audience research |
| — | Search & Answer Visibility Director (`SearchVisibilityAgent`) | SEO / AEO / GEO strategy |
| 3 Copy | Senior Conversion Copywriter (`AdCopyAgent`) | Ad copy |
| 4 Creative | Creative Director (`ImageCreatorAgent`) | DALL·E campaign visuals |
| 5 Policy (gate) | Facebook Policy Compliance Officer (`FacebookPolicyAgent`) | Meta policy review |
| 6 Approval (gate) | Client Approval Manager (`ClientApprovalAgent`) | Final client sign-off |
| 7 Execution | Media Operations Director (`FacebookManagerAgent`) | Meta publishing / paid ops |
| 8 Tracking | Campaign Operations Director (`CampaignOpsAgent`) | Schedule, budget, reporting |

Communication flows are defined in [`agency.py`](agency.py). Paid publishing is reachable only via
`Client Approval Manager → Media Operations Director` — there is no direct CEO → Media edge.

## Running the apps

Install dependencies (see also [`.cursor/environment.json`](.cursor/environment.json)):

```bash
pip install -r requirements.txt fastapi "uvicorn[standard]" websockets gradio pytest
```

Then launch one of the entry points:

- `python ui_entry.py` — Gradio chat UI (default http://127.0.0.1:7860)
- `python agency.py` — terminal / Gradio demo
- `python web_bridge.py` — FastAPI + WebSocket bridge serving the Manifest AI web UI
  (http://127.0.0.1:8000); see [docs/README-BRIDGE.md](docs/README-BRIDGE.md)

All entry points require `OPENAI_API_KEY`. Runs default to the `staging` safety profile
(`MANIFEST_AI_ENV=staging`), which blocks live external mutations — see [docs/STAGING.md](docs/STAGING.md).

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
OPENAI_API_KEY=your_openai_api_key
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_AD_ACCOUNT_ID=your_ad_account_id
FACEBOOK_PAGE_ID=your_page_id
SCRAPE_CREATORS_API_KEY=your_scrapecreators_key
```

Variable names must match exactly what the code reads via `os.getenv(...)`. See
[docs/CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md) for the complete mapping. `OPENAI_API_KEY` is
required; the `FACEBOOK_*` and `SCRAPE_CREATORS_API_KEY` values are only needed for the execution
and live-research stages.

### Facebook Marketing API setup

To exercise the Media Operations stage you need a Facebook app with the Marketing API:

1. Create a Business app at [Facebook for Developers](https://developers.facebook.com/).
2. Add the **Marketing API** product to the app.
3. From **Settings → Basic**, copy the **App ID** and **App Secret**.
4. Generate an access token with ad-management permissions via the
   [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
5. Find your Ad Account ID (format `act_123456789`) in Ads Manager and your Page ID in Page settings.
6. Put all values in `.env` as shown above. The Facebook Business SDK is installed via
   `requirements.txt` (`facebook_business`).

## Documentation

- [docs/AGENCY_SWARM_SETUP.md](docs/AGENCY_SWARM_SETUP.md) — Agency Swarm framework references
- [docs/CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md) — environment variable mapping
- [docs/GUARDRAILS.md](docs/GUARDRAILS.md) — enforced governance invariants
- [docs/STAGING.md](docs/STAGING.md) — staging vs production safety profiles
- [docs/GO-LIVE-RUNBOOK.md](docs/GO-LIVE-RUNBOOK.md) — production go-live procedure
- [docs/README-BRIDGE.md](docs/README-BRIDGE.md) — live web bridge architecture
- [docs/TESTING.md](docs/TESTING.md) — test suite and how to run it
- [docs/adr/](docs/adr/) — Architecture Decision Records
- [agency_manifesto.md](agency_manifesto.md) — shared agency mission and context
```
