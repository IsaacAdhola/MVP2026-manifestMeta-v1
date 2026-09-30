import os
import subprocess
import sys

from dotenv import load_dotenv
from model_router import apply_provider_env

load_dotenv()
apply_provider_env()

from firebase_adapter import initialize_firebase

initialize_firebase()

from agency_swarm import Agency
from FacebookManagerAgent import FacebookManagerAgent
from ImageCreatorAgent import ImageCreatorAgent
from AdCopyAgent import AdCopyAgent
from MetaMarkCEO import MetaMarkCEO
from ResearchAgent import ResearchAgent
from FacebookPolicyAgent import FacebookPolicyAgent
from ClientApprovalAgent import ClientApprovalAgent
from CampaignOpsAgent import CampaignOpsAgent
from SearchVisibilityAgent import SearchVisibilityAgent
from PerformanceAnalystAgent import PerformanceAnalystAgent
from CommunityManagerAgent import CommunityManagerAgent
from ConversionPageAgent import ConversionPageAgent
from CulturalIntelligenceAgent import CulturalIntelligenceAgent

ceo = MetaMarkCEO()
adCopyAgent = AdCopyAgent()
imageCreatorAgent = ImageCreatorAgent()
facebookManagerAgent = FacebookManagerAgent()
researchAgent = ResearchAgent()
facebookPolicyAgent = FacebookPolicyAgent()
clientApprovalAgent = ClientApprovalAgent()
campaignOpsAgent = CampaignOpsAgent()
searchVisibilityAgent = SearchVisibilityAgent()
performanceAnalystAgent = PerformanceAnalystAgent()
communityManagerAgent = CommunityManagerAgent()
conversionPageAgent = ConversionPageAgent()
culturalIntelligenceAgent = CulturalIntelligenceAgent()

# Agency Swarm v1.x: directional SendMessage flows as (sender, receiver) tuples.
# Lists also parse, but tuples match the official docs and migration guide.
_communication_flows = [
    (ceo, researchAgent),
    (researchAgent, ceo),
    (ceo, culturalIntelligenceAgent),
    (culturalIntelligenceAgent, ceo),
    (researchAgent, culturalIntelligenceAgent),
    (culturalIntelligenceAgent, adCopyAgent),
    (ceo, searchVisibilityAgent),
    (searchVisibilityAgent, ceo),
    (researchAgent, searchVisibilityAgent),
    (searchVisibilityAgent, researchAgent),
    (ceo, adCopyAgent),
    (adCopyAgent, ceo),
    (searchVisibilityAgent, adCopyAgent),
    (adCopyAgent, searchVisibilityAgent),
    (ceo, imageCreatorAgent),
    (imageCreatorAgent, ceo),
    (ceo, conversionPageAgent),
    (conversionPageAgent, ceo),
    (ceo, facebookPolicyAgent),
    (ceo, clientApprovalAgent),
    (ceo, campaignOpsAgent),
    (ceo, performanceAnalystAgent),
    (performanceAnalystAgent, ceo),
    (campaignOpsAgent, performanceAnalystAgent),
    (ceo, communityManagerAgent),
    (communityManagerAgent, ceo),
    (adCopyAgent, imageCreatorAgent),
    (imageCreatorAgent, facebookPolicyAgent),
    (facebookPolicyAgent, ceo),
    (facebookPolicyAgent, clientApprovalAgent),
    (clientApprovalAgent, ceo),
    (clientApprovalAgent, facebookManagerAgent),
    (facebookManagerAgent, ceo),
    (facebookManagerAgent, campaignOpsAgent),
    (campaignOpsAgent, ceo),
]

agency = Agency(
    ceo,
    communication_flows=_communication_flows,
    shared_instructions="./agency_manifesto.md",
)

from client_gateway import run_client_turn


def _demo_gradio(server_name="127.0.0.1", server_port=7860, share=False, allowed_paths=None):
    """Local Gradio chat UI (product path). Official Agency Swarm UIs: agency.tui() / copilot_demo()."""
    import gradio as gr
    from pathlib import Path as _Path

    def _chat(message, history):
        try:
            output = run_client_turn(message, agency).text
            return output
        except Exception as exc:
            from error_logger import log_error

            log_error("Chief Growth Strategist", exc, location="agency.py:_chat")
            return f"[Error] {exc}"

    _default_allowed = allowed_paths or [
        str(_Path(__file__).resolve().parent / "generated_assets" / "images"),
    ]
    demo = gr.ChatInterface(
        fn=_chat,
        title="Manifest AI",
        description=(
            "Talk to the CEO to plan and run your Meta campaign.\n"
            "Research, creative, compliance, and Facebook execution run inside the company."
        ),
    )
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        allowed_paths=_default_allowed,
    )


agency.demo_gradio = _demo_gradio


def build_independent_agency(agent):
    """Run one specialist without team routing. The CEO remains the team communicator."""
    return Agency(
        agent,
        communication_flows=[],
        shared_instructions="./agency_manifesto.md",
    )


def _configure_console_encoding() -> None:
    # Rich output in run_demo uses unicode box-drawing and emoji characters.
    # On Windows, ensure code page/stdio are UTF-8 to avoid encode errors.
    if os.name == "nt":
        try:
            subprocess.run(
                ["chcp", "65001"],
                check=False,
                capture_output=True,
                text=True,
                shell=True,
            )
        except Exception:
            pass

    for stream_name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


if __name__ == "__main__":
    _configure_console_encoding()

    noninteractive = os.environ.get("MANIFEST_AI_NONINTERACTIVE") or not sys.stdin.isatty()
    if noninteractive:
        print(
            "Interactive input is not available. "
            "Run this script in a terminal to chat with the agency."
        )
        sys.exit(0)

    ui_mode = (os.environ.get("MANIFEST_AI_UI") or "gradio").strip().lower()
    try:
        if ui_mode == "tui":
            agency.tui()
        elif ui_mode == "copilot":
            agency.copilot_demo()
        else:
            agency.demo_gradio()
    except RuntimeError as exc:
        message = str(exc)
        if "Run still active after _ensure_no_active_run" in message:
            print(
                "Agency run ended due to an active pending action. "
                "This usually happens after repeated tool retries. "
                "Please rerun after resolving the reported blocker."
            )
            sys.exit(1)
        raise
