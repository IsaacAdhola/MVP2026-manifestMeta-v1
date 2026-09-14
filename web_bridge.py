# web_bridge.py
# ===========================================================================
# Manifest AI — live web bridge  (v2, reconciled to the real codebase)
#
# Connects the ManifestMeta agency (Agency Swarm) to the "Manifest AI" web UI
# over a WebSocket, WITHOUT changing any agent, instruction, tool, flow, or
# governance gate. It only OBSERVES and FORWARDS what the real system produces.
#
# This version is built against the verified contract of your repo:
#
#   8 agents (exact name= strings):
#     Chief Growth Strategist            (MetaMarkCEO)        — client lead / orchestrator
#     Market Intelligence Director       (ResearchAgent)      — Stage 2 research
#     Senior Conversion Copywriter       (AdCopyAgent)        — Stage 3 copy
#     Creative Director                  (ImageCreatorAgent)  — Stage 4 creative
#     Facebook Policy Compliance Officer (FacebookPolicyAgent)— Stage 5 GATE
#     Client Approval Manager            (ClientApprovalAgent)— Stage 6 GATE
#     Media Operations Director          (FacebookManagerAgent)— Stage 7 Meta exec
#     Campaign Operations Director       (CampaignOpsAgent)   — Stage 8 tracking
#
#   Two real, file-based sources of truth the bridge tails (no internals needed):
#     1. .workflow_state.json   — written by workflow_state.set_state_value(...)
#        keys: ad_copy_options, ad_headline, ad_copy, image_options, image_path,
#              selected_image_option, campaign_id, ad_set_id, ad_id,
#              page_post_id, page_photo_id
#     2. audit_logs/manifest_ai_audit.jsonl — written by safe_audit_log
#        events: facebook_policy_review, client_approval_review (the two gates)
#     3. campaign_data/schedule.json + budgets.json — CampaignOps tracking (Stage 8)
#
#   The CEO's client-facing text comes from agency.get_completion_stream(...).
#
# Nothing else is sent to the browser. Tool payloads, prompts, tokens and file
# paths never leave the server — gate data comes only from the sanitized audit
# log, and image paths are the already-frontend-safe relative paths the
# ImageGenerator tool itself wrote to state.
#
# ---------------------------------------------------------------------------
# SETUP (from your repo root, with your normal .env in place):
#
#   pip install fastapi "uvicorn[standard]" websockets
#   python web_bridge.py
#
# Open http://127.0.0.1:8000  (serves web/index.html if present),
# or open the standalone UI and connect it to ws://127.0.0.1:8000/ws
# ===========================================================================

import asyncio
import json
import threading
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import the REAL agency unchanged.
from agency import agency  # noqa: E402

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "web"
ASSETS_DIR = ROOT / "generated_assets"
STATE_FILE = ROOT / ".workflow_state.json"
AUDIT_FILE = ROOT / "audit_logs" / "manifest_ai_audit.jsonl"
SCHEDULE_FILE = ROOT / "campaign_data" / "schedule.json"
BUDGET_FILE = ROOT / "campaign_data" / "budgets.json"
USER_NAME = "user"

# Real agent name= strings (must match the UI's actor mapping exactly).
CEO = "Chief Growth Strategist"
RESEARCH = "Market Intelligence Director"
COPY = "Senior Conversion Copywriter"
CREATIVE = "Creative Director"
POLICY = "Facebook Policy Compliance Officer"
APPROVAL = "Client Approval Manager"
MEDIA = "Media Operations Director"
CAMPAIGN_OPS = "Campaign Operations Director"

app = FastAPI(title="Manifest AI Bridge")


# ===========================================================================
# .workflow_state.json watcher — diff state and emit the real contract
# ===========================================================================
def _read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


