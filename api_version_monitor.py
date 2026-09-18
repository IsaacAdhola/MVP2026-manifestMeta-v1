"""
API Version Monitoring and Safe Upgrade System
Automatically detects API upgrades and manages safe testing and rollout.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from safe_audit_log import write_audit_event


class UpgradeStatus(Enum):
    """Status of an API upgrade"""
    DETECTED = "detected"
    TESTING = "testing"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    REJECTED = "rejected"


_MONITOR_DIR = Path(__file__).resolve().parent / ".api_versions"
_MONITOR_DIR.mkdir(exist_ok=True)


class APIVersionMonitor:
    """
    Monitors API versions and manages safe upgrade testing.
    """
    
    def __init__(self):
        self._state_file = _MONITOR_DIR / "versions.json"
        self._versions: dict[str, dict[str, Any]] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load version state from disk"""
        if self._state_file.exists():
            try:
                self._versions = json.loads(self._state_file.read_text(encoding="utf-8"))
            except Exception:
                self._versions = {}
    
    def _save_state(self) -> None:
        """Save version state to disk"""
        self._state_file.write_text(
            json.dumps(self._versions, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
    
    def check_for_updates(self) -> dict[str, Any]:
        """
        Check PyPI for package updates.
        Returns dict of package -> current_version, latest_version
        """
        updates = {}
        
        try:
            # Check openai package
            result = subprocess.run(
                ["pip", "index", "versions", "openai"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Parse output to get latest version
                for line in result.stdout.split("\n"):
                    if "Available versions:" in line:
                        # Extract first (latest) version
                        versions = line.split(":")[1].strip().split(",")
                        if versions:
                            latest = versions[0].strip()
                            updates["openai"] = {
                                "current": self._get_installed_version("openai"),
                                "latest": latest,
                                "checked_at": datetime.now(timezone.utc).isoformat(),
                            }
        except Exception as e:
            write_audit_event(
                event_type="version_check_failed",
                actor="api_version_monitor",
                outcome="error",
                details={"package": "openai", "error": str(e)},
            )
        
        return updates
    
    def _get_installed_version(self, package: str) -> str:
        """Get currently installed version of a package"""
        try:
            result = subprocess.run(
                ["pip", "show", package],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":")[1].strip()
        except Exception:
            pass
        return "unknown"
    
    def detect_upgrade(
        self,
        package: str,
        current_version: str,
        new_version: str,
    ) -> str:
        """
        Detect a new API version.
        Returns upgrade_id for tracking.
        """
        upgrade_id = f"{package}_{new_version}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        
        self._versions[upgrade_id] = {
            "package": package,
            "current_version": current_version,
            "new_version": new_version,
            "status": UpgradeStatus.DETECTED.value,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "test_results": [],
            "cost_comparison": None,
            "quality_comparison": None,
        }
        
        self._save_state()
        
        write_audit_event(
            event_type="api_upgrade_detected",
            actor="api_version_monitor",
            outcome="detected",
            details={
                "package": package,
                "current": current_version,
                "new": new_version,
                "upgrade_id": upgrade_id,
            },
        )
        
        return upgrade_id
    
    def record_test_result(
        self,
        upgrade_id: str,
        test_name: str,
        passed: bool,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record result of an upgrade test"""
        if upgrade_id not in self._versions:
            return
        
        self._versions[upgrade_id]["test_results"].append({
            "test_name": test_name,
            "passed": passed,
            "details": details or {},
            "tested_at": datetime.now(timezone.utc).isoformat(),
        })
        
        self._save_state()
    
    def should_auto_upgrade(self, upgrade_id: str) -> bool:
        """
        Determine if upgrade should be automatically applied.
        Auto-upgrade criteria:
        - All tests pass
        - Cost neutral or cheaper
        - Performance equal or better
        - Backward compatible
        """
        if upgrade_id not in self._versions:
            return False
        
        upgrade = self._versions[upgrade_id]
        
        # Check all tests passed
        test_results = upgrade.get("test_results", [])
        if not test_results:
            return False
        
        all_passed = all(t.get("passed", False) for t in test_results)
        if not all_passed:
            return False
        
        # Check cost
        cost_comp = upgrade.get("cost_comparison")
        if cost_comp and cost_comp.get("new_cost", 999) > cost_comp.get("current_cost", 0):
            return False  # More expensive = no auto-upgrade
        
        # Check quality
        quality_comp = upgrade.get("quality_comparison")
        if quality_comp and quality_comp.get("new_quality", 0) < quality_comp.get("current_quality", 100):
            return False  # Lower quality = no auto-upgrade
        
        return True
    
    def approve_upgrade(self, upgrade_id: str, approved_by: str) -> None:
        """Manually approve an upgrade"""
        if upgrade_id not in self._versions:
            return
        
        self._versions[upgrade_id]["status"] = UpgradeStatus.APPROVED.value
        self._versions[upgrade_id]["approved_by"] = approved_by
        self._versions[upgrade_id]["approved_at"] = datetime.now(timezone.utc).isoformat()
        
        self._save_state()
        
        write_audit_event(
            event_type="api_upgrade_approved",
            actor=approved_by,
            outcome="approved",
            details={"upgrade_id": upgrade_id},
        )
    
    def get_pending_upgrades(self) -> list[dict[str, Any]]:
        """Get all upgrades pending approval"""
        pending = []
        for upgrade_id, upgrade in self._versions.items():
            if upgrade["status"] in [UpgradeStatus.DETECTED.value, UpgradeStatus.TESTING.value]:
                pending.append({
                    "upgrade_id": upgrade_id,
                    **upgrade,
                })
        return pending


# Global monitor instance
_monitor = APIVersionMonitor()


def get_version_monitor() -> APIVersionMonitor:
    """Get global version monitor instance"""
    return _monitor


__all__ = [
    "APIVersionMonitor",
    "UpgradeStatus",
    "get_version_monitor",
]
