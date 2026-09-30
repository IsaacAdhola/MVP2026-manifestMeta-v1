"""ASGI entry for Docker: uvicorn app:api --host 0.0.0.0 --port 8000."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from model_router import apply_provider_env
from slack_http import slack_url_challenge, summarize_slack_envelope

load_dotenv()
apply_provider_env()

_handler = None


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    if _slack_configured():
        try:
            print("[app] Loading Slack handler...")
            _slack_handler()
            print("[app] Slack handler ready")
        except Exception as exc:
            print(f"[app] Slack handler warmup failed: {exc}")
    yield


api = FastAPI(title="Manifest AI", lifespan=_lifespan)


def _slack_configured() -> bool:
    token = (os.getenv("SLACK_BOT_TOKEN") or "").strip()
    secret = (os.getenv("SLACK_SIGNING_SECRET") or "").strip()
    return bool(token and secret)


def _slack_handler():
    global _handler
    if _handler is None:
        if not _slack_configured():
            return None
        from slack_bolt.adapter.fastapi import SlackRequestHandler

        from agency import agency  # noqa: F401
        from slack_app import build_slack_app

        _handler = SlackRequestHandler(build_slack_app())
    return _handler


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "manifest-ai"}


@api.post("/slack/events")
async def slack_events(req: Request):
    payload: dict = {}
    try:
        payload = await req.json()
    except Exception:
        payload = {}

    print(f"[slack/events] {summarize_slack_envelope(payload)}")
    challenge = slack_url_challenge(payload)
    if challenge is not None:
        print("[slack/events] url_verification challenge acknowledged")
        return PlainTextResponse(challenge)

    handler = _slack_handler()
    if handler is None:
        return JSONResponse(
            {
                "error": (
                    "Slack is not configured. Set SLACK_BOT_TOKEN and "
                    "SLACK_SIGNING_SECRET at container runtime."
                )
            },
            status_code=503,
        )
    return await handler.handle(req)


@api.post("/slack/interactive")
async def slack_interactive(req: Request):
    handler = _slack_handler()
    if handler is None:
        return JSONResponse(
            {"error": "Slack is not configured."},
            status_code=503,
        )
    return await handler.handle(req)
