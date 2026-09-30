"""Unit tests for staging-only Firebase persistence. No live credentials required."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import firebase_adapter
import workflow_state


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


def test_development_does_not_initialize(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    assert firebase_adapter.initialize_firebase() is False
    assert firebase_adapter.firestore_available() is False


def test_production_is_blocked_even_with_credentials(monkeypatch, tmp_path) -> None:
    key_file = tmp_path / "dummy.json"
    key_file.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    monkeypatch.setenv("FIREBASE_CREDENTIALS_PATH", str(key_file))
    assert firebase_adapter.initialize_firebase() is False
    assert firebase_adapter.save_workflow_state({"k": "v"}) is False


def test_staging_missing_credentials_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    monkeypatch.setenv("FIREBASE_CREDENTIALS_PATH", "./does-not-exist.json")
    assert firebase_adapter.initialize_firebase() is False
    assert firebase_adapter.firestore_available() is False


def test_staging_mocked_client_round_trip(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    fake = FakeFirestore()
    firebase_adapter.attach_test_client(fake)
    assert firebase_adapter.firestore_available() is True
    assert firebase_adapter.save_workflow_state({"campaign_id": "c1"}) is True
    loaded = firebase_adapter.load_workflow_state()
    assert loaded == {"campaign_id": "c1"}


def test_workflow_state_stays_local_in_development(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(workflow_state, "_STATE_FILE", state_file)
    firebase_adapter.reset_for_tests()
    workflow_state.clear_state()
    workflow_state.set_state_value("ad_copy", "hello")
    assert workflow_state.get_state_value("ad_copy") == "hello"
    assert json.loads(state_file.read_text(encoding="utf-8"))["ad_copy"] == "hello"


def test_workflow_state_dual_writes_in_staging(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(workflow_state, "_STATE_FILE", state_file)
    fake = FakeFirestore()
    firebase_adapter.attach_test_client(fake)
    workflow_state.set_state_value("ad_copy", "staging copy")
    assert json.loads(state_file.read_text(encoding="utf-8"))["ad_copy"] == "staging copy"
    remote = firebase_adapter.load_workflow_state()
    assert remote is not None
    assert remote["ad_copy"] == "staging copy"


def test_workflow_state_hydrates_from_remote_when_local_empty(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "manifest-ai-meta")
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(workflow_state, "_STATE_FILE", state_file)
    fake = FakeFirestore()
    firebase_adapter.attach_test_client(fake)
    firebase_adapter.save_workflow_state({"handoff_status": "intake_recorded"})
    assert not state_file.exists()
    assert workflow_state.get_state_value("handoff_status") == "intake_recorded"
    assert json.loads(state_file.read_text(encoding="utf-8"))["handoff_status"] == "intake_recorded"


def test_agency_py_keeps_v1_constructor() -> None:
    source = Path(__file__).resolve().parent.joinpath("agency.py").read_text(encoding="utf-8")
    assert "agency = Agency(" in source
    assert "communication_flows=_communication_flows" in source
    assert (
        "shared_instructions='./agency_manifesto.md'" in source
        or 'shared_instructions="./agency_manifesto.md"' in source
    )
    assert "from firebase_adapter import initialize_firebase" in source
    assert "(ceo, researchAgent)" in source
    assert "[ceo, researchAgent]" not in source
