# Manifest AI — Live Web Bridge (v2, reconciled to the real codebase)

Connects your **ManifestMeta** agency (Agency Swarm) to the **Manifest AI** web experience over a
WebSocket. It does **not** change any agent, instruction, tool, flow, or governance gate. It only
*observes and forwards* what the real system produces.

## What the front end mirrors (verified against your repo)

**8 agents — exact `name=` strings, mapped 1:1 to the constellation:**
- Chief Growth Strategist (MetaMarkCEO) — client lead / orchestrator, the only agent you talk to
- Market Intelligence Director (ResearchAgent) — Stage 2
- Senior Conversion Copywriter (AdCopyAgent) — Stage 3
- Creative Director (ImageCreatorAgent) — Stage 4
- Facebook Policy Compliance Officer (FacebookPolicyAgent) — Stage 5 **gate**
- Client Approval Manager (ClientApprovalAgent) — Stage 6 **gate**
- Media Operations Director (FacebookManagerAgent) — Stage 7 Meta execution
- Campaign Operations Director (CampaignOpsAgent) — Stage 8 tracking

**Real comm graph** (from `agency.py`) — note there is **no CEO→Media edge**: Facebook publishing is
reachable only via `Client Approval Manager → Media Operations Director`. The UI draws exactly this.

**Real 8-stage pipeline** (from the CEO `instructions.md`): Intake → Research → Copy → Creative →
Policy → Approval → Execution → Tracking. The header stage-tracker reflects it.

**Governance shown as the code enforces it:** `AdCampaignStarter`, `AdSetCreator`, `AdCreator` all
default to **PAUSED** (`activate_immediately=False`); the UI badges execution objects **PAUSED** until
go-live. Nothing reaches Stage 7 without `approved` from both gates.

## How it stays faithful — three file-based sources of truth

The bridge never parses tool internals. It tails the same files your tools already write:

1. **`.workflow_state.json`** (via `workflow_state.set_state_value`) — diffed each tick:
   - `ad_copy_options` → `copy_options` event (Stage 3 choice)
   - `image_options` (with frontend-safe `image_path`) → `image_options` event (Stage 4 choice)
   - `campaign_id` / `ad_set_id` / `ad_id` → `execution` event (badged PAUSED)
   - `page_post_id` / `page_photo_id` → `execution` event (badged LIVE)
2. **`audit_logs/manifest_ai_audit.jsonl`** (via `safe_audit_log`) — the only inter-agent gate data:
   - `facebook_policy_review` → `gate` (Policy: approved / revise / blocked + concern_areas)
   - `client_approval_review` → `gate` (Approval: approved / revise + missing_approvals)
3. **`campaign_data/schedule.json` + `budgets.json`** — CampaignOps tracking (Stage 8).

The **CEO's client-facing text** comes from `agency.get_completion_stream(...)`. Agent→agent handoffs
seen on the stream drive the flow animation; tool payloads are ignored on purpose.

**Images:** the bridge serves `generated_assets/` at the same relative path the tools stored, so the
UI's `image_path` resolves directly. No hardcoded images in live mode — only what the Creative
Director actually generated this run.

## Run

```bash
# from your repo root, with your normal .env present
pip install fastapi "uvicorn[standard]" websockets
python web_bridge.py
```

Open **http://127.0.0.1:8000** (serves `web/index.html` if you drop the bundled UI there), or open the
standalone **Manifest AI** UI and connect it to `ws://127.0.0.1:8000/ws` (connection panel, top-right).

## The one version-specific spot

Agency Swarm's streaming surface differs slightly between releases. Only **`_probe_stream_item(item)`**
may need a small tweak against your installed version — it reads `sender` / `receiver` / `content` off
each streamed item. If CEO text or handoffs don't appear, `print(repr(item))` once inside that function
and tell me the real attribute names; everything else (gates, options, execution, images) comes from
the files above and is already exact.

## Selection → backend (Stage 4)

When the client picks a creative in the UI, it sends a normal reply to the CEO **plus**
`selection: {kind, option}`. In the real flow the CEO then calls **`ImageSelector`** with that option,
which writes `image_path` + `selected_image_option` to state — exactly the rule-14 conversational
selection. No structure changes.
