import concurrent.futures
from typing import List, Dict, Optional
from models.risk import Risk, RiskSeverity, RiskCategory, ReviewResult
from agents.security_agent import SecurityAgent
from agents.cost_agent import CostAgent
from agents.identity_agent import IdentityAgent
from agents.reliability_agent import ReliabilityAgent
from tools.foundry_iq_client import FoundryIQClient
from tools.report_generator import ReportGenerator
from config.waf_pillars import WAF_PILLARS
import json
import os


BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "blueprints")


class ArchitectureReviewOrchestrator:
    """
    Orchestrates 4 specialist agents (Security, Cost, Identity, Reliability)
    to perform enterprise-grade Azure architecture reviews.
    """

    def __init__(self):
        self.foundry = FoundryIQClient()
        self.agents = {
            RiskCategory.SECURITY: SecurityAgent(self.foundry),
            RiskCategory.COST: CostAgent(self.foundry),
            RiskCategory.IDENTITY: IdentityAgent(self.foundry),
            RiskCategory.RELIABILITY: ReliabilityAgent(self.foundry),
        }
        self.report_generator = ReportGenerator()

    def run_review(
        self,
        context: dict,
        waf_pillar: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> dict:
        """
        Full review pipeline:
        1. Run all 4 specialist agents in parallel
        2. Aggregate and rank top 5 risks
        3. Apply WAF pillar re-ranking if specified
        4. Map to tier blueprint
        5. Return full result
        """
        # Step 1 — Run agents in parallel
        results: Dict[RiskCategory, ReviewResult] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(agent.run, context): category
                for category, agent in self.agents.items()
            }
            for future in concurrent.futures.as_completed(futures):
                category = futures[future]
                try:
                    results[category] = future.result()
                except Exception as e:
                    print(f"[WARNING] Agent {category} failed: {e}")

        # Step 2 — Aggregate all risks
        all_risks: List[Risk] = []
        for result in results.values():
            all_risks.extend(result.risks)

        # Step 3 — Rank top 5 risks
        top5 = self._rank_risks(all_risks, waf_pillar)[:5]

        # Step 4 — Calculate overall risk score
        overall_score = self._overall_score(results)

        # Step 5 — Load tier blueprint
        blueprint = self._load_blueprint(tier or self._auto_detect_tier(context))

        # Step 6 — Build response
        return {
            "subscription": context.get("subscription_name", "Unknown"),
            "landing_zone": context.get("landing_zone", "Unknown"),
            "overall_risk_score": overall_score,
            "agent_results": {
                cat.value: {
                    "summary": r.summary,
                    "resources_scanned": r.resources_scanned,
                    "risk_count": r.risk_count,
                    "critical_count": r.critical_count,
                    "risk_score": r.risk_score,
                }
                for cat, r in results.items()
            },
            "top5_risks": [self._risk_to_dict(r) for r in top5],
            "all_risks_count": len(all_risks),
            "waf_pillar_focus": waf_pillar,
            "blueprint": blueprint,
            "total_estimated_savings": sum(r.estimated_savings for r in all_risks),
        }

    def _rank_risks(self, risks: List[Risk], waf_pillar: Optional[str] = None) -> List[Risk]:
        severity_order = {
            RiskSeverity.CRITICAL: 4,
            RiskSeverity.HIGH: 3,
            RiskSeverity.MEDIUM: 2,
            RiskSeverity.LOW: 1,
        }
        boosted_categories = []
        if waf_pillar and waf_pillar in WAF_PILLARS:
            boosted_categories = WAF_PILLARS[waf_pillar].get("weight_boost", [])

        def rank_key(r: Risk):
            boost = 1 if r.category.value.upper() in boosted_categories else 0
            return (boost, severity_order.get(r.severity, 0))

        return sorted(risks, key=rank_key, reverse=True)

    def _overall_score(self, results: Dict[RiskCategory, ReviewResult]) -> int:
        if not results:
            return 100
        return round(sum(r.risk_score for r in results.values()) / len(results))

    def _auto_detect_tier(self, context: dict) -> str:
        resource_count = context.get("resource_count", 0)
        if resource_count < 30:
            return "smb"
        elif resource_count < 150:
            return "midmarket"
        return "enterprise"

    def _load_blueprint(self, tier: str) -> dict:
        path = os.path.join(BLUEPRINTS_DIR, f"{tier}.json")
        try:
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"tier": tier, "error": "Blueprint not found"}

    def _risk_to_dict(self, r: Risk) -> dict:
        return {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "severity": r.severity.value,
            "category": r.category.value,
            "effort": r.effort.value,
            "impact": r.impact,
            "remediation": r.remediation,
            "reference_url": r.reference_url,
            "resource": r.resource,
            "estimated_savings": r.estimated_savings,
        }
