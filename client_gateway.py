"""Shared client-facing turn runner for Gradio, Slack, and the web bridge."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from ImageCreatorAgent.tools.ImageGenerator import DEFAULT_IMAGE_COUNT, MAX_IMAGE_COUNT
from workflow_state import get_brief, get_state_value, isolate_stale_demo_state, set_state_value

ROOT = Path(__file__).resolve().parent
IMAGE_MD = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
CHOICE_MESSAGE = re.compile(
    r"^(option\s*[123]\b|yes\b|yeah\b|yep\b|ok\b|okay\b|"
    r"i like (the )?(first|second|third|option))",
    re.IGNORECASE,
)
DEMO_ENV_VAR = "MANIFEST_AI_DEMO"
_DEMO_TRUTHY = frozenset({"1", "true", "yes", "on"})
RECENT_TURNS_KEY = "recent_founder_turns"
MAX_RECENT_TURNS = 8


def is_choice_message(message: str) -> bool:
    return bool(CHOICE_MESSAGE.search((message or "").strip()))


def remember_founder_turn(message: str) -> None:
    text = (message or "").strip()
    if not text:
        return
    history = get_state_value(RECENT_TURNS_KEY) or []
    if not isinstance(history, list):
        history = []
    history.append(text[:500])
    set_state_value(RECENT_TURNS_KEY, history[-MAX_RECENT_TURNS:])


def build_desk_memory_prefix() -> str:
    """Remind the CEO of this client so Slack DMs stay one conversation."""
    brief = get_brief()
    copies = get_state_value("ad_copy_options") or []
    images = get_state_value("image_options") or []
    campaign_id = get_state_value("campaign_id") or ""
    history = get_state_value(RECENT_TURNS_KEY) or []
    if not brief and not copies and not images and not campaign_id and not history:
        return ""
    lines = [
        "[Desk memory — continue this conversation. Do not restart Welcome/intake "
        "if the business is already known. Do not quote this block to the founder.]",
    ]
    if isinstance(brief, dict) and any(brief.values()):
        lines.append(
            "Known brief: "
            f"business={brief.get('business') or ''} | "
            f"goal={brief.get('campaign_goal') or ''} | "
            f"audience={brief.get('target_customer') or ''} | "
            f"geo={brief.get('geography') or ''} | "
            f"type={brief.get('campaign_type') or ''} | "
            f"platform={brief.get('platform') or ''}."
        )
    if isinstance(copies, list) and copies:
        lines.append(f"{len(copies)} copy options are on file. Option 1/2/3 or 'I like the second copy' selects copy.")
    if isinstance(images, list) and images:
        lines.append(f"{len(images)} image options are on file. Option 1/2/3 selects an image.")
    if campaign_id:
        lines.append(
            f"Meta campaign_id={campaign_id}. "
            "Media can pause/activate/get_status via CampaignLifecycle. "
            "Campaign Ops can walk the dashboard."
        )
    if isinstance(history, list) and history:
        recent = " | ".join(str(item)[:120] for item in history[-4:])
        lines.append(f"Recent founder turns: {recent}")
    lines.append(
        "If the founder does not know audience, competitors, or next step: "
        "run live Ad Library research and recommend. "
        "If they ask to walk campaigns or pause, send Campaign Ops / Media."
    )
    lines.append("Founder said:")
    return "\n".join(lines) + "\n"


def demo_mode_enabled() -> bool:
    return os.getenv(DEMO_ENV_VAR, "").strip().lower() in _DEMO_TRUTHY


def _demo_client_reply(message: str) -> ClientReply:
    return ClientReply(
        text=(
            "[MANIFEST_AI_DEMO] Offline demo reply. "
            "Unset MANIFEST_AI_DEMO so Slack and other live paths run the agency desk. "
            f"Client said: {(message or '')[:500]}"
        )
    )


@dataclass
class ClientReply:
    text: str
    image_paths: list[str] = field(default_factory=list)
    copy_options: list[dict] = field(default_factory=list)
    image_options: list[dict] = field(default_factory=list)

    @property
    def ask_copy_choice(self) -> bool:
        return len(self.copy_options) >= 2

    @property
    def ask_image_choice(self) -> bool:
        return len(self.image_options) >= 2


def ensure_client_facing_assets(output: str) -> str:
    """If specialists produced copy or images, make sure the client actually sees them."""
    text = output or ""
    extras: list[str] = []

    if get_state_value("pending_client_copy"):
        copies = get_state_value("ad_copy_options") or []
        if copies and "Headline:" not in text:
            extras.append("Here are three copy directions for you to choose from.")
            for index, option in enumerate(copies[:3], 1):
                extras.append(
                    f"Option {index}: {option.get('headline', '')}. "
                    f"{option.get('ad_copy', '')}"
                )
            extras.append("Which copy direction should we use — Option 1, 2, or 3?")
        set_state_value("pending_client_copy", False)

    if get_state_value("pending_client_images"):
        images = get_state_value("image_options") or []
        if isinstance(images, list) and images:
            shown_names = {
                Path(raw.strip()).name
                for _alt, raw in IMAGE_MD.findall(text or "")
                if raw.strip()
            }
            missing = []
            for item in images[:MAX_IMAGE_COUNT]:
                if not isinstance(item, dict):
                    continue
                rel = (item.get("image_path") or "").replace("\\", "/")
                if rel and Path(rel).name in shown_names:
                    continue
                missing.append(item)
            if missing:
                extras.append(f"Here are your {len(images)} image options:")
                for item in missing:
                    rel = item.get("image_path") or ""
                    abs_path = (ROOT / rel).resolve() if rel else None
                    shown = abs_path.as_posix() if abs_path and abs_path.exists() else rel
                    note = item.get("creative_note") or ""
                    extras.append(
                        f"Option {item.get('option')}: {note}\n"
                        f"![Option {item.get('option')}]({shown})"
                    )
                choice = (
                    "Which image direction feels right for your brand — Option 1, 2, or 3?"
                    if len(images) == DEFAULT_IMAGE_COUNT
                    else f"Which image direction feels right — pick Option 1 through {len(images)}?"
                )
                extras.append(choice)
        set_state_value("pending_client_images", False)

    if extras:
        return text.rstrip() + "\n\n" + "\n\n".join(extras)
    return text


def collect_image_paths(text: str, extra_options: list | None = None) -> list[str]:
    paths: list[str] = []
    for _alt, raw in IMAGE_MD.findall(text or ""):
        candidate = Path(raw.strip())
        if not candidate.is_absolute():
            candidate = (ROOT / candidate).resolve()
        if candidate.exists() and candidate.as_posix() not in paths:
            paths.append(candidate.as_posix())
    for item in extra_options or []:
        if not isinstance(item, dict):
            continue
        rel = item.get("image_path") or ""
        if not rel:
            continue
        candidate = Path(rel)
        if not candidate.is_absolute():
            candidate = (ROOT / candidate).resolve()
        if candidate.exists() and candidate.as_posix() not in paths:
            paths.append(candidate.as_posix())
    return paths


def run_client_turn(message: str, agency_obj=None, conversation_id: str | None = None) -> ClientReply:
    """Run one client message through the CEO and return a Slack/web-safe reply."""
    if demo_mode_enabled():
        return _demo_client_reply(message)

    if agency_obj is None:
        from agency import agency as agency_obj

    try:
        isolate_stale_demo_state(message)
        if not is_choice_message(message):
            if get_state_value("pending_client_copy"):
                set_state_value("pending_client_copy", False)
            if get_state_value("pending_client_images"):
                set_state_value("pending_client_images", False)

        desk_message = f"{build_desk_memory_prefix()}{message}"
        remember_founder_turn(message)
        output = None
        if conversation_id:
            try:
                from generate_response import generate_response

                output = generate_response(desk_message, conversation_id, agency_obj=agency_obj)
            except Exception:
                output = None
        if output is None:
            result = agency_obj.get_response_sync(desk_message)
            output = str(result.final_output) if getattr(result, "final_output", None) is not None else str(result)
    except Exception as exc:
        from error_logger import log_error

        log_error("Chief Growth Strategist", exc, location="client_gateway.run_client_turn")
        cause = exc.__cause__ or getattr(exc, "__context__", None)
        extra = f" ({type(cause).__name__}: {cause})" if cause else ""
        return ClientReply(text=f"[Error] {exc}{extra}")

    show_copy = bool(get_state_value("pending_client_copy"))
    show_images = bool(get_state_value("pending_client_images"))
    text = ensure_client_facing_assets(output or "(no response)")
    copies = get_state_value("ad_copy_options") or [] if show_copy else []
    images = get_state_value("image_options") or [] if show_images else []
    if not isinstance(copies, list):
        copies = []
    if not isinstance(images, list):
        images = []
    this_turn_images = [item for item in images[:MAX_IMAGE_COUNT] if isinstance(item, dict)]
    collected_paths = collect_image_paths(text, this_turn_images)
    return ClientReply(
        text=text,
        image_paths=collected_paths,
        copy_options=[item for item in copies[:DEFAULT_IMAGE_COUNT] if isinstance(item, dict)],
        image_options=this_turn_images,
    )
