#!/usr/bin/env python3
"""
Azure Architecture Review Copilot — CLI Entry Point
Usage:
  python main.py                         # Run demo review
  python main.py --pillar security       # WAF Security pillar focus
  python main.py --tier enterprise       # Force enterprise tier
  python main.py --export report.json    # Export ADR to JSON
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import ArchitectureReviewOrchestrator
from tools.azure_client import AzureClient
from tools.report_generator import ReportGenerator
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold blue]Azure Architecture Review Copilot[/bold blue]\n"
        "[dim]Multi-Agent AI powered by Foundry IQ + Azure OpenAI[/dim]",
        border_style="blue"
    ))


def print_results(result: dict):
    score = result["overall_risk_score"]
    color = "red" if score < 60 else "yellow" if score < 80 else "green"

    console.print(f"\n[bold]Overall Risk Score:[/bold] [{color}]{score}/100[/{color}]")
    console.print(f"[bold]Subscription:[/bold] {result['subscription']}")
    console.print(f"[bold]Landing Zone:[/bold] {result['landing_zone']}")
    console.print(f"[bold]Estimated Monthly Savings:[/bold] [green]${result['total_estimated_savings']:,.0f}[/green]\n")

    # Agent results table
    table = Table(title="AI Agent Analysis", show_header=True)
    table.add_column("Agent", style="bold")
    table.add_column("Resources Scanned", justify="center")
    table.add_column("Risks Found", justify="center")
    table.add_column("Risk Score", justify="center")

    for category, data in result["agent_results"].items():
        score_val = data["risk_score"]
        score_color = "red" if score_val < 60 else "yellow" if score_val < 80 else "green"
        table.add_row(
            f"{category} Agent",
            str(data["resources_scanned"]),
            str(data["risk_count"]),
            f"[{score_color}]{score_val}%[/{score_color}]",
        )
    console.print(table)

    # Top 5 risks
    console.print("\n[bold]Top 5 Risks:[/bold]")
    severity_colors = {"Critical": "red", "High": "orange3", "Medium": "yellow", "Low": "green"}
    for i, risk in enumerate(result["top5_risks"], 1):
        color = severity_colors.get(risk["severity"], "white")
        console.print(f"  {i}. [{color}][{risk['severity']}][/{color}] {risk['title']}")
        console.print(f"     → {risk['remediation']}")

    # Blueprint
    bp = result.get("blueprint", {})
    if bp:
        console.print(f"\n[bold]Recommended Blueprint:[/bold] {bp.get('name', 'N/A')}")
        console.print(f"  {bp.get('description', '')}")


def main():
    parser = argparse.ArgumentParser(description="Azure Architecture Review Copilot")
    parser.add_argument("--pillar", choices=["reliability", "security", "cost", "operational_excellence", "performance"],
                        help="WAF pillar to focus on")
    parser.add_argument("--tier", choices=["smb", "midmarket", "enterprise"],
                        help="Architecture tier (auto-detected if not set)")
    parser.add_argument("--export", metavar="FILE", help="Export ADR report to JSON file")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown ADR to console")
    args = parser.parse_args()

    print_banner()
    console.print("[dim]Connecting to Azure environment...[/dim]")

    azure_client = AzureClient()
    context = azure_client.get_environment_context()

    console.print(f"[dim]Running 4 specialist agents in parallel...[/dim]\n")

    orchestrator = ArchitectureReviewOrchestrator()
    result = orchestrator.run_review(context, waf_pillar=args.pillar, tier=args.tier)

    print_results(result)

    report_gen = ReportGenerator()

    if args.export:
        report_gen.generate_json(result, args.export)
        console.print(f"\n[green]✅ ADR exported to:[/green] {args.export}")

    if args.markdown:
        md = report_gen.generate_markdown(result)
        console.print("\n" + md)


if __name__ == "__main__":
    main()
