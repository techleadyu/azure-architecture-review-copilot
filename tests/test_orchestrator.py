import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import ArchitectureReviewOrchestrator
from tools.azure_client import AzureClient


def test_demo_review_runs():
    client = AzureClient()
    context = client.get_environment_context()
    orchestrator = ArchitectureReviewOrchestrator()
    result = orchestrator.run_review(context)

    assert result is not None
    assert "overall_risk_score" in result
    assert len(result["top5_risks"]) <= 5
    assert "blueprint" in result
    print("✅ Demo review passed")


def test_waf_pillar_rerank():
    client = AzureClient()
    context = client.get_environment_context()
    orchestrator = ArchitectureReviewOrchestrator()
    result = orchestrator.run_review(context, waf_pillar="security")

    assert result is not None
    # Security/Identity risks should appear first
    if result["top5_risks"]:
        first = result["top5_risks"][0]
        assert first["category"] in ["Security", "Identity"]
    print("✅ WAF pillar rerank passed")


def test_tier_blueprint():
    client = AzureClient()
    context = client.get_environment_context()
    orchestrator = ArchitectureReviewOrchestrator()
    for tier in ["smb", "midmarket", "enterprise"]:
        result = orchestrator.run_review(context, tier=tier)
        assert result["blueprint"]["tier"] == tier
    print("✅ Tier blueprint selection passed")


if __name__ == "__main__":
    test_demo_review_runs()
    test_waf_pillar_rerank()
    test_tier_blueprint()
    print("\n✅ All tests passed!")
