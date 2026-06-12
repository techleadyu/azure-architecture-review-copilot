import json
import os
from typing import List
from models.risk import Risk, RiskSeverity, RiskCategory, EffortLevel, ReviewResult
from tools.foundry_iq_client import FoundryIQClient
from config.settings import Settings


class SecurityAgent:
    """Specialist agent: detects security vulnerabilities and misconfigurations."""

    CATEGORY = RiskCategory.SECURITY

    def __init__(self, foundry_client: FoundryIQClient = None):
        self.foundry = foundry_client or FoundryIQClient()

    def run(self, context: dict) -> ReviewResult:
        if Settings.DEMO_MODE:
            return self._demo_result(context)
        return self._live_result(context)

    def _live_result(self, context: dict) -> ReviewResult:
        prompt = f"""
        You are an Azure Security specialist agent. Analyze the following Azure environment context
        and identify the top security risks. For each risk, provide:
        - title, description, severity (Critical/High/Medium/Low)
        - effort (S/M/L), impact, remediation steps
        - Microsoft reference URL from Azure Architecture Center or WAF security pillar

        Context:
        {json.dumps(context, indent=2)}

        Return a JSON array of risks.
        """
        response = self.foundry.query(prompt, domain="security")
        risks = self._parse_risks(response)
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary=f"Scanned {context.get('resource_count', 0)} resources. Found {len(risks)} security risks.",
            resources_scanned=context.get("resource_count", 0),
            risk_score=self._calculate_score(risks),
        )

    def _demo_result(self, context: dict) -> ReviewResult:
        risks = [
            Risk(
                id="SEC-001",
                title="Overly Permissive Storage Account Access",
                description="Storage account allows public read access to blobs without authentication.",
                severity=RiskSeverity.CRITICAL,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="High",
                remediation="Disable public blob access: set allowBlobPublicAccess=false on all storage accounts.",
                reference_url="https://learn.microsoft.com/azure/storage/blobs/anonymous-read-access-prevent",
                resource="storageaccount-prod-001",
            ),
            Risk(
                id="SEC-002",
                title="Public IP on Sensitive VM",
                description="Critical VM is directly exposed to the internet with no NSG rule restriction.",
                severity=RiskSeverity.HIGH,
                category=self.CATEGORY,
                effort=EffortLevel.MEDIUM,
                impact="High",
                remediation="Remove public IP, route traffic through Azure Firewall or Application Gateway.",
                reference_url="https://learn.microsoft.com/azure/security/fundamentals/network-best-practices",
                resource="vm-prod-db-001",
            ),
            Risk(
                id="SEC-003",
                title="Unencrypted Data in Storage",
                description="Storage account not using customer-managed keys (CMK) for sensitive data.",
                severity=RiskSeverity.MEDIUM,
                category=self.CATEGORY,
                effort=EffortLevel.MEDIUM,
                impact="Medium",
                remediation="Enable CMK encryption via Azure Key Vault for storage accounts with sensitive data.",
                reference_url="https://learn.microsoft.com/azure/storage/common/customer-managed-keys-overview",
                resource="storageaccount-archive-002",
            ),
        ]
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary="Scanned 122 resources. Identified 8 risks (demo: showing top 3).",
            resources_scanned=122,
            risk_score=72,
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
