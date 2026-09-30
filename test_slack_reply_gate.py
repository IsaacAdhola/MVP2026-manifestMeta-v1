"""Unit tests for the Slack GPT reply gate. GPT is always mocked."""

from __future__ import annotations

import slack_reply_gate


class _FakeLLM:
    def __init__(self, payload: str = '{"reply": false}') -> None:
        self.payload = payload
        self.calls: list[tuple] = []

    def __call__(self, model: str, system: str, user: str, max_tokens: int = 40, temperature: float = 0.0) -> str:
        self.calls.append((model, system, user, max_tokens, temperature))
        return self.payload


def test_normalize_strips_ceo_display_name() -> None:
    assert slack_reply_gate.normalize_client_text(
        "@Manifest Meta Ceo this is a test give me three images"
    ) == "this is a test give me three images"
    assert slack_reply_gate.normalize_client_text(
        "Manifest AI, please continue"
    ) == "please continue"


def test_empty_mention_stays_silent_without_gpt(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": true}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client("", mentioned=True, channel_type="channel") is False
    assert slack_reply_gate.should_reply_to_client("   ", mentioned=True) is False
    assert fake.calls == []


def test_emoji_only_stays_silent_without_gpt(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": true}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client("👍") is False
    assert slack_reply_gate.should_reply_to_client("🎉 🔥") is False
    assert fake.calls == []


def test_option_buttons_always_reply_without_gpt(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client("Option 1", source="action") is True
    assert slack_reply_gate.should_reply_to_client("Option 2") is True
    assert slack_reply_gate.should_reply_to_client("option 3 please") is True
    assert fake.calls == []


def test_campaign_feedback_replies(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": true}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client(
        "The coffee shop draft is too cute. Make it more premium.",
        channel_type="im",
    ) is True
    assert fake.calls == []


def test_ok_ack_does_not_reply(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client("ok", channel_type="im") is False
    assert slack_reply_gate.should_reply_to_client("thanks") is False


def test_human_chatter_does_not_reply(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client(
        "anyone want lunch at 12?",
        channel_type="channel",
        mentioned=False,
    ) is False


def test_empty_ask_mention_does_not_reply(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client(
        "hey",
        channel_type="channel",
        mentioned=True,
    ) is True


def test_real_request_mention_replies(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": true}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client(
        "we need three post options for this weekend",
        channel_type="channel",
        mentioned=True,
    ) is True


def test_gpt_yes_no_text_is_parsed(monkeypatch) -> None:
    fake = _FakeLLM("YES")
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client("Please draft a Facebook campaign.") is True
    fake.payload = "no"
    assert slack_reply_gate.should_reply_to_client("lol") is False


def test_hello_in_dm_replies_without_gpt(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client("hello app", channel_type="im") is True
    assert slack_reply_gate.should_reply_to_client("hello there", channel_type="im") is True
    assert fake.calls == []


def test_image_request_in_dm_replies_without_gpt(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client(
        "this is a test make three images that have people reading and post it on my facebook",
        channel_type="im",
    ) is True
    assert fake.calls == []


def test_ceo_alias_mention_still_counts_as_work(monkeypatch) -> None:
    fake = _FakeLLM('{"reply": false}')
    monkeypatch.setattr(slack_reply_gate, "llm_text", fake)
    assert slack_reply_gate.should_reply_to_client(
        "this is a test give me three images of people reading",
        channel_type="im",
        mentioned=True,
    ) is True
    assert fake.calls == []


def test_gpt_failure_on_work_request_still_replies(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("openai down")

    monkeypatch.setattr(slack_reply_gate, "llm_text", _boom)
    assert slack_reply_gate.should_reply_to_client(
        "Can you run ads for my shop?",
        channel_type="im",
    ) is True


def test_gpt_failure_on_ack_stays_silent(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("openai down")

    monkeypatch.setattr(slack_reply_gate, "llm_text", _boom)
    assert slack_reply_gate.should_reply_to_client("hello there", channel_type="im") is True
