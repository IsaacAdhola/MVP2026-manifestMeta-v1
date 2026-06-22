from agency_swarm.agents import Agent


class FacebookPolicyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Facebook Policy Compliance Officer",
            description=(
                "Reviews Facebook posts, paid ads, campaign claims, targeting notes, "
                "and publishing plans against Meta policy references before media execution."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
        )
