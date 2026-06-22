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

from dotenv import load_dotenv
load_dotenv()

ceo = MetaMarkCEO()
adCopyAgent = AdCopyAgent()
imageCreatorAgent = ImageCreatorAgent()
facebookManagerAgent = FacebookManagerAgent()
researchAgent = ResearchAgent()
facebookPolicyAgent = FacebookPolicyAgent()
clientApprovalAgent = ClientApprovalAgent()

agency = Agency([
                  ceo,
                 [ceo, researchAgent],
                 [researchAgent, ceo],
                 [ceo, adCopyAgent],
                 [ceo, imageCreatorAgent],
                 [ceo, facebookPolicyAgent],
                 [ceo, clientApprovalAgent],
                 [adCopyAgent, imageCreatorAgent],
                 [imageCreatorAgent, facebookPolicyAgent],
                 [facebookPolicyAgent, ceo],
                 [facebookPolicyAgent, clientApprovalAgent],
                 [clientApprovalAgent, ceo],
                 [clientApprovalAgent, facebookManagerAgent],
                 [facebookManagerAgent, ceo]],
                shared_instructions='./agency_manifesto.md')


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

    if not sys.stdin.isatty():
        print(
            "Interactive input is not available. "
            "Run this script in a terminal to chat with the agency."
        )
        sys.exit(0)

    try:
        agency.run_demo()
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