from agency_swarm import Agent
from model_router import MODEL_GPT


class CampaignOpsAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Campaign Operations Director",
            description=(
                "Owns the campaign calendar, post schedule, live/scheduled/completed post tracking, "
                "client budget management, and client-facing reporting. "
                "Does not create copy, images, or ads."
            ),
            model=MODEL_GPT,
            instructions="./instructions.md",
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools",
        )
