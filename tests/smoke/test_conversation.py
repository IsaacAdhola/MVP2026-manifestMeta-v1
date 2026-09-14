"""Smoke test: a scripted client conversation produces real CEO responses.

Exercises the full agency end to end through the Chief Growth Strategist. Requires OPENAI_API_KEY.
Runs in the default ``staging`` profile, so no live Meta mutations occur.
"""

import pytest


def _reply(agency, message: str) -> str:
    """Get a text reply from the agency across Agency Swarm API variants."""
    if hasattr(agency, "get_response_sync"):
        result = agency.get_response_sync(message)
        return str(getattr(result, "final_output", result) or "")
    return str(agency.get_completion(message))


@pytest.mark.requires_openai
def test_client_conversation_smoke():
    from agency import agency

    first = _reply(
        agency,
        "Hi, I run a med spa in Dallas. We do Botox, fillers, and laser treatments. "
        "I want to grow my client base on Facebook. Where do we start?",
    )
    assert first.strip(), "CEO returned an empty first response"

    second = _reply(
        agency,
        "Mostly women 30-55 in North Dallas. Goal is booked appointments. "
        "Could you look into local competitors?",
    )
    assert second.strip(), "CEO returned an empty second response"
