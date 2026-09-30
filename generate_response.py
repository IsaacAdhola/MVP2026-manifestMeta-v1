"""Generate an agency reply and persist Slack conversation threads.

v1 removed `Agency.get_completion`. This helper is the public "generate response /
get completion" entry for later Slack HTTP integration. It uses
`Agency.get_response_sync` and v1 `ThreadManager` load/save callbacks.

`conversation_id` is the Slack thread timestamp (`thread_ts`). Existing Socket Mode
in `slack_app.py` is unchanged.
"""

from __future__ import annotations

from typing import Any

from agency_swarm.utils.thread import ThreadManager

from thread_store import get_threads, init_thread_store, save_threads


def generate_response(
    message: str,
    conversation_id: str,
    *,
    agency_obj: Any | None = None,
) -> str:
    """Send `message` through the agency, continuing Slack thread `conversation_id`."""
    cid = str(conversation_id or "").strip()
    if not cid:
        raise ValueError("conversation_id is required (use the Slack thread timestamp)")
    if agency_obj is None:
        from agency import agency as live_agency

        agency_obj = live_agency

    init_thread_store()

    thread_manager = ThreadManager(
        load_threads_callback=lambda: get_threads(cid),
        save_threads_callback=lambda threads: save_threads(cid, threads),
    )
    entry = agency_obj.entry_points[0]
    agency_context = agency_obj.get_agent_context(
        entry.name,
        thread_manager_override=thread_manager,
    )
    result = agency_obj.get_response_sync(
        message,
        agency_context_override=agency_context,
    )
    save_threads(cid, thread_manager.get_all_messages())
    if getattr(result, "final_output", None) is not None:
        return str(result.final_output)
    return str(result)


get_completion = generate_response
