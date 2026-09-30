"""Provider routing by unique strength.

OpenAI (GPT-4o + gpt-image-1)
    Unique: native image generation. Claude cannot generate images.
    Strong: mature function calling for Facebook Graph / Ads SDK tools.
    Use for Creative Director, Media Operations, Campaign Operations.

Anthropic (Claude)
    Unique: instruction-following, policy honesty, long-form writing, CRO.
    Weak: no image generation, no live social firehose.
    Use for CEO, copy, policy, search, landing/CRO, performance, approval.

xAI (Grok Fast)
    Unique: live culture/social voice and strong agentic tool-calling.
    Weak: image generation not wired here; weaker policy/document work.
    Use for research, cultural intelligence, community.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def apply_provider_env() -> None:
    claude_key = (
        os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("claude_api_key")
        or os.getenv("CLAUDE_API_KEY")
        or os.getenv("ANTROPIC_API_KEY")
        or ""
    ).strip()
    if claude_key:
        os.environ["ANTHROPIC_API_KEY"] = claude_key

    grok_key = (os.getenv("XAI_API_KEY") or os.getenv("xai_api_key") or "").strip()
    if grok_key:
        os.environ["XAI_API_KEY"] = grok_key


apply_provider_env()

MODEL_GPT = os.getenv("MANIFEST_GPT_MODEL", "gpt-4o")
MODEL_CLAUDE = os.getenv("MANIFEST_CLAUDE_MODEL", "anthropic/claude-sonnet-4-5")
MODEL_GROK = os.getenv("MANIFEST_GROK_MODEL", "xai/grok-4-1-fast-reasoning")
MODEL_IMAGE = os.getenv("MANIFEST_IMAGE_MODEL", "dall-e-3")
MODEL_IMAGE_FALLBACK = os.getenv("MANIFEST_IMAGE_FALLBACK", "gpt-image-1")


def agent_model(model: str) -> str:
    """Agency Swarm only accepts openai/, litellm/, or any-llm/ prefixes."""
    name = (model or "").strip()
    if not name or name.startswith(("openai/", "litellm/", "any-llm/")):
        return name or MODEL_GPT
    return f"litellm/{name}"


def llm_text(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 1400,
    temperature: float = 0.5,
) -> str:
    apply_provider_env()
    from litellm import completion

    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()
