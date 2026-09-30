from agency_swarm import Agent
from model_router import MODEL_GPT


class ImageCreatorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Creative Director",
            description=(
                "Senior graphic designer / art director: art-direction note, "
                "three distinct DALL-E ad concepts, designer rationale, and a recommendation. "
                "Does not write final copy, conduct research, or execute media."
            ),
            model=MODEL_GPT,
            instructions="./instructions.md",
            # Large design PDF lives in knowledge/ and is consulted locally — do not
            # auto-sync via files_folder (OpenAI vector-store sync hangs UI startup).
            files_folder=None,
            schemas_folder=None,
            tools=[],
            tools_folder="./tools"
        )
