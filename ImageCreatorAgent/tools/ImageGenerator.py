from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
import openai
import os
import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from urllib.request import urlopen
from error_logger import log_error
from model_router import MODEL_IMAGE, MODEL_IMAGE_FALLBACK
from workflow_state import get_state_value, set_state_value

from dotenv import load_dotenv
load_dotenv()

DEFAULT_IMAGE_COUNT = 3
MAX_IMAGE_COUNT = 10
DALLE_IMAGES_PER_API_CALL = 1
DALLE_IMAGE_SIZE = "1024x1024"
MISSING_OPENAI_KEY_MESSAGE = (
    "OPENAI_API_KEY is missing. DALL-E cannot generate images until the key is set in .env."
)
VARIATION_SUFFIXES = (
    "Vibrant, high-energy composition with bold colors.",
    "Clean, minimal composition with soft natural tones.",
    "Warm, lifestyle-focused composition showing real people.",
)
CONCEPT_BRIEF_DELIMITER = r"\r?\n---\r?\n"
DESIGNER_SAFETY_SUFFIX = (
    "No competitor logos, trademark letters, or brand marks "
    "(including a New Balance-style N). No readable words, slogans, "
    "or misspelled labels on the product."
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_IMAGE_OUTPUT_DIR = _PROJECT_ROOT / "generated_assets" / "images"


def _require_openai_key() -> str:
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(MISSING_OPENAI_KEY_MESSAGE)
    return key


def _get_openai_client():
    return openai.OpenAI(api_key=_require_openai_key())


def resolve_image_count(requested: int | None) -> int:
    if requested is None:
        return DEFAULT_IMAGE_COUNT
    try:
        count = int(requested)
    except (TypeError, ValueError):
        return DEFAULT_IMAGE_COUNT
    return max(1, min(count, MAX_IMAGE_COUNT))


def parse_concept_briefs(raw: str | list | tuple | None) -> list[str]:
    """Split production-ready DALL-E briefs. One concept per segment; not near-duplicates."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]
    text = str(raw).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(CONCEPT_BRIEF_DELIMITER, text) if part.strip()]


def build_client_image_prompt(
    *,
    visual_prompt: str = "",
    ad_copy: str = "",
    theme: str = "",
    specific_requests: str = "",
    variation_suffix: str = "",
    concept_brief: str = "",
) -> str:
    """Build a DALL-E prompt from the client's brief only. Never inject a sample product."""
    production = (concept_brief or "").strip()
    if production:
        return production
    subject = (
        (visual_prompt or "").strip()
        or (specific_requests or "").strip()
        or (ad_copy or "").strip()
    )
    if not subject:
        raise ValueError(
            "No client visual brief. Pass the client's image request "
            "(visual_prompt, specific_requests, or ad_copy)."
        )
    parts = [f"Create an image for this client brief: {subject}."]
    theme_text = (theme or "").strip()
    if theme_text:
        parts.append(f"Visual style: {theme_text}.")
    extra = (specific_requests or "").strip()
    if extra and extra != subject:
        parts.append(f"Specific requests: {extra}.")
    if variation_suffix:
        parts.append(variation_suffix)
    parts.append(DESIGNER_SAFETY_SUFFIX)
    return " ".join(parts)


def _variation_suffix(index: int) -> str:
    if 1 <= index <= len(VARIATION_SUFFIXES):
        return VARIATION_SUFFIXES[index - 1]
    return f"Distinct visual direction {index} of the same client brief."


def _new_image_path(index):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _IMAGE_OUTPUT_DIR / f"manifest_ai_image_{timestamp}_{uuid4().hex[:8]}_option_{index}.png"


def _frontend_safe_path(path):
    return path.relative_to(_PROJECT_ROOT).as_posix()


class ImageGenerator(BaseTool):
    """
    Generates still images with the OpenAI Images API (DALL-E) from the client's actual brief.
    Default is three distinct options. Honor a different count when the client asks.
    Never substitute a sample product, coffee shop, or leftover campaign copy.
    """

    visual_prompt: str = Field(
        default="",
        description=(
            "The client's actual image request or creative brief. "
            "This is the subject. Never replace it with a sample brand or coffee demo."
        ),
    )
    ad_copy: str = Field(
        default="",
        description="Approved ad copy to illustrate when the client selected copy. Optional for image-only requests.",
    )
    theme: str = Field(
        default="",
        description="Optional visual style notes from the client or locked creative direction.",
    )
    specific_requests: Optional[str] = Field(
        None,
        description="Any extra client constraints for the image (product, setting, people, colors to avoid).",
    )
    image_count: int = Field(
        default=DEFAULT_IMAGE_COUNT,
        description=(
            "Number of image options to generate. Default is 3. "
            "Honor the client's requested count (1 through 10)."
        ),
    )
    concept_briefs: str = Field(
        default="",
        description=(
            "Production-ready DALL-E briefs for distinct ad concepts, same campaign. "
            "Separate each concept with a line containing only ---. "
            "Each brief must include subject, setting, camera/composition, lighting, "
            "style, negative space for headline, and aspect. Never leftover coffee."
        ),
    )

    def _generate_single(self, client, prompt: str, index: int, creative_note: str = "") -> dict:
        """Generate one DALL-E image and return its option dict."""
        try:
            response = client.images.generate(
                model=MODEL_IMAGE,
                prompt=prompt,
                n=DALLE_IMAGES_PER_API_CALL,
                size=DALLE_IMAGE_SIZE,
            )
        except Exception as primary_exc:
            try:
                response = client.images.generate(
                    model=MODEL_IMAGE_FALLBACK,
                    prompt=prompt,
                    n=DALLE_IMAGES_PER_API_CALL,
                    size=DALLE_IMAGE_SIZE,
                )
            except Exception as exc:
                log_error("Creative Director", exc, location="ImageGenerator._generate_single")
                raise RuntimeError(
                    f"DALL-E image generation failed for option {index}: {type(exc).__name__}: {exc}"
                ) from primary_exc
        image_data = response.data[0]
        has_b64 = bool(getattr(image_data, "b64_json", None))
        has_url = bool(getattr(image_data, "url", None))
        if has_b64:
            image_path = self.save_base64_image(image_data.b64_json, index)
        elif has_url:
            image_path = self.save_image_url(image_data.url, index)
        else:
            raise ValueError("Image API response did not include image data.")
        return {
            "option": index,
            "image_asset_id": Path(image_path).stem,
            "image_path": image_path,
            "creative_note": creative_note
            or f"Image option {index} — a distinct visual direction for client selection.",
        }

    def run(self):
        _require_openai_key()
        client = _get_openai_client().with_options(timeout=180)
        briefs = parse_concept_briefs(self.concept_briefs)
        image_count = resolve_image_count(
            len(briefs) if briefs else self.image_count
        )
        prompt_kwargs = {
            "visual_prompt": self.visual_prompt or "",
            "ad_copy": self.ad_copy or "",
            "theme": self.theme or "",
            "specific_requests": self.specific_requests or "",
        }
        existing = get_state_value("image_options") or []
        append_single = (
            image_count == 1
            and isinstance(existing, list)
            and bool(existing)
            and bool(get_state_value("pending_client_images"))
        )
        start_index = len(existing) + 1 if append_single else 1
        image_options = list(existing) if append_single else []
        for offset in range(image_count):
            index = start_index + offset
            brief = briefs[offset] if offset < len(briefs) else ""
            prompt = build_client_image_prompt(
                **prompt_kwargs,
                concept_brief=brief,
                variation_suffix="" if brief else _variation_suffix(index),
            )
            note = (
                brief.splitlines()[0][:220]
                if brief
                else f"Image option {index} — a distinct visual direction for client selection."
            )
            option = self._generate_single(client, prompt, index, creative_note=note)
            image_options.append(option)

        default_image_path = image_options[0]["image_path"]
        set_state_value("image_options", image_options)
        set_state_value("image_path", default_image_path)
        set_state_value("pending_client_images", True)

        return json.dumps({
            "image_options": image_options,
            "default_selected_option": 1,
            "next_step": "Ask the client to choose one image option before compliance review and media execution.",
        }, ensure_ascii=False)

    def save_base64_image(self, image_data, index=1):
        _IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        image_path = _new_image_path(index)
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_data))
        return _frontend_safe_path(image_path)

    def save_image_url(self, image_url, index=1):
        with urlopen(image_url) as response:
            image_bytes = response.read()
        _IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        image_path = _new_image_path(index)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        return _frontend_safe_path(image_path)

if __name__ == "__main__":
    tool = ImageGenerator(
        visual_prompt="A beautiful sunset over a river",
        theme="Nature",
        specific_requests="Include a river in the image.",
    )
    result = tool.run()
    print(result)
