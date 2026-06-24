"""Test script to verify agency can start the Gradio demo"""
import sys
import traceback
import subprocess

print("Testing agency Gradio demo startup...")
print("=" * 50)

try:
    print("\n1. Importing and initializing agency...")
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
                     [adCopyAgent, imageCreatorAgent],
                     [ceo, imageCreatorAgent],
                     [ceo, facebookPolicyAgent],
                     [ceo, clientApprovalAgent],
                     [imageCreatorAgent, facebookPolicyAgent],
                     [facebookPolicyAgent, ceo],
                     [facebookPolicyAgent, clientApprovalAgent],
                     [clientApprovalAgent, ceo],
                     [clientApprovalAgent, facebookManagerAgent],
                     [facebookManagerAgent, ceo]],
                    shared_instructions='./agency_manifesto.md')
    
    print("   [OK] Agency initialized")
    
    print("\n2. Testing agency entrypoint smoke startup...")
    print("   (Running agency.py in non-interactive mode to verify clean startup path)")

    try:
        proc = subprocess.run(
            [sys.executable, "agency.py"],
            capture_output=True,
            text=True,
            timeout=120,
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
        if not hasattr(agency, "demo_gradio"):
            raise RuntimeError("demo_gradio method not found on Agency object.")
        print("   [OK] agency.py startup path executed cleanly in non-interactive mode")
        print("   [OK] demo_gradio method exists for UI startup")
    except Exception as e:
        print(f"   [ERROR] Failed startup smoke check: {e}")
        raise
    
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





