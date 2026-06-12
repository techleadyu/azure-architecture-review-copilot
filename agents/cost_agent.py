import json
from typing import List
from models.risk import Risk, RiskSeverity, RiskCategory, EffortLevel, ReviewResult
from tools.foundry_iq_client import FoundryIQClient
from config.settings import Settings


class CostAgent:
    """Specialist agent: identifies cost inefficiencies and FinOps opportunities."""

    CATEGORY = RiskCategory.COST

    def __init__(self, foundry_client: FoundryIQClient = None):
        self.foundry = foundry_client or FoundryIQClient()

    def run(self, context: dict) -> ReviewResult:
        if Settings.DEMO_MODE:
            return self._demo_result(context)
        return self._live_result(context)

    def _live_result(self, context: dict) -> ReviewResult:
        prompt = f"""
        You are an Azure FinOps specialist agent. Analyze the following Azure environment context
        and identify cost inefficiencies and optimization opportunities.
        For each finding provide: title, description, severity, effort, estimated_savings (USD/month),
        remediation steps, and Microsoft FinOps/Cost Management reference URL.

        Context:
        {json.dumps(context, indent=2)}

        Return a JSON array of risks.
        """
        response = self.foundry.query(prompt, domain="cost")
        risks = self._parse_risks(response)
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary=f"Analyzed spend and {context.get('resource_count', 0)} resources. Found {len(risks)} cost opportunities.",
            resources_scanned=context.get("resource_count", 0),
            risk_score=self._calculate_score(risks),
        )

    def _demo_result(self, context: dict) -> ReviewResult:
        risks = [
            Risk(
                id="COST-001",
                title="Underutilized Virtual Machines",
                description="6 VMs running at <5% CPU and <10% memory for the past 30 days.",
                severity=RiskSeverity.MEDIUM,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="Medium",
                remediation="Rightsize or deallocate idle VMs. Consider Reserved Instances for stable workloads.",
                reference_url="https://learn.microsoft.com/azure/cost-management-billing/costs/cost-optimization-recommendations",
                resource="vm-dev-pool-*",
                estimated_savings=1840.0,
            ),
            Risk(
                id="COST-002",
                title="No Reserved Instances for Production VMs",
                description="All production VMs running on Pay-As-You-Go. Committed workloads missing reservation savings.",
                severity=RiskSeverity.HIGH,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="High",
                remediation="Purchase 1-year Reserved Instances for stable prod VMs — up to 40% savings.",
                reference_url="https://learn.microsoft.com/azure/cost-management-billing/reservations/save-compute-costs-reservations",
                resource="vm-prod-*",
                estimated_savings=12690.0,
            ),
            Risk(
                id="COST-003",
                title="Orphaned Managed Disks",
                description="14 managed disks unattached to any VM, incurring storage costs.",
                severity=RiskSeverity.LOW,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="Low",
                remediation="Review and delete confirmed orphaned disks. Snapshot before deletion.",
                reference_url="https://learn.microsoft.com/azure/virtual-machines/disks-find-unattached-portal",
                resource="disk-orphan-*",
                estimated_savings=320.0,
            ),
        ]
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary="Analyzed spend & resources. Identified 6 opportunities (demo: showing top 3). Est. savings: $14,850/mo.",
            resources_scanned=98,
            risk_score=64,
        )

    def _parse_risks(self, response: str) -> List[Risk]:
        try:
            data = json.loads(response)
            return [Risk(**r) for r in data]
        except Exception:
            return []

    def _calculate_score(self, risks: List[Risk]) -> int:
        weights = {RiskSeverity.CRITICAL: 25, RiskSeverity.HIGH: 15, RiskSeverity.MEDIUM: 8, RiskSeverity.LOW: 3}
        penalty = sum(weights.get(r.severity, 0) for r in risks)
        return max(0, 100 - penalty)
