"""Client image generation: three DALL-E images, client prompt, live desk reasoning."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_NESTED = Path(__file__).resolve().parent
_ROOT = _NESTED.parent
for _path in (str(_NESTED), str(_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import client_gateway
from ImageCreatorAgent.tools.ImageGenerator import (
    DEFAULT_IMAGE_COUNT,
    MAX_IMAGE_COUNT,
    MISSING_OPENAI_KEY_MESSAGE,
    ImageGenerator,
    build_client_image_prompt,
    parse_concept_briefs,
    resolve_image_count,
)
from manifest_types.request_types import (
    DEMO_ENV_VAR,
    DEFAULT_IMAGE_COUNT as TYPE_DEFAULT_IMAGE_COUNT,
    GenerateClientImagesRequest,
)


TINY_PNG_B64 = base64.b64encode(b"fake-png-bytes").decode("ascii")


def _state_patches(monkeypatch, module, store: dict) -> None:
    def getter(key, default=None):
        return store.get(key, default)

    def setter(key, value):
        store[key] = value

    monkeypatch.setattr(module, "get_state_value", getter)
    monkeypatch.setattr(module, "set_state_value", setter)
    if hasattr(module, "get_brief"):
        monkeypatch.setattr(module, "get_brief", lambda: store.get("client_brief") or {})


def _fake_dalle_client(monkeypatch, module, tmp_path) -> MagicMock:
    image = SimpleNamespace(b64_json=TINY_PNG_B64, url=None)
    client = MagicMock()
    client.with_options.return_value = client
    client.images.generate.return_value = SimpleNamespace(data=[image])
    monkeypatch.setattr(module, "_get_openai_client", lambda: client)
    monkeypatch.setattr(module, "_IMAGE_OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(module, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    return client


class TestImageCountContract:
    def test_named_default_is_three(self) -> None:
        assert DEFAULT_IMAGE_COUNT == 3
        assert TYPE_DEFAULT_IMAGE_COUNT == 3
        tool = ImageGenerator(visual_prompt="people reading in a library")
        assert tool.image_count == DEFAULT_IMAGE_COUNT

    def test_types_default_is_three(self) -> None:
        req = GenerateClientImagesRequest(visual_prompt="a red bicycle on a city street")
        assert req.image_count == DEFAULT_IMAGE_COUNT

    def test_honors_client_requested_count(self) -> None:
        assert resolve_image_count(1) == 1
        assert resolve_image_count(5) == 5
        assert resolve_image_count(None) == DEFAULT_IMAGE_COUNT
        assert resolve_image_count(99) == MAX_IMAGE_COUNT


class TestClientPromptNotCoffee:
    def test_prompt_uses_client_brief_not_coffee(self) -> None:
        prompt = build_client_image_prompt(
            visual_prompt="people reading in a quiet library",
            theme="editorial photography",
        )
        lowered = prompt.lower()
        assert "people reading" in lowered
        assert "library" in lowered
        assert "coffee" not in lowered
        assert "latte" not in lowered
        assert "atlas peak" not in lowered

    def test_run_ignores_leftover_coffee_state(self, monkeypatch, tmp_path) -> None:
        import ImageCreatorAgent.tools.ImageGenerator as ig

        store: dict = {}
        monkeypatch.setattr(ig, "set_state_value", lambda key, value: store.__setitem__(key, value))
        client = _fake_dalle_client(monkeypatch, ig, tmp_path)
        tool = ImageGenerator(
            visual_prompt="people reading in a quiet library",
            theme="editorial photography",
            ad_copy="",
        )
        tool.run()
        assert client.images.generate.call_count == DEFAULT_IMAGE_COUNT
        for call in client.images.generate.call_args_list:
            prompt = call.kwargs["prompt"].lower()
            assert "people reading" in prompt
            assert "coffee" not in prompt
            assert "latte" not in prompt
            assert "atlas peak" not in prompt
            assert call.kwargs["n"] == 1
            assert call.kwargs["model"] == "dall-e-3"
        assert len(store.get("image_options") or []) == DEFAULT_IMAGE_COUNT


class TestDalleRun:
    def test_missing_openai_key_fails_clearly(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        tool = ImageGenerator(visual_prompt="a red bicycle")
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            tool.run()

    def test_missing_key_message_is_stable(self) -> None:
        assert "OPENAI_API_KEY" in MISSING_OPENAI_KEY_MESSAGE
        assert "coffee" not in MISSING_OPENAI_KEY_MESSAGE.lower()


class TestDemoGateAndAgencyTurn:
    def test_demo_mode_off_by_default(self, monkeypatch) -> None:
        monkeypatch.delenv(DEMO_ENV_VAR, raising=False)
        monkeypatch.delenv("MANIFEST_AI_DEMO", raising=False)
        assert client_gateway.demo_mode_enabled() is False

    def test_live_path_invokes_agency_not_canned_demo(self, monkeypatch) -> None:
        monkeypatch.delenv("MANIFEST_AI_DEMO", raising=False)
        store = {
            "pending_client_copy": False,
            "pending_client_images": False,
            "ad_copy_options": [],
            "image_options": [],
        }
        _state_patches(monkeypatch, client_gateway, store)
        monkeypatch.setattr(client_gateway, "isolate_stale_demo_state", lambda message="": [])
        agency = MagicMock()
        agency.get_response_sync.return_value = SimpleNamespace(
            final_output="Here is a plan for people reading in a library."
        )
        reply = client_gateway.run_client_turn(
            "make three images of people reading",
            agency,
        )
        agency.get_response_sync.assert_called_once()
        assert "make three images of people reading" in agency.get_response_sync.call_args[0][0]
        assert "people reading" in reply.text
        assert "coffee" not in reply.text.lower()
        assert "[MANIFEST_AI_DEMO]" not in reply.text

    def test_demo_mode_skips_agency_when_explicitly_enabled(self, monkeypatch) -> None:
        monkeypatch.setenv("MANIFEST_AI_DEMO", "1")
        agency = MagicMock()
        reply = client_gateway.run_client_turn("make three images of people reading", agency)
        agency.get_response_sync.assert_not_called()
        assert "[MANIFEST_AI_DEMO]" in reply.text

    def test_gateway_fills_in_missing_image_options(self, monkeypatch, tmp_path) -> None:
        monkeypatch.delenv("MANIFEST_AI_DEMO", raising=False)
        option_paths = []
        for index in range(1, 4):
            path = tmp_path / f"option_{index}.png"
            path.write_bytes(b"png")
            option_paths.append(path.as_posix())
        store = {
            "pending_client_copy": False,
            "pending_client_images": True,
            "ad_copy_options": [],
            "image_options": [
                {
                    "option": index,
                    "image_path": option_paths[index - 1],
                    "creative_note": f"direction {index}",
                }
                for index in range(1, 4)
            ],
        }
        _state_patches(monkeypatch, client_gateway, store)
        monkeypatch.setattr(client_gateway, "isolate_stale_demo_state", lambda message="": [])
        monkeypatch.setattr(client_gateway, "ROOT", tmp_path)

        def _this_turn(_message: str):
            store["pending_client_images"] = True
            return SimpleNamespace(final_output=f"Option 1\n![Option 1]({option_paths[0]})")

        agency = MagicMock()
        agency.get_response_sync.side_effect = _this_turn
        reply = client_gateway.run_client_turn("show the images", agency)
        assert reply.ask_image_choice is True
        assert len(reply.image_options) == DEFAULT_IMAGE_COUNT
        assert "Option 2" in reply.text
        assert "Option 3" in reply.text

    def test_stale_image_options_are_not_attached_when_this_turn_has_none(
        self, monkeypatch, tmp_path
    ) -> None:
        leftover = tmp_path / "coffee_option_1.png"
        leftover.write_bytes(b"png")
        store = {
            "pending_client_copy": False,
            "pending_client_images": False,
            "ad_copy_options": [],
            "image_options": [
                {
                    "option": 1,
                    "image_path": leftover.as_posix(),
                    "creative_note": "leftover coffee",
                }
            ],
        }
        _state_patches(monkeypatch, client_gateway, store)
        monkeypatch.setattr(client_gateway, "isolate_stale_demo_state", lambda message="": [])
        monkeypatch.setattr(client_gateway, "ROOT", tmp_path)
        agency = MagicMock()
        agency.get_response_sync.return_value = SimpleNamespace(
            final_output="Trail running shoe ads are next. What is the monthly budget?"
        )
        reply = client_gateway.run_client_turn(
            "3 DALL-E ads for a trail running shoe",
            agency,
        )
        assert leftover.as_posix() not in reply.image_paths
        assert reply.image_options == []
        assert "coffee" not in reply.text.lower()

    def test_choice_message_keeps_pending_images(self, monkeypatch) -> None:
        store = {
            "pending_client_images": True,
            "pending_client_copy": False,
            "ad_copy_options": [],
            "image_options": [{"option": 1, "image_path": "x.png", "creative_note": "dusk"}],
            "client_brief": {"business": "Harborline Lantern Co."},
        }
        _state_patches(monkeypatch, client_gateway, store)
        monkeypatch.setattr(client_gateway, "isolate_stale_demo_state", lambda message="": [])
        agency = MagicMock()
        seen: dict = {}

        def _sync(message: str):
            seen["pending"] = store.get("pending_client_images")
            seen["message"] = message
            return SimpleNamespace(final_output="Option 1 locked for Harborline.")

        agency.get_response_sync.side_effect = _sync
        client_gateway.run_client_turn("Option 1", agency)
        assert seen["pending"] is True
        assert "Harborline" in seen["message"]

    def test_choice_helpers(self) -> None:
        assert client_gateway.is_choice_message("Option 1") is True
        assert client_gateway.is_choice_message("I like the second copy") is True
        assert client_gateway.is_choice_message("Full creative job for Harborline") is False

    def test_conversation_id_uses_generate_response(self, monkeypatch) -> None:
        monkeypatch.delenv("MANIFEST_AI_DEMO", raising=False)
        store = {"client_brief": {"business": "Harborline Lantern Co."}}
        _state_patches(monkeypatch, client_gateway, store)
        monkeypatch.setattr(client_gateway, "isolate_stale_demo_state", lambda message="": [])
        called: dict = {}

        def _fake_generate(message: str, conversation_id: str, agency_obj=None) -> str:
            called["message"] = message
            called["conversation_id"] = conversation_id
            return "Continuing Harborline — Option 1 stays locked."

        monkeypatch.setattr("generate_response.generate_response", _fake_generate)
        agency = MagicMock()
        reply = client_gateway.run_client_turn(
            "I like the second copy",
            agency,
            conversation_id="D123",
        )
        assert called["conversation_id"] == "D123"
        assert "Harborline" in called["message"]
        agency.get_response_sync.assert_not_called()
        assert "Continuing Harborline" in reply.text

    def test_generate_response_error_falls_back_to_sync(self, monkeypatch) -> None:
        monkeypatch.delenv("MANIFEST_AI_DEMO", raising=False)
        store = {"client_brief": {"business": "Harborline Lantern Co."}}
        _state_patches(monkeypatch, client_gateway, store)
        monkeypatch.setattr(client_gateway, "isolate_stale_demo_state", lambda message="": [])

        def _boom(message: str, conversation_id: str, agency_obj=None) -> str:
            raise RuntimeError("thread manager failed")

        monkeypatch.setattr("generate_response.generate_response", _boom)
        agency = MagicMock()
        agency.get_response_sync.return_value = SimpleNamespace(
            final_output="Fallback kept Harborline in this chat."
        )
        reply = client_gateway.run_client_turn("pause the campaign", agency, conversation_id="D123")
        agency.get_response_sync.assert_called_once()
        assert "Harborline" in agency.get_response_sync.call_args[0][0]
        assert "Fallback kept Harborline" in reply.text


class TestStaleDemoIsolation:
    def test_isolate_drops_coffee_fixture_for_new_brief(self, monkeypatch, tmp_path) -> None:
        import workflow_state

        state_file = tmp_path / ".workflow_state.json"
        state_file.write_text(
            '{"ad_copy": "Fresh coffee, roasted weekly.", '
            '"image_options": [{"option": 1, "image_path": "generated_assets/images/coffee.png"}], '
            '"campaign_id": "52506749995438"}',
            encoding="utf-8",
        )
        monkeypatch.setattr(workflow_state, "_STATE_FILE", state_file)
        monkeypatch.setattr(workflow_state, "save_workflow_state", lambda data: False)
        removed = workflow_state.isolate_stale_demo_state(
            "3 DALL-E ads for a trail running shoe"
        )
        assert "ad_copy" in removed
        assert "image_options" in removed
        assert "campaign_id" in removed
        leftover = workflow_state._read_local_state()
        assert "coffee" not in str(leftover).lower()

    def test_isolate_keeps_state_when_client_asks_about_coffee(
        self, monkeypatch, tmp_path
    ) -> None:
        import workflow_state

        state_file = tmp_path / ".workflow_state.json"
        state_file.write_text(
            '{"ad_copy": "Fresh coffee, roasted weekly."}',
            encoding="utf-8",
        )
        monkeypatch.setattr(workflow_state, "_STATE_FILE", state_file)
        monkeypatch.setattr(workflow_state, "save_workflow_state", lambda data: False)
        removed = workflow_state.isolate_stale_demo_state(
            "keep going on the Atlas Peak coffee campaign"
        )
        assert removed == []
        assert "Fresh coffee" in state_file.read_text(encoding="utf-8")

    def test_isolate_drops_when_new_brief_says_do_not_reuse_demo(self, monkeypatch, tmp_path) -> None:
        import workflow_state

        state_file = tmp_path / ".workflow_state.json"
        state_file.write_text(
            '{"research_brief": {"client_business": "Atlas Peak specialty coffee subscription"}, '
            '"ad_copy": "Fresh coffee, roasted weekly."}',
            encoding="utf-8",
        )
        monkeypatch.setattr(workflow_state, "_STATE_FILE", state_file)
        monkeypatch.setattr(workflow_state, "save_workflow_state", lambda data: False)
        removed = workflow_state.isolate_stale_demo_state(
            "Do not reuse Atlas Peak or coffee. Full creative job for Harborline Lantern Co."
        )
        assert "research_brief" in removed
        leftover = workflow_state._read_local_state()
        assert "atlas peak" not in json.dumps(leftover).lower()


class TestAgentsSequential:
    def test_ceo_agent_lists_brief_tool_and_rejects_coffee_default(self) -> None:
        from MetaMarkCEO import MetaMarkCEO
        from MetaMarkCEO.tools.ClientBriefRecorder import ClientBriefRecorder

        ceo = MetaMarkCEO()
        assert ceo.name == "Chief Growth Strategist"
        tool_files = [path.stem for path in Path("MetaMarkCEO/tools").glob("*.py") if path.stem != "__init__"]
        assert "ClientBriefRecorder" in tool_files
        instructions = Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8")
        assert "never substitute" in instructions.lower()
        assert "three dall-e" in instructions.lower()
        brief = ClientBriefRecorder(
            business="trail running shoe brand",
            campaign_goal="traffic to product page",
            target_customer="runners 25-40",
            geography="Colorado",
        )
        payload = brief.model_dump()
        assert payload["business"] == "trail running shoe brand"
        assert "coffee" not in str(payload).lower()

    def test_creative_agent_lists_image_tools_default_three(self) -> None:
        from ImageCreatorAgent import ImageCreatorAgent

        creative = ImageCreatorAgent()
        assert creative.name == "Creative Director"
        tool_files = [
            path.stem
            for path in Path("ImageCreatorAgent/tools").glob("*.py")
            if path.stem != "__init__"
        ]
        assert "ImageGenerator" in tool_files
        assert "ImageSelector" in tool_files
        instructions = Path("ImageCreatorAgent/instructions.md").read_text(encoding="utf-8")
        assert "dall-e" in instructions.lower()
        assert "visual_prompt" in instructions
        assert "never use leftover coffee" in instructions.lower()
        tool = ImageGenerator(visual_prompt="3 DALL-E ads for a trail running shoe")
        assert tool.image_count == DEFAULT_IMAGE_COUNT
        prompt = build_client_image_prompt(visual_prompt="3 DALL-E ads for a trail running shoe")
        assert "trail running shoe" in prompt.lower()
        assert "coffee" not in prompt.lower()


class TestDesignerAgencyContract:
    def test_parse_three_production_briefs(self) -> None:
        raw = (
            "Concept A: hero shoe on wet basalt, 1:1, negative space top-left.\n"
            "---\n"
            "Concept B: tight product still on moss, overhead, quiet palette.\n"
            "---\n"
            "Concept C: mid-stride on switchback, rain, no faces, forest edge."
        )
        briefs = parse_concept_briefs(raw)
        assert len(briefs) == DEFAULT_IMAGE_COUNT
        assert "wet basalt" in briefs[0]
        assert "moss" in briefs[1]
        assert "switchback" in briefs[2]
        assert all("coffee" not in item.lower() for item in briefs)

    def test_run_uses_concept_briefs_not_generic_suffixes(
        self, monkeypatch, tmp_path
    ) -> None:
        import ImageCreatorAgent.tools.ImageGenerator as ig

        store: dict = {}
        monkeypatch.setattr(ig, "set_state_value", lambda key, value: store.__setitem__(key, value))
        monkeypatch.setattr(ig, "get_state_value", lambda key, default=None: store.get(key, default))
        client = _fake_dalle_client(monkeypatch, ig, tmp_path)
        tool = ImageGenerator(
            visual_prompt="Northline Trail Co waterproof trail running shoe",
            concept_briefs=(
                "Hero 1:1 feed: women's waterproof trail shoe on wet basalt, PNW forest, negative space top third, no neon, no smiling models.\n"
                "---\n"
                "Detail 1:1 feed: overhead still of the same shoe on moss and rain droplets, quiet earth palette, headline room left.\n"
                "---\n"
                "Motion 1:1 feed: mid-stride on a wet switchback, anonymous runner, capable quiet tone, no stock-photo smiles."
            ),
        )
        tool.run()
        assert client.images.generate.call_count == DEFAULT_IMAGE_COUNT
        prompts = [call.kwargs["prompt"].lower() for call in client.images.generate.call_args_list]
        assert "wet basalt" in prompts[0]
        assert "moss" in prompts[1]
        assert "switchback" in prompts[2]
        assert all("vibrant, high-energy" not in item for item in prompts)
        assert all("coffee" not in item and "atlas peak" not in item for item in prompts)
        assert len(store.get("image_options") or []) == DEFAULT_IMAGE_COUNT

    def test_creative_director_instructions_are_art_direction(self) -> None:
        instructions = Path("ImageCreatorAgent/instructions.md").read_text(encoding="utf-8").lower()
        for phrase in (
            "senior graphic designer",
            "art-direction note",
            "three distinct ad concepts",
            "production-ready dall-e brief",
            "recommend one",
            "do not invent a product",
            "visual_prompt",
            "never use leftover coffee",
        ):
            assert phrase in instructions, f"missing designer phrase: {phrase}"

    def test_ceo_must_run_full_creative_desk(self) -> None:
        instructions = Path("MetaMarkCEO/instructions.md").read_text(encoding="utf-8").lower()
        for phrase in (
            "full creative job",
            "must not skip research",
            "must not skip copy",
            "policy check",
            "do not spend ad budget",
            "complete creative brief",
        ):
            assert phrase in instructions, f"missing CEO desk phrase: {phrase}"

    def test_manifesto_forbids_skipping_the_desk(self) -> None:
        manifesto = Path("agency_manifesto.md").read_text(encoding="utf-8").lower()
        assert "full creative job" in manifesto
        assert "skipping research, culture, copy, or art direction is forbidden" in manifesto
        assert "minimum client context" in manifesto
