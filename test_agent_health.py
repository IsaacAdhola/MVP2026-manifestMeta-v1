"""Agency health diagnostic — second-pass proof the desk is fixed.

Run (PowerShell, from the nested agency folder):

    $env:PYTHONPATH = "c:\\Users\\New\\Downloads\\MVP2026-manifestMeta-master;c:\\Users\\New\\Downloads\\MVP2026-manifestMeta-master\\MVP2026-manifestMeta-master"
    python test_agent_health.py
    python -m pytest test_agent_health.py test_dalle_client_images.py -v

Prints a per-agent report. Exits non-zero on any failure. Never prints API keys.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

NESTED = Path(__file__).resolve().parent
ROOT = NESTED.parent
for _path in (str(NESTED), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from client_gateway import DEMO_ENV_VAR, demo_mode_enabled, run_client_turn
from ImageCreatorAgent.tools.ImageGenerator import (
    DALLE_IMAGES_PER_API_CALL,
    DEFAULT_IMAGE_COUNT,
    MISSING_OPENAI_KEY_MESSAGE,
    ImageGenerator,
    build_client_image_prompt,
)
from workflow_state import isolate_stale_demo_state

TRAIL_SHOE_BRIEF = "3 DALL-E ads for a trail running shoe"
SECRET_MARKERS = ("sk-proj-", "sk-live-", "xoxb-", "xapp-", "BEGIN PRIVATE KEY")
COFFEE_DEFAULT_MARKERS = (
    'default="coffee',
    "default='coffee",
    "ad_copy=\"Fresh coffee",
    "visual_prompt=\"coffee",
)

DESK_AGENTS = (
    {
        "role": "Chief Growth Strategist",
        "package": "MetaMarkCEO",
        "class_name": "MetaMarkCEO",
        "folder": "MetaMarkCEO",
        "required_tools": ("ClientBriefRecorder",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Market Intelligence Director",
        "package": "ResearchAgent",
        "class_name": "ResearchAgent",
        "folder": "ResearchAgent",
        "required_tools": ("InDepthMarketResearch",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Cultural Intelligence Director",
        "package": "CulturalIntelligenceAgent",
        "class_name": "CulturalIntelligenceAgent",
        "folder": "CulturalIntelligenceAgent",
        "required_tools": ("TrendVoiceBrief",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Search & Answer Visibility Director",
        "package": "SearchVisibilityAgent",
        "class_name": "SearchVisibilityAgent",
        "folder": "SearchVisibilityAgent",
        "required_tools": ("SearchVisibilityBriefBuilder",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Senior Conversion Copywriter",
        "package": "AdCopyAgent",
        "class_name": "AdCopyAgent",
        "folder": "AdCopyAgent",
        "required_tools": ("AdCopyGenerator",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Landing Page & CRO Director",
        "package": "ConversionPageAgent",
        "class_name": "ConversionPageAgent",
        "folder": "ConversionPageAgent",
        "required_tools": ("LandingPageBriefBuilder",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Creative Director",
        "package": "ImageCreatorAgent",
        "class_name": "ImageCreatorAgent",
        "folder": "ImageCreatorAgent",
        "required_tools": ("ImageGenerator", "ImageSelector"),
        "must_not_hardcode_coffee": True,
        "owns_images": True,
    },
    {
        "role": "Facebook Policy Compliance Officer",
        "package": "FacebookPolicyAgent",
        "class_name": "FacebookPolicyAgent",
        "folder": "FacebookPolicyAgent",
        "required_tools": ("FacebookPolicyChecklist",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Client Approval Manager",
        "package": "ClientApprovalAgent",
        "class_name": "ClientApprovalAgent",
        "folder": "ClientApprovalAgent",
        "required_tools": ("ClientApprovalChecklist",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Media Operations Director",
        "package": "FacebookManagerAgent",
        "class_name": "FacebookManagerAgent",
        "folder": "FacebookManagerAgent",
        "required_tools": ("ExecuteApprovedMedia", "PauseClaimPlacements", "CampaignLifecycle"),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Campaign Operations Director",
        "package": "CampaignOpsAgent",
        "class_name": "CampaignOpsAgent",
        "folder": "CampaignOpsAgent",
        "required_tools": ("CampaignDashboard",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Community Manager",
        "package": "CommunityManagerAgent",
        "class_name": "CommunityManagerAgent",
        "folder": "CommunityManagerAgent",
        "required_tools": ("CommentReplyDrafts",),
        "must_not_hardcode_coffee": True,
    },
    {
        "role": "Performance Analyst",
        "package": "PerformanceAnalystAgent",
        "class_name": "PerformanceAnalystAgent",
        "folder": "PerformanceAnalystAgent",
        "required_tools": ("PerformanceInsightBuilder",),
        "must_not_hardcode_coffee": True,
    },
)


def _tool_stems(folder: str) -> list[str]:
    tools_dir = NESTED / folder / "tools"
    if not tools_dir.is_dir():
        return []
    return sorted(
        path.stem
        for path in tools_dir.glob("*.py")
        if path.stem != "__init__"
    )


def _read_text(relative: str) -> str:
    return (NESTED / relative).read_text(encoding="utf-8")


def _source_has_secret(text: str) -> bool:
    return any(marker in text for marker in SECRET_MARKERS)


def _source_has_coffee_default(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in COFFEE_DEFAULT_MARKERS)


def inspect_agent(spec: dict) -> dict:
    errors: list[str] = []
    folder = spec["folder"]
    tools = _tool_stems(folder)
    instructions_path = Path(folder) / "instructions.md"
    imported = False
    role = spec["role"]
    try:
        module = __import__(spec["package"], fromlist=[spec["class_name"]])
        cls = getattr(module, spec["class_name"])
        agent = cls()
        imported = True
        if getattr(agent, "name", "") != role:
            errors.append(f"name mismatch: {getattr(agent, 'name', '')!r} != {role!r}")
    except Exception as exc:
        errors.append(f"import/init failed: {type(exc).__name__}: {exc}")

    for required in spec["required_tools"]:
        if required not in tools:
            errors.append(f"missing tool {required}")

    if not instructions_path.exists():
        errors.append("instructions.md missing")
    else:
        instructions = _read_text(str(instructions_path))
        if _source_has_secret(instructions):
            errors.append("instructions contain a secret marker")
        if spec.get("owns_images"):
            if "dall-e" not in instructions.lower():
                errors.append("image agent instructions omit DALL-E")
            if "visual_prompt" not in instructions:
                errors.append("image agent instructions omit visual_prompt")

    tool_sources = []
    for stem in tools:
        path = NESTED / folder / "tools" / f"{stem}.py"
        body = path.read_text(encoding="utf-8")
        tool_sources.append(body)
        if _source_has_secret(body):
            errors.append(f"{stem} contains a secret marker")
        if spec["must_not_hardcode_coffee"] and _source_has_coffee_default(body):
            errors.append(f"{stem} hardcodes a coffee default")

    if spec.get("owns_images"):
        if DEFAULT_IMAGE_COUNT != 3:
            errors.append(f"DEFAULT_IMAGE_COUNT is {DEFAULT_IMAGE_COUNT}, expected 3")
        if DALLE_IMAGES_PER_API_CALL != 1:
            errors.append("DALL-E must request n=1 per API call and loop for options")
        tool = ImageGenerator(visual_prompt=TRAIL_SHOE_BRIEF)
        if tool.image_count != DEFAULT_IMAGE_COUNT:
            errors.append(f"ImageGenerator default count is {tool.image_count}")
        prompt = build_client_image_prompt(visual_prompt=TRAIL_SHOE_BRIEF)
        if "trail running shoe" not in prompt.lower():
            errors.append("image prompt dropped the client subject")
        if "coffee" in prompt.lower():
            errors.append("image prompt injected coffee")

    return {
        "role": role,
        "status": "PASS" if not errors else "FAIL",
        "tools": tools,
        "imported": imported,
        "errors": errors,
    }


def inspect_demo_gate() -> dict:
    errors: list[str] = []
    previous = os.environ.pop(DEMO_ENV_VAR, None)
    try:
        if demo_mode_enabled():
            errors.append("demo gate is ON by default")
    finally:
        if previous is not None:
            os.environ[DEMO_ENV_VAR] = previous
    return {
        "role": "Demo gate",
        "status": "PASS" if not errors else "FAIL",
        "tools": [DEMO_ENV_VAR],
        "imported": True,
        "errors": errors,
    }


def inspect_missing_key() -> dict:
    errors: list[str] = []
    previous = os.environ.pop("OPENAI_API_KEY", None)
    try:
        ImageGenerator(visual_prompt=TRAIL_SHOE_BRIEF).run()
        errors.append("missing OPENAI_API_KEY did not raise")
    except RuntimeError as exc:
        if "OPENAI_API_KEY" not in str(exc):
            errors.append(f"missing-key error was unclear: {exc}")
        if "coffee" in str(exc).lower():
            errors.append("missing-key error fell back to coffee")
        if "OPENAI_API_KEY" not in MISSING_OPENAI_KEY_MESSAGE:
            errors.append("MISSING_OPENAI_KEY_MESSAGE is not honest")
    except Exception as exc:
        errors.append(f"missing key raised {type(exc).__name__}: {exc}")
    finally:
        if previous is not None:
            os.environ["OPENAI_API_KEY"] = previous
    return {
        "role": "ImageGenerator missing key",
        "status": "PASS" if not errors else "FAIL",
        "tools": ["ImageGenerator"],
        "imported": True,
        "errors": errors,
    }


def inspect_second_pass_client_turn(tmp_dir: Path) -> dict:
    import workflow_state

    errors: list[str] = []
    state_file = tmp_dir / ".workflow_state.json"
    leftover = {
        "ad_copy": "Fresh coffee, roasted weekly. Unpublished test creative.",
        "image_options": [
            {
                "option": 1,
                "image_path": "generated_assets/images/atlas_peak_coffee.png",
                "creative_note": "Atlas Peak leftover",
            }
        ],
        "campaign_id": "52506749995438",
        "cultural_voice_brief": "cortado before stand-up",
        "pending_client_copy": False,
        "pending_client_images": False,
    }
    state_file.write_text(json.dumps(leftover), encoding="utf-8")
    original_state = workflow_state._STATE_FILE
    original_save = workflow_state.save_workflow_state
    workflow_state._STATE_FILE = state_file
    workflow_state.save_workflow_state = lambda data: False
    original_root = None
    import client_gateway

    original_root = client_gateway.ROOT
    client_gateway.ROOT = tmp_dir
    try:
        removed = isolate_stale_demo_state(TRAIL_SHOE_BRIEF)
        if "ad_copy" not in removed:
            errors.append("stale coffee ad_copy was not isolated")

        class _Agency:
            def get_response_sync(self, message: str):
                if "trail running shoe" not in message.lower():
                    raise AssertionError(f"agency did not receive client brief: {message}")
                options = []
                for index in range(1, DEFAULT_IMAGE_COUNT + 1):
                    image = tmp_dir / f"trail_shoe_{index}.png"
                    image.write_bytes(b"png")
                    options.append(
                        {
                            "option": index,
                            "image_path": image.as_posix(),
                            "creative_note": f"trail running shoe direction {index}",
                        }
                    )
                workflow_state.set_state_value("image_options", options)
                workflow_state.set_state_value("pending_client_images", True)
                return SimpleNamespace(final_output="Option 1 only\n")

        os.environ.pop(DEMO_ENV_VAR, None)
        reply = run_client_turn(TRAIL_SHOE_BRIEF, _Agency())
        if "[MANIFEST_AI_DEMO]" in reply.text:
            errors.append("live turn used the canned demo path")
        if "coffee" in reply.text.lower() or "atlas peak" in reply.text.lower():
            errors.append("client reply leaked leftover coffee demo")
        if len(reply.image_options) != DEFAULT_IMAGE_COUNT:
            errors.append(
                f"expected {DEFAULT_IMAGE_COUNT} images, got {len(reply.image_options)}"
            )
        if not reply.ask_image_choice:
            errors.append("client was not asked to choose among image options")
        leftover_after = json.loads(state_file.read_text(encoding="utf-8"))
        if "fresh coffee" in json.dumps(leftover_after).lower():
            errors.append("shared state still holds leftover coffee copy")
    except Exception as exc:
        errors.append(f"second-pass turn failed: {type(exc).__name__}: {exc}")
    finally:
        workflow_state._STATE_FILE = original_state
        workflow_state.save_workflow_state = original_save
        if original_root is not None:
            client_gateway.ROOT = original_root
    return {
        "role": "Second-pass client turn",
        "status": "PASS" if not errors else "FAIL",
        "tools": ["run_client_turn", "isolate_stale_demo_state", "ImageGenerator"],
        "imported": True,
        "errors": errors,
    }


def collect_report(tmp_dir: Path | None = None) -> list[dict]:
    rows = [inspect_agent(spec) for spec in DESK_AGENTS]
    rows.append(inspect_demo_gate())
    rows.append(inspect_missing_key())
    if tmp_dir is not None:
        rows.append(inspect_second_pass_client_turn(tmp_dir))
        return rows
    import tempfile

    with tempfile.TemporaryDirectory(prefix="manifest_agent_health_") as raw:
        rows.append(inspect_second_pass_client_turn(Path(raw)))
    return rows


def format_report(rows: list[dict]) -> str:
    lines = [
        "Manifest AI / MetaMark agent health",
        f"Image contract: DEFAULT_IMAGE_COUNT={DEFAULT_IMAGE_COUNT} "
        f"DALLE_IMAGES_PER_API_CALL={DALLE_IMAGES_PER_API_CALL}",
        f"Demo gate default: {'ON' if demo_mode_enabled() else 'OFF'} ({DEMO_ENV_VAR})",
        f"Client brief under test: {TRAIL_SHOE_BRIEF}",
        "",
    ]
    for row in rows:
        tools = ", ".join(row["tools"]) if row["tools"] else "(none)"
        lines.append(f"{row['status']}  {row['role']}")
        lines.append(f"      tools: {tools}")
        if row["errors"]:
            for error in row["errors"]:
                lines.append(f"      ERROR: {error}")
        else:
            lines.append("      last error: none")
    failed = sum(1 for row in rows if row["status"] == "FAIL")
    lines.append("")
    lines.append(f"Result: {failed} failed / {len(rows)} checked")
    return "\n".join(lines)


def test_every_desk_agent_imports_and_has_tools() -> None:
    rows = [inspect_agent(spec) for spec in DESK_AGENTS]
    failed = [row for row in rows if row["status"] == "FAIL"]
    assert not failed, format_report(rows)


def test_demo_gate_off_and_missing_key_is_honest() -> None:
    demo = inspect_demo_gate()
    key = inspect_missing_key()
    failed = [row for row in (demo, key) if row["status"] == "FAIL"]
    assert not failed, format_report([demo, key])


def test_second_pass_trail_shoe_turn(tmp_path: Path) -> None:
    row = inspect_second_pass_client_turn(tmp_path)
    assert row["status"] == "PASS", format_report([row])


if __name__ == "__main__":
    report_rows = collect_report()
    print(format_report(report_rows))
    if any(row["status"] == "FAIL" for row in report_rows):
        raise SystemExit(1)
    raise SystemExit(0)
