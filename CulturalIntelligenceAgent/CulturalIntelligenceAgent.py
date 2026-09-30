from agency_swarm import Agent
from model_router import MODEL_GROK, agent_model


class CulturalIntelligenceAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Cultural Intelligence Director",
            description=(
                "Reads culture, language, and current audience energy for the category. "
                "Feeds voice and angle to copy — does not replace market or ad-library research."
            ),
            model=agent_model(MODEL_GROK),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
