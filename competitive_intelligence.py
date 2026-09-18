"""
Competitive Intelligence Dashboard
Tracks competitors: Jasper, Copy.ai, Juma, YodAI, Markifact, Superscale
Monitors feature releases, pricing changes, and market positioning
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from safe_audit_log import write_audit_event


class CompetitorFeatureCategory(Enum):
    """Categories for competitor features"""
    AI_MODELS = "ai_models"
    INTEGRATIONS = "integrations"
    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    PRICING = "pricing"
    COMPLIANCE = "compliance"
    PLATFORM = "platform"


_INTEL_DIR = Path(__file__).resolve().parent / ".competitive_intel"
_INTEL_DIR.mkdir(exist_ok=True)


class CompetitiveIntelligence:
    """
    Tracks competitor features, pricing, and positioning.
    Generates differential analysis reports.
    """
    
    # Known competitors with their key attributes
    COMPETITORS = {
        "jasper": {
            "name": "Jasper AI",
            "url": "https://www.jasper.ai",
            "focus": "Enterprise content creation",
            "target": "Large enterprises, marketing teams",
            "pricing_model": "seat-based",
            "estimated_price_range": "$39-$125/user/month",
        },
        "copyai": {
            "name": "Copy.ai",
            "url": "https://www.copy.ai",
            "focus": "Sales and marketing copy",
            "target": "SMBs, solopreneurs",
            "pricing_model": "seat-based",
            "estimated_price_range": "$36-$186/user/month",
        },
        "juma": {
            "name": "Juma AI",
            "url": "https://juma.ai",
            "focus": "AI marketing automation",
            "target": "Mid-market businesses",
            "pricing_model": "usage-based",
            "estimated_price_range": "Custom pricing",
        },
        "yodai": {
            "name": "YodAI",
            "url": "https://yod.ai",
            "focus": "Multi-channel marketing",
            "target": "SMBs",
            "pricing_model": "tiered",
            "estimated_price_range": "$99-$499/month",
        },
        "markifact": {
            "name": "Markifact",
            "url": "https://markifact.com",
            "focus": "Marketing artifact generation",
            "target": "Agencies, consultants",
            "pricing_model": "project-based",
            "estimated_price_range": "$500-$2000/project",
        },
        "superscale": {
            "name": "Superscale",
            "url": "https://superscale.com",
            "focus": "Growth marketing automation",
            "target": "Startups, growth teams",
            "pricing_model": "usage-based",
            "estimated_price_range": "$299-$999/month",
        },
    }
    
    def __init__(self):
        self._state_file = _INTEL_DIR / "competitors.json"
        self._data: dict[str, dict[str, Any]] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load competitor intelligence from disk"""
        if self._state_file.exists():
            try:
                self._data = json.loads(self._state_file.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}
        
        # Initialize if empty
        if not self._data:
            for comp_id, comp_info in self.COMPETITORS.items():
                self._data[comp_id] = {
                    **comp_info,
                    "features": [],
                    "pricing_history": [],
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
    
    def _save_state(self) -> None:
        """Save competitor intelligence to disk"""
        self._state_file.write_text(
            json.dumps(self._data, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
    
    def record_feature(
        self,
        competitor_id: str,
        feature_name: str,
        category: CompetitorFeatureCategory,
        description: str,
        announced_date: Optional[str] = None,
    ) -> None:
        """Record a competitor feature"""
        if competitor_id not in self._data:
            return
        
        feature = {
            "name": feature_name,
            "category": category.value,
            "description": description,
            "announced_date": announced_date or datetime.now(timezone.utc).isoformat(),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self._data[competitor_id]["features"].append(feature)
        self._data[competitor_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        
        write_audit_event(
            event_type="competitor_feature_tracked",
            actor="competitive_intelligence",
            outcome="recorded",
            details={
                "competitor": competitor_id,
                "feature": feature_name,
                "category": category.value,
            },
        )
    
    def record_pricing_change(
        self,
        competitor_id: str,
        old_price: Optional[str],
        new_price: str,
        notes: Optional[str] = None,
    ) -> None:
        """Record a competitor pricing change"""
        if competitor_id not in self._data:
            return
        
        change = {
            "old_price": old_price,
            "new_price": new_price,
            "notes": notes,
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if "pricing_history" not in self._data[competitor_id]:
            self._data[competitor_id]["pricing_history"] = []
        
        self._data[competitor_id]["pricing_history"].append(change)
        self._data[competitor_id]["estimated_price_range"] = new_price
        self._data[competitor_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        
        write_audit_event(
            event_type="competitor_pricing_changed",
            actor="competitive_intelligence",
            outcome="recorded",
            details={
                "competitor": competitor_id,
                "old_price": old_price,
                "new_price": new_price,
            },
        )
    
    def get_competitor_data(self, competitor_id: str) -> Optional[dict[str, Any]]:
        """Get all data for a competitor"""
        return self._data.get(competitor_id)
    
    def get_all_competitors(self) -> dict[str, dict[str, Any]]:
        """Get all competitor data"""
        return self._data
    
    def generate_feature_gap_analysis(self) -> dict[str, Any]:
        """
        Generate analysis of feature gaps compared to MetaMarkAgency.
        """
        # MetaMarkAgency features
        our_features = {
            "multi_agent_architecture": True,
            "built_in_governance": True,
            "human_in_loop": True,
            "end_to_end_execution": True,
            "compliance_first": True,
            "open_architecture": True,
            "facebook_integration": True,
            "policy_compliance": True,
            "client_approval_workflow": True,
            "research_automation": True,
            "image_generation": True,
            "ad_copy_generation": True,
        }
        
        # Analyze competitors
        competitor_features = {}
        for comp_id, comp_data in self._data.items():
            features = comp_data.get("features", [])
            feature_set = {f["name"].lower().replace(" ", "_") for f in features}
            competitor_features[comp_id] = feature_set
        
        # Our unique features
        unique_to_us = []
        for feature in our_features:
            has_it = False
            for comp_features in competitor_features.values():
                if feature in comp_features:
                    has_it = True
                    break
            if not has_it:
                unique_to_us.append(feature)
        
        return {
            "our_unique_features": unique_to_us,
            "our_total_features": len(our_features),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def generate_pricing_comparison(self) -> dict[str, Any]:
        """Generate pricing comparison report"""
        comparison = {}
        
        for comp_id, comp_data in self._data.items():
            comparison[comp_id] = {
                "name": comp_data["name"],
                "pricing_model": comp_data["pricing_model"],
                "price_range": comp_data["estimated_price_range"],
                "last_changed": (
                    comp_data["pricing_history"][-1]["changed_at"]
                    if comp_data.get("pricing_history")
                    else "Never"
                ),
            }
        
        # Add our pricing
        comparison["metamarkagency"] = {
            "name": "MetaMarkAgency",
            "pricing_model": "campaign-based",
            "price_range": "$499-$1999/campaign",
            "differentiator": "Pay per campaign, not per seat. No hidden fees.",
        }
        
        return {
            "comparison": comparison,
            "our_advantage": "Campaign-based pricing vs seat/usage-based",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def generate_dashboard(self) -> str:
        """Generate markdown dashboard"""
        lines = [
            "# Competitive Intelligence Dashboard",
            "",
            f"*Last Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "## Competitor Overview",
            "",
        ]
        
        for comp_id, comp_data in self._data.items():
            lines.append(f"### {comp_data['name']}")
            lines.append(f"- **URL**: {comp_data['url']}")
            lines.append(f"- **Focus**: {comp_data['focus']}")
            lines.append(f"- **Target**: {comp_data['target']}")
            lines.append(f"- **Pricing**: {comp_data['estimated_price_range']} ({comp_data['pricing_model']})")
            lines.append(f"- **Features Tracked**: {len(comp_data.get('features', []))}")
            lines.append(f"- **Last Updated**: {comp_data['last_updated'][:10]}")
            lines.append("")
        
        # Feature gap analysis
        lines.append("## Feature Gap Analysis")
        lines.append("")
        gap_analysis = self.generate_feature_gap_analysis()
        lines.append(f"**Our Unique Features ({len(gap_analysis['our_unique_features'])}):**")
        for feature in gap_analysis["our_unique_features"]:
            lines.append(f"- ✅ {feature.replace('_', ' ').title()}")
        lines.append("")
        
        # Pricing comparison
        lines.append("## Pricing Comparison")
        lines.append("")
        pricing = self.generate_pricing_comparison()
        lines.append("| Competitor | Model | Price Range |")
        lines.append("|------------|-------|-------------|")
        for comp_id, comp_info in pricing["comparison"].items():
            lines.append(f"| {comp_info['name']} | {comp_info['pricing_model']} | {comp_info['price_range']} |")
        lines.append("")
        lines.append(f"**Our Advantage:** {pricing['our_advantage']}")
        lines.append("")
        
        # Market positioning
        lines.append("## Market Positioning")
        lines.append("")
        lines.append("**MetaMarkAgency's 7 Key Differentiators:**")
        lines.append("1. 🤖 **True Multi-Agent Architecture** - Not a single AI, but a team of specialized agents")
        lines.append("2. 🛡️ **Built-in Governance** - Governed shared memory prevents data leakage")
        lines.append("3. 👤 **Human-in-Loop** - Client approval workflow, not autonomous posting")
        lines.append("4. 🎯 **End-to-End Execution** - From research to posting, fully automated")
        lines.append("5. ✅ **Compliance-First** - Facebook policy checking built-in")
        lines.append("6. 🔌 **Open Architecture** - Self-hostable, customizable, no vendor lock-in")
        lines.append("7. 💰 **SMB Pricing** - $499/campaign vs $5000+ traditional agencies")
        lines.append("")
        
        return "\n".join(lines)


# Global intelligence instance
_intel = CompetitiveIntelligence()


def get_competitive_intelligence() -> CompetitiveIntelligence:
    """Get global competitive intelligence instance"""
    return _intel


# Initialize with baseline features (can be updated via API/scraping)
def initialize_baseline_data():
    """Initialize baseline competitor feature data"""
    intel = get_competitive_intelligence()
    
    # Jasper features (known from public info)
    intel.record_feature("jasper", "Brand Voice", CompetitorFeatureCategory.AI_MODELS, 
                        "Learns and mimics brand voice")
    intel.record_feature("jasper", "SEO Mode", CompetitorFeatureCategory.PLATFORM,
                        "SEO-optimized content generation")
    
    # Copy.ai features
    intel.record_feature("copyai", "Sales Workflow", CompetitorFeatureCategory.AUTOMATION,
                        "Automated sales email sequences")
    intel.record_feature("copyai", "Chat Interface", CompetitorFeatureCategory.PLATFORM,
                        "Conversational AI interface")
    
    # Note: Other competitors would be populated via web scraping or manual updates


__all__ = [
    "CompetitiveIntelligence",
    "CompetitorFeatureCategory",
    "get_competitive_intelligence",
    "initialize_baseline_data",
]
