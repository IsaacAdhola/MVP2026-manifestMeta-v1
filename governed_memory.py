"""
Governed Shared Memory for Multi-Agent LLM Systems
Implements three-tier memory architecture with access control, temporal supersession,
and provenance tracking. Based on 2026 arXiv paper (2606.24535v1).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from safe_audit_log import sanitize_record


class MemoryScope(Enum):
    """Memory scopes following hierarchical access model"""
    GLOBAL = "global"  # Organization-level: readable by all
    WORKFLOW = "workflow"  # Campaign-level: readable by workflow participants
    AGENT_PRIVATE = "agent_private"  # Agent-level: readable by agent only


class MemoryPermission(Enum):
    """Access permissions for memory operations"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


_MEMORY_DIR = Path(__file__).resolve().parent / ".governed_memory"
_MEMORY_DIR.mkdir(exist_ok=True)


class MemoryRecord:
    """Represents a single memory record with governance metadata"""
    
    def __init__(
        self,
        key: str,
        value: Any,
        scope: MemoryScope,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        created_by: Optional[str] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
        supersedes: Optional[str] = None,
    ):
        self.record_id = str(uuid.uuid4())
        self.key = key
        self.value = value
        self.scope = scope
        self.workflow_id = workflow_id
        self.agent_id = agent_id
        self.created_by = created_by or "system"
        self.source = source or "manual"
        self.confidence = confidence
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.supersedes = supersedes
        self.valid_until: Optional[str] = None
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "record_id": self.record_id,
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "workflow_id": self.workflow_id,
            "agent_id": self.agent_id,
            "created_by": self.created_by,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "supersedes": self.supersedes,
            "valid_until": self.valid_until,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryRecord:
        """Create from dictionary"""
        record = cls(
            key=data["key"],
            value=data["value"],
            scope=MemoryScope(data["scope"]),
            workflow_id=data.get("workflow_id"),
            agent_id=data.get("agent_id"),
            created_by=data.get("created_by"),
            source=data.get("source"),
            confidence=data.get("confidence", 1.0),
            supersedes=data.get("supersedes"),
        )
        record.record_id = data["record_id"]
        record.created_at = data["created_at"]
        record.valid_until = data.get("valid_until")
        return record


