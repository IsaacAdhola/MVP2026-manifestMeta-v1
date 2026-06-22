"""
conftest.py — pytest configuration for Manifest AI agency.

Adds the project root to sys.path so that test files can import agents,
tools, and utilities as top-level modules (e.g. `from AdCopyAgent import ...`).
Also prevents pytest from trying to run the root __init__.py as a test package.
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so top-level imports work.
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Tell pytest to ignore the root __init__.py (it uses relative imports
# intended for the package, not for direct test discovery).
collect_ignore = ["__init__.py"]
