"""
ui_entry.py — Gradio-based UI entry point for Manifest AI.

Run this file to launch the agency as a web UI:

    python ui_entry.py

The Gradio demo exposes only the user ↔ CEO (Chief Growth Strategist) conversation.
All inter-agent communications (CEO → Research, Copy, Image, Policy, Approval,
FacebookManager → CEO) are handled internally as background tool calls and are NOT
surfaced as raw JSON or intermediate messages in the UI chat window.

To expose the UI on a specific port or host, pass --port and --host flags or set
SERVER_HOST / SERVER_PORT environment variables.

Environment variables required (see .env):
    OPENAI_API_KEY, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET,
    FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID, FACEBOOK_AD_ACCOUNT_ID,
    SCRAPE_CREATORS_API_KEY
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()


def _configure_console_encoding() -> None:
    if os.name == "nt":
        try:
            subprocess.run(
                ["chcp", "65001"],
                check=False,
                capture_output=True,
                text=True,
                shell=True,
            )
        except Exception:
            pass
    for stream_name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def _missing_env_keys() -> list[str]:
    required = [
        "OPENAI_API_KEY",
        "FACEBOOK_APP_ID",
        "FACEBOOK_APP_SECRET",
        "FACEBOOK_ACCESS_TOKEN",
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_AD_ACCOUNT_ID",
        "SCRAPE_CREATORS_API_KEY",
    ]
    return [k for k in required if not os.getenv(k, "").strip()]


def main() -> None:
    _configure_console_encoding()

    parser = argparse.ArgumentParser(description="Launch Manifest AI Gradio UI")
    parser.add_argument("--host", default=os.getenv("SERVER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", "7860")))
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link")
    args = parser.parse_args()

    missing = _missing_env_keys()
    if missing:
        print(
            f"[ui_entry] WARNING: The following environment variables are not set: "
            f"{', '.join(missing)}\n"
            "Some agent tools may fail at runtime. Add them to your .env file."
        )

    # Import agency here so environment is already loaded
    print("[ui_entry] Importing agency (this can take a minute)...")
    # #region agent log
    try:
        import json as _json
        import time as _time
        from pathlib import Path as _Path
        _log = _Path(__file__).resolve().parent / "debug-9c2ba9.log"
        with open(_log, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps({
                "sessionId": "9c2ba9",
                "runId": "pre-fix",
                "hypothesisId": "F",
                "location": "ui_entry.py:main:before_import",
                "message": "about to import agency",
                "data": {"host": args.host, "port": args.port},
                "timestamp": int(_time.time() * 1000),
            }, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # #endregion
    from agency import agency  # noqa: PLC0415
    # #region agent log
    try:
        import json as _json
        import time as _time
        from pathlib import Path as _Path
        _log = _Path(__file__).resolve().parent / "debug-9c2ba9.log"
        with open(_log, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps({
                "sessionId": "9c2ba9",
                "runId": "pre-fix",
                "hypothesisId": "F",
                "location": "ui_entry.py:main:after_import",
                "message": "agency import complete",
                "data": {"agent_count": len(getattr(agency, "agents", []) or [])},
                "timestamp": int(_time.time() * 1000),
            }, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # #endregion
    print("[ui_entry] Agency imported. Launching Gradio...")

    # Ensure the image output folder exists so Gradio can whitelist it.
    import pathlib
    image_dir = pathlib.Path("generated_assets/images")
    image_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"\n[ui_entry] Starting Manifest AI Gradio UI at "
        f"http://{args.host}:{args.port}\n"
        "Only the user ↔ Chief Growth Strategist conversation is visible in the UI.\n"
        "Inter-agent communications run in the background.\n"
        f"Generated images served from: {image_dir.resolve()}\n"
    )

    # demo_gradio() is attached to the agency instance in agency.py.
    # allowed_paths lets Gradio serve local image files so ![Option N](path)
    # markdown in the chatbot renders as an inline image the client can see.
    agency.demo_gradio(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        allowed_paths=[str(image_dir.resolve())],
    )


if __name__ == "__main__":
    main()
