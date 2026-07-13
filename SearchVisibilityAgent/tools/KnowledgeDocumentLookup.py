"""Local knowledge PDF lookup — reads from knowledge/ without OpenAI vector-store sync."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agency_swarm.tools import BaseTool
from pydantic import Field

_AGENT_ROOT = Path(__file__).resolve().parents[1]
_KNOWLEDGE_DIR = _AGENT_ROOT / "knowledge"

_DOC_MAP = {
    "seo": "Search_Engine_Optimization.pdf",
    "aeo": "answer_engine_optimization_holtschulte_202508.pdf",
    "geo": "GEO.pdf",
}


class KnowledgeDocumentLookup(BaseTool):
    """
    Looks up relevant passages from local SEO/AEO/GEO knowledge PDFs.
    Use this instead of inventing rules. Do not paste entire PDFs into chat.
    """

    topic: str = Field(
        ...,
        description="Which knowledge area to consult: seo, aeo, or geo.",
    )
    query: str = Field(
        ...,
        description="What you need from the knowledge base (keywords, structure, citations, etc.).",
    )
    max_chars: int = Field(
        default=2500,
        description="Max characters of extracted text to return (keep handoffs concise).",
    )

    def run(self):
        topic = (self.topic or "").strip().lower()
        filename = _DOC_MAP.get(topic)
        if not filename:
            return json.dumps({
                "error": f"Unknown topic '{self.topic}'. Use one of: seo, aeo, geo.",
                "available": list(_DOC_MAP.keys()),
            })

        pdf_path = _KNOWLEDGE_DIR / filename
        if not pdf_path.exists():
            return json.dumps({
                "error": f"Knowledge file missing: {pdf_path.as_posix()}",
                "hint": "Place the PDF under SearchVisibilityAgent/knowledge/.",
            })

        text = self._extract_text(pdf_path)
        if not text.strip():
            return json.dumps({
                "document": filename,
                "topic": topic,
                "query": self.query,
                "excerpt": "",
                "note": "Could not extract text from PDF. Confirm the file is a readable PDF.",
            })

        excerpt = self._relevant_excerpt(text, self.query, self.max_chars)
        return json.dumps({
            "document": filename,
            "topic": topic,
            "query": self.query,
            "excerpt": excerpt,
            "usage": "Apply these principles to the client brief. Do not dump raw PDF text to the client.",
        }, ensure_ascii=False)

    def _extract_text(self, pdf_path: Path) -> str:
        # Prefer pypdf if installed; fall back to a lightweight binary scan.
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(pdf_path))
            parts = []
            for page in reader.pages[:40]:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)
        except Exception:
            pass
        try:
            raw = pdf_path.read_bytes()
            # Recover readable ASCII/UTF-8-ish strings from PDF streams.
            chunks = re.findall(rb"[\x20-\x7E]{6,}", raw)
            return "\n".join(c.decode("latin-1", errors="ignore") for c in chunks[:5000])
        except Exception:
            return ""

    def _relevant_excerpt(self, text: str, query: str, max_chars: int) -> str:
        words = [w.lower() for w in re.findall(r"[a-zA-Z0-9]{3,}", query or "")]
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if not paragraphs:
            return text[:max_chars]

        if not words:
            return "\n\n".join(paragraphs[:8])[:max_chars]

        scored = []
        for p in paragraphs:
            pl = p.lower()
            score = sum(1 for w in words if w in pl)
            if score:
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = [p for _, p in scored[:12]] or paragraphs[:8]
        out = "\n\n".join(chosen)
        return out[:max_chars]
