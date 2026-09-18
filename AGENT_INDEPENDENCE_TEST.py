#!/usr/bin/env python3
"""
Agent Independence Testing Suite
Tests that each agent can be instantiated and used independently
"""

import sys
from pathlib import Path

# Suppress OpenAI API warnings during testing
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-independence-testing")

print("="*70)
print("AGENT INDEPENDENCE TEST SUITE")
print("="*70)
print()

results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_agent(agent_name: str, agent_class, module_path: str):
    """Test if an agent can be instantiated independently."""
    print(f"Testing: {agent_name}")
    print(f"  Module: {module_path}")
    
    try:
        # Try to instantiate
        agent = agent_class()
        
        # Verify attributes
        assert hasattr(agent, 'name'), f"{agent_name} missing 'name' attribute"
        assert hasattr(agent, 'description'), f"{agent_name} missing 'description' attribute"
        assert hasattr(agent, 'instructions'), f"{agent_name} missing 'instructions' attribute"
        
        print(f"  ✅ Name: {agent.name}")
        print(f"  ✅ Description: {agent.description[:60]}...")
        print(f"  ✅ Instructions: {type(agent.instructions).__name__}")
        
        # Check for tools
        if hasattr(agent, 'tools'):
            tool_count = len(agent.tools) if agent.tools else 0
            print(f"  ✅ Tools: {tool_count} registered")
        
        # Check independence markers
        independence_score = 10
        
        # Has own instructions?
        if agent.instructions:
            print(f"  ✅ Has independent instructions")
        else:
            print(f"  ⚠️  No instructions file")
            independence_score -= 2
        
        # Has own tools?
        if hasattr(agent, 'tools') and agent.tools:
            print(f"  ✅ Has independent tools")
        else:
            print(f"  ℹ️  No tools (coordinator role)")
        
        results["passed"].append({
            "name": agent_name,
            "agent_name": agent.name,
            "independence_score": independence_score
        })
        
        print(f"  ✅ PASSED - Independence Score: {independence_score}/10")
        print()
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ FAILED: {error_msg}")
        results["failed"].append({
            "name": agent_name,
            "error": error_msg
        })
        print()
        return False

# Test each agent
print("1. Testing MetaMarkCEO (Chief Growth Strategist)")
print("-" * 70)
try:
    from MetaMarkCEO import MetaMarkCEO
    test_agent("MetaMarkCEO", MetaMarkCEO, "MetaMarkCEO/MetaMarkCEO.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "MetaMarkCEO", "error": str(e)})

print("2. Testing ResearchAgent (Market Intelligence Director)")
print("-" * 70)
try:
    from ResearchAgent import ResearchAgent
    test_agent("ResearchAgent", ResearchAgent, "ResearchAgent/ResearchAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "ResearchAgent", "error": str(e)})

print("3. Testing SearchVisibilityAgent (Search & Answer Visibility Director)")
print("-" * 70)
try:
    from SearchVisibilityAgent import SearchVisibilityAgent
    test_agent("SearchVisibilityAgent", SearchVisibilityAgent, "SearchVisibilityAgent/SearchVisibilityAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "SearchVisibilityAgent", "error": str(e)})

print("4. Testing AdCopyAgent (Senior Conversion Copywriter)")
print("-" * 70)
try:
    from AdCopyAgent import AdCopyAgent
    test_agent("AdCopyAgent", AdCopyAgent, "AdCopyAgent/AdCopyAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "AdCopyAgent", "error": str(e)})

print("5. Testing ImageCreatorAgent (Creative Director)")
print("-" * 70)
try:
    from ImageCreatorAgent import ImageCreatorAgent
    test_agent("ImageCreatorAgent", ImageCreatorAgent, "ImageCreatorAgent/ImageCreatorAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "ImageCreatorAgent", "error": str(e)})

print("6. Testing FacebookPolicyAgent (Facebook Policy Compliance Officer)")
print("-" * 70)
try:
    from FacebookPolicyAgent import FacebookPolicyAgent
    test_agent("FacebookPolicyAgent", FacebookPolicyAgent, "FacebookPolicyAgent/FacebookPolicyAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "FacebookPolicyAgent", "error": str(e)})

print("7. Testing ClientApprovalAgent (Client Approval Manager)")
print("-" * 70)
try:
    from ClientApprovalAgent import ClientApprovalAgent
    test_agent("ClientApprovalAgent", ClientApprovalAgent, "ClientApprovalAgent/ClientApprovalAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "ClientApprovalAgent", "error": str(e)})

print("8. Testing FacebookManagerAgent (Media Operations Director)")
print("-" * 70)
try:
    from FacebookManagerAgent import FacebookManagerAgent
    test_agent("FacebookManagerAgent", FacebookManagerAgent, "FacebookManagerAgent/FacebookManagerAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "FacebookManagerAgent", "error": str(e)})

print("9. Testing CampaignOpsAgent (Campaign Operations Director)")
print("-" * 70)
try:
    from CampaignOpsAgent import CampaignOpsAgent
    test_agent("CampaignOpsAgent", CampaignOpsAgent, "CampaignOpsAgent/CampaignOpsAgent.py")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    results["failed"].append({"name": "CampaignOpsAgent", "error": str(e)})

# Summary
print("="*70)
print("TEST SUMMARY")
print("="*70)
print(f"✅ Passed: {len(results['passed'])}")
print(f"❌ Failed: {len(results['failed'])}")
print(f"⚠️  Warnings: {len(results['warnings'])}")
print()

if results['passed']:
    print("PASSED AGENTS:")
    for agent in results['passed']:
        score = agent.get('independence_score', 10)
        print(f"  ✅ {agent['agent_name']} - Independence: {score}/10")
    print()

if results['failed']:
    print("FAILED AGENTS:")
    for agent in results['failed']:
        print(f"  ❌ {agent['name']}: {agent['error'][:80]}")
    print()

# Independence Score
if results['passed']:
    avg_score = sum(a.get('independence_score', 10) for a in results['passed']) / len(results['passed'])
    print(f"AVERAGE INDEPENDENCE SCORE: {avg_score:.1f}/10")
    print()

# Exit code
exit_code = 0 if len(results['failed']) == 0 else 1
print(f"Exit Code: {exit_code}")
sys.exit(exit_code)
