from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class MetaMarkCEO(Agent):
    def __init__(self):
        super().__init__(
            name="Chief Growth Strategist",
            description=(
                "Acts as Manifest AI's executive client lead. Owns client intake, "
                "strategic direction, specialist delegation, and premium client-facing communication."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools"
        )
