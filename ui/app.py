import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import ArchitectureReviewOrchestrator
from tools.azure_client import AzureClient
from tools.report_generator import ReportGenerator
from config.waf_pillars import WAF_PILLARS
import plotly.graph_objects as go

st.set_page_config(
    page_title="Azure Architecture Review Copilot",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Microsoft_Azure.svg/150px-Microsoft_Azure.svg.png", width=60)
    st.title("Azure Architecture\nReview Copilot")
    st.caption("Multi-Agent AI Copilot")
    st.divider()

    st.subheader("⚙️ Review Settings")
    tier = st.selectbox("Architecture Tier", ["Auto-Detect", "SMB", "Mid-Market", "Enterprise"])
    waf_pillar = st.selectbox("WAF Pillar Focus", ["None"] + [v["name"] for v in WAF_PILLARS.values()])
    st.divider()

    subscription = st.text_input("Subscription Name", value="Contoso - Production")
    landing_zone = st.text_input("Landing Zone", value="Enterprise Scale")

    run_btn = st.button("🚀 Run Architecture Review", type="primary", use_container_width=True)

# ── Main ────────────────────────────────────────────────────────────────
st.title("Hello, Architect 👋")
st.caption("AI-powered review of your Azure environment")

if "review_result" not in st.session_state:
    st.session_state.review_result = None

if run_btn or st.session_state.review_result is None:
    with st.spinner("Running 4 specialist agents in parallel..."):
        azure_client = AzureClient()
        context = azure_client.get_environment_context()
        context["subscription_name"] = subscription
        context["landing_zone"] = landing_zone

        tier_map = {"Auto-Detect": None, "SMB": "smb", "Mid-Market": "midmarket", "Enterprise": "enterprise"}
        pillar_map = {v["name"]: k for k, v in WAF_PILLARS.items()}
        pillar_key = pillar_map.get(waf_pillar)

        orchestrator = ArchitectureReviewOrchestrator()
        result = orchestrator.run_review(context, waf_pillar=pillar_key, tier=tier_map[tier])
        st.session_state.review_result = result

result = st.session_state.review_result
if not result:
    st.stop()

# ── Summary Banner ──────────────────────────────────────────────────────
score = result["overall_risk_score"]
score_color = "red" if score < 60 else "orange" if score < 80 else "green"
savings = result["total_estimated_savings"]
risks = result["top5_risks"]
critical = sum(1 for r in risks if r["severity"] == "Critical")
high = sum(1 for r in risks if r["severity"] == "High")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Overall Risk Score", f"{score}/100")
col2.metric("Critical Risks", critical, delta=None)
col3.metric("High Risks", high, delta=None)
col4.metric("Total Risks", result["all_risks_count"])
col5.metric("Est. Savings", f"${savings:,.0f}/mo")

st.divider()

# ── Agent Results ───────────────────────────────────────────────────────
st.subheader("🤖 AI Agent Analysis")
agent_cols = st.columns(4)
agent_icons = {"Security": "🔐", "Cost": "💰", "Identity": "👤", "Reliability": "🛡️"}

for i, (cat, data) in enumerate(result["agent_results"].items()):
    with agent_cols[i]:
        s = data["risk_score"]
        color = "🔴" if s < 60 else "🟡" if s < 80 else "🟢"
        st.markdown(f"### {agent_icons.get(cat, '🔷')} {cat} Agent")
        st.metric("Risk Score", f"{s}%", delta=None)
        st.caption(f"Scanned: {data['resources_scanned']} resources")
        st.caption(f"Risks: {data['risk_count']} ({data['critical_count']} critical)")

st.divider()

# ── Top 5 Risks + Donut Chart ───────────────────────────────────────────
col_risks, col_chart = st.columns([3, 2])

with col_risks:
    st.subheader("🚨 Top 5 Risks")
    severity_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    for i, r in enumerate(result["top5_risks"], 1):
        icon = severity_colors.get(r["severity"], "⚪")
        with st.expander(f"{i}. {icon} [{r['severity']}] {r['title']}"):
            st.write(f"**Category:** {r['category']} | **Effort:** {r['effort']} | **Impact:** {r['impact']}")
            st.write(f"**Description:** {r['description']}")
            st.write(f"**Remediation:** {r['remediation']}")
            if r.get("reference_url"):
                st.markdown(f"[📖 Microsoft Reference]({r['reference_url']})")
            if r.get("estimated_savings", 0) > 0:
                st.success(f"💰 Est. savings: ${r['estimated_savings']:,.0f}/mo")

with col_chart:
    st.subheader("📊 Risk by Category")
    cats = list(result["agent_results"].keys())
    counts = [result["agent_results"][c]["risk_count"] for c in cats]
    fig = go.Figure(data=[go.Pie(
        labels=cats, values=counts, hole=0.5,
        marker_colors=["#E53E3E", "#48BB78", "#9F7AEA", "#4299E1"],
    )])
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Blueprints ───────────────────────────────────────────────────────────
st.subheader("🏗️ Recommended Blueprints")
bp = result.get("blueprint", {})
bp_cols = st.columns(3)
tiers_info = [
    ("SMB", "smb", "Optimized for small teams", "75%"),
    ("Mid-Market", "midmarket", "Balanced scale & governance", "92%"),
    ("Enterprise", "enterprise", "Advanced scale & compliance", "80%"),
]
active_tier = bp.get("tier", "midmarket")
for col, (name, key, desc, match) in zip(bp_cols, tiers_info):
    with col:
        is_active = key == active_tier
        border = "border: 2px solid #4299E1; border-radius: 8px; padding: 12px;" if is_active else "border: 1px solid #ccc; border-radius: 8px; padding: 12px;"
        st.markdown(f"<div style='{border}'><b>{'✅ ' if is_active else ''}{name} Blueprint</b><br><small>{desc}</small><br><b style='color:green'>{match} Match</b></div>", unsafe_allow_html=True)

st.divider()

# ── Export ───────────────────────────────────────────────────────────────
st.subheader("📤 Export Architecture Decision Report")
col_dl1, col_dl2 = st.columns(2)
report_gen = ReportGenerator()

with col_dl1:
    json_report = report_gen.generate_json(result)
    st.download_button("⬇️ Download ADR (JSON)", data=json_report, file_name="azure_adr_report.json", mime="application/json")

with col_dl2:
    md_report = report_gen.generate_markdown(result)
    st.download_button("⬇️ Download ADR (Markdown)", data=md_report, file_name="azure_adr_report.md", mime="text/markdown")

# ── Copilot Chat ─────────────────────────────────────────────────────────
st.divider()
st.subheader("💬 Architecture Copilot")
quick_actions = ["Show me the top risks", "Give me remediation plan", "Map to CAF framework", "Focus on Well-Architected pillars"]
selected_action = st.radio("Quick Actions", quick_actions, horizontal=True, label_visibility="collapsed")
chat_input = st.chat_input("Ask me anything about your Azure architecture...")

if chat_input or selected_action:
    query = chat_input or selected_action
    with st.chat_message("assistant", avatar="🤖"):
        if "top risks" in query.lower():
            st.write("Here are your top 3 critical risks:")
            for r in result["top5_risks"][:3]:
                st.write(f"- **{r['severity']}**: {r['title']}")
        elif "remediation" in query.lower():
            st.write("Prioritized remediation plan (by severity + effort):")
            for i, r in enumerate(result["top5_risks"], 1):
                st.write(f"{i}. **{r['title']}** — {r['remediation']}")
        elif "caf" in query.lower():
            st.write("Your environment maps to the **Azure Cloud Adoption Framework** Enterprise Scale Landing Zone. Key alignment areas: Management Groups, Policy-driven governance, Hub-Spoke networking.")
            st.markdown("[📖 Learn more: CAF Enterprise Scale](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/)")
        elif "well-architected" in query.lower():
            st.write("Well-Architected Framework pillar summary based on your review:")
            for pillar, data in WAF_PILLARS.items():
                st.write(f"- {data['icon']} **{data['name']}**: {data['description']}")
        else:
            st.write(f"I've noted your query: *{query}*. In live mode, I'd provide grounded answers from Azure Architecture Center via Foundry IQ.")
