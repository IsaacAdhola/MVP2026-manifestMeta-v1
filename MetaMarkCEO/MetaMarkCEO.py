from agency_swarm.agents import Agent


class MetaMarkCEO(Agent):
    def __init__(self):
        super().__init__(
            name="Chief Growth Strategist",
            description=(
                "Acts as Manifest AI's executive client lead. Owns client intake, "
                "strategic direction, specialist delegation, and premium client-facing communication."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools"
        )
