# Manifest AI — Go-Live Runbook (plain English)

This is the step-by-step to turn Manifest AI from a working prototype into a real service
your clients log into and use. No jargon. Follow it top to bottom.

There are **three machines** in the finished system:
1. **Your clients' browsers** — they open the web app (the file we built).
2. **A always-on server** — runs your Python agency + the bridge. This is the part that
   actually talks to OpenAI and Facebook.
3. **Facebook + Google + OpenAI** — the outside services your server calls.

You already have #1 (the UI) and the agency code for #2. This runbook gets #2 hosted and
connects #3.

---

## The honest order of operations

Do these in order. Each unlocks the next. Rough time on the right (human time; the coding
parts are minutes with Claude Code).

1. **Host the backend** so it has a public address. (~1 hour)
2. **Add your API keys** (OpenAI + Facebook). (~30 min, plus Meta review wait)
3. **Turn on Google sign-in** for clients. (~45 min)
4. **Point the web app at your server** and deploy it. (~20 min)
5. **Meta App Review** so it can post to client ad accounts. (form is ~1 hour; **Meta takes days to weeks** to approve)

The first 4 can be done in an afternoon. #5 is the long pole — start it early because Meta's
approval is out of your hands.

---

## Step 1 — Host the backend (the always-on server)

Your agency is Python. It needs to run somewhere that never sleeps. Easiest managed option
(no servers to babysit): **Render** or **Railway**. Both deploy straight from a GitHub repo.

**Recommended: Render (free tier to start, ~$7/mo for always-on).**

1. Push your agency repo (the one with `agency.py` + `web_bridge.py`) to GitHub.
2. Go to render.com → New → **Web Service** → connect that repo.
3. Settings:
   - **Build command:** `pip install -r requirements.txt fastapi "uvicorn[standard]" websockets`
   - **Start command:** `python web_bridge.py`
   - **Instance type:** Starter ($7/mo — the free tier sleeps after 15 min, which drops
     client sessions; pay the $7 for real use).
4. Deploy. Render gives you a public address like `https://manifest-ai.onrender.com`.
5. Your WebSocket address is the same with `wss://` and `/ws`:
   `wss://manifest-ai.onrender.com/ws`. Write it down — the web app needs it.

> One change for hosting: in `web_bridge.py`, the last line currently binds to
> `127.0.0.1` (your laptop only). For a host it must bind to `0.0.0.0` and use the host's
> port. Claude Code can make this one-line change — tell it: "make web_bridge.py read PORT
> from the environment and bind 0.0.0.0 for Render."

---

## Step 2 — Add your API keys (server-side only)

Keys live on the **server**, never in the web app. On Render: your service →
**Environment** → add these (your agency's `.env.example` lists the exact names):

- `OPENAI_API_KEY` — from platform.openai.com. This powers the creative images.
- `FACEBOOK_ACCESS_TOKEN` / `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` / `FACEBOOK_AD_ACCOUNT_ID` /
  `FACEBOOK_PAGE_ID` — from your Meta app (Step 5).

Redeploy after adding them. Test: open `https://your-address.onrender.com` — you should see
the bridge's "running" JSON. That means the server is alive.

---

## Step 3 — Google sign-in for clients

The web app shows "Continue with Google." To make it real:

1. Go to console.cloud.google.com → **APIs & Services → Credentials**.
2. **Create OAuth client ID** → type **Web application**.
3. **Authorized JavaScript origins:** your web app's address (from Step 4),
   e.g. `https://app.manifestai.com`.
4. **Authorized redirect URI:** `https://your-backend-address/auth/google/callback`.
5. Copy the **Client ID** and **Client secret**. The secret goes on the server (Step 2 env
   vars); the Client ID goes in the web app's sign-in button.

> The button is wired and styled. Claude Code connects it to Google with the official
> "Sign in with Google" library — tell it: "wire the Continue-with-Google button to real
> Google OAuth using client ID X, and verify the token on the server."

---

## Step 4 — Deploy the web app

The web app is one self-contained file. Two easy options:

- **Simplest:** let the backend serve it. `web_bridge.py` already serves `web/index.html`.
  Put the latest UI there and clients just visit your backend address. Done.
- **Nicer (own domain):** drop the HTML on **Netlify** or **Vercel** (drag-and-drop the
  file), point a domain like `app.manifestai.com` at it. Then set the app's bridge address
  to your `wss://...` server from Step 1.

Either way, set the connection address once so clients never see a connect box — Claude Code
can hardcode `wss://your-backend/ws` and auto-connect on load, and hide the connect panel for
clients (keep it only for you/admin).

---

## Step 5 — Meta App Review (the long pole — start now)

To post ads to a **client's** Facebook account, Meta must approve your app for the
`ads_management` and `pages_manage_posts` permissions. This is a review process, not a code
change.

1. developers.facebook.com → your app → **App Review → Permissions and Features**.
2. Request `ads_management`, `pages_show_list`, `pages_manage_posts`, `business_management`.
3. Record a screen capture showing how your app uses each (your walkthrough demo is perfect
   for this).
4. Submit. **Meta typically takes several days to a few weeks.** Until approved, you can only
   post to ad accounts you own (great for piloting with your own/first client account in
   "managed" mode).

> While you wait: run in **managed mode** — you connect your own Meta business account, onboard
> the first client there, and they brief + approve in the UI. That's exactly the hybrid model
> you picked, and it needs **no** Meta review to start.

---

## Multi-client (when you're past the pilot)

For many self-serve clients each using *their own* ad account, two additions (real backend
work, but well-trodden):
- **Database** (Postgres on Render, ~$7/mo) to store client accounts, businesses, and their
  Meta tokens.
- **"Connect Facebook" OAuth** so each client authorizes their own ad account. The button is
  already in onboarding; Claude Code connects it to Meta's OAuth and stores the returned token
  per client.

Start in managed mode (one account, you oversee). Add the database + per-client OAuth only
when you have clients waiting.

---

## What to hand Claude Code (in your repo)

Paste this:

> Make this agency client-ready: (1) update web_bridge.py to bind 0.0.0.0 and read PORT from
> env for Render; (2) wire the "Continue with Google" button to real Google OAuth (client ID
> from env) with server-side token verification; (3) wire the onboarding "Connect Facebook"
> button to Meta OAuth and store the per-client token; (4) add a Postgres model for
> clients/businesses/tokens; (5) auto-connect the UI to wss://<our-backend>/ws and hide the
> connect panel for non-admin users. Keep all agent, instruction, tool, and gate logic
> unchanged. Verify _probe_stream_item matches our installed agency_swarm version.

That one message covers every code change. Everything else above is account setup you do in
the Render / Google / Meta dashboards.

---

## Cost to run (rough, monthly)

- Backend host (Render Starter): ~$7
- Database (when multi-client): ~$7
- OpenAI image generation: usage-based (~$0.04 per image; a few dollars per campaign)
- Facebook ad spend: your clients' money, billed by Meta to their accounts
- Domain: ~$12/year

You can pilot the whole thing for under $15/month before any client ad spend.
