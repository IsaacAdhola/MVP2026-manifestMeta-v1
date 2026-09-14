"""Smoke test: agency.py reaches its non-interactive startup path cleanly.

Runs agency.py as a subprocess with MANIFEST_AI_NONINTERACTIVE=1 so it exercises the real import +
startup path without launching an interactive Gradio server. Requires OPENAI_API_KEY.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.requires_openai
def test_agency_noninteractive_startup():
    proc = subprocess.run(
        [sys.executable, "agency.py"],
        stdin=subprocess.DEVNULL,
        env={**os.environ, "MANIFEST_AI_NONINTERACTIVE": "1"},
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(_ROOT),
        check=False,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, f"agency.py exited {proc.returncode}. Output:\n{combined}"
    assert "Interactive input is not available." in combined, combined


@pytest.mark.requires_openai
def test_gradio_available():
    import gradio  # noqa: F401
