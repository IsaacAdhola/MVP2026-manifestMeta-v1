"""Staging-only Firestore adapter for the nested Agency Swarm.

Official init pattern: credentials.Certificate(path) then
firebase_admin.initialize_app(cred, options={"projectId": ...})
https://firebase.google.com/docs/admin/setup
https://firebase.google.com/docs/firestore/quickstart-server

On Cloud Functions, ADC via initialize_app() is preferred when no key file is
deployed. Secrets for functions stay in Secret Manager (SecretParam), not .env.
https://firebase.google.com/docs/functions/config-env

Agents never initialize against production. Missing deps or credentials log an
error and leave local JSON as the working store.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STAGING_ENVIRONMENT = "staging"
ALLOWED_STAGING_PROJECT_ID = "manifest-ai-meta"
BLOCKED_ENVIRONMENTS = frozenset({"production", "prod"})
WORKFLOW_COLLECTION = "workflow_state"
WORKFLOW_DOCUMENT = "current"

_AGENCY_ROOT = Path(__file__).resolve().parent

_app: Any = None
_db: Any = None
_init_attempted = False
_available = False


@dataclass(frozen=True)
class StagingFirebaseConfig:
    environment: str
    project_id: str
    credentials_path: Path | None


def reset_for_tests() -> None:
    global _app, _db, _init_attempted, _available
    _app = None
    _db = None
    _init_attempted = False
    _available = False


def attach_test_client(db: Any) -> None:
    """Inject a fake Firestore client for unit tests."""
    global _db, _init_attempted, _available
    _db = db
    _init_attempted = True
    _available = db is not None


def get_environment() -> str:
    return (os.getenv("ENVIRONMENT") or "development").strip().lower()


def load_config() -> StagingFirebaseConfig:
    raw_path = (os.getenv("FIREBASE_CREDENTIALS_PATH") or "").strip()
    credentials_path: Path | None = None
    if raw_path:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (_AGENCY_ROOT / candidate).resolve()
        credentials_path = candidate
    return StagingFirebaseConfig(
        environment=get_environment(),
        project_id=(os.getenv("FIREBASE_PROJECT_ID") or "").strip(),
        credentials_path=credentials_path,
    )


def _is_production(config: StagingFirebaseConfig) -> bool:
    if config.environment in BLOCKED_ENVIRONMENTS:
        return True
    return "production" in config.project_id.lower()


def _can_use_staging(config: StagingFirebaseConfig) -> bool:
    if _is_production(config):
        logger.error("Firebase adapter refused initialization for production")
        return False
    if config.environment != STAGING_ENVIRONMENT:
        return False
    if config.project_id and config.project_id != ALLOWED_STAGING_PROJECT_ID:
        logger.error(
            "Firebase adapter refused unexpected staging project id (expected %s)",
            ALLOWED_STAGING_PROJECT_ID,
        )
        return False
    return True


def initialize_firebase() -> bool:
    """Initialize Admin SDK once. Never raises; False means use local storage."""
    global _app, _db, _init_attempted, _available
    if _init_attempted:
        return _available
    _init_attempted = True
    config = load_config()
    if not _can_use_staging(config):
        _available = False
        return False

    cred_path = config.credentials_path
    if cred_path is not None and not cred_path.is_file():
        logger.error(
            "Firebase staging credentials file is missing; using local JSON"
        )
        _available = False
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except Exception as exc:
        logger.error("firebase-admin is not available; using local JSON: %s", exc)
        _available = False
        return False

    options = {"projectId": config.project_id} if config.project_id else None
    try:
        try:
            _app = firebase_admin.get_app()
        except ValueError:
            if cred_path is not None:
                cred = credentials.Certificate(str(cred_path))
                _app = firebase_admin.initialize_app(cred, options=options)
            else:
                _app = firebase_admin.initialize_app(options=options)
        _db = firestore.client()
        _available = True
        logger.info(
            "Firebase Admin initialized for staging project %s",
            config.project_id or ALLOWED_STAGING_PROJECT_ID,
        )
        return True
    except Exception as exc:
        logger.error("Firebase Admin failed; falling back to local JSON: %s", exc)
        _app = None
        _db = None
        _available = False
        return False


def is_production_environment() -> bool:
    return _is_production(load_config())


def firestore_available() -> bool:
    return initialize_firebase()


def _json_safe(data: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(data, default=str))


def save_document(collection: str, doc_id: str, data: dict[str, Any]) -> bool:
    if not collection or not doc_id:
        return False
    if not firestore_available() or _db is None:
        return False
    try:
        _db.collection(collection).document(doc_id).set(_json_safe(data))
        return True
    except Exception as exc:
        logger.error("Firestore write failed for collection %s; using local store: %s", collection, exc)
        return False


def load_document(collection: str, doc_id: str) -> dict[str, Any] | None:
    if not collection or not doc_id:
        return None
    if not firestore_available() or _db is None:
        return None
    try:
        snapshot = _db.collection(collection).document(doc_id).get()
        if not snapshot.exists:
            return None
        payload = snapshot.to_dict() or {}
        return payload if isinstance(payload, dict) else None
    except Exception as exc:
        logger.error("Firestore read failed for collection %s; using local store: %s", collection, exc)
        return None


def save_workflow_state(data: dict[str, Any]) -> bool:
    return save_document(WORKFLOW_COLLECTION, WORKFLOW_DOCUMENT, data)


def load_workflow_state() -> dict[str, Any] | None:
    return load_document(WORKFLOW_COLLECTION, WORKFLOW_DOCUMENT)
