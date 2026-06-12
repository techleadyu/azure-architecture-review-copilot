import json
import os
from datetime import datetime
from typing import List
from models.risk import Risk


class ReportGenerator:
    """Generates Architecture Decision Reports (ADR) from review results."""

    def generate_json(self, review_result: dict, output_path: str = None) -> str:
        """Export full review result as a JSON ADR."""
        report = {
            "report_type": "Azure Architecture Decision Report (ADR)",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generated_by": "Azure Architecture Review Copilot",
            "powered_by": ["Azure AI Foundry (Foundry IQ)", "Azure OpenAI GPT-4o", "Microsoft CAF", "WAF"],
            **review_result,
        }
        content = json.dumps(report, indent=2)
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(content)
        return content

    def generate_markdown(self, review_result: dict) -> str:
        """Generate a readable Markdown ADR report."""
        score = review_result.get("overall_risk_score", 0)
        risks = review_result.get("top5_risks", [])
        blueprint = review_result.get("blueprint", {})
        savings = review_result.get("total_estimated_savings", 0)

        lines = [
            "# Azure Architecture Decision Report (ADR)",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Subscription:** {review_result.get('subscription', 'N/A')}",
            f"**Landing Zone:** {review_result.get('landing_zone', 'N/A')}",
            f"**Overall Risk Score:** {score}/100",
            f"**Estimated Monthly Savings:** ${savings:,.0f}",
            "",
            "---",
            "## Top 5 Risks",
            "",
        ]
        for i, r in enumerate(risks, 1):
            lines += [
                f"### {i}. [{r['severity']}] {r['title']}",
                f"- **Category:** {r['category']}",
                f"- **Resource:** `{r.get('resource', 'N/A')}`",
                f"- **Description:** {r['description']}",
                f"- **Remediation:** {r['remediation']}",
                f"- **Effort:** {r['effort']} | **Impact:** {r['impact']}",
                f"- **Reference:** [{r['reference_url']}]({r['reference_url']})",
                "",
            ]

        if blueprint:
            lines += [
                "---",
                f"## Recommended Blueprint: {blueprint.get('tier', 'N/A').upper()}",
                blueprint.get("description", ""),
                "",
                "**Key Principles:**",
            ]
            for p in blueprint.get("principles", []):
                lines.append(f"- {p}")

        lines += [
            "",
            "---",
            "*Powered by Azure Architecture Review Copilot | Foundry IQ + Azure OpenAI*",
        ]
        return "\n".join(lines)
