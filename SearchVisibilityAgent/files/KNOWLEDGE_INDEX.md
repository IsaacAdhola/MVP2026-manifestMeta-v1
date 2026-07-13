# Search Visibility Knowledge Index

**Do not memorize PDF content.** Consult the local knowledge PDFs under `SearchVisibilityAgent/knowledge/` (and use tools that read them) when creating or revising SEO / AEO / GEO strategy.

Large PDFs are kept in `../knowledge/` (not auto-uploaded to OpenAI vector store) so the Gradio UI can start quickly.

| Document | Path | Use when |
|----------|------|----------|
| GEO | `knowledge/GEO.pdf` | Generative-engine visibility, citation-worthiness, AI-overview presence |
| Search Engine Optimization | `knowledge/Search_Engine_Optimization.pdf` | Keywords, on-page SEO, structure, technical/content SEO |
| Answer Engine Optimization | `knowledge/answer_engine_optimization_holtschulte_202508.pdf` | Answer-ready structure, Q&A, featured-snippet / AEO patterns |

## How to use
1. Identify whether the task is SEO, AEO, GEO, or a mix.
2. Use `KnowledgeDocumentLookup` (or File Search if available) against the matching PDF.
3. Apply findings via `SearchVisibilityBriefBuilder` / `ContentVisibilityChecklist`.
4. Hand off a concise strategy package — never dump raw PDF text into client chat.
