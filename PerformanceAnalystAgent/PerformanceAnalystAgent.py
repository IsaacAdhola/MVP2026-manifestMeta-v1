from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class PerformanceAnalystAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Performance Analyst",
            description=(
                "Turns campaign metrics and ops data into client-safe performance insights, "
                "pacing notes, and next-action recommendations. Does not publish or change ads."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
