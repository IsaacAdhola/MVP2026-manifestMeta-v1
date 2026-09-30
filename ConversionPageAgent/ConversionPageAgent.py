from agency_swarm import Agent
from model_router import MODEL_CLAUDE, agent_model


class ConversionPageAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Landing Page & CRO Director",
            description=(
                "Builds landing-page structure, headlines, proof blocks, and CRO audits "
                "for paid traffic. Does not publish websites or Meta ads."
            ),
            model=agent_model(MODEL_CLAUDE),
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
