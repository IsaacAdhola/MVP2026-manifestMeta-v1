"""Shared pytest configuration for the Manifest AI test suite.

Responsibilities:
- Put the repository root on ``sys.path`` so tests can import top-level packages
  (``from AdCopyAgent import ...``, ``import config``, ``import workflow_state``) regardless of
  where pytest is invoked from.
- Auto-skip tests marked ``requires_openai`` when ``OPENAI_API_KEY`` is not set, so the offline
  suite (``tests/unit`` + ``tests/guardrails``) always runs cleanly without credentials.

Tests that read repository files with relative paths (e.g. ``Path("agency.py")``) expect pytest to
be run from the repository root, which is the documented convention (see docs/TESTING.md).
"""

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def pytest_collection_modifyitems(config, items):
    if os.getenv("OPENAI_API_KEY"):
        return
    skip_openai = pytest.mark.skip(reason="OPENAI_API_KEY not set; skipping OpenAI-dependent test")
    for item in items:
        if "requires_openai" in item.keywords:
            item.add_marker(skip_openai)