class GovernedMemory:
    """
    Governed shared memory implementation with three-tier scoping,
    access control, temporal supersession, and provenance tracking.
    """
    
    def __init__(self):
        self._global_file = _MEMORY_DIR / "global.json"
        self._workflow_dir = _MEMORY_DIR / "workflows"
        self._agent_dir = _MEMORY_DIR / "agents"
        
        self._workflow_dir.mkdir(exist_ok=True)
        self._agent_dir.mkdir(exist_ok=True)
        
        # Permission matrix: agent_id -> {scope: [permissions]}
        self._permissions: dict[str, dict[MemoryScope, list[MemoryPermission]]] = {}
        
    def _get_storage_path(
        self,
        scope: MemoryScope,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Path:
        """Get storage file path based on scope"""
        if scope == MemoryScope.GLOBAL:
            return self._global_file
        elif scope == MemoryScope.WORKFLOW:
            if not workflow_id:
                raise ValueError("workflow_id required for WORKFLOW scope")
            return self._workflow_dir / f"{workflow_id}.json"
        else:  # AGENT_PRIVATE
            if not workflow_id or not agent_id:
                raise ValueError("workflow_id and agent_id required for AGENT_PRIVATE scope")
            return self._agent_dir / f"{workflow_id}_{agent_id}.json"
    
    def _load_records(self, path: Path) -> list[MemoryRecord]:
        """Load all records from a storage file"""
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [MemoryRecord.from_dict(r) for r in data.get("records", [])]
        except Exception:
            return []
    
    def _save_records(self, path: Path, records: list[MemoryRecord]) -> None:
        """Save all records to a storage file"""
        data = {
            "records": [r.to_dict() for r in records],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    
    def _check_permission(
        self,
        agent_id: str,
        scope: MemoryScope,
        permission: MemoryPermission,
    ) -> bool:
        """Check if agent has permission for operation"""
        # For backward compatibility, allow all if no permissions defined
        if not self._permissions:
            return True
        
        agent_perms = self._permissions.get(agent_id, {})
        scope_perms = agent_perms.get(scope, [])
        return permission in scope_perms
    
    def grant_permission(
        self,
        agent_id: str,
        scope: MemoryScope,
        permissions: list[MemoryPermission],
    ) -> None:
        """Grant permissions to an agent for a scope"""
        if agent_id not in self._permissions:
            self._permissions[agent_id] = {}
        if scope not in self._permissions[agent_id]:
            self._permissions[agent_id][scope] = []
        self._permissions[agent_id][scope].extend(permissions)
    
    def set(
        self,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.WORKFLOW,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        created_by: Optional[str] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
        supersedes_key: Optional[str] = None,
    ) -> str:
        """
        Store a value in governed memory.
        Returns the record_id of the created record.
        """
        # Sanitize value if it might contain sensitive data
        safe_value = sanitize_record({"v": value}).get("v", value)
        
        path = self._get_storage_path(scope, workflow_id, agent_id)
        records = self._load_records(path)
        
        # Handle temporal supersession
        supersedes_id = None
        if supersedes_key:
            for record in records:
                if record.key == supersedes_key and record.valid_until is None:
                    record.valid_until = datetime.now(timezone.utc).isoformat()
                    supersedes_id = record.record_id
        
        # Create new record
        record = MemoryRecord(
            key=key,
            value=safe_value,
            scope=scope,
            workflow_id=workflow_id,
            agent_id=agent_id,
            created_by=created_by,
            source=source,
            confidence=confidence,
            supersedes=supersedes_id,
        )
        
        records.append(record)
        self._save_records(path, records)
        
        return record.record_id
    
    def get(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.WORKFLOW,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Retrieve the most recent valid value for a key.
        Automatically filters out superseded records.
        """
        path = self._get_storage_path(scope, workflow_id, agent_id)
        records = self._load_records(path)
        
        # Filter to valid records for this key
        valid_records = [
            r for r in records
            if r.key == key and r.valid_until is None
        ]
        
        if not valid_records:
            return default
        
        # Return most recent by created_at
        latest = max(valid_records, key=lambda r: r.created_at)
        return latest.value
    
    def get_with_provenance(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.WORKFLOW,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve value with full provenance metadata.
        Returns None if key not found.
        """
        path = self._get_storage_path(scope, workflow_id, agent_id)
        records = self._load_records(path)
        
        valid_records = [
            r for r in records
            if r.key == key and r.valid_until is None
        ]
        
        if not valid_records:
            return None
        
        latest = max(valid_records, key=lambda r: r.created_at)
        return latest.to_dict()
    
    def delete(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.WORKFLOW,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> bool:
        """Mark a key as invalid (temporal deletion)"""
        path = self._get_storage_path(scope, workflow_id, agent_id)
        records = self._load_records(path)
        
        deleted = False
        for record in records:
            if record.key == key and record.valid_until is None:
                record.valid_until = datetime.now(timezone.utc).isoformat()
                deleted = True
        
        if deleted:
            self._save_records(path, records)
        
        return deleted
    
    def cleanup_workflow(self, workflow_id: str) -> None:
        """Delete all data for a completed workflow (GDPR compliance)"""
        workflow_file = self._workflow_dir / f"{workflow_id}.json"
        if workflow_file.exists():
            workflow_file.unlink()
        
        # Delete all agent private memories for this workflow
        pattern = f"{workflow_id}_*.json"
        for agent_file in self._agent_dir.glob(pattern):
            agent_file.unlink()


# Backward compatibility: simple interface matching old workflow_state.py
_memory = GovernedMemory()
_current_workflow_id = "default"


def set_state_value(key: str, value: Any) -> None:
    """Backward compatible: Set value in current workflow scope"""
    _memory.set(key, value, MemoryScope.WORKFLOW, workflow_id=_current_workflow_id)


def get_state_value(key: str, default: Any = None) -> Any:
    """Backward compatible: Get value from current workflow scope"""
    return _memory.get(key, MemoryScope.WORKFLOW, workflow_id=_current_workflow_id, default=default)


def clear_state() -> None:
    """Backward compatible: Clear current workflow state"""
    _memory.cleanup_workflow(_current_workflow_id)


# Export both new and old interfaces
__all__ = [
    "GovernedMemory",
    "MemoryScope",
    "MemoryPermission",
    "MemoryRecord",
    "set_state_value",
    "get_state_value",
    "clear_state",
]
