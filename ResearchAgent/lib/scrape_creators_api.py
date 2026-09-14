import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.scrapecreators.com"


def get_api_key() -> str:
    api_key = (os.getenv("SCRAPE_CREATORS_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("Missing SCRAPE_CREATORS_API_KEY in environment.")
    return api_key


def clean_params(params: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            cleaned[key] = str(value).lower()
        else:
            cleaned[key] = value
    return cleaned


def scrape_creators_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={"x-api-key": get_api_key()},
        params=clean_params(params or {}),
        timeout=60,
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

    if isinstance(data, dict):
        data["ok"] = True
        data["http_status"] = response.status_code
    return data
