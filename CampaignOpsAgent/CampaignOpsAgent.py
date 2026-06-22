from agency_swarm.agents import Agent


class CampaignOpsAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Campaign Operations Director",
            description=(
                "Owns the campaign calendar, post schedule, live/scheduled/completed post tracking, "
                "client budget management, and client-facing reporting. "
                "Does not create copy, images, or ads."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
        )
