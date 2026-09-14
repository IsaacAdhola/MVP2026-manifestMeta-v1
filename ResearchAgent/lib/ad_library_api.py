import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_VERSION = "v25.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_access_token() -> str:
    token = (
        os.getenv("META_AD_LIBRARY_ACCESS_TOKEN")
        or os.getenv("Facebook_ad_library_tolken")
        or os.getenv("FACEBOOK_AD_LIBRARY_TOKEN")
        or ""
    ).strip()
    if not token:
        raise ValueError(
            "Missing Meta Ad Library token. Set META_AD_LIBRARY_ACCESS_TOKEN "
            "or Facebook_ad_library_tolken in environment."
        )
    return token


def normalize_list(values: list[str] | None, default: list[str] | None = None) -> list[str]:
    cleaned = [value.strip() for value in (values or []) if value and value.strip()]
    return cleaned or list(default or [])


def graph_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = dict(params)
    payload["access_token"] = get_access_token()
    response = requests.get(
        f"{GRAPH_API_BASE_URL}/{path.lstrip('/')}",
        params=payload,
        timeout=45,
    )
    try:
        data = response.json()
    except ValueError:
        data = {"error": {"message": response.text}}

    if response.status_code >= 400:
        return {
            "ok": False,
            "http_status": response.status_code,
            "error": data.get("error", data),
        }

    data["ok"] = True
    return data


def json_list(values: list[str]) -> str:
    return json.dumps(values)
