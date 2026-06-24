import os
from typing import Any

import requests
from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()


class FacebookTokenDiagnostics(BaseTool):
    """
    Validates the configured Facebook access token and reports readiness for page posting.
    """

    include_accounts_lookup: bool = Field(
        default=True,
        description="Whether to query /me/accounts to verify page token access.",
    )

    def _env(self, key: str) -> str:
        value = (os.getenv(key) or "").strip()
        if not value:
            raise ValueError(f"Missing {key} in environment.")
        return value

    def _get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = requests.get(url, params=params, timeout=30)
        try:
            data = response.json()
        except ValueError:
            data = {"error": {"message": response.text}}
        if response.status_code >= 400:
            return {"error": data.get("error", data), "http_status": response.status_code}
        return data

    def run(self):
        app_id = self._env("FACEBOOK_APP_ID")
        app_secret = self._env("FACEBOOK_APP_SECRET")
        access_token = self._env("FACEBOOK_ACCESS_TOKEN")
        page_id = self._env("FACEBOOK_PAGE_ID")

        app_token = f"{app_id}|{app_secret}"
        debug = self._get_json(
            "https://graph.facebook.com/debug_token",
            {"input_token": access_token, "access_token": app_token},
        )

        data = debug.get("data", {})
        token_error = data.get("error")
        scopes = sorted(data.get("scopes", []) or [])

        result: dict[str, Any] = {
            "token_is_valid": bool(data.get("is_valid")),
            "token_type": data.get("type", ""),
            "scopes": scopes,
            "required_scopes_for_page_posting": [
                "pages_manage_posts",
                "pages_show_list",
            ],
            "missing_required_scopes": sorted(
                {"pages_manage_posts", "pages_show_list"} - set(scopes)
            ),
            "token_error": token_error,
            "target_page_id": page_id,
            "accounts_lookup": None,
        }

        if self.include_accounts_lookup:
            token_type = data.get("type", "").upper()
            if token_type == "PAGE":
                # PAGE tokens cannot call /me/accounts — verify the page directly instead.
                page_data = self._get_json(
                    f"https://graph.facebook.com/{page_id}",
                    {"access_token": access_token, "fields": "id,name"},
                )
                if page_data.get("error"):
                    result["accounts_lookup"] = {
                        "note": "PAGE token: used direct page lookup instead of /me/accounts.",
                        "error": page_data.get("error"),
                        "http_status": page_data.get("http_status"),
                    }
                else:
                    result["accounts_lookup"] = {
                        "note": "PAGE token: used direct page lookup instead of /me/accounts.",
                        "target_page_found": str(page_data.get("id")) == page_id,
                        "page_name": page_data.get("name", ""),
                        "target_page_tasks": [],
                    }
            else:
                accounts = self._get_json(
                    "https://graph.facebook.com/me/accounts",
                    {"access_token": access_token, "fields": "id,name,tasks"},
                )
                if accounts.get("error"):
                    result["accounts_lookup"] = {
                        "error": accounts.get("error"),
                        "http_status": accounts.get("http_status"),
                    }
                    return result
                pages = accounts.get("data", []) or []
                matched = [p for p in pages if str(p.get("id")) == page_id]
                result["accounts_lookup"] = {
                    "pages_count": len(pages),
                    "target_page_found": bool(matched),
                    "target_page_tasks": (matched[0].get("tasks", []) if matched else []),
                }

        return result


if __name__ == "__main__":
    tool = FacebookTokenDiagnostics()
    print(tool.run())
