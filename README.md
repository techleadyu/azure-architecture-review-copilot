<div align="center">

# 🔷 Azure Architecture Review Copilot

### Multi-Agent AI Copilot — Agents League Hackathon 2026

[![Hackathon](https://img.shields.io/badge/Hackathon-Agents%20League%202026-blueviolet?style=for-the-badge)](https://devpost.com/hackathons)
[![Track](https://img.shields.io/badge/Track-Reasoning%20Agents-blue?style=for-the-badge)](https://devpost.com/hackathons)
[![IQ Layer](https://img.shields.io/badge/IQ%20Layer-Foundry%20IQ%20%2B%20Fabric%20IQ-0078d4?style=for-the-badge)](https://learn.microsoft.com/azure/ai-foundry/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **Multi-agent AI system that orchestrates Security, Cost, Identity & Reliability agents to perform enterprise-grade Azure architecture reviews — powered by Foundry IQ + Azure OpenAI GPT-4o**

[![Deploy to Azure](https://aka.ms/deploytoazure)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Ftechleadyu%2Fazure-architecture-review-copilot%2Fmaster%2Fazuredeploy.json)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Solution Architecture](#-solution-architecture)
- [Technology Stack](#-technology-stack)
- [Quick Start — Demo Mode (No Azure required)](#-quick-start--demo-mode-no-azure-required)
- [Full Setup — Real Azure Tenant](#-full-setup--real-azure-tenant)
- [Configuration Reference](#-configuration-reference)
- [Run Commands](#-run-commands)
- [Deploy to Azure](#-deploy-to-azure-1)
- [Project Structure](#-project-structure)
- [Judging Criteria Alignment](#-judging-criteria-alignment)
- [References](#-references)

---

## 🔷 Overview

**Azure Architecture Review Copilot** is an enterprise-grade, multi-agent AI system that orchestrates four specialized agents to perform automated Azure architecture health reviews in minutes instead of days.

| Agent | Role |
|---|---|
| 🛡️ **Security Agent** | Detects vulnerabilities, misconfigs, public exposure |
| 💰 **Cost Agent** | Identifies FinOps opportunities, rightsizing, reserved instances |
| 👤 **Identity Agent** | Reviews RBAC, Entra ID posture, MFA, service principals |
| ☁️ **Reliability Agent** | Evaluates DR, HA, backup, resiliency, SLA coverage |

**Demo flow:** Ingest → Analyze (4 agents parallel) → Top 5 Risks → Remediation Roadmap → Blueprint Map → Export ADR

---

## 🔴 Problem Statement

Azure environments grow complex quickly. Security gaps, cost overruns, identity misconfigurations, and reliability risks go undetected until they cause outages or breaches. Manual reviews are slow, expensive, and inconsistent. There is no single tool that:

- Orchestrates multi-domain specialist agents in parallel
- Grounds answers in Microsoft official docs (CAF, WAF, Architecture Center)
- Maps findings to business tier (SMB / Mid-Market / Enterprise)
- Re-ranks recommendations by Well-Architected Framework pillar
- Exports a stakeholder-ready Architecture Decision Report

---

## 🏗️ Solution Architecture

```
User Input (subscription / landing zone / WAF pillar)
        │
        ▼
ArchitectureReviewOrchestrator  ← coordinates all agents
        │
        ├── SecurityAgent     → detects misconfigs, public access, encryption gaps
        ├── CostAgent         → finds reserved instance gaps, idle VMs, orphaned disks
        ├── IdentityAgent     → reviews RBAC overreach, MFA, expired credentials
        └── ReliabilityAgent  → checks DR, HA, backup, monitoring coverage
        │
        ▼
Top 5 Risks (ranked by severity + WAF pillar weight)
        │
        ▼
Blueprint Mapping — SMB / Mid-Market / Enterprise
        │
        ▼
Architecture Decision Report (ADR) — JSON + Markdown export
```

---

## 🔧 Technology Stack

| Component | Technology |
|---|---|
| Agent Orchestration | Microsoft Azure AI Foundry |
| IQ Layer (Primary) | **Foundry IQ** — grounded RAG over Azure Architecture Center, CAF, WAF |
| IQ Layer (Secondary) | **Fabric IQ** — business impact scoring |
| Language Model | Azure OpenAI GPT-4o |
| UI | Streamlit (responsive, dark/light/system theme) |
| Backend | Python 3.11+ |
| Auth | Azure Identity (DefaultAzureCredential / Service Principal) |
| Knowledge Sources | Azure Architecture Center · Cloud Adoption Framework · Well-Architected Framework |
| Dev Tooling | GitHub Copilot in VS Code |
| Deployment | Azure App Service (Linux) · ARM Template |

---

## ⚡ Quick Start — Demo Mode (No Azure required)

> **No Azure subscription required.** DEMO_MODE uses realistic mock data so you can explore the full UI immediately.

### Prerequisites

- Python 3.11+
- Git

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/techleadyu/azure-architecture-review-copilot.git
cd azure-architecture-review-copilot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env template (demo mode is ON by default)
cp .env.example .env

# 4. Run the Streamlit UI
streamlit run ui/app.py

# OR run the CLI
python main.py
```

The app opens at **http://localhost:8501** with full demo data showing all 4 agents, Top 5 Risks, blueprints, charts, and ADR export.

---

## 🔵 Full Setup — Real Azure Tenant

### Step 1 — Prerequisites

- Azure subscription with Contributor access
- Azure CLI installed: `az --version`
- Python 3.11+

### Step 2 — Create Azure Resources

**Option A — Deploy with ARM template (one click)**

Click the **Deploy to Azure** button at the top, or run:

```bash
az deployment group create \
  --resource-group <YOUR-RESOURCE-GROUP> \
  --template-file azuredeploy.json \
  --parameters projectName=arcreview location=eastus
```

**Option B — Manual CLI**

```bash
# Login
az login

# Create resource group
az group create --name rg-arcreview --location eastus

# Create Azure OpenAI
az cognitiveservices account create \
  --name arcreview-openai \
  --resource-group rg-arcreview \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4o model
az cognitiveservices account deployment create \
  --name arcreview-openai \
  --resource-group rg-arcreview \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 30 \
  --sku-name Standard
```

### Step 3 — Configure Environment

Edit the `.env` file (copy from `.env.example` first):

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Where to find it | File it configures |
|---|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure Portal → Subscriptions | `tools/azure_client.py` |
| `AZURE_TENANT_ID` | Azure Portal → Microsoft Entra ID → Overview | `config/settings.py` |
| `AZURE_CLIENT_ID` | App registration → Application (client) ID | `config/settings.py` |
| `AZURE_CLIENT_SECRET` | App registration → Certificates & secrets | `config/settings.py` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource → Keys and Endpoint | `tools/foundry_iq_client.py` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI resource → KEY 1 | `tools/foundry_iq_client.py` |
| `AZURE_OPENAI_DEPLOYMENT` | Name given to GPT-4o deployment | `tools/foundry_iq_client.py` |
| `AZURE_AI_PROJECT_ENDPOINT` | AI Foundry project → Settings | `tools/foundry_iq_client.py` |
| `AZURE_AI_PROJECT_API_KEY` | AI Foundry project → Keys | `tools/foundry_iq_client.py` |
| `DEMO_MODE` | Set `false` for live mode | All agents |

### Step 4 — Create a Service Principal

```bash
# Create service principal with Reader role
az ad sp create-for-rbac \
  --name "sp-arcreview" \
  --role Reader \
  --scopes /subscriptions/<YOUR-SUBSCRIPTION-ID> \
  --sdk-auth
# Copy clientId → AZURE_CLIENT_ID
# Copy clientSecret → AZURE_CLIENT_SECRET
# Copy tenantId → AZURE_TENANT_ID
```

### Step 5 — Run

```bash
streamlit run ui/app.py
```

---

## ⚙️ Configuration Reference

All configuration lives in `.env`. Loaded by `config/settings.py`.

### Files to modify per scenario

| Scenario | File(s) to edit |
|---|---|
| Change Azure credentials | `.env` |
| Add new risk rules | `agents/security_agent.py`, `agents/cost_agent.py`, etc. |
| Change blueprint content | `data/blueprints/smb.json`, `midmarket.json`, `enterprise.json` |
| Change WAF pillars | `config/waf_pillars.py` |
| Change UI colors / layout | `ui/app.py` (CSS variables at top of CSS block) |
| Change Streamlit theme | `.streamlit/config.toml` |
| Change port | `.streamlit/config.toml` → `[server] port` |

### Theme (`.streamlit/config.toml`)

```toml
[theme]
base = "light"              # "light" or "dark"
primaryColor = "#0078d4"    # Azure blue
backgroundColor = "#f8fafc"
textColor = "#1a1a2e"
```

> The UI also auto-switches dark/light based on your OS/device preference via CSS media queries.

---

## 🚀 Run Commands

```bash
# Streamlit UI
streamlit run ui/app.py
streamlit run ui/app.py --server.port 8080

# CLI
python main.py
python main.py --pillar security
python main.py --pillar cost
python main.py --tier smb
python main.py --tier enterprise
python main.py --export reports/adr.json
python main.py --markdown

# Tests
python tests/test_orchestrator.py

# Install
pip install -r requirements.txt
```

---

## ☁️ Deploy to Azure

[![Deploy to Azure](https://aka.ms/deploytoazure)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Ftechleadyu%2Fazure-architecture-review-copilot%2Fmaster%2Fazuredeploy.json)

Deploys: Azure OpenAI (GPT-4o) · Key Vault · App Service (Linux) · Log Analytics

| Parameter | Default | Description |
|---|---|---|
| `projectName` | `arcreview` | Short prefix for resource names (max 12) |
| `location` | `eastus` | Azure region |
| `openAiSkuName` | `S0` | Azure OpenAI tier |
| `gpt4oModelCapacity` | `30` | TPM capacity (thousands) |

---

## 📁 Project Structure

```
azure-architecture-review-copilot/
│
├── main.py                       # CLI entry point
├── requirements.txt              # Python dependencies
├── azuredeploy.json              # ARM template (Deploy to Azure)
├── .env.example                  # Environment variable template
│
├── agents/
│   ├── orchestrator.py           # Multi-agent coordinator
│   ├── security_agent.py         # Security specialist
│   ├── cost_agent.py             # Cost/FinOps specialist
│   ├── identity_agent.py         # Identity/RBAC specialist
│   └── reliability_agent.py      # Reliability specialist
│
├── tools/
│   ├── foundry_iq_client.py      # Foundry IQ / Azure OpenAI client
│   ├── azure_client.py           # Azure resource fetcher
│   └── report_generator.py       # ADR report generator
│
├── models/risk.py                # Risk, ReviewResult data models
├── config/
│   ├── settings.py               # Environment variable loader
│   └── waf_pillars.py            # Well-Architected Framework pillars
│
├── data/blueprints/
│   ├── smb.json                  # SMB blueprint
│   ├── midmarket.json            # Mid-Market blueprint
│   └── enterprise.json           # Enterprise blueprint
│
├── ui/app.py                     # Streamlit dashboard
├── tests/test_orchestrator.py    # Tests
└── .streamlit/config.toml        # Theme + server config
```

---

## 📊 Judging Criteria Alignment

| Criterion | Weight | How this addresses it |
|---|---|---|
| **Accuracy & Relevance** | 20% | Grounded via Foundry IQ from Azure Architecture Center, CAF, WAF. Cited URLs on every risk. |
| **Reasoning & Multi-step** | 20% | 4 agents run in parallel, findings aggregated, ranked by severity + WAF pillar weight, mapped to blueprints. |
| **Creativity & Originality** | 15% | Tier-aware blueprints (SMB/Mid/Enterprise) + WAF pillar re-ranking + real-time copilot chat. |
| **UX & Presentation** | 15% | Enterprise Streamlit dashboard, responsive, dark/light/system theme, ADR export. |
| **Reliability & Safety** | 20% | Demo mode fallback, lazy imports, no hardcoded secrets, error handling, cited references. |
| **Community Vote** | 10% | Open source, clear README, one-click Deploy to Azure. |

---

## 📖 References

| Source | Link |
|---|---|
| Azure Architecture Center | https://learn.microsoft.com/azure/architecture/ |
| Cloud Adoption Framework | https://learn.microsoft.com/azure/cloud-adoption-framework/ |
| Well-Architected Framework | https://learn.microsoft.com/azure/well-architected/ |
| Enterprise Scale Landing Zone | https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/architecture |
| Azure AI Foundry | https://learn.microsoft.com/azure/ai-foundry/ |
| Azure RBAC Best Practices | https://learn.microsoft.com/azure/role-based-access-control/best-practices |
| Azure Cost Management | https://learn.microsoft.com/azure/cost-management-billing/ |
| Azure WAF Reliability | https://learn.microsoft.com/azure/well-architected/reliability/ |
| Azure WAF Security | https://learn.microsoft.com/azure/well-architected/security/ |

---

## 👤 Author

**Yash Upadhyay** — Azure / Cloud Engineer | Agentic AI Engineering in Microsoft Ecosystem

*Built for [Agents League Hackathon 2026](https://devpost.com/hackathons) — Reasoning Agents Track*

---

<div align="center">
  <sub>Powered by Azure AI Foundry · Foundry IQ · Azure OpenAI GPT-4o · Microsoft CAF · WAF</sub>
</div>
