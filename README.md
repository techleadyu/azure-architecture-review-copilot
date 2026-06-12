# Azure Architecture Review Copilot

> **Agents League Hackathon 2026 — Reasoning Agents Track**
> Powered by **Foundry IQ** + **Azure OpenAI GPT-4o** + **Microsoft CAF & WAF**

![Banner](docs/banner.png)

## 🔷 Overview

**Azure Architecture Review Copilot** is a multi-agent AI system that orchestrates four specialized agents — **Security, Cost, Identity, and Reliability** — to perform enterprise-grade Azure architecture assessments in minutes.

It ingests Azure environment context, detects the **Top 5 risks**, generates a **prioritized remediation roadmap**, maps findings to **SMB / Mid-Market / Enterprise** architecture blueprints, and applies **Azure Well-Architected Framework pillar guidance** based on user priorities.

---

## 🎯 Problem Statement

Azure environments grow complex quickly. Security gaps, cost overruns, identity misconfigurations, and reliability risks go undetected until they cause outages or breaches. Manual architecture reviews are slow, expensive, and inconsistent.

## ✅ Solution Outcome

| Outcome | Detail |
|---|---|
| ⚡ Speed | Detect top architecture risks in minutes instead of days |
| 📖 Grounded | Cited remediation steps from Azure Architecture Center via Foundry IQ |
| 🏗️ Tiered | SMB / Mid-Market / Enterprise blueprint recommendations |
| 📋 Exportable | Architecture Decision Report (ADR) in JSON + Markdown |
| 🎯 Pillar-aware | Re-rank findings based on WAF pillar priorities |

---

## 🤖 Agent Architecture

```
User Input
    │
    ▼
ArchitectureReviewOrchestrator
    ├── SecurityAgent    → Detects vulnerabilities & misconfigurations
    ├── CostAgent        → Identifies FinOps & rightsizing opportunities
    ├── IdentityAgent    → Reviews RBAC, Entra ID, service principals
    └── ReliabilityAgent → Evaluates DR, HA, backup, resiliency
    │
    ▼
Top 5 Risks (ranked by severity + WAF pillar weight)
    │
    ▼
Blueprint Mapping (SMB / Mid-Market / Enterprise)
    │
    ▼
Architecture Decision Report (ADR Export)
```

---

## 🔧 Technology Stack

| Component | Technology |
|---|---|
| Agent Orchestration | Microsoft Azure AI Foundry |
| IQ Layer (Primary) | **Foundry IQ** — grounded RAG over Azure docs |
| IQ Layer (Secondary) | **Fabric IQ** — business impact scoring |
| Language Model | Azure OpenAI GPT-4o |
| Knowledge Sources | Azure Architecture Center, CAF, WAF |
| UI | Streamlit |
| Backend | Python 3.11+ |
| Code Assistance | GitHub Copilot |

---

## 🚀 Demo Flow

1. **Ingest** — Azure subscription context (or demo mode)
2. **Analyze** — 4 agents run in parallel
3. **Detect** — Top 5 risks with severity, evidence, effort, impact
4. **Recommend** — Prioritized remediation + WAF pillar alignment
5. **Blueprint** — Tier-appropriate architecture guidance
6. **Export** — Download ADR report (JSON / Markdown)

---

## 🏃 Quick Start

### Prerequisites
- Python 3.11+
- Azure subscription (optional — demo mode works without it)

### Setup

```bash
git clone https://github.com/techleadyu/azure-architecture-review-copilot.git
cd azure-architecture-review-copilot
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials (or leave DEMO_MODE=true)
```

### Run CLI

```bash
python main.py
python main.py --pillar security
python main.py --tier enterprise --export report.json
```

### Run Streamlit UI

```bash
streamlit run ui/app.py
```

---

## 📊 Scoring Rubric Alignment

| Criterion | How this project addresses it |
|---|---|
| Accuracy & Relevance (20%) | Grounded answers via Foundry IQ from official Azure docs |
| Reasoning & Multi-step (20%) | 4-agent orchestration with parallel analysis + risk ranking |
| Creativity & Originality (15%) | Tier-aware blueprints + WAF pillar re-ranking |
| UX & Presentation (15%) | Streamlit dashboard + ADR export |
| Reliability & Safety (20%) | Demo mode fallback, error handling, cited references |
| Community Vote (10%) | Open source, clear README, demo video |

---

## 📁 Project Structure

```
azure-architecture-review-copilot/
├── main.py                    # CLI entry point
├── agents/
│   ├── orchestrator.py        # Multi-agent coordinator
│   ├── security_agent.py      # Security specialist
│   ├── cost_agent.py          # Cost/FinOps specialist
│   ├── identity_agent.py      # Identity/RBAC specialist
│   └── reliability_agent.py   # Reliability specialist
├── tools/
│   ├── foundry_iq_client.py   # Foundry IQ integration
│   ├── azure_client.py        # Azure resource fetcher
│   └── report_generator.py    # ADR report generator
├── models/risk.py             # Risk data models
├── config/
│   ├── settings.py            # Configuration
│   └── waf_pillars.py         # WAF pillar definitions
├── data/blueprints/           # SMB/Mid/Enterprise blueprints
├── ui/app.py                  # Streamlit dashboard
└── docs/                      # Architecture docs
```

---

## 📖 References

- [Azure Architecture Center](https://learn.microsoft.com/azure/architecture/)
- [Cloud Adoption Framework](https://learn.microsoft.com/azure/cloud-adoption-framework/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
- [Foundry IQ Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Azure Enterprise Scale Landing Zone](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/architecture)

---

## 👤 Author

**Yash Upadhyay** — Azure / Cloud Engineer | Agentic AI Engineering in Microsoft Ecosystem

*Built for Agents League Hackathon 2026 — Reasoning Agents Track*
