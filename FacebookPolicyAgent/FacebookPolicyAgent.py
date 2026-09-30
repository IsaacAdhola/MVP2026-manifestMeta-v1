from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class FacebookPolicyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Facebook Policy Compliance Officer",
            description=(
                "Reviews Facebook posts, paid ads, campaign claims, targeting notes, "
                "and publishing plans against Meta policy references before media execution."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
