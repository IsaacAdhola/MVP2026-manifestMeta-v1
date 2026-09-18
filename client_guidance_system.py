"""
Client Guidance & Campaign Recommendation System
Helps clients who don't know what type of ads to run.
Provides intelligent recommendations based on their goals, industry, and budget.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from agent_tracking_system import CampaignType


class ClientGoal(Enum):
    """High-level client goals"""
    GROW_BRAND = "grow_brand_awareness"
    GET_CUSTOMERS = "get_new_customers"
    INCREASE_SALES = "increase_sales"
    BUILD_COMMUNITY = "build_community"
    LAUNCH_PRODUCT = "launch_new_product"
    DRIVE_TRAFFIC = "drive_website_traffic"
    GET_LEADS = "generate_leads"
    RETARGET = "retarget_existing_audience"


class Industry(Enum):
    """Industry verticals for tailored recommendations"""
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    LOCAL_BUSINESS = "local_business"
    RESTAURANT = "restaurant"
    PROFESSIONAL_SERVICES = "professional_services"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    NONPROFIT = "nonprofit"
    ENTERTAINMENT = "entertainment"


class BusinessStage(Enum):
    """Business maturity stage"""
    STARTUP = "startup"  # < 1 year, building audience
    GROWING = "growing"  # 1-3 years, proven product
    ESTABLISHED = "established"  # 3+ years, optimizing
    ENTERPRISE = "enterprise"  # Large scale, multi-product


_GUIDANCE_DIR = Path(__file__).resolve().parent / ".client_guidance"
_GUIDANCE_DIR.mkdir(exist_ok=True)


class CampaignRecommendation:
    """Represents a recommended campaign strategy"""
    
    def __init__(
        self,
        campaign_type: CampaignType,
        priority: int,  # 1 = highest
        reasoning: str,
        budget_recommendation: tuple[float, float],  # (min, max)
        expected_outcomes: list[str],
        timeline: str,
        best_practices: list[str],
    ):
        self.campaign_type = campaign_type
        self.priority = priority
        self.reasoning = reasoning
        self.budget_recommendation = budget_recommendation
        self.expected_outcomes = expected_outcomes
        self.timeline = timeline
        self.best_practices = best_practices
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_type": self.campaign_type.value,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "budget_recommendation": {
                "min": self.budget_recommendation[0],
                "max": self.budget_recommendation[1],
            },
            "expected_outcomes": self.expected_outcomes,
            "timeline": self.timeline,
            "best_practices": self.best_practices,
        }


class ClientGuidanceSystem:
    """
    Intelligent recommendation engine for clients who don't know what campaigns to run.
    Analyzes goals, industry, budget, and stage to provide tailored campaign strategies.
    """
    
    # Campaign recommendation rules based on goals and context
    RECOMMENDATION_RULES = {
        # Goal: Grow Brand Awareness
        ClientGoal.GROW_BRAND: {
            "startup": [
                (CampaignType.AWARENESS, "Build initial brand recognition"),
                (CampaignType.ENGAGEMENT, "Create social proof and community"),
            ],
            "growing": [
                (CampaignType.AWARENESS, "Expand reach to new audiences"),
                (CampaignType.TRAFFIC, "Drive traffic to showcase offerings"),
            ],
            "established": [
                (CampaignType.AWARENESS, "Maintain top-of-mind presence"),
                (CampaignType.RETARGETING, "Re-engage existing audience"),
            ],
        },
        
        # Goal: Get New Customers
        ClientGoal.GET_CUSTOMERS: {
            "startup": [
                (CampaignType.TRAFFIC, "Drive qualified traffic to landing page"),
                (CampaignType.LEADS, "Build email list for nurturing"),
            ],
            "growing": [
                (CampaignType.CONVERSIONS, "Direct conversion campaigns"),
                (CampaignType.RETARGETING, "Convert warm leads"),
            ],
            "established": [
                (CampaignType.CONVERSIONS, "Optimize conversion funnels"),
                (CampaignType.RETARGETING, "Advanced retargeting strategies"),
            ],
        },
        
        # Goal: Launch New Product
        ClientGoal.LAUNCH_PRODUCT: {
            "startup": [
                (CampaignType.PRODUCT_LAUNCH, "Create launch buzz"),
                (CampaignType.AWARENESS, "Introduce product to market"),
            ],
            "growing": [
                (CampaignType.PRODUCT_LAUNCH, "Leverage existing audience"),
                (CampaignType.RETARGETING, "Target existing customers"),
            ],
            "established": [
                (CampaignType.PRODUCT_LAUNCH, "Multi-channel launch strategy"),
                (CampaignType.AWARENESS, "Expand to new segments"),
            ],
        },
    }
    
    def __init__(self):
        self._history_file = _GUIDANCE_DIR / "guidance_history.json"
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._load_history()
    
    def _load_history(self) -> None:
        """Load guidance history"""
        if self._history_file.exists():
            try:
                self._history = json.loads(self._history_file.read_text(encoding="utf-8"))
            except Exception:
                self._history = {}
    
    def _save_history(self) -> None:
        """Save guidance history"""
        self._history_file.write_text(
            json.dumps(self._history, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )
    
    def get_recommendations(
        self,
        client_id: str,
        goal: ClientGoal,
        industry: Industry,
        business_stage: BusinessStage,
        monthly_budget: float,
        current_audience_size: int = 0,
        has_existing_customers: bool = False,
    ) -> list[CampaignRecommendation]:
        """
        Generate personalized campaign recommendations.
        """
        recommendations = []
        
        # Get base recommendations from rules
        stage_key = business_stage.value if business_stage.value != "enterprise" else "established"
        base_recs = self.RECOMMENDATION_RULES.get(goal, {}).get(stage_key, [])
        
        for priority, (campaign_type, reasoning) in enumerate(base_recs, start=1):
            # Budget allocation based on priority
            if priority == 1:
                budget = (monthly_budget * 0.6, monthly_budget * 0.7)
            else:
                budget = (monthly_budget * 0.3, monthly_budget * 0.4)
            
            # Industry-specific adjustments
            reasoning = self._add_industry_context(reasoning, industry)
            
            # Generate expected outcomes
            outcomes = self._generate_outcomes(
                campaign_type,
                business_stage,
                monthly_budget,
                current_audience_size
            )
            
            # Timeline estimation
            timeline = self._estimate_timeline(campaign_type, business_stage)
            
            # Best practices
            best_practices = self._get_best_practices(campaign_type, industry)
            
            recommendations.append(CampaignRecommendation(
                campaign_type=campaign_type,
                priority=priority,
                reasoning=reasoning,
                budget_recommendation=budget,
                expected_outcomes=outcomes,
                timeline=timeline,
                best_practices=best_practices,
            ))
        
        # Add retargeting if they have existing customers
        if has_existing_customers and not any(r.campaign_type == CampaignType.RETARGETING for r in recommendations):
            recommendations.append(CampaignRecommendation(
                campaign_type=CampaignType.RETARGETING,
                priority=len(recommendations) + 1,
                reasoning="You have existing customers - retargeting can drive repeat business",
                budget_recommendation=(monthly_budget * 0.2, monthly_budget * 0.3),
                expected_outcomes=[
                    "Higher ROI than cold traffic",
                    "Increased customer lifetime value",
                    "Better conversion rates (3-5x vs cold ads)",
                ],
                timeline="2-4 weeks for initial results",
                best_practices=self._get_best_practices(CampaignType.RETARGETING, industry),
            ))
        
        # Save to history
        if client_id not in self._history:
            self._history[client_id] = []
        
        self._history[client_id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": goal.value,
            "industry": industry.value,
            "business_stage": business_stage.value,
            "budget": monthly_budget,
            "recommendations": [r.to_dict() for r in recommendations],
        })
        
        self._save_history()
        
        return recommendations
    
    def _add_industry_context(self, base_reasoning: str, industry: Industry) -> str:
        """Add industry-specific context to reasoning"""
        industry_notes = {
            Industry.ECOMMERCE: "E-commerce businesses see best results with visual ads and retargeting",
            Industry.SAAS: "SaaS companies should focus on educating audience before conversion",
            Industry.LOCAL_BUSINESS: "Local targeting and community engagement are key",
            Industry.RESTAURANT: "Food photography and limited-time offers drive engagement",
            Industry.PROFESSIONAL_SERVICES: "Trust-building and testimonials are critical",
        }
        
        note = industry_notes.get(industry, "")
        if note:
            return f"{base_reasoning}. {note}"
        return base_reasoning
    
    def _generate_outcomes(
        self,
        campaign_type: CampaignType,
        business_stage: BusinessStage,
        budget: float,
        audience_size: int
    ) -> list[str]:
        """Generate expected outcomes based on campaign type and context"""
        outcomes_map = {
            CampaignType.AWARENESS: [
                f"Reach: {int(budget * 100)}-{int(budget * 200)} impressions",
                "Brand recall increase: 15-30%",
                "Social media followers: +10-20%",
            ],
            CampaignType.TRAFFIC: [
                f"Website visitors: {int(budget * 5)}-{int(budget * 10)} per month",
                "Bounce rate: 40-60% (target < 50%)",
                "Time on site: 2-4 minutes",
            ],
            CampaignType.CONVERSIONS: [
                f"Estimated conversions: {int(budget * 0.1)}-{int(budget * 0.3)}",
                "Cost per conversion: $50-$150",
                "ROI: 2-4x (after optimization)",
            ],
            CampaignType.LEADS: [
                f"Leads generated: {int(budget * 0.5)}-{int(budget * 1.0)}",
                "Cost per lead: $10-$50",
                "Lead quality score: 6-8/10",
            ],
            CampaignType.RETARGETING: [
                "Conversion rate: 3-5x higher than cold traffic",
                "Cost per acquisition: 40-60% lower",
                "Customer return rate: +15-25%",
            ],
        }
        
        return outcomes_map.get(campaign_type, ["Results vary by execution"])
    
    def _estimate_timeline(self, campaign_type: CampaignType, business_stage: BusinessStage) -> str:
        """Estimate timeline for results"""
        timelines = {
            CampaignType.AWARENESS: "2-3 weeks for initial metrics, 2-3 months for brand lift",
            CampaignType.TRAFFIC: "1-2 weeks for initial traffic, optimize over 4-6 weeks",
            CampaignType.CONVERSIONS: "3-4 weeks for data, 2-3 months for optimization",
            CampaignType.LEADS: "1-2 weeks for initial leads, qualify over 4 weeks",
            CampaignType.RETARGETING: "1-2 weeks for initial conversions, scale over 4 weeks",
            CampaignType.PRODUCT_LAUNCH: "2-4 weeks for launch buzz, monitor for 8 weeks",
        }
        
        return timelines.get(campaign_type, "4-8 weeks typical")
    
    def _get_best_practices(self, campaign_type: CampaignType, industry: Industry) -> list[str]:
        """Get campaign-specific best practices"""
        practices_map = {
            CampaignType.AWARENESS: [
                "Use eye-catching visuals and bold messaging",
                "Target broad audiences with interests aligned to your product",
                "Test multiple ad formats (video, carousel, image)",
                "Focus on frequency: 3-5 exposures per person",
            ],
            CampaignType.TRAFFIC: [
                "Optimize landing pages before running ads",
                "Use clear CTAs (e.g., 'Learn More', 'Shop Now')",
                "A/B test headlines and descriptions",
                "Track bounce rate and time on site",
            ],
            CampaignType.CONVERSIONS: [
                "Install Facebook Pixel for conversion tracking",
                "Use dynamic product ads if e-commerce",
                "Create urgency with limited-time offers",
                "Optimize for specific conversion events",
            ],
            CampaignType.LEADS: [
                "Use lead forms to reduce friction",
                "Offer valuable incentive (guide, discount, consultation)",
                "Follow up within 24 hours",
                "Segment leads by quality for nurturing",
            ],
            CampaignType.RETARGETING: [
                "Segment audiences by behavior (viewed, added to cart, purchased)",
                "Show different ads based on where they dropped off",
                "Exclude recent converters to avoid ad fatigue",
                "Use dynamic ads to show products they viewed",
            ],
        }
        
        return practices_map.get(campaign_type, [])
    
    def generate_onboarding_questionnaire(self) -> dict[str, Any]:
        """Generate questionnaire for new clients to determine campaign strategy"""
        return {
            "questions": [
                {
                    "id": "goal",
                    "question": "What's your primary goal for this campaign?",
                    "type": "single_choice",
                    "options": [
                        {"value": ClientGoal.GROW_BRAND.value, "label": "Grow brand awareness"},
                        {"value": ClientGoal.GET_CUSTOMERS.value, "label": "Get new customers"},
                        {"value": ClientGoal.INCREASE_SALES.value, "label": "Increase sales from existing customers"},
                        {"value": ClientGoal.BUILD_COMMUNITY.value, "label": "Build social community"},
                        {"value": ClientGoal.LAUNCH_PRODUCT.value, "label": "Launch a new product"},
                        {"value": ClientGoal.DRIVE_TRAFFIC.value, "label": "Drive website traffic"},
                        {"value": ClientGoal.GET_LEADS.value, "label": "Generate leads"},
                    ],
                },
                {
                    "id": "industry",
                    "question": "What industry are you in?",
                    "type": "single_choice",
                    "options": [
                        {"value": i.value, "label": i.value.replace("_", " ").title()}
                        for i in Industry
                    ],
                },
                {
                    "id": "business_stage",
                    "question": "How long has your business been operating?",
                    "type": "single_choice",
                    "options": [
                        {"value": BusinessStage.STARTUP.value, "label": "Less than 1 year"},
                        {"value": BusinessStage.GROWING.value, "label": "1-3 years"},
                        {"value": BusinessStage.ESTABLISHED.value, "label": "3+ years"},
                        {"value": BusinessStage.ENTERPRISE.value, "label": "Large enterprise"},
                    ],
                },
                {
                    "id": "monthly_budget",
                    "question": "What's your monthly marketing budget?",
                    "type": "number",
                    "placeholder": "e.g., 1000",
                },
                {
                    "id": "current_audience_size",
                    "question": "How many followers/customers do you currently have?",
                    "type": "number",
                    "placeholder": "e.g., 5000",
                },
                {
                    "id": "has_existing_customers",
                    "question": "Do you have existing customers to retarget?",
                    "type": "boolean",
                },
            ],
        }


# Global guidance system
_guidance = ClientGuidanceSystem()


def get_guidance_system() -> ClientGuidanceSystem:
    """Get global guidance system instance"""
    return _guidance


__all__ = [
    "ClientGuidanceSystem",
    "ClientGoal",
    "Industry",
    "BusinessStage",
    "CampaignRecommendation",
    "get_guidance_system",
]
