from agency_swarm import Agent
from model_router import MODEL_GROK, agent_model


class CommunityManagerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Community Manager",
            description=(
                "Drafts on-brand comment replies, DM responses, and community voice notes. "
                "Does not publish to Facebook without Media Operations and approval."
            ),
            model=agent_model(MODEL_GROK),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
