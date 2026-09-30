"""Copy LLM helper. Claude owns writing; GPT-4o is not used for ad copy."""

import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_AGENT_DIR = Path(__file__).resolve().parent
for path in (_ROOT, _AGENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from model_router import MODEL_CLAUDE, llm_text


def complete_copy(system: str, user: str, max_tokens: int = 1400) -> str:
    return llm_text(MODEL_CLAUDE, system, user, max_tokens=max_tokens)


def get_openai_client():
    """Deprecated. Copy tools should use complete_copy (Claude)."""
    import openai
    from dotenv import load_dotenv

    load_dotenv()
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_copy_options(text: str) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    blocks = re.split(r"\n?\s*Option\s+\d+\s*:\s*", text.strip(), flags=re.IGNORECASE)
    for block in blocks:
        if not block.strip():
            continue
        headline_match = re.search(r"Headline:\s*(.+?)(?:\n|$)", block, flags=re.IGNORECASE)
        copy_match = re.search(
            r"Ad Copy:\s*(.+?)(?:\n(?:Rationale|Why This Works):|$)",
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        rationale_match = re.search(
            r"(?:Rationale|Why This Works):\s*(.+)$",
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if headline_match and copy_match:
            options.append(
                {
                    "headline": headline_match.group(1).strip(),
                    "ad_copy": copy_match.group(1).strip(),
                    "rationale": rationale_match.group(1).strip() if rationale_match else "",
                }
            )
    return options
