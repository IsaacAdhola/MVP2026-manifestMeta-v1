#!/usr/bin/env python3
"""Generate competitive intelligence dashboard"""

from competitive_intelligence import get_competitive_intelligence, initialize_baseline_data

# Initialize baseline data
initialize_baseline_data()

# Get intelligence
intel = get_competitive_intelligence()

# Generate dashboard
dashboard = intel.generate_dashboard()

# Save to file
with open("COMPETITIVE_DASHBOARD.md", "w") as f:
    f.write(dashboard)

print("✅ Competitive dashboard generated: COMPETITIVE_DASHBOARD.md")
print()
print(dashboard)
