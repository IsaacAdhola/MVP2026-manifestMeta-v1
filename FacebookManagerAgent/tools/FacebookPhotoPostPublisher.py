import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from agency_swarm.tools import BaseTool
from pydantic import Field

from dotenv import load_dotenv

_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from workflow_state import get_state_value, set_state_value

try:
    from ..facebook_auth import get_page_access_token, get_required_env, initialize_business_sdk
except ImportError:
    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import get_page_access_token, get_required_env, initialize_business_sdk

load_dotenv()


class FacebookPhotoPostPublisher(BaseTool):
    """
    Publishes a generated local image to the configured Facebook Page with a caption.
    """

    message: str = Field(..., description="Caption text to publish with the image.")
    image_path: str | None = Field(
        default=None,
        description="Optional local image path. If omitted, uses the last generated image from workflow state.",
    )
    published: bool = Field(
        default=True,
        description="Whether to publish immediately. Set false for an unpublished/draft photo post.",
    )

    def _resolve_image_path(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.is_absolute():
            path = Path(_WORKSPACE_DIR) / path
        return str(path.resolve())

    def run(self):
        page_id = get_required_env("FACEBOOK_PAGE_ID")
        env = initialize_business_sdk()
        page_token, meta = get_page_access_token(env["access_token"], page_id)
        if not page_token:
            return (
                "Error publishing photo post: unable to resolve a valid page token "
                f"for page {page_id}. Diagnostics: {meta}"
            )

        resolved_image_path = self.image_path or get_state_value("image_path")
        if not resolved_image_path:
            raise ValueError("Image path not found. Please generate an image first.")
        resolved_image_path = self._resolve_image_path(resolved_image_path)
        if not os.path.exists(resolved_image_path):
            raise ValueError(f"Image file does not exist: {resolved_image_path}")

        with open(resolved_image_path, "rb") as image_file:
            response = requests.post(
                f"https://graph.facebook.com/v25.0/{page_id}/photos",
                data={
                    "access_token": page_token,
                    "caption": self.message,
                    "published": str(self.published).lower(),
                },
                files={"source": image_file},
                timeout=60,
            )

        try:
            data = response.json()
        except ValueError:
            data = {"error": {"message": response.text}}

        if response.status_code >= 400 or data.get("error"):
            error = data.get("error", data)
            return (
                "Error publishing photo post: "
                f"{error.get('message', error)} "
                f"(code={error.get('code')}, subcode={error.get('error_subcode')})"
            )

        set_state_value("page_photo_id", data.get("id"))
        if data.get("post_id"):
            set_state_value("page_post_id", data.get("post_id"))

        return (
            "Photo post published successfully. "
            f"Photo ID: {data.get('id')}. Post ID: {data.get('post_id')}."
        )


if __name__ == "__main__":
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tool = FacebookPhotoPostPublisher(
        message=f"Automated agency photo post test at {timestamp}.",
        published=False,
    )
    print(tool.run())
