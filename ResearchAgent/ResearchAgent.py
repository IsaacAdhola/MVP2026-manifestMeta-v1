from agency_swarm.agents import Agent


class ResearchAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Market Intelligence Director",
            description=(
                "Leads market intelligence for Manifest AI by researching competitors, "
                "audiences, demographics, and ad-library patterns. This is the only "
                "agent with access to competitor ad research tools."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
        )
