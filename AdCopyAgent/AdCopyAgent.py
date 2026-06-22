from agency_swarm.agents import Agent


class AdCopyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Senior Conversion Copywriter",
            description=(
                "Writes high-converting ad copy from approved strategy, audience, offer, "
                "tone, and research insights. Does not conduct research, generate images, or execute media."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools"
        )
