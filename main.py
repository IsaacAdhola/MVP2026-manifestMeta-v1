"""Firebase Cloud Functions (2nd gen) HTTP entry for the Slack swarm."""

from __future__ import annotations

import json
import os
from typing import Any

from firebase_functions import https_fn, options
from firebase_functions.params import SecretParam, StringParam

from slack_http import slack_url_challenge

SLACK_BOT_TOKEN = SecretParam("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = SecretParam("SLACK_SIGNING_SECRET")
OPENAI_API_KEY = SecretParam("OPENAI_API_KEY")

SLACK_CHANNEL_ID = StringParam("SLACK_CHANNEL_ID", default="")
AGENT_MODEL_NAME = StringParam("AGENT_MODEL_NAME", default="gpt-4o")

_HANDLER = None


def _bind_runtime_env() -> None:
    os.environ["SLACK_BOT_TOKEN"] = SLACK_BOT_TOKEN.value
    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET.value
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY.value
    os.environ["SLACK_CHANNEL_ID"] = SLACK_CHANNEL_ID.value
    os.environ["AGENT_MODEL_NAME"] = AGENT_MODEL_NAME.value
    os.environ.setdefault("ENVIRONMENT", "staging")
    os.environ.setdefault("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    from firebase_adapter import initialize_firebase

    initialize_firebase()


def _slack_handler():
    global _HANDLER
    if _HANDLER is None:
        _bind_runtime_env()
        from slack_bolt.adapter.flask import SlackRequestHandler

        from slack_app import build_slack_app

        _HANDLER = SlackRequestHandler(build_slack_app())
    return _HANDLER


def _parse_payload(req: https_fn.Request) -> dict[str, Any]:
    data = req.get_json(silent=True)
    if isinstance(data, dict):
        return data
    raw = req.get_data(as_text=True) or ""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


@https_fn.on_request(
    secrets=[SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, OPENAI_API_KEY],
    region=options.SupportedRegion.US_CENTRAL1,
    memory=options.MemoryOption.GB_1,
    timeout_sec=540,
    max_instances=10,
)
def handle_slack_agent(req: https_fn.Request) -> https_fn.Response:
    try:
        if req.method == "GET":
            return https_fn.Response("ok", status=200)

        payload = _parse_payload(req)
        challenge = slack_url_challenge(payload)
        if challenge is not None:
            return https_fn.Response(challenge, status=200, mimetype="text/plain")

        channel_id = SLACK_CHANNEL_ID.value or os.environ.get("SLACK_CHANNEL_ID", "")
        model_name = AGENT_MODEL_NAME.value
        print(f"SUCCESS: Swarm triggered in {channel_id} using {model_name}")

        flask_response = _slack_handler().handle(req)
        return https_fn.Response(
            flask_response.get_data(as_text=True),
            status=int(flask_response.status_code),
            headers=dict(flask_response.headers),
        )
    except Exception as exc:
        print(f"CRITICAL_ERROR: Agent swarm failed: {exc}")
        return https_fn.Response("Internal agent error", status=500)
