from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class SearchVisibilityAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Search & Answer Visibility Director",
            description=(
                "Owns SEO, AEO, and GEO strategy and audits using knowledge files. "
                "Delivers keyword plans, visibility briefs, and revision checklists — "
                "does not write final long-form copy, create images, or manage Meta ads."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            # SEO/AEO/GEO PDFs live in knowledge/ and are consulted via
            # KnowledgeDocumentLookup — do not auto-sync via files_folder
            # (OpenAI vector-store sync hangs Gradio UI startup).
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