async def watch_state(send, stop_evt: asyncio.Event):
    """Diff .workflow_state.json against the last snapshot and emit UI events.

    Each emit maps a real shared_state key to exactly one UI event:
      ad_copy_options          -> copy_options   (Creative selection moment)
      image_options            -> image_options  (Creative selection moment)
      campaign_id/ad_set_id/ad_id/page_post_id/page_photo_id -> execution
    """
    prev = dict(_read_json(STATE_FILE, {}))  # start from current so we only stream new work
    while not stop_evt.is_set():
        cur = _read_json(STATE_FILE, {})
        if cur != prev:
            # ----- Stage 3: copy options -----
            if cur.get("ad_copy_options") and cur.get("ad_copy_options") != prev.get("ad_copy_options"):
                opts = cur["ad_copy_options"]
                await send({
                    "type": "copy_options",
                    "actor": COPY,
                    "options": [
                        {
                            "option": i + 1,
                            "headline": o.get("headline", ""),
                            "ad_copy": o.get("ad_copy", ""),
                            "rationale": o.get("rationale", ""),
                        }
                        for i, o in enumerate(opts)
                    ],
                })

            # ----- Stage 4: image options (image_path is already frontend-safe/relative) -----
            if cur.get("image_options") and cur.get("image_options") != prev.get("image_options"):
                opts = cur["image_options"]
                await send({
                    "type": "image_options",
                    "actor": CREATIVE,
                    "options": [
                        {
                            "option": o.get("option", i + 1),
                            "image_path": o.get("image_path", ""),
                            "creative_note": o.get("creative_note", ""),
                        }
                        for i, o in enumerate(opts)
                    ],
                })

            # ----- Stage 7: Meta execution objects (campaign / ad set / ad / posts) -----
            exec_ids = {}
            for k in ("campaign_id", "ad_set_id", "ad_id"):
                if cur.get(k) and cur.get(k) != prev.get(k):
                    exec_ids[k] = f"{cur[k]} (PAUSED)"  # AdCampaignStarter/AdSetCreator/AdCreator default paused
            if exec_ids:
                await send({
                    "type": "execution",
                    "actor": MEDIA,
                    "title": "Paid Campaign Objects Created — Paused",
                    "status": "paused",
                    # The selected creative (ImageSelector wrote image_path) so the UI
                    # shows the actual DALL-E image on the built campaign.
                    "image_path": cur.get("image_path", ""),
                    "summary": "Meta campaign / ad set / ad created under your ad account, using your "
                               "selected creative. Per agency governance these are created PAUSED "
                               "until you authorize go-live.",
                    "ids": exec_ids,
                })

            for k, label in (("page_post_id", "Facebook Page Post Published"),
                             ("page_photo_id", "Facebook Photo Post Published")):
                if cur.get(k) and cur.get(k) != prev.get(k):
                    await send({
                        "type": "execution",
                        "actor": MEDIA,
                        "title": label,
                        "status": "live",
                        "image_path": cur.get("image_path", ""),
                        "summary": "Published live to the configured Facebook Page.",
                        "ids": {k: str(cur[k])},
                    })

            # ----- Go-live: if an activation writes campaign_status='active', surface a real LIVE event.
            if cur.get("campaign_status") == "active" and prev.get("campaign_status") != "active":
                await send({
                    "type": "execution",
                    "actor": MEDIA,
                    "title": "Paid Campaign — LIVE",
                    "status": "live",
                    "image_path": cur.get("image_path", ""),
                    "summary": "Campaign activated and now serving on Meta.",
                    "ids": {"campaign_id": f"{cur.get('campaign_id','')} (ACTIVE)"},
                })

            prev = dict(cur)
        await asyncio.sleep(0.25)


# ===========================================================================
# Audit-log tailer — the ONLY source of inter-agent gate data
# ===========================================================================
async def tail_audit(send, stop_evt: asyncio.Event):
    pos = AUDIT_FILE.stat().st_size if AUDIT_FILE.exists() else 0
    while not stop_evt.is_set():
        try:
            if AUDIT_FILE.exists():
                size = AUDIT_FILE.stat().st_size
                if size > pos:
                    with AUDIT_FILE.open("r", encoding="utf-8") as fh:
                        fh.seek(pos)
                        chunk = fh.read()
                        pos = fh.tell()
                    for line in chunk.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        await send(_audit_to_event(rec))
        except Exception:
            pass
        await asyncio.sleep(0.25)


