from agency_swarm import Agent
from model_router import MODEL_GPT


class FacebookManagerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Media Operations Director",
            description=(
                "Executes Facebook Page publishing and paid Meta ad operations from approved copy, "
                "creative, schedule, targeting, budget, and links. Does not write copy, create images, or conduct research."
            ),
            model=MODEL_GPT,
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools"
        )
