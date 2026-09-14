"""
Simulates a real client conversation with the Manifest AI CEO agent.
Sends messages programmatically and prints the full exchange.
"""
import sys
import os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from agency import agency

DIVIDER = "\n" + "=" * 70 + "\n"

def send(message: str, label: str = "CLIENT") -> str:
    print(f"\n{'─' * 70}")
    print(f"  {label}: {message}")
    print(f"{'─' * 70}")
    response = agency.get_completion(message)
    print(f"\n  MANIFEST AI:\n")
    print(f"  {response}")
    return response


if __name__ == "__main__":
    print(DIVIDER)
    print("  MANIFEST AI — LIVE CONVERSATION TEST")
    print("  Simulating a new client engagement from scratch")
    print(DIVIDER)

    # Turn 1 — opening message, new client
    send(
        "Hi, I run a med spa in Dallas. We do Botox, fillers, laser treatments, "
        "and body contouring. I want to grow my client base on Facebook — "
        "I'm not sure if I need organic posts or paid ads, maybe both. "
        "My budget is flexible but I'd like to keep it smart. Where do we start?"
    )

    # Turn 2 — answering CEO's intake question
    send(
        "Mostly women between 30 and 55, professional, disposable income. "
        "We're in North Dallas — Plano, Frisco, Allen area. "
        "Main goal is booked appointments. We have a strong before/after gallery "
        "and our reviews are excellent — 4.9 stars. "
        "I don't know much about competitors honestly, could you look into that?"
    )

    print(DIVIDER)
    print("  TEST COMPLETE")
    print(DIVIDER)