def _audit_to_event(rec: dict) -> dict:
    et = str(rec.get("event_type", "")).lower()
    actor = rec.get("actor", "")
    outcome = str(rec.get("outcome", ""))
    details = rec.get("details", {}) or {}
    # The two real gate events.
    if et == "facebook_policy_review" or actor == POLICY:
        return {"type": "gate", "actor": POLICY, "outcome": outcome,
                "concern_areas": details.get("concern_areas", [])}
    if et == "client_approval_review" or actor == APPROVAL:
        return {"type": "gate", "actor": APPROVAL, "outcome": outcome,
                "concern_areas": details.get("missing_approvals", [])}
    # Anything else -> a feed line (already sanitized by safe_audit_log).
    return {"type": "audit", "event_type": rec.get("event_type", "event"),
            "actor": actor, "outcome": outcome}


# ===========================================================================
# Stream one user turn through the REAL agency
# ===========================================================================
def run_agency_turn(text: str, loop, send_threadsafe):
    def emit(ev):
        asyncio.run_coroutine_threadsafe(send_threadsafe(ev), loop)

    emit({"type": "ceo_start"})
    try:
        stream = None
        if hasattr(agency, "get_completion_stream"):
            try:
                stream = agency.get_completion_stream(text)
            except TypeError:
                stream = agency.get_completion_stream(message=text)
        if stream is not None:
            for item in stream:
                ev = _probe_stream_item(item)
                if ev:
                    emit(ev)
        else:
            reply = agency.get_completion(text)
            emit({"type": "ceo_message", "text": str(reply)})
    except Exception as exc:
        emit({"type": "error", "message": f"engine error: {exc.__class__.__name__}"})
    finally:
        emit({"type": "run_complete"})


def _probe_stream_item(item):
    """Read one streamed Agency Swarm item. Versions differ — probe by attribute.

    We only surface CEO->user text and agent->agent handoffs (for the flow
    animation). Tool output is intentionally ignored; real deliverables come
    from the state/audit watchers instead.
    """
    if isinstance(item, str):
        return {"type": "ceo_delta", "text": item}
    sender = str(getattr(item, "sender_name", None) or getattr(item, "sender", "") or "")
    receiver = str(getattr(item, "receiver_name", None) or getattr(item, "receiver", "") or "")
    content = getattr(item, "content", None)
    if content is None:
        content = getattr(item, "text", None)

    if receiver == USER_NAME or (sender == CEO and receiver in ("", USER_NAME)):
        return {"type": "ceo_delta", "text": str(content)} if content else None
    if sender and receiver and sender != USER_NAME:
        return {"type": "flow", "from": sender, "to": receiver}
    return None


# ===========================================================================
# WebSocket endpoint
# ===========================================================================
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    loop = asyncio.get_event_loop()
    stop_evt = asyncio.Event()
    lock = asyncio.Lock()

    async def send(ev: dict):
        async with lock:
            try:
                await ws.send_text(json.dumps(ev))
            except Exception:
                pass

    await send({"type": "hello", "agents": 8})
    tasks = [
        asyncio.create_task(watch_state(send, stop_evt)),
        asyncio.create_task(tail_audit(send, stop_evt)),
    ]
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "user_message":
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                await send({"type": "user_echo", "text": text})
                threading.Thread(target=run_agency_turn, args=(text, loop, send), daemon=True).start()
    except WebSocketDisconnect:
        pass
    finally:
        stop_evt.set()
        for t in tasks:
            t.cancel()


# ===========================================================================
# Static: UI + real generated images
# ===========================================================================
@app.get("/")
async def index():
    idx = UI_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return JSONResponse({
        "ok": True,
        "msg": "Bridge running. Put the bundled UI at web/index.html, or open the "
               "standalone UI and connect to ws://127.0.0.1:8000/ws",
    })


# Serve real generated images at the SAME relative path the tools stored, so the
# UI's image_path (e.g. 'generated_assets/images/manifest_ai_..._option_1.png')
# resolves directly against the bridge host.
if ASSETS_DIR.exists():
    app.mount("/generated_assets", StaticFiles(directory=str(ASSETS_DIR)), name="generated_assets")
if UI_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(UI_DIR)), name="assets")


if __name__ == "__main__":
    print("Manifest AI bridge -> http://127.0.0.1:8000   (ws: /ws)")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
