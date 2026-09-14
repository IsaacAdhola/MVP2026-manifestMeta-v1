import os
import sys
from datetime import datetime, timezone

from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from facebook_business.adobjects.page import Page
from facebook_business.exceptions import FacebookRequestError
from pydantic import Field

_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from error_logger import log_error
from workflow_state import set_state_value

try:
    from ..facebook_auth import (
        get_page_access_token,
        get_required_env,
        initialize_business_sdk,
    )
except ImportError:
    _PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _PARENT_DIR not in sys.path:
        sys.path.insert(0, _PARENT_DIR)
    from facebook_auth import (
        get_page_access_token,
        get_required_env,
        initialize_business_sdk,
    )

load_dotenv()


class FacebookPagePostPublisher(BaseTool):
    """
    Publishes a post directly to the configured Facebook Page.
    """

    message: str = Field(..., description="Text to publish on the Facebook Page.")
    link: str | None = Field(
        default=None,
        description="Optional URL to include in the post.",
    )
    published: bool = Field(
        default=True,
        description="Whether to publish immediately. Set false for an unpublished/draft post.",
    )
    scheduled_publish_time: str | None = Field(
        default=None,
        description="ISO 8601 UTC datetime. If set, creates a scheduled unpublished post.",
    )

    def run(self):
        actor = "Media Operations Director"
        try:
            page_id = get_required_env("FACEBOOK_PAGE_ID")
            env = initialize_business_sdk()
            base_token = env["access_token"]
            page_token, meta = get_page_access_token(base_token, page_id)
            if not page_token:
                message = (
                    "Error publishing page post: unable to resolve a valid page token "
                    f"for page {page_id}."
                )
                log_error(actor, message, location="FacebookPagePostPublisher.run")
                return message
            initialize_business_sdk(access_token=page_token)

            payload = {"message": self.message}
            if self.link:
                payload["link"] = self.link
            if self.scheduled_publish_time:
                dt = datetime.fromisoformat(self.scheduled_publish_time.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                payload["published"] = False
                payload["scheduled_publish_time"] = int(dt.timestamp())
            elif not self.published:
                payload["published"] = False

            page = Page(page_id)
            response = page.create_feed(params=payload)
            post_id = response.get("id", "")
            set_state_value("page_post_id", post_id)
            mode = "scheduled" if self.scheduled_publish_time else ("unpublished" if not self.published else "live")
            set_state_value("page_post_mode", mode)
            return (
                f"Page post {mode} successfully. Post ID: {post_id}. "
                f"Token source: {meta.get('source', 'unknown')}."
            )
        except FacebookRequestError as exc:
            log_error(
                actor,
                exc,
                location="FacebookPagePostPublisher.run",
                context={
                    "api_error_code": exc.api_error_code(),
                    "api_error_subcode": exc.api_error_subcode(),
                },
            )
            return (
                "Error publishing page post: "
                f"{exc.api_error_message()} (code={exc.api_error_code()}, "
                f"subcode={exc.api_error_subcode()})"
            )
        except Exception as exc:
            log_error(actor, exc, location="FacebookPagePostPublisher.run")
            return f"Error publishing page post: {exc}"


if __name__ == "__main__":
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    tool = FacebookPagePostPublisher(
        message=f"Automated agency test post at {timestamp}.",
        link="https://example.com",
    )
    print(tool.run())
