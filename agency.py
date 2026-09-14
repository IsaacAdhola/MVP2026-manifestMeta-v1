import os
import subprocess
import sys

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

from dotenv import load_dotenv
load_dotenv()

ceo = MetaMarkCEO()
adCopyAgent = AdCopyAgent()
imageCreatorAgent = ImageCreatorAgent()
facebookManagerAgent = FacebookManagerAgent()
researchAgent = ResearchAgent()
facebookPolicyAgent = FacebookPolicyAgent()
clientApprovalAgent = ClientApprovalAgent()
campaignOpsAgent = CampaignOpsAgent()
searchVisibilityAgent = SearchVisibilityAgent()

_communication_flows = [
    [ceo, researchAgent],
    [researchAgent, ceo],
    [ceo, searchVisibilityAgent],
    [searchVisibilityAgent, ceo],
    [researchAgent, searchVisibilityAgent],
    [searchVisibilityAgent, researchAgent],
    [ceo, adCopyAgent],
    [searchVisibilityAgent, adCopyAgent],
    [adCopyAgent, searchVisibilityAgent],
    [ceo, imageCreatorAgent],
    [ceo, facebookPolicyAgent],
    [ceo, clientApprovalAgent],
    [ceo, campaignOpsAgent],
    [adCopyAgent, imageCreatorAgent],
    [imageCreatorAgent, facebookPolicyAgent],
    [facebookPolicyAgent, ceo],
    [facebookPolicyAgent, clientApprovalAgent],
    [clientApprovalAgent, ceo],
    [clientApprovalAgent, facebookManagerAgent],
    [facebookManagerAgent, ceo],
    [facebookManagerAgent, campaignOpsAgent],
    [campaignOpsAgent, ceo],
]

agency = Agency(
    ceo,
    communication_flows=_communication_flows,
    shared_instructions='./agency_manifesto.md',
)

# Attach a demo_gradio helper so tests and ui_entry.py can call agency.demo_gradio(...)
def _demo_gradio(server_name="127.0.0.1", server_port=7860, share=False, allowed_paths=None):
    import gradio as gr
    from pathlib import Path as _Path

    def _chat(message, history):
        try:
            result = agency.get_response_sync(message)
            output = str(result.final_output) if result.final_output is not None else "(no response)"
            return output
        except Exception as exc:
            return f"[Error] {exc}"

    _default_allowed = allowed_paths or [
        str(_Path(__file__).resolve().parent / "generated_assets" / "images"),
    ]
    demo = gr.ChatInterface(
        fn=_chat,
        title="Manifest AI — Marketing Agency",
        description=(
            "Chat with the Chief Growth Strategist to plan your Facebook campaign.\n"
            "All specialist work (research, creative, compliance, approval) runs in the background."
        ),
    )
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        allowed_paths=_default_allowed,
    )

agency.demo_gradio = _demo_gradio


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

if __name__ == '__main__':
    _configure_console_encoding()

    noninteractive = os.environ.get("MANIFEST_AI_NONINTERACTIVE") or not sys.stdin.isatty()
    if noninteractive:
        print(
            "Interactive input is not available. "
            "Run this script in a terminal to chat with the agency."
        )
        sys.exit(0)

    try:
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