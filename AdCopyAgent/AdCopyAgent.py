from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class AdCopyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Senior Conversion Copywriter",
            description=(
                "Writes high-converting ad copy from approved strategy, audience, offer, "
                "tone, and research insights. Does not conduct research, generate images, or execute media."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools"
        )
