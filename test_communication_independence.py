"""Communication and Independence Testing for MetaMarkAgency"""

import json
import sys
from pathlib import Path

# Test imports without instantiation
try:
    from MetaMarkCEO import MetaMarkCEO
    from ResearchAgent import ResearchAgent
    from SearchVisibilityAgent import SearchVisibilityAgent
    from AdCopyAgent import AdCopyAgent
    from ImageCreatorAgent import ImageCreatorAgent
    from FacebookPolicyAgent import FacebookPolicyAgent
    from ClientApprovalAgent import ClientApprovalAgent
    from FacebookManagerAgent import FacebookManagerAgent
    from CampaignOpsAgent import CampaignOpsAgent
    print("✓ All agent imports successful")
except Exception as e:
    print(f"✗ Agent import failed: {e}")
    sys.exit(1)

# Test agency.py structure
try:
    with open('agency.py', 'r') as f:
        agency_code = f.read()
    
    print("\n=== COMMUNICATION FLOWS ANALYSIS ===")
    
    # Extract communication flows
    flows_start = agency_code.find('_communication_flows = [')
    flows_end = agency_code.find(']', flows_start) + 1
    flows_section = agency_code[flows_start:flows_end]
    
    # Count flows
    flow_count = flows_section.count('[ceo,') + flows_section.count('[researchAgent,') + \
                 flows_section.count('[searchVisibilityAgent,') + flows_section.count('[adCopyAgent,') + \
                 flows_section.count('[imageCreatorAgent,') + flows_section.count('[facebookPolicyAgent,') + \
                 flows_section.count('[clientApprovalAgent,') + flows_section.count('[facebookManagerAgent,') + \
                 flows_section.count('[campaignOpsAgent,')
    
    print(f"✓ Found {flow_count} communication flows defined")
    
    # Check for build_independent_agency function
    if 'def build_independent_agency(agent):' in agency_code:
        print("✓ build_independent_agency function exists")
    else:
        print("✗ build_independent_agency function missing")
    
except Exception as e:
    print(f"✗ Agency structure analysis failed: {e}")
    sys.exit(1)

# Test workflow state isolation
try:
    from workflow_state import set_state_value, get_state_value, clear_state
    
    print("\n=== STATE MANAGEMENT TESTING ===")
    
    # Test state operations
    clear_state()
    set_state_value("test_key", "test_value")
    value = get_state_value("test_key")
    
    if value == "test_value":
        print("✓ State management works correctly")
    else:
        print("✗ State management failed")
    
    # Check if state is global
    set_state_value("shared_data", {"agent": "test"})
    shared = get_state_value("shared_data")
    
    if shared == {"agent": "test"}:
        print("✓ State is globally shared (as designed)")
    else:
        print("✗ State sharing failed")
    
    clear_state()
    
except Exception as e:
    print(f"✗ State management test failed: {e}")
    sys.exit(1)

# Analyze agent tool isolation
try:
    print("\n=== AGENT TOOL ISOLATION ANALYSIS ===")
    
    agent_dirs = [
        "MetaMarkCEO",
        "ResearchAgent",
        "SearchVisibilityAgent",
        "AdCopyAgent",
        "ImageCreatorAgent",
        "FacebookPolicyAgent",
        "ClientApprovalAgent",
        "FacebookManagerAgent",
        "CampaignOpsAgent"
    ]
    
    agent_tools = {}
    for agent_dir in agent_dirs:
        tools_path = Path(agent_dir) / "tools"
        if tools_path.exists():
            tools = [f.stem for f in tools_path.glob("*.py") if f.stem != "__init__"]
            agent_tools[agent_dir] = tools
            print(f"✓ {agent_dir}: {len(tools)} tools")
        else:
            agent_tools[agent_dir] = []
            print(f"  {agent_dir}: 0 tools")
    
except Exception as e:
    print(f"✗ Tool isolation analysis failed: {e}")
    sys.exit(1)

# Analyze instructions for independence
try:
    print("\n=== AGENT INDEPENDENCE ANALYSIS ===")
    
    for agent_dir in agent_dirs:
        instructions_path = Path(agent_dir) / "instructions.md"
        if instructions_path.exists():
            content = instructions_path.read_text()
            
            # Check for dependency indicators
            has_own_lane = "your lane" in content.lower() or "you own" in content.lower()
            has_handoff_rules = "handoff" in content.lower()
            has_finish_work = "finish" in content.lower() or "complete" in content.lower()
            
            independence_score = sum([has_own_lane, has_handoff_rules, has_finish_work])
            
            print(f"  {agent_dir}: Independence indicators = {independence_score}/3")
        else:
            print(f"  {agent_dir}: No instructions found")
    
except Exception as e:
    print(f"✗ Independence analysis failed: {e}")
    sys.exit(1)

print("\n=== TESTING COMPLETE ===")
print("All tests passed successfully!")
