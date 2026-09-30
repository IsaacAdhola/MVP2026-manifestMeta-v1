"""Upload failures must not swallow the CEO text reply."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import slack_app


def test_inbox_poller_skips_old_and_seen_messages() -> None:
    seen: set[str] = set()
    start_ts = 1000.0
    assert slack_app._message_is_new("999.0", start_ts, seen) is False
    assert slack_app._message_is_new("1000.5", start_ts, seen) is True
    seen.add("1000.5")
    assert slack_app._message_is_new("1000.5", start_ts, seen) is False
    assert slack_app._message_is_new(None, start_ts, seen) is False


class _FakeClient:
    def __init__(self, upload_error: Exception | None = None) -> None:
        self.upload_error = upload_error
        self.posts: list[dict] = []
        self.uploads = 0

    def chat_postMessage(self, **payload):
        self.posts.append(payload)
        return {"ts": "1.0"}

    def files_upload_v2(self, **_payload):
        self.uploads += 1
        if self.upload_error:
            raise self.upload_error


def test_post_reply_survives_missing_files_write_scope(tmp_path: Path, monkeypatch) -> None:
    image = tmp_path / "people-reading.png"
    image.write_bytes(b"png")
    monkeypatch.setattr(slack_app, "ROOT", tmp_path)
    logged: list[str] = []

    def _log(_actor, _error, *, location="", **_kwargs):
        logged.append(location)
        return {}

    monkeypatch.setattr("error_logger.log_error", _log)
    client = _FakeClient(upload_error=RuntimeError("missing_scope files:write"))
    reply = SimpleNamespace(
        text="Here are three image directions.",
        image_paths=[str(image)],
        ask_copy_choice=False,
        ask_image_choice=False,
    )
    slack_app._post_reply(client, "D123", "1.0", reply)
    assert client.uploads == 1
    assert any("files:write" in (post.get("text") or "") for post in client.posts)
    assert "slack_app._post_reply.upload" in logged
    assert any("three image directions" in (post.get("text") or "") for post in client.posts)


def test_dispatch_does_not_raise_when_gate_fails() -> None:
    class _BoomClient:
        def chat_postMessage(self, **_payload):
            raise RuntimeError("slack down")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("classifier exploded")

    import slack_reply_gate

    original = slack_reply_gate.should_reply_to_client
    slack_reply_gate.should_reply_to_client = _boom
    try:
        slack_app.dispatch_user_message(
            {"channel": "D123", "channel_type": "im", "text": "make three images"},
            _BoomClient(),
            "make three images",
            mentioned=False,
            bot_user_id="U123",
        )
    finally:
        slack_reply_gate.should_reply_to_client = original
