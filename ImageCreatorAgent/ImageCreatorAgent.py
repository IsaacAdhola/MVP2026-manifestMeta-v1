from agency_swarm.agents import Agent


class ImageCreatorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Creative Director",
            description=(
                "Creates campaign visuals from approved copy, visual direction, and brand constraints. "
                "Does not write final copy, conduct research, or execute media."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools"
        )
