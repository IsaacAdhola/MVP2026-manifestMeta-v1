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
        # #region agent log
        try:
            import json as _json
            import time as _time
            _log = _Path(__file__).resolve().parent / "debug-9c2ba9.log"
            with open(_log, "a", encoding="utf-8") as _f:
                _f.write(_json.dumps({
                    "sessionId": "9c2ba9",
                    "runId": "pre-fix",
                    "hypothesisId": "C",
                    "location": "agency.py:_chat:entry",
                    "message": "gradio chat received",
                    "data": {
                        "msg_len": len(message or ""),
                        "msg_preview": (message or "")[:120],
                        "history_len": len(history or []),
                    },
                    "timestamp": int(_time.time() * 1000),
                }, ensure_ascii=True) + "\n")
        except Exception:
            pass
        # #endregion
        try:
            result = agency.get_response_sync(message)
            output = str(result.final_output) if result.final_output is not None else "(no response)"
            # #region agent log
            try:
                import re as _re
                import json as _json
                import time as _time
                _imgs = _re.findall(r"!\[[^\]]*\]\(([^)]+)\)", output or "")
                _log = _Path(__file__).resolve().parent / "debug-9c2ba9.log"
                with open(_log, "a", encoding="utf-8") as _f:
                    _f.write(_json.dumps({
                        "sessionId": "9c2ba9",
                        "runId": "pre-fix",
                        "hypothesisId": "C",
                        "location": "agency.py:_chat:exit",
                        "message": "gradio chat response",
                        "data": {
                            "output_len": len(output or ""),
                            "markdown_image_paths": _imgs[:5],
                            "unique_image_paths": len(set(_imgs)),
                        },
                        "timestamp": int(_time.time() * 1000),
                    }, ensure_ascii=True) + "\n")
            except Exception:
                pass
            # #endregion
            return output
        except Exception as exc:
            from error_logger import log_error
            log_error("Chief Growth Strategist", exc, location="agency.py:_chat")
            return f"[Error] {exc}"

    _default_allowed = allowed_paths or [
        str(_Path(__file__).resolve().parent / "generated_assets" / "images"),
    ]
    # #region agent log
    try:
        import json as _json
        import time as _time
        _log = _Path(__file__).resolve().parent / "debug-9c2ba9.log"
        with open(_log, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps({
                "sessionId": "9c2ba9",
                "runId": "pre-fix",
                "hypothesisId": "C",
                "location": "agency.py:_demo_gradio:launch",
                "message": "launching gradio with allowed_paths",
                "data": {"allowed_paths": _default_allowed},
                "timestamp": int(_time.time() * 1000),
            }, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # #endregion
    demo = gr.ChatInterface(
        fn=_chat,
        title="Manifest AI — Marketing Agency",
        description=(
            "Chat with the Chief Growth Strategist to plan your Facebook campaign.\n"
            "All specialist work (research, creative, compliance, approval) runs in the background."
        ),
    )
    # #region agent log
    try:
        import json as _json
        import time as _time
        _log = _Path(__file__).resolve().parent / "debug-9c2ba9.log"
        with open(_log, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps({
                "sessionId": "9c2ba9",
                "runId": "pre-fix",
                "hypothesisId": "F",
                "location": "agency.py:_demo_gradio:before_launch",
                "message": "about to call demo.launch",
                "data": {
                    "server_name": server_name,
                    "server_port": server_port,
                    "allowed_paths": _default_allowed,
                },
                "timestamp": int(_time.time() * 1000),
            }, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # #endregion
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