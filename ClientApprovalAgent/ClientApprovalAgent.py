from agency_swarm.agents import Agent


class ClientApprovalAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Client Approval Manager",
            description=(
                "Verifies final client approval for selected copy, selected creative, schedule, "
                "budget, targeting, destination links, and policy approval before media execution."
            ),
            model="gpt-4o",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
        )
