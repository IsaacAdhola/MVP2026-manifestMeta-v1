"""Unit tests for generate_response Slack persistence helper."""

from __future__ import annotations

from types import SimpleNamespace

import firebase_adapter
import generate_response
import thread_store


class FakeThreadManager:
    def __init__(self, load_threads_callback=None, save_threads_callback=None) -> None:
        self.messages = list(load_threads_callback() if load_threads_callback else [])
        self._save = save_threads_callback

    def add_message(self, message: dict) -> None:
        self.messages.append(message)
        if self._save:
            self._save(self.messages)

    def get_all_messages(self) -> list:
        return list(self.messages)


class FakeAgency:
    def __init__(self) -> None:
        self.entry_points = [SimpleNamespace(name="Chief Growth Strategist")]
        self.calls: list[str] = []
        self.last_context = None
        self.get_completion = None

    def get_agent_context(self, agent_name: str, thread_manager_override=None):
        assert agent_name == "Chief Growth Strategist"
        self.last_context = thread_manager_override
        return SimpleNamespace(thread_manager=thread_manager_override)

    def get_response_sync(self, message: str, agency_context_override=None):
        self.calls.append(message)
        manager = getattr(agency_context_override, "thread_manager", None)
        if manager is not None:
            manager.add_message({"role": "user", "content": message, "callerAgent": None})
            manager.add_message({"role": "assistant", "content": "welcome back", "callerAgent": None})
        return SimpleNamespace(final_output="welcome back")


def setup_function() -> None:
    firebase_adapter.reset_for_tests()


def teardown_function() -> None:
    firebase_adapter.reset_for_tests()


def test_generate_response_continues_saved_slack_thread(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    monkeypatch.setattr(generate_response, "ThreadManager", FakeThreadManager)
    conversation_id = "1710000000.123456"
    thread_store.save_threads(
        conversation_id,
        [{"role": "user", "content": "hi", "callerAgent": None}],
    )
    agency = FakeAgency()
    reply = generate_response.generate_response(
        "remember me?",
        conversation_id,
        agency_obj=agency,
    )
    assert reply == "welcome back"
    assert agency.calls == ["remember me?"]
    saved = thread_store.get_threads(conversation_id)
    assert saved[0]["content"] == "hi"
    assert saved[-1]["content"] == "welcome back"


def test_generate_response_starts_new_conversation_when_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    monkeypatch.setattr(generate_response, "ThreadManager", FakeThreadManager)
    agency = FakeAgency()
    reply = generate_response.generate_response("hello", "new-thread", agency_obj=agency)
    assert reply == "welcome back"
    saved = thread_store.get_threads("new-thread")
    assert saved[-1]["content"] == "welcome back"


def test_get_completion_alias_uses_v1_get_response_sync(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    monkeypatch.setattr(generate_response, "ThreadManager", FakeThreadManager)
    agency = FakeAgency()
    reply = generate_response.get_completion("ping", "thread-a", agency_obj=agency)
    assert reply == "welcome back"
    assert agency.calls == ["ping"]
    assert not callable(agency.get_completion)


def test_generate_response_requires_conversation_id() -> None:
    try:
        generate_response.generate_response("hi", " ", agency_obj=FakeAgency())
    except ValueError as exc:
        assert "conversation_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")
