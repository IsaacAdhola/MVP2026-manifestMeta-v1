from agency_swarm.agents import Agent


class FacebookManagerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Media Operations Director",
            description=(
                "Executes Facebook Page publishing and paid Meta ad operations from approved copy, "
                "creative, schedule, targeting, budget, and links. Does not write copy, create images, or conduct research."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools"
        )
