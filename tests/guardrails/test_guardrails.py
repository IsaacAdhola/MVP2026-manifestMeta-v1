"""Governance guardrail invariants. These must never regress. No API key required.

See docs/GUARDRAILS.md and docs/adr/0002-governance-guardrails.md.
"""

from pathlib import Path

import config
from FacebookManagerAgent.tools.AdCampaignStarter import AdCampaignStarter
from FacebookManagerAgent.tools.AdSetCreator import AdSetCreator

_ROOT = Path(__file__).resolve().parents[2]


def _field_default(tool_cls, field):
    model_fields = getattr(tool_cls, "model_fields", None)
    if model_fields and field in model_fields:
        return model_fields[field].default
    return tool_cls.__fields__[field].default  # pragma: no cover - pydantic v1 fallback


# Invariant 1: paid objects are created paused by default.
def test_campaign_starter_defaults_to_paused():
    assert _field_default(AdCampaignStarter, "activate_immediately") is False


def test_ad_set_creator_defaults_to_paused():
    assert _field_default(AdSetCreator, "activate_immediately") is False


# Invariant 3: no direct CEO -> Media edge; Media reachable only via Client Approval.
def test_no_direct_ceo_to_media_edge():
    agency_src = (_ROOT / "agency.py").read_text(encoding="utf-8")
    assert "[ceo, facebookManagerAgent]" not in agency_src, (
        "Forbidden direct CEO -> Media Operations edge found in agency.py"
    )
    assert "[clientApprovalAgent, facebookManagerAgent]" in agency_src, (
        "Media Operations must be reachable via Client Approval"
    )


# Runtime backstop: staging blocks live mutations; production allows; unknown fails safe.
def test_staging_blocks_live_mutations(monkeypatch):
    monkeypatch.setenv("MANIFEST_AI_ENV", "staging")
    assert config.live_mutations_allowed() is False
    notice = AdCampaignStarter(campaign_name="Test", budget=1000).run()
    assert isinstance(notice, str) and "BLOCKED" in notice
    assert "staging" in notice


def test_production_allows_live_mutations(monkeypatch):
    monkeypatch.setenv("MANIFEST_AI_ENV", "production")
    assert config.current_env() == "production"
    assert config.live_mutations_allowed() is True


def test_unknown_env_fails_safe_to_staging(monkeypatch):
    monkeypatch.setenv("MANIFEST_AI_ENV", "bogus")
    assert config.current_env() == "staging"
    assert config.live_mutations_allowed() is False


def test_default_env_is_staging(monkeypatch):
    monkeypatch.delenv("MANIFEST_AI_ENV", raising=False)
    assert config.current_env() == "staging"
