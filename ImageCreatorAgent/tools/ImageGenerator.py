from agency_swarm.tools import BaseTool
from agency_swarm.util import get_openai_client
from pydantic import Field
from typing import Optional
import openai
import os
import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from urllib.request import urlopen
from workflow_state import set_state_value

from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_IMAGE_OUTPUT_DIR = _PROJECT_ROOT / "generated_assets" / "images"


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
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
        )
        image_data = response.data[0]
        if getattr(image_data, "b64_json", None):
            image_path = self.save_base64_image(image_data.b64_json, index)
        elif getattr(image_data, "url", None):
            image_path = self.save_image_url(image_data.url, index)
        else:
            raise ValueError("Image API response did not include image data.")
        return {
            "option": index,
            "image_asset_id": Path(image_path).stem,
            "image_path": image_path,
            "creative_note": f"Image option {index} — a distinct visual direction for client selection.",
        }

    def run(self):
        client = get_openai_client().with_options(timeout=180)
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
        self._shared_state.set("image_options", image_options)
        self._shared_state.set("image_path", default_image_path)
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



