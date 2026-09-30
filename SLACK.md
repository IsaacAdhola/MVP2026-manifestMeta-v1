# Connect Manifest AI to Slack

Founders DM the bot or @mention it in a channel. They only talk to the CEO (Chief Growth Strategist). Research, copy, images, policy, approval, and Facebook posting stay inside the company.

This follows the current Slack developer docs: [docs.slack.dev](https://docs.slack.dev/), [Bolt for Python](https://docs.slack.dev/tools/bolt-python/getting-started), and [Slack CLI for Windows](https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli-for-windows/).

Local HTTP testing uses **Events API + ngrok** (`uvicorn app:api` on port 8000). Keep **Socket Mode off** while that is live. Slack App Home must allow Messages (not read-only) or Slack shows “Sending messages to this app has been turned off.”

## 1. Install the Slack CLI (Windows)

From PowerShell:

```powershell
irm https://downloads.slack-edge.com/slack-cli/install-windows.ps1 | iex
```

Close and reopen the terminal, then confirm:

```powershell
slack version
```

You should see Slack CLI v4.8.0 or later.

## 2. Log in to your workspace

```powershell
slack login
```

Open the printed URL, approve access, then paste the ticket/code back into the terminal.

## 3. Create the Slack app from this repo

Do **not** run `slack create`. This agency already has the Bolt app.

From `MVP2026-manifestMeta-master/`:

```powershell
slack run
```

When prompted, choose **Create a new app**, pick your workspace, and install it. The app settings come from `manifest.json` (same scopes as `slack_app_manifest.yaml`).

### Manual alternative

1. Open [https://api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From an app manifest**.
2. Pick your workspace.
3. Paste `manifest.json` (JSON tab) or `slack_app_manifest.yaml` (YAML tab).
4. Create the app.
5. **App Home** → **Messages Tab** On. Check **Allow users to send Slash commands and messages from the messages tab**. Messages tab must not be read-only.
6. **Socket Mode** → Off for ngrok HTTP. Event Subscriptions Request URL: `https://<ngrok-host>/slack/events`. Interactivity: `https://<ngrok-host>/slack/interactive`. Bot events: `app_mention`, `message.im`.
7. **OAuth & Permissions** → bot scopes include `chat:write`, `im:history`, `im:read`, `im:write`, `app_mentions:read`, `files:write` → **Reinstall to Workspace**. Copy `xoxb-...` as `SLACK_BOT_TOKEN`.
8. **Basic Information** → **Signing Secret**. Copy that as `SLACK_SIGNING_SECRET`.

## 4. Put the keys in `.env`

In `MVP2026-manifestMeta-master/.env`:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
```

Do not commit these values. For Cloud Functions, put the bot token, signing secret, and OpenAI key in Secret Manager instead of plaintext `.env`.

## 5. Run the bot

From `MVP2026-manifestMeta-master/`:

```powershell
pip install -r requirements.txt
python slack_app.py
```

Or with the Slack CLI (same Socket Mode app):

```powershell
slack run
```

When it prints `Agency ready. Connecting to Slack...`, open Slack, find **Manifest AI**, and send a DM: `Welcome, I need a Facebook campaign for my coffee shop.`

In a channel, invite the bot, then: `@Manifest AI we need three post options for this weekend.`

## How it behaves

- One client question at a time, same as Gradio.
- Copy options get **Option 1 / 2 / 3** buttons.
- Generated images upload into the Slack thread.
- The agency lock allows one campaign turn at a time so shared state does not collide.
- Paid campaigns still create **paused**. Organic posts still need policy + approval first.

## Later: public HTTP on Cloud Functions

Staging hosting is Cloud Functions for Firebase (`handle_slack_agent`). After that URL exists:

1. Turn Socket Mode off (or leave it on only for local `python slack_app.py`).
2. Event Subscriptions Request URL: `https://<function-url>/`
3. Interactivity Request URL: `https://<function-url>/`
4. Set Secret Manager: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `OPENAI_API_KEY`.

Local HTTP (ngrok or similar) still works:

```powershell
python slack_app.py --http --port 3000
```

You still need `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`. You can omit `SLACK_APP_TOKEN`.

## Docker (HTTP on port 8000)

From `MVP2026-manifestMeta-master/`:

```powershell
docker compose up --build
```

Or:

```powershell
docker build -t metamark-agency:local .
docker run --rm -p 8000:8000 --env-file .env metamark-agency:local
```

- Health: `http://localhost:8000/health`
- Slack Events Request URL: `https://<public-host>/slack/events`
- Interactivity Request URL: `https://<public-host>/slack/interactive`

Pass tokens at runtime. The image does not copy `.env` or Firebase key files.
