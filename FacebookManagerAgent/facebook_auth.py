import os
from typing import Any

import requests
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi

load_dotenv()


def get_required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise ValueError(f"Missing {name} in environment.")
    return value


def initialize_business_sdk(access_token: str | None = None) -> dict[str, str]:
    token = (access_token or get_required_env("FACEBOOK_ACCESS_TOKEN")).strip()
    app_id = get_required_env("FACEBOOK_APP_ID")
    app_secret = get_required_env("FACEBOOK_APP_SECRET")
    FacebookAdsApi.init(access_token=token, app_id=app_id, app_secret=app_secret)
    return {
        "access_token": token,
        "app_id": app_id,
        "app_secret": app_secret,
    }


def graph_get(path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://graph.facebook.com/{path.lstrip('/')}"
    payload = dict(params or {})
    payload["access_token"] = token
    response = requests.get(url, params=payload, timeout=30)
    try:
        data = response.json()
    except ValueError:
        data = {"error": {"message": response.text}}
    if response.status_code >= 400:
        return {"error": data.get("error", data), "http_status": response.status_code}
    return data


def debug_token(input_token: str) -> dict[str, Any]:
    app_id = get_required_env("FACEBOOK_APP_ID")
    app_secret = get_required_env("FACEBOOK_APP_SECRET")
    app_token = f"{app_id}|{app_secret}"
    return graph_get("debug_token", app_token, {"input_token": input_token})


def get_page_access_token(user_or_page_token: str, page_id: str) -> tuple[str | None, dict[str, Any]]:
    """
    Returns (page_access_token, metadata).
    If token is already page-scoped for the target page, it is returned unchanged.
    """
    debug = debug_token(user_or_page_token)
    data = debug.get("data", {})
    if not data.get("is_valid"):
        return None, {"debug_token": debug}

    if (data.get("type") or "").upper() == "PAGE":
        return user_or_page_token, {"debug_token": debug, "source": "page_token"}

    accounts = graph_get(
        "me/accounts",
        user_or_page_token,
        {"fields": "id,name,tasks,access_token"},
    )
    if accounts.get("error"):
        return None, {"debug_token": debug, "accounts_lookup": accounts}

    for page in accounts.get("data", []) or []:
        if str(page.get("id")) == str(page_id):
            token = (page.get("access_token") or "").strip()
            if token:
                return token, {
                    "debug_token": debug,
                    "accounts_lookup": {"matched_page_id": str(page.get("id"))},
                    "source": "me_accounts_exchange",
                }

    return None, {
        "debug_token": debug,
        "accounts_lookup": {"error": f"Target page {page_id} not found in /me/accounts."},
    }
