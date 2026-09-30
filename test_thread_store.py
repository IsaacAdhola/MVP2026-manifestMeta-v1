"""Unit tests for Slack conversation thread persistence. No live Firebase required."""

from __future__ import annotations

import json
from typing import Any

import firebase_adapter
import thread_store


class _FakeSnapshot:
    def __init__(self, data: dict[str, Any] | None) -> None:
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data or {})


class _FakeDocument:
    def __init__(self) -> None:
        self.data: dict[str, Any] | None = None

    def set(self, data: dict[str, Any]) -> None:
        self.data = dict(data)

    def get(self) -> _FakeSnapshot:
        return _FakeSnapshot(self.data)


class _FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, _FakeDocument] = {}

    def document(self, doc_id: str) -> _FakeDocument:
        if doc_id not in self.documents:
            self.documents[doc_id] = _FakeDocument()
        return self.documents[doc_id]


class FakeFirestore:
    def __init__(self) -> None:
        self.collections: dict[str, _FakeCollection] = {}

    def collection(self, name: str) -> _FakeCollection:
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]


def setup_function() -> None:
    firebase_adapter.reset_for_tests()


def teardown_function() -> None:
    firebase_adapter.reset_for_tests()


def test_missing_conversation_returns_empty_list(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    assert thread_store.get_threads("1710000000.123456") == []


def test_local_round_trip_in_development(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    messages = [{"role": "user", "content": "hello", "agent": "CEO", "callerAgent": None}]
    thread_store.save_threads("1710000000.123456", messages)
    loaded = thread_store.get_threads("1710000000.123456")
    assert loaded == messages
    saved_path = tmp_path / "1710000000.123456.json"
    assert json.loads(saved_path.read_text(encoding="utf-8"))["threads"] == messages


def test_staging_writes_firestore_document(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    fake = FakeFirestore()
    firebase_adapter.attach_test_client(fake)
    messages = [{"role": "assistant", "content": "hi"}]
    thread_store.save_threads("slack-thread-1", messages)
    loaded = thread_store.get_threads("slack-thread-1")
    assert loaded == messages
    remote = fake.collection("slack_threads").document("slack-thread-1").data
    assert remote is not None
    assert remote["conversation_id"] == "slack-thread-1"
    assert remote["threads"] == messages


def test_production_does_not_write(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    thread_store.save_threads("prod-thread", [{"role": "user", "content": "nope"}])
    assert thread_store.get_threads("prod-thread") == []
    assert list(tmp_path.glob("*.json")) == []


def test_blank_conversation_id_is_ignored(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setattr(thread_store, "THREADS_DIR", tmp_path)
    thread_store.save_threads("  ", [{"role": "user", "content": "x"}])
    assert thread_store.get_threads("") == []
    assert thread_store.get_threads("   ") == []
