from agency_swarm import Agent
from model_router import MODEL_GROK, agent_model


class ResearchAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Market Intelligence Director",
            description=(
                "Leads market intelligence for Manifest AI by researching competitors, "
                "audiences, demographics, and ad-library patterns. This is the only "
                "agent with access to competitor ad research tools."
            ),
            model=agent_model(MODEL_GROK),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
