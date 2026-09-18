"""Detailed Communication Flow Analysis"""

import json
from pathlib import Path

# Parse communication flows from agency.py
with open('agency.py', 'r') as f:
    content = f.read()

# Extract flows
flows = []
lines = content.split('\n')
in_flows = False
for line in lines:
    if '_communication_flows = [' in line:
        in_flows = True
        continue
    if in_flows:
        if line.strip() == ']':
            break
        if '[' in line:
            # Extract agent names
            parts = line.split('[')[1].split(']')[0]
            agents = [a.strip() for a in parts.split(',')]
            if len(agents) == 2:
                flows.append(tuple(agents))

print(f"Total communication flows: {len(flows)}")
print("\nAll communication flows:")
for i, (src, dest) in enumerate(flows, 1):
    print(f"{i:2}. {src:25} -> {dest}")

# Map agents
agent_map = {
    'ceo': 'MetaMarkCEO (Chief Growth Strategist)',
    'researchAgent': 'ResearchAgent (Market Intelligence Director)',
    'searchVisibilityAgent': 'SearchVisibilityAgent (Search & Answer Visibility Director)',
    'adCopyAgent': 'AdCopyAgent (Senior Conversion Copywriter)',
    'imageCreatorAgent': 'ImageCreatorAgent (Creative Director)',
    'facebookPolicyAgent': 'FacebookPolicyAgent (Facebook Policy Compliance Officer)',
    'clientApprovalAgent': 'ClientApprovalAgent (Client Approval Manager)',
    'facebookManagerAgent': 'FacebookManagerAgent (Media Operations Director)',
    'campaignOpsAgent': 'CampaignOpsAgent (Campaign Operations Director)',
}

# Analyze connectivity
print("\n\n=== AGENT CONNECTIVITY ANALYSIS ===")
outbound = {}
inbound = {}
bidirectional = set()

for src, dest in flows:
    outbound[src] = outbound.get(src, []) + [dest]
    inbound[dest] = inbound.get(dest, []) + [src]
    
    # Check for bidirectional
    if (dest, src) in flows:
        bidirectional.add(tuple(sorted([src, dest])))

print("\nOutbound connections (who each agent can talk to):")
for agent in agent_map.keys():
    connections = outbound.get(agent, [])
    print(f"  {agent:25} can talk to: {len(connections)} agents - {connections}")

print("\nInbound connections (who can talk to each agent):")
for agent in agent_map.keys():
    connections = inbound.get(agent, [])
    print(f"  {agent:25} receives from: {len(connections)} agents - {connections}")

print("\nBidirectional communication pairs:")
for pair in sorted(bidirectional):
    print(f"  {pair[0]} <-> {pair[1]}")

# Check for isolated agents
print("\n\n=== ISOLATION CHECK ===")
all_agents = set(agent_map.keys())
connected_agents = set(outbound.keys()) | set(inbound.keys())
isolated = all_agents - connected_agents

if isolated:
    print(f"⚠ Isolated agents (no connections): {isolated}")
else:
    print("✓ No isolated agents found")

# Check for dead-ends
print("\n=== DEAD-END CHECK ===")
for agent in all_agents:
    out = len(outbound.get(agent, []))
    inn = len(inbound.get(agent, []))
    if inn > 0 and out == 0:
        print(f"⚠ {agent} is a dead-end (receives but cannot send)")
    elif inn == 0 and out > 0:
        print(f"⚠ {agent} is a source-only (sends but cannot receive)")

# Analyze CEO as hub
print("\n=== CEO HUB ANALYSIS ===")
ceo_out = outbound.get('ceo', [])
ceo_in = inbound.get('ceo', [])
print(f"CEO outbound connections: {len(ceo_out)}")
print(f"CEO inbound connections: {len(ceo_in)}")
print(f"CEO total connectivity: {len(set(ceo_out + ceo_in))} unique agents")

# Check manifesto alignment
print("\n=== MANIFESTO ALIGNMENT CHECK ===")
manifesto_path = Path('agency_manifesto.md')
if manifesto_path.exists():
    manifesto = manifesto_path.read_text()
    
    # Check for each agent mentioned
    for agent_key, agent_name in agent_map.items():
        title = agent_name.split('(')[1].rstrip(')')
        if title in manifesto:
            print(f"✓ {title} documented in manifesto")
        else:
            print(f"✗ {title} NOT found in manifesto")

# Save detailed flow data
flow_data = {
    'total_flows': len(flows),
    'flows': [{'from': src, 'to': dest} for src, dest in flows],
    'outbound': {k: v for k, v in outbound.items()},
    'inbound': {k: v for k, v in inbound.items()},
    'bidirectional': [list(pair) for pair in bidirectional],
    'agent_map': agent_map
}

with open('communication_flow_data.json', 'w') as f:
    json.dump(flow_data, f, indent=2)

print("\n✓ Flow data saved to communication_flow_data.json")
