import json
from typing import List
from models.risk import Risk, RiskSeverity, RiskCategory, EffortLevel, ReviewResult
from tools.foundry_iq_client import FoundryIQClient
from config.settings import Settings


class IdentityAgent:
    """Specialist agent: reviews RBAC, Entra ID posture, and privilege exposure."""

    CATEGORY = RiskCategory.IDENTITY

    def __init__(self, foundry_client: FoundryIQClient = None):
        self.foundry = foundry_client or FoundryIQClient()

    def run(self, context: dict) -> ReviewResult:
        if Settings.DEMO_MODE:
            return self._demo_result(context)
        return self._live_result(context)

    def _live_result(self, context: dict) -> ReviewResult:
        prompt = f"""
        You are an Azure Identity & Access Management specialist agent.
        Analyze the Azure environment context for RBAC over-privilege, service principal risks,
        missing MFA, and Entra ID misconfigurations.

        Context:
        {json.dumps(context, indent=2)}

        Return a JSON array of identity/access risks with severity, effort, remediation, and reference URLs.
        """
        response = self.foundry.query(prompt, domain="identity")
        risks = self._parse_risks(response)
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary=f"Reviewed {context.get('identity_count', 0)} identities. Found {len(risks)} access risks.",
            resources_scanned=context.get("identity_count", 0),
            risk_score=self._calculate_score(risks),
        )

    def _demo_result(self, context: dict) -> ReviewResult:
        risks = [
            Risk(
                id="IDN-001",
                title="Owner Role Assigned Directly to Users",
                description="5 users have Owner role at subscription scope — violates least-privilege principle.",
                severity=RiskSeverity.CRITICAL,
                category=self.CATEGORY,
                effort=EffortLevel.MEDIUM,
                impact="High",
                remediation="Replace Owner with scoped Contributor/Reader roles. Use PIM for privileged access.",
                reference_url="https://learn.microsoft.com/azure/role-based-access-control/best-practices",
                resource="subscription-scope",
            ),
            Risk(
                id="IDN-002",
                title="Service Principals with Expired Credentials",
                description="3 app registrations have client secrets expired >30 days — potential auth failures.",
                severity=RiskSeverity.HIGH,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="High",
                remediation="Rotate credentials and implement automated secret rotation via Key Vault.",
                reference_url="https://learn.microsoft.com/azure/active-directory/develop/howto-create-service-principal-portal",
                resource="app-registration-*",
            ),
            Risk(
                id="IDN-003",
                title="MFA Not Enforced for All Users",
                description="12 user accounts without MFA enrollment. Conditional Access policy not applied.",
                severity=RiskSeverity.HIGH,
                category=self.CATEGORY,
                effort=EffortLevel.SMALL,
                impact="High",
                remediation="Enable Conditional Access policy requiring MFA for all users accessing Azure portal.",
                reference_url="https://learn.microsoft.com/azure/active-directory/conditional-access/howto-conditional-access-policy-all-users-mfa",
                resource="entra-id-tenant",
            ),
        ]
        return ReviewResult(
            category=self.CATEGORY,
            risks=risks,
            summary="Reviewed 89 identities. Identified 7 risks (demo: showing top 3).",
            resources_scanned=89,
            risk_score=70,
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
