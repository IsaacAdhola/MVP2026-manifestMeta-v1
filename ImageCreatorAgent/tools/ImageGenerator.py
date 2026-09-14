from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional
import openai
import os
import base64
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from urllib.request import urlopen
from error_logger import log_error
from workflow_state import set_state_value, get_state_value

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def _get_openai_client():
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_IMAGE_OUTPUT_DIR = _PROJECT_ROOT / "generated_assets" / "images"
# #region agent log
_DEBUG_LOG_PATH = _PROJECT_ROOT / "debug-9c2ba9.log"


def _agent_dbg(hypothesis_id: str, location: str, message: str, data: dict | None = None, run_id: str = "pre-fix"):
    try:
        payload = {
            "sessionId": "9c2ba9",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass
# #endregion


def _new_image_path(index):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _IMAGE_OUTPUT_DIR / f"manifest_ai_image_{timestamp}_{uuid4().hex[:8]}_option_{index}.png"


def _frontend_safe_path(path):
    return path.relative_to(_PROJECT_ROOT).as_posix()

class ImageGenerator(BaseTool):
    """
    Generates images based on ad copy and specific themes or requests, utilizing DALL-E 3.
    """

    ad_copy: str = Field(
        ..., description="The ad copy to base the image on."
    )
    theme: str = Field(
        ..., description="The specific theme or visual goals for the image."
    )
    specific_requests: Optional[str] = Field(
        None, description="Any specific requests related to the image creation."
    )
    image_count: int = Field(
        default=3,
        description="Number of image options to generate for client selection. Use 1 to 3.",
    )

    def _generate_single(self, client, prompt: str, index: int) -> dict:
        """Generate one image and return its option dict."""
        # #region agent log
        _agent_dbg("B", "ImageGenerator.py:_generate_single:entry", "starting image API call", {
            "index": index,
            "prompt_len": len(prompt),
            "prompt_suffix_tail": prompt[-80:],
            "model": "gpt-image-1",
        })
        # #endregion
        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
        except Exception as exc:
            # #region agent log
            _agent_dbg("A", "ImageGenerator.py:_generate_single:api_error", "image API failed", {
                "index": index,
                "error_type": type(exc).__name__,
                "error": str(exc)[:300],
            })
            # #endregion
            log_error("Creative Director", exc, location="ImageGenerator._generate_single")
            raise
        image_data = response.data[0]
        has_b64 = bool(getattr(image_data, "b64_json", None))
        has_url = bool(getattr(image_data, "url", None))
        if has_b64:
            raw_bytes = base64.b64decode(image_data.b64_json)
            content_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
            image_path = self.save_base64_image(image_data.b64_json, index)
        elif has_url:
            image_path = self.save_image_url(image_data.url, index)
            abs_path = _PROJECT_ROOT / image_path
            content_hash = hashlib.sha256(abs_path.read_bytes()).hexdigest()[:16] if abs_path.exists() else "missing"
            raw_bytes = abs_path.read_bytes() if abs_path.exists() else b""
        else:
            # #region agent log
            _agent_dbg("A", "ImageGenerator.py:_generate_single:empty", "API returned no image payload", {
                "index": index,
                "response_keys": list(getattr(image_data, "model_fields", {}) or []),
            })
            # #endregion
            raise ValueError("Image API response did not include image data.")
        abs_saved = _PROJECT_ROOT / image_path
        # #region agent log
        _agent_dbg("B", "ImageGenerator.py:_generate_single:saved", "image saved", {
            "index": index,
            "image_path": image_path,
            "has_b64": has_b64,
            "has_url": has_url,
            "byte_len": len(raw_bytes),
            "content_hash": content_hash,
            "file_exists": abs_saved.exists(),
            "file_size": abs_saved.stat().st_size if abs_saved.exists() else 0,
        })
        # #endregion
        return {
            "option": index,
            "image_asset_id": Path(image_path).stem,
            "image_path": image_path,
            "creative_note": f"Image option {index} — a distinct visual direction for client selection.",
        }

    def run(self):
        # #region agent log
        prior_path = get_state_value("image_path")
        prior_options = get_state_value("image_options") or []
        _agent_dbg("A", "ImageGenerator.py:run:entry", "ImageGenerator invoked", {
            "ad_copy_len": len(self.ad_copy or ""),
            "theme": (self.theme or "")[:80],
            "image_count": self.image_count,
            "prior_image_path": prior_path,
            "prior_option_count": len(prior_options),
            "prior_paths": [o.get("image_path") for o in prior_options][:3] if isinstance(prior_options, list) else [],
        })
        # #endregion
        client = _get_openai_client().with_options(timeout=180)
        image_count = max(1, min(self.image_count, 3))
        base_prompt = (
            f"Create an image that visually represents: {self.ad_copy}. "
            f"Theme: {self.theme}. "
            f"{('Specific requests: ' + self.specific_requests) if self.specific_requests else ''}"
        )
        variation_suffixes = [
            "Vibrant, high-energy composition with bold colors.",
            "Clean, minimal composition with soft natural tones.",
            "Warm, lifestyle-focused composition showing real people.",
        ]
        image_options = []
        for index in range(1, image_count + 1):
            suffix = variation_suffixes[index - 1] if index <= len(variation_suffixes) else ""
            prompt = f"{base_prompt} {suffix}".strip()
            option = self._generate_single(client, prompt, index)
            image_options.append(option)

        default_image_path = image_options[0]["image_path"]
        paths = [o["image_path"] for o in image_options]
        unique_paths = len(set(paths))
        # #region agent log
        _agent_dbg("D", "ImageGenerator.py:run:exit", "ImageGenerator finished", {
            "option_count": len(image_options),
            "paths": paths,
            "unique_path_count": unique_paths,
            "default_image_path": default_image_path,
            "same_path_bug": unique_paths < len(paths),
        })
        # #endregion
        set_state_value("image_options", image_options)
        set_state_value("image_path", default_image_path)

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
    tool = ImageGenerator(ad_copy="A beautiful sunset", theme="Nature",
                          specific_requests="Include a river in the image.")
    result = tool.run()
    print(result)
    # Note: image_path is stored in shared_state and will be available to other tools



