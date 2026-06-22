from agency_swarm.tools import BaseTool
from pydantic import Field
import json
from workflow_state import set_state_value


class ImageSelector(BaseTool):
    """
    Records the client's chosen image option and sets it as the active image for downstream agents.
    Call this after the client replies with their preferred option (1, 2, or 3).
    """

    selected_option: int = Field(
        ...,
        description="The option number the client chose: 1, 2, or 3.",
    )

    def run(self):
        image_options = self._shared_state.get("image_options", [])

        if not image_options:
            return json.dumps({
                "error": "No image options found in session state. Run ImageGenerator first."
            })

        match = next((o for o in image_options if o["option"] == self.selected_option), None)
        if not match:
            available = [o["option"] for o in image_options]
            return json.dumps({
                "error": f"Option {self.selected_option} not found. Available options: {available}"
            })

        selected_path = match["image_path"]
        self._shared_state.set("image_path", selected_path)
        set_state_value("image_path", selected_path)
        set_state_value("selected_image_option", self.selected_option)

        return json.dumps({
            "selected_option": self.selected_option,
            "image_path": selected_path,
            "status": "Client selection recorded. Ready for compliance review and media execution.",
        })
