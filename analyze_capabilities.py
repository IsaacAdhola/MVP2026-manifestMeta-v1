"""Agent Capability and Dependency Analysis"""

import json
from pathlib import Path

# Agent directories
agents = {
    'MetaMarkCEO': 'Chief Growth Strategist',
    'ResearchAgent': 'Market Intelligence Director',
    'SearchVisibilityAgent': 'Search & Answer Visibility Director',
    'AdCopyAgent': 'Senior Conversion Copywriter',
    'ImageCreatorAgent': 'Creative Director',
    'FacebookPolicyAgent': 'Facebook Policy Compliance Officer',
    'ClientApprovalAgent': 'Client Approval Manager',
    'FacebookManagerAgent': 'Media Operations Director',
    'CampaignOpsAgent': 'Campaign Operations Director',
}

print("=== AGENT CAPABILITY MATRIX ===\n")

capabilities = {}

for agent_dir, agent_name in agents.items():
    print(f"\n{'='*70}")
    print(f"{agent_name} ({agent_dir})")
    print('='*70)
    
    # Read instructions
    instructions_path = Path(agent_dir) / 'instructions.md'
    if instructions_path.exists():
        instructions = instructions_path.read_text()
        
        # Extract key capabilities from instructions
        caps = []
        deps = []
        
        # Check for keywords indicating capabilities
        if 'research' in instructions.lower():
            caps.append('Market research')
        if 'copy' in instructions.lower() or 'write' in instructions.lower():
            caps.append('Content writing')
        if 'image' in instructions.lower() or 'visual' in instructions.lower():
            caps.append('Image generation')
        if 'policy' in instructions.lower() or 'compliance' in instructions.lower():
            caps.append('Policy compliance')
        if 'approval' in instructions.lower():
            caps.append('Approval management')
        if 'publish' in instructions.lower() or 'post' in instructions.lower():
            caps.append('Publishing/execution')
        if 'schedule' in instructions.lower() or 'campaign' in instructions.lower():
            caps.append('Campaign operations')
        if 'seo' in instructions.lower() or 'keyword' in instructions.lower():
            caps.append('SEO strategy')
        
        # Check for dependencies on other agents
        for other_agent, other_name in agents.items():
            if other_agent != agent_dir:
                if other_name.lower() in instructions.lower():
                    deps.append(other_name)
        
        # Count tool dependencies
        tools_path = Path(agent_dir) / 'tools'
        tool_count = 0
        tool_list = []
        if tools_path.exists():
            tool_files = [f for f in tools_path.glob('*.py') if f.stem != '__init__']
            tool_count = len(tool_files)
            tool_list = [f.stem for f in tool_files]
        
        print(f"\nTools: {tool_count}")
        if tool_list:
            for tool in tool_list:
                print(f"  - {tool}")
        
        print(f"\nCore Capabilities:")
        if caps:
            for cap in caps:
                print(f"  ✓ {cap}")
        else:
            print("  (No specific capabilities detected from instructions)")
        
        print(f"\nDependencies on other agents:")
        if deps:
            for dep in set(deps):
                print(f"  → {dep}")
        else:
            print("  (No explicit agent dependencies)")
        
        # Check independence indicators
        independence_score = 0
        indicators = []
        
        if 'your lane' in instructions.lower() or 'you own' in instructions.lower():
            independence_score += 3
            indicators.append("Clear lane ownership")
        
        if 'do not' in instructions.lower():
            do_nots = instructions.lower().count('do not')
            if do_nots >= 5:
                independence_score += 2
                indicators.append(f"Strong boundaries ({do_nots} 'do not' statements)")
        
        if 'handoff' in instructions.lower():
            independence_score += 2
            indicators.append("Explicit handoff protocol")
        
        if tool_count > 0:
            independence_score += min(tool_count, 3)
            indicators.append(f"Self-sufficient tools ({tool_count})")
        
        if 'finished package' in instructions.lower() or 'complete' in instructions.lower():
            independence_score += 1
            indicators.append("Finish-before-handoff protocol")
        
        # Normalize score to 1-10
        normalized_score = min(10, max(1, independence_score))
        
        print(f"\nIndependence Score: {normalized_score}/10")
        print("Independence Indicators:")
        for indicator in indicators:
            print(f"  • {indicator}")
        
        capabilities[agent_dir] = {
            'name': agent_name,
            'tool_count': tool_count,
            'tools': tool_list,
            'capabilities': caps,
            'dependencies': list(set(deps)),
            'independence_score': normalized_score,
            'indicators': indicators
        }

# Save capability matrix
with open('capability_matrix.json', 'w') as f:
    json.dump(capabilities, f, indent=2)

print("\n\n" + "="*70)
print("SUMMARY: INDEPENDENCE SCORES")
print("="*70)

sorted_agents = sorted(capabilities.items(), key=lambda x: x[1]['independence_score'], reverse=True)
for agent_dir, data in sorted_agents:
    score = data['independence_score']
    name = data['name']
    bar = '█' * score + '░' * (10 - score)
    print(f"{name:50} {bar} {score}/10")

print(f"\n✓ Capability matrix saved to capability_matrix.json")
