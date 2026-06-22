"""Test script to verify agency imports and initialization"""
import sys
import traceback

print("Testing agency import and initialization...")
print("=" * 50)

try:
    print("\n1. Testing imports...")
    from agency_swarm import Agency
    from FacebookManagerAgent import FacebookManagerAgent
    from ImageCreatorAgent import ImageCreatorAgent
    from AdCopyAgent import AdCopyAgent
    from MetaMarkCEO import MetaMarkCEO
    from ResearchAgent import ResearchAgent
    from FacebookPolicyAgent import FacebookPolicyAgent
    from ClientApprovalAgent import ClientApprovalAgent
    from dotenv import load_dotenv
    print("   [OK] All imports successful")
    
    print("\n2. Loading environment variables...")
    load_dotenv()
    print("   [OK] Environment variables loaded")
    
    print("\n3. Instantiating agents...")
    ceo = MetaMarkCEO()
    print("   [OK] MetaMarkCEO created")
    
    adCopyAgent = AdCopyAgent()
    print("   [OK] AdCopyAgent created")
    
    imageCreatorAgent = ImageCreatorAgent()
    print("   [OK] ImageCreatorAgent created")
    
    facebookManagerAgent = FacebookManagerAgent()
    print("   [OK] FacebookManagerAgent created")

    researchAgent = ResearchAgent()
    print("   [OK] ResearchAgent created")

    facebookPolicyAgent = FacebookPolicyAgent()
    print("   [OK] FacebookPolicyAgent created")

    clientApprovalAgent = ClientApprovalAgent()
    print("   [OK] ClientApprovalAgent created")
    
    print("\n4. Creating agency...")
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
    print("   [OK] Agency created successfully")
    
    print("\n5. Checking agency structure...")
    print(f"   - Entry point: {agency.entry_point.name if hasattr(agency, 'entry_point') else 'N/A'}")
    print(f"   - Number of agents: {len(agency.agents) if hasattr(agency, 'agents') else 'N/A'}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] ALL TESTS PASSED - Agency is ready to run!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

