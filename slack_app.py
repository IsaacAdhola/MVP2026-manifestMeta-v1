"""
Manifest AI Slack entry point.

Socket Mode (no public URL):
    python slack_app.py

HTTP Events API (after you host the bot):
    set SLACK_SIGNING_SECRET and omit SLACK_APP_TOKEN, then:
    python slack_app.py --http --port 3000

Clients talk only to the Chief Growth Strategist. Specialists stay internal.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

from model_router import apply_provider_env

load_dotenv()
apply_provider_env()

ROOT = Path(__file__).resolve().parent
_TURN_LOCK = threading.Lock()
CLIENT_SAFE_ERROR = "Something went wrong on our side. Try that request again."
SLACK_PROGRESS_SECONDS = 45
LONG_TURN = re.compile(
    r"\b(creative job|dall-e|research|campaign|competitor|images?|lantern|ads?)\b",
    re.IGNORECASE,
)
SLACK_INBOX_POLL_SECONDS = 8
SLACK_INBOX_HISTORY_LIMIT = 5
_SEEN_EVENT_TS: set[str] = set()
_SEEN_LOCK = threading.Lock()
_MAX_SEEN_EVENTS = 1000
SLACK_TURN_ACK = (
    "On it. I'll stay in this conversation — research, creatives, or campaign "
    "ops can take a few minutes. You do not have to know the next step."
)


def _claim_event_ts(ts: str | None) -> bool:
    """Return True once per Slack event ts so Socket Mode and the inbox poller do not double-run."""
    if not ts:
        return True
    with _SEEN_LOCK:
        if ts in _SEEN_EVENT_TS:
            return False
        _SEEN_EVENT_TS.add(ts)
        if len(_SEEN_EVENT_TS) > _MAX_SEEN_EVENTS:
            _SEEN_EVENT_TS.clear()
            _SEEN_EVENT_TS.add(ts)
        return True


def _message_is_new(ts: str | None, start_ts: float, seen: set[str]) -> bool:
    if not ts or ts in seen:
        return False
    try:
        return float(ts) >= start_ts
    except (TypeError, ValueError):
        return False


def _poll_direct_inbox(app, bot_user_id: str | None) -> None:
    """Read DMs from Slack history when Socket Mode / ngrok events never arrive."""
    from error_logger import log_error

    seen: set[str] = set()
    start_ts = time.time()
    while True:
        time.sleep(SLACK_INBOX_POLL_SECONDS)
        try:
            listed = app.client.conversations_list(types="im", limit=50)
            for channel in listed.get("channels") or []:
                channel_id = channel.get("id")
                if not channel_id:
                    continue
                history = app.client.conversations_history(
                    channel=channel_id,
                    limit=SLACK_INBOX_HISTORY_LIMIT,
                )
                for message in reversed(history.get("messages") or []):
                    ts = message.get("ts")
                    if not _message_is_new(ts, start_ts, seen):
                        if ts:
                            seen.add(ts)
                        continue
                    seen.add(ts)
                    if message.get("bot_id") or message.get("user") == bot_user_id:
                        continue
                    text = message.get("text") or ""
                    print("[slack] inbox poller delivering DM")
                    dispatch_user_message(
                        {
                            "channel": channel_id,
                            "channel_type": "im",
                            "text": text,
                            "ts": ts,
                            "user": message.get("user"),
                        },
                        app.client,
                        text,
                        False,
                        bot_user_id,
                    )
        except Exception as exc:
            err = str(exc)
            if "missing_scope" in err:
                print(
                    "[slack] inbox poller stopped: conversations.list needs im:read "
                    "(Socket Mode DMs still work)."
                )
                return
            log_error("Chief Growth Strategist", exc, location="slack_app._poll_direct_inbox")


def _safe_post(client, channel: str | None, thread_ts: str | None, text: str) -> None:
    if not channel or not text:
        return
    try:
        payload = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        client.chat_postMessage(**payload)
    except Exception as exc:
        from error_logger import log_error

        log_error("Chief Growth Strategist", exc, location="slack_app._safe_post")


def _missing_slack_keys(http_mode: bool) -> list[str]:
    required = ["SLACK_BOT_TOKEN"]
    if http_mode:
        required.append("SLACK_SIGNING_SECRET")
    else:
        required.append("SLACK_APP_TOKEN")
    return [name for name in required if not (os.getenv(name) or "").strip()]


def _resolve_local_image(path: str) -> Path | None:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (ROOT / candidate).resolve()
    return candidate if candidate.exists() else None


def _post_reply(client, channel: str, thread_ts: str | None, reply) -> None:
    from slack_format import chunk_text, markdown_to_slack, option_buttons

    slack_text, md_paths = markdown_to_slack(reply.text)
    chunks = chunk_text(slack_text) or ["The team finished this step. What should we do next?"]
    parent_ts = thread_ts
    for index, chunk in enumerate(chunks):
        payload = {"channel": channel, "text": chunk}
        if parent_ts:
            payload["thread_ts"] = parent_ts
        try:
            posted = client.chat_postMessage(**payload)
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="slack_app._post_reply.text")
            continue
        if index == 0 and not parent_ts:
            parent_ts = posted.get("ts")

    seen: set[str] = set()
    upload_paths = list(md_paths) + list(reply.image_paths or [])
    for raw in upload_paths:
        local = _resolve_local_image(raw)
        if local is None or local.as_posix() in seen:
            continue
        seen.add(local.as_posix())
        try:
            try:
                client.files_upload_v2(
                    channel=channel,
                    thread_ts=parent_ts,
                    file=str(local),
                    filename=local.name,
                    title=local.stem,
                )
            except TypeError:
                client.files_upload_v2(
                    channels=channel,
                    thread_ts=parent_ts,
                    file=str(local),
                    filename=local.name,
                    title=local.stem,
                )
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="slack_app._post_reply.upload")
            _safe_post(
                client,
                channel,
                parent_ts,
                "The written reply is above. File upload needs the Slack files:write scope — reinstall the app after adding it.",
            )

    for kind, should_ask in (("copy", reply.ask_copy_choice), ("image", reply.ask_image_choice)):
        if not should_ask:
            continue
        buttons = option_buttons(kind)
        try:
            client.chat_postMessage(
                channel=channel,
                thread_ts=parent_ts,
                text=buttons["text"],
                blocks=buttons["blocks"],
            )
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="slack_app._post_reply.buttons")


def _run_turn(text: str, client, channel: str, thread_ts: str | None) -> None:
    from client_gateway import run_client_turn
    from error_logger import log_error

    acquired = _TURN_LOCK.acquire(blocking=False)
    if not acquired:
        _safe_post(
            client,
            channel,
            thread_ts,
            "Still on the previous request — research or images can take a few minutes. I'll reply in this thread when that package is ready.",
        )
        return
    stop_progress = threading.Event()
    long_turn = bool(LONG_TURN.search(text or "")) or len(text or "") > 80

    def _progress() -> None:
        n = 1
        while not stop_progress.wait(SLACK_PROGRESS_SECONDS):
            _safe_post(
                client,
                channel,
                thread_ts,
                f"Still working ({n}) — live competitor research and creatives are in progress. Stay in this chat; I'll come back with options.",
            )
            n += 1

    try:
        _safe_post(client, channel, thread_ts, SLACK_TURN_ACK)
        if long_turn:
            threading.Thread(target=_progress, daemon=True, name="slack-progress").start()
        reply = run_client_turn(text, conversation_id=channel)
        if (reply.text or "").startswith("[Error]"):
            log_error(
                "Chief Growth Strategist",
                reply.text,
                location="slack_app._run_turn.client_reply",
            )
            _safe_post(client, channel, thread_ts, CLIENT_SAFE_ERROR)
            return
        _post_reply(client, channel, thread_ts, reply)
    except Exception as exc:
        log_error("Chief Growth Strategist", exc, location="slack_app._run_turn")
        _safe_post(client, channel, thread_ts, CLIENT_SAFE_ERROR)
    finally:
        stop_progress.set()
        _TURN_LOCK.release()


def dispatch_user_message(
    event: dict,
    client,
    text: str,
    mentioned: bool,
    bot_user_id: str | None = None,
) -> None:
    """Route a DM or mention into the CEO turn without raising to Bolt."""
    from slack_format import strip_bot_mention
    from slack_reply_gate import normalize_client_text, should_reply_to_client

    try:
        cleaned = normalize_client_text(strip_bot_mention(text, bot_user_id))
        if not cleaned:
            print("[slack] empty text after mention strip; staying silent")
            return
        if not _claim_event_ts(event.get("ts")):
            print("[slack] duplicate event ts skipped")
            return
        channel = event.get("channel")
        channel_type = event.get("channel_type")
        gate_pass = should_reply_to_client(
            cleaned,
            channel_type=channel_type,
            mentioned=mentioned,
            source="message",
        )
        if not gate_pass:
            print(
                "[slack] reply gate stayed silent "
                f"channel_type={channel_type} mentioned={mentioned}"
            )
            return
        print(
            "[slack] starting CEO turn "
            f"channel_type={channel_type} mentioned={mentioned}"
        )
        thread_ts = event.get("thread_ts")
        if channel_type != "im":
            thread_ts = thread_ts or event.get("ts")
        threading.Thread(
            target=_run_turn,
            args=(cleaned, client, channel, thread_ts),
            daemon=True,
        ).start()
    except Exception as exc:
        from error_logger import log_error

        log_error("Chief Growth Strategist", exc, location="slack_app.dispatch_user_message")
        _safe_post(client, event.get("channel"), event.get("thread_ts"), CLIENT_SAFE_ERROR)


def build_slack_app():
    from slack_bolt import App
    from slack_format import should_ignore_slack_event

    app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        signing_secret=os.getenv("SLACK_SIGNING_SECRET") or "socket-mode-local",
    )
    bot_user_id = {"value": None}

    def _bot_id():
        if not bot_user_id["value"]:
            bot_user_id["value"] = app.client.auth_test().get("user_id")
        return bot_user_id["value"]

    def _handle_user_text(event: dict, client, text: str, mentioned: bool = False) -> None:
        dispatch_user_message(event, client, text, mentioned, bot_user_id=_bot_id())

    @app.event("app_mention")
    def on_mention(event, client):
        try:
            print("[slack] app_mention received")
            if should_ignore_slack_event(event):
                print("[slack] app_mention ignored (bot or subtype)")
                return
            _handle_user_text(event, client, event.get("text") or "", mentioned=True)
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="slack_app.on_mention")
            _safe_post(client, event.get("channel"), event.get("thread_ts"), CLIENT_SAFE_ERROR)

    @app.event("message")
    def on_message(event, client):
        try:
            if should_ignore_slack_event(event):
                return
            channel_type = event.get("channel_type")
            if channel_type != "im":
                print(
                    "[slack] channel message ignored without @mention; "
                    f"channel_type={channel_type}"
                )
                return
            print("[slack] dm message received")
            _handle_user_text(event, client, event.get("text") or "", mentioned=False)
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="slack_app.on_message")
            _safe_post(client, event.get("channel"), event.get("thread_ts"), CLIENT_SAFE_ERROR)

    def _on_option(ack, body, client):
        try:
            ack()
            actions = body.get("actions") or []
            if not actions:
                return
            choice = actions[0].get("value") or "Option 1"
            channel = body.get("channel", {}).get("id")
            thread_ts = (body.get("message") or {}).get("thread_ts") or (body.get("message") or {}).get("ts")
            from slack_reply_gate import should_reply_to_client

            if not should_reply_to_client(choice, source="action"):
                return
            threading.Thread(
                target=_run_turn,
                args=(choice, client, channel, thread_ts),
                daemon=True,
            ).start()
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="slack_app._on_option")
            channel = (body or {}).get("channel", {}).get("id")
            thread_ts = ((body or {}).get("message") or {}).get("ts")
            _safe_post(client, channel, thread_ts, CLIENT_SAFE_ERROR)

    for kind in ("copy", "image"):
        for index in (1, 2, 3):
            app.action(f"pick_{kind}_{index}")(_on_option)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Manifest AI in Slack")
    parser.add_argument("--http", action="store_true", help="Use HTTP Events API instead of Socket Mode")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", os.getenv("SLACK_PORT", "3000"))))
    args = parser.parse_args()

    missing = _missing_slack_keys(http_mode=args.http)
    if missing:
        print(
            "Slack is not configured yet. Add these to .env, then rerun:\n  "
            + "\n  ".join(missing)
            + "\nSee SLACK.md for the app setup steps."
        )
        sys.exit(1)

    manifest_path = ROOT / "manifest.json"
    socket_mode_in_manifest = True
    request_url = ""
    if manifest_path.exists():
        import json as _manifest_json
        _settings = _manifest_json.loads(manifest_path.read_text(encoding="utf-8")).get("settings") or {}
        socket_mode_in_manifest = bool(_settings.get("socket_mode_enabled"))
        request_url = str((_settings.get("event_subscriptions") or {}).get("request_url") or "")
    if not args.http and not socket_mode_in_manifest:
        print(
            "[slack_app] Slack app manifest has socket_mode_enabled=false. "
            "DMs are sent to the Event Subscriptions URL, not this Socket Mode process. "
            f"Configured URL host: {request_url or '(none)'}. "
            "That ngrok-free URL returns 403 to Slack. Turn Socket Mode ON at "
            "https://api.slack.com/apps for this app, then restart slack_app.py."
        )

    print("[slack_app] Loading Manifest AI agency...")
    from agency import agency  # noqa: F401

    print("[slack_app] Agency ready. Connecting to Slack...")
    app = build_slack_app()
    try:
        poller_bot_id = app.client.auth_test().get("user_id")
    except Exception:
        poller_bot_id = None
    threading.Thread(
        target=_poll_direct_inbox,
        args=(app, poller_bot_id),
        daemon=True,
        name="slack-inbox-poller",
    ).start()
    print("[slack_app] DM inbox poller started (covers silent Socket Mode / dead ngrok).")
    if args.http:
        app.start(port=args.port)
        return

    from slack_bolt.adapter.socket_mode import SocketModeHandler

    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()


if __name__ == "__main__":
    main()
