"""Smoke test: the full agency imports, initializes, and wires all 9 agents.

Requires OPENAI_API_KEY because agent initialization talks to OpenAI (vector stores). Auto-skipped
offline via the ``requires_openai`` marker.
"""

import pytest


@pytest.mark.requires_openai
def test_agency_imports_and_wires_nine_agents():
    from agency import agency

    agents = getattr(agency, "agents", None)
    assert agents is not None, "agency has no 'agents' attribute"
    assert len(agents) == 9, f"expected 9 agents, found {len(agents)}"
    assert hasattr(agency, "demo_gradio"), "demo_gradio helper missing from agency"
