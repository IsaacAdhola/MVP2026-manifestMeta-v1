import os
import sys
from pathlib import Path

import requests
from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from error_logger import log_error
from workflow_state import get_state_value, set_state_value

try:
    from ..facebook_auth import get_page_access_token, get_required_env, initialize_business_sdk, graph_get
except ImportError:
    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import get_page_access_token, get_required_env, initialize_business_sdk, graph_get

load_dotenv()


class InstagramPhotoPublisher(BaseTool):
    """
    Publishes an approved local image to the Instagram business account linked to the Facebook Page.
    """

    caption: str = Field(..., description="Instagram caption.")
    image_path: str | None = Field(
        default=None,
        description="Local image path. Uses workflow state if omitted.",
    )

    def _resolve_image_path(self, image_path: str) -> Path:
        path = Path(image_path)
        if not path.is_absolute():
            path = Path(_WORKSPACE_DIR) / path
        return path.resolve()

    def run(self):
        actor = "Media Operations Director"
        try:
            page_id = get_required_env("FACEBOOK_PAGE_ID")
            env = initialize_business_sdk()
            page_token, _meta = get_page_access_token(env["access_token"], page_id)
            token = page_token or env["access_token"]
            page = graph_get(f"v25.0/{page_id}", token, {"fields": "instagram_business_account"})
            if page.get("error"):
                return f"Instagram publish blocked: could not read Page IG account. {page.get('error')}"
            ig = (page.get("instagram_business_account") or {}).get("id")
            if not ig:
                return (
                    "Instagram publish blocked: this Facebook Page has no linked Instagram "
                    "business account."
                )

            resolved = self.image_path or get_state_value("image_path")
            if not resolved:
                return "Instagram publish blocked: no image path. Generate and select an image first."
            image_file = self._resolve_image_path(resolved)
            if not image_file.exists():
                return f"Instagram publish blocked: image file not found at {image_file.name}."

            # Instagram Graph requires a public image URL. Hosting local files is out of
            # scope, so return a precise next action rather than a fake success.
            return (
                "Instagram photo publishing requires a public image URL on the Instagram "
                "Content Publishing API. The Page is linked, but this agency currently "
                "publishes local images to Facebook Page photos. Post the selected image "
                "to Facebook with FacebookPhotoPostPublisher, or provide a public HTTPS "
                f"image URL for Instagram account {ig}."
            )
        except Exception as exc:
            log_error(actor, exc, location="InstagramPhotoPublisher.run")
            return f"Instagram publish failed: {type(exc).__name__}: {exc}"
