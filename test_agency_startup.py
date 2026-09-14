"""Test script to verify agency can start the Gradio demo"""
import os
import sys
import traceback
import subprocess

print("Testing agency Gradio demo startup...")
print("=" * 50)

try:
    print("\n1. Importing agency module (single init path)...")
    from agency import agency as _imported_agency
    print("   [OK] Agency initialized")

    agent_count = len(_imported_agency.agents) if hasattr(_imported_agency, "agents") else 0
    if agent_count != 9:
        raise RuntimeError(f"Expected 9 agents in agency, found {agent_count}")
    print(f"   [OK] All {agent_count} agents present")

    if not hasattr(_imported_agency, "demo_gradio"):
        raise RuntimeError("demo_gradio method not found on Agency object.")
    print("   [OK] demo_gradio method exists for UI startup")

    print("\n2. Testing agency entrypoint smoke startup...")
    print("   (Running agency.py in non-interactive mode to verify clean startup path)")

    try:
        proc = subprocess.run(
            [sys.executable, "agency.py"],
            stdin=subprocess.DEVNULL,
            env={**os.environ, "MANIFEST_AI_NONINTERACTIVE": "1"},
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        combined_output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            raise RuntimeError(
                f"agency.py exited with code {proc.returncode}. Output: {combined_output}"
            )
        if "Interactive input is not available." not in combined_output:
            raise RuntimeError(
                "agency.py did not reach expected non-interactive startup path."
            )
        print("   [OK] agency.py startup path executed cleanly in non-interactive mode")
    except Exception as e:
        print(f"   [ERROR] Failed startup smoke check: {e}")
        raise

    print("\n3. Checking Gradio availability...")
    try:
        import gradio as gr  # noqa: F401
        print("   [OK] gradio is installed")
    except ImportError as e:
        raise RuntimeError(f"gradio is not installed: {e}") from e

    print("\n" + "=" * 50)
    print("[SUCCESS] Agency is ready to run!")
    print("=" * 50)
    print("\nTo start the agency, run:")
    print("  python agency.py")
    print("\nThe Gradio interface will start and display a URL.")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
