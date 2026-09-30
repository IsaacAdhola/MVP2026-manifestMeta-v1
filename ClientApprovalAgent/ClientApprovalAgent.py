from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class ClientApprovalAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Client Approval Manager",
            description=(
                "Verifies final client approval for selected copy, selected creative, schedule, "
                "budget, targeting, destination links, and policy approval before media execution."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
