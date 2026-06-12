import json
from typing import List
from models.risk import Risk, RiskSeverity, RiskCategory, EffortLevel, ReviewResult
from tools.foundry_iq_client import FoundryIQClient
from config.settings import Settings


class ReliabilityAgent:
    """Specialist agent: evaluates resiliency, DR, HA, and service continuity."""

    CATEGORY = RiskCategory.RELIABILITY

    def __init__(self, foundry_client: FoundryIQClient = None):
        self.foundry = foundry_client or FoundryIQClient()

    def run(self, context: dict) -> ReviewResult:
        if Settings.DEMO_MODE:
            return self._demo_result(context)
        return self._live_result(context)

    def _live_result(self, context: dict) -> ReviewResult:
        prompt = f"""
        You are an Azure Reliability and Resiliency specialist agent.
        Analyze the Azure environment for single points of failure, missing backup policies,
        no availability zones, missing DR plans, and SLA risks.

        Context:
        {json.dumps(context, indent=2)}

        Return a JSON array of reliability risks with severity, effort, remediation, and WAF Reliability pillar reference URLs.
        """
        response = self.foundry.query(prompt, domain="reliability")
        risks = self._parse_risks(response)
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary=f"Analyzed {context.get('resource_count', 0)} services. Found {len(risks)} reliability risks.",
            resources_scanned=context.get("resource_count", 0),
            risk_score=self._calculate_score(risks),
        )

    def _demo_result(self, context: dict) -> ReviewResult:
        risks = [
            Risk(
                id="REL-001",
                title="No Backup Policy on Critical VMs",
                description="8 production VMs have no Azure Backup policy configured.",
                severity=RiskSeverity.HIGH,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="High",
                remediation="Enable Azure Backup with GRS vault. Set daily backup with 30-day retention.",
                reference_url="https://learn.microsoft.com/azure/backup/backup-azure-vms-introduction",
                resource="vm-prod-*",
            ),
            Risk(
                id="REL-002",
                title="Single Region Deployment — No DR Plan",
                description="All production services deployed in a single region with no failover configuration.",
                severity=RiskSeverity.HIGH,
                category=self.CATEGORY,
                effort=EffortLevel.LARGE,
                impact="High",
                remediation="Implement Azure Site Recovery or active-passive geo-redundant deployment.",
                reference_url="https://learn.microsoft.com/azure/reliability/availability-zones-overview",
                resource="rg-prod-eastus",
            ),
            Risk(
                id="REL-003",
                title="No Health Alerts or SLA Monitoring",
                description="Critical services have no Azure Monitor alerts for availability or latency thresholds.",
                severity=RiskSeverity.MEDIUM,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="Medium",
                remediation="Configure Azure Monitor alert rules and Action Groups for all critical services.",
                reference_url="https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-overview",
                resource="monitor-workspace-prod",
            ),
        ]
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary="Analyzed 35 services. Identified 4 risks (demo: showing top 3).",
            resources_scanned=35,
            risk_score=68,
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
