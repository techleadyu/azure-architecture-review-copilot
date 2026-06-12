import streamlit as st
import sys
import os
from datetime import datetime

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

# ── Custom CSS matching reference design ──────────────────────────────────
st.markdown("""
<style>
  /* Global font */
  html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

  /* Hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #0f1923 !important;
    min-width: 260px !important;
    max-width: 260px !important;
  }
  [data-testid="stSidebar"] * { color: #c9d1d9 !important; }
  [data-testid="stSidebar"] .sidebar-brand {
    padding: 20px 16px 8px;
    display: flex; align-items: center; gap: 10px;
  }
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 { color: #ffffff !important; font-size: 15px !important; }

  /* Nav items */
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 16px; border-radius: 6px; cursor: pointer;
    font-size: 14px; color: #8b949e; margin: 2px 8px;
    transition: background .15s;
  }
  .nav-item:hover { background: #1c2a35; color: #e6edf3; }
  .nav-item.active { background: linear-gradient(135deg,#0078d4,#6f42c1); color: #ffffff !important; }
  .nav-icon { font-size: 16px; width: 20px; text-align: center; }

  /* Environment card */
  .env-card {
    background: #1c2a35; border-radius: 10px; padding: 14px 16px;
    margin: 10px 8px; border: 1px solid #2d3f4e;
  }
  .env-label { font-size: 11px; color: #8b949e; margin-bottom: 2px; }
  .env-value { font-size: 13px; color: #e6edf3; font-weight: 500; }
  .connected-dot { display:inline-block; width:8px; height:8px;
    border-radius:50%; background:#3fb950; margin-right:5px; }

  /* ── Top header bar ── */
  .top-header {
    background: #ffffff; border-bottom: 1px solid #e8ecf0;
    padding: 14px 28px; display: flex; align-items: center;
    justify-content: space-between;
  }
  .greeting-title { font-size: 24px; font-weight: 700; color: #1a1a2e; margin:0; }
  .greeting-sub { font-size: 13px; color: #6b7280; margin:0; }
  .new-review-btn {
    background: linear-gradient(135deg,#0078d4,#6f42c1);
    color: white !important; border: none; border-radius: 8px;
    padding: 9px 18px; font-size: 13px; font-weight: 600;
    cursor: pointer; display:flex; align-items:center; gap:6px;
  }

  /* ── Summary banner ── */
  .summary-banner {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 60%, #0f1f3d 100%);
    border-radius: 14px; padding: 24px 28px;
    margin: 20px 20px 0; position: relative; overflow: hidden;
    display: flex; align-items: center; justify-content: space-between;
  }
  .banner-title { font-size: 16px; font-weight: 700; color: #ffffff; }
  .banner-sub { font-size: 12px; color: #8b9dc3; }
  .score-ring-wrap { text-align:center; }
  .score-ring-num { font-size: 36px; font-weight: 800; color: #ffffff; }
  .score-ring-label { font-size: 11px; color: #8b9dc3; }
  .stat-box { text-align: center; padding: 0 20px; }
  .stat-num { font-size: 22px; font-weight: 800; }
  .stat-label { font-size: 11px; color: #8b9dc3; }
  .stat-critical { color: #ff6b6b; }
  .stat-high { color: #ffa500; }
  .stat-medium { color: #ffd700; }
  .stat-low { color: #51cf66; }
  .view-report-btn {
    background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
    color: white !important; border-radius: 8px; padding: 8px 16px;
    font-size: 12px; cursor: pointer; white-space: nowrap;
  }
  .robot-img { position: absolute; right: 200px; top: 0; height: 130%; opacity: 0.9; }

  /* ── Section headers ── */
  .section-header {
    display: flex; justify-content: space-between; align-items: center;
    margin: 20px 0 12px;
  }
  .section-title { font-size: 16px; font-weight: 700; color: #1a1a2e; }
  .section-link { font-size: 12px; color: #0078d4; cursor: pointer; }

  /* ── Agent cards ── */
  .agent-card {
    background: #ffffff; border: 1px solid #e8ecf0; border-radius: 12px;
    padding: 16px; position: relative;
  }
  .agent-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
  .agent-icon {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 18px;
  }
  .agent-icon-sec { background: #e8f0fe; }
  .agent-icon-cost { background: #e6f9f0; }
  .agent-icon-idn { background: #f0e8fe; }
  .agent-icon-rel { background: #e8f4fe; }
  .agent-name { font-size: 14px; font-weight: 700; color: #1a1a2e; }
  .agent-stat { font-size: 12px; color: #6b7280; margin: 3px 0; }
  .risk-badge {
    display: inline-block; padding: 2px 10px; border-radius: 4px;
    font-size: 11px; font-weight: 600; margin: 8px 0 4px;
  }
  .risk-critical { background:#fff0f0; color:#e03030; }
  .risk-high { background:#fff5e6; color:#d97706; }
  .risk-medium { background:#fffbe6; color:#b45309; }
  .risk-low { background:#f0fdf4; color:#166534; }
  .progress-bar-wrap { background: #e8ecf0; border-radius: 4px; height: 6px; margin-top: 8px; }
  .progress-bar-fill { height: 6px; border-radius: 4px; }
  .fill-critical { background: #ef4444; }
  .fill-high { background: #f59e0b; }
  .fill-medium { background: #10b981; }
  .fill-low { background: #3b82f6; }

  /* ── Risk list ── */
  .risk-row {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0; border-bottom: 1px solid #f3f4f6;
  }
  .risk-num {
    width: 26px; height: 26px; border-radius: 50%;
    background: #f3f4f6; display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: #374151; flex-shrink: 0;
  }
  .risk-title { font-size: 13px; font-weight: 600; color: #1a1a2e; }
  .risk-desc { font-size: 11px; color: #6b7280; }
  .sev-badge {
    padding: 2px 10px; border-radius: 4px; font-size: 11px;
    font-weight: 700; flex-shrink: 0; white-space: nowrap;
  }
  .sev-critical { background:#fee2e2; color:#dc2626; }
  .sev-high { background:#fef3c7; color:#d97706; }
  .sev-medium { background:#fef9c3; color:#ca8a04; }
  .sev-low { background:#dcfce7; color:#16a34a; }

  /* ── Blueprint cards ── */
  .bp-card {
    border: 1px solid #e8ecf0; border-radius: 12px; padding: 16px;
    text-align: center; cursor: pointer; transition: all .2s;
  }
  .bp-card.active { border: 2px solid #0078d4; background: #f0f7ff; }
  .bp-icon { font-size: 32px; margin-bottom: 8px; }
  .bp-name { font-size: 14px; font-weight: 700; color: #1a1a2e; }
  .bp-desc { font-size: 12px; color: #6b7280; margin: 4px 0; }
  .bp-match { font-size: 12px; font-weight: 700; color: #16a34a; margin-top: 6px; }
  .bp-match-neutral { color: #0078d4; }

  /* ── Right chat panel ── */
  .chat-panel {
    background: #ffffff; border-left: 1px solid #e8ecf0;
    height: 100vh; overflow-y: auto; padding: 0;
  }
  .chat-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 16px; border-bottom: 1px solid #e8ecf0; position: sticky; top: 0;
    background: white; z-index: 10;
  }
  .chat-header-title { font-size: 14px; font-weight: 700; color: #1a1a2e; }
  .chat-msg {
    background: #f9fafb; border-radius: 8px; padding: 12px;
    margin: 12px; font-size: 13px; color: #374151; line-height: 1.5;
  }
  .chat-prompt { font-size: 13px; font-weight: 600; color: #374151; margin: 4px 16px; }
  .quick-btn {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px; margin: 4px 12px; border-radius: 8px;
    border: 1px solid #e8ecf0; font-size: 13px; color: #374151;
    cursor: pointer; background: white;
  }
  .quick-btn:hover { background: #f0f7ff; border-color: #0078d4; }
  .waf-section { padding: 16px; border-top: 1px solid #e8ecf0; }
  .waf-title { font-size: 13px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
  .waf-focus { font-size: 12px; color: #6b7280; }
  .waf-pillars { display: flex; gap: 10px; margin-top: 10px; }
  .waf-pill {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; border: 2px solid #e8ecf0; cursor: pointer;
  }
  .waf-pill.active-waf { border-color: #0078d4; background: #e8f4ff; }

  /* Main content area */
  .main-content { padding: 0 20px 40px; }

  /* Card container */
  .card { background: #ffffff; border: 1px solid #e8ecf0; border-radius: 12px; padding: 20px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Overview"
if "waf_focus" not in st.session_state:
    st.session_state.waf_focus = "security"
if "chat_query" not in st.session_state:
    st.session_state.chat_query = "Show me the top risks"
if "subscription" not in st.session_state:
    st.session_state.subscription = "Contoso - Production"
if "landing_zone" not in st.session_state:
    st.session_state.landing_zone = "Enterprise Scale"

# ── Run review on first load ───────────────────────────────────────────────
def run_review(tier_key=None, pillar_key=None):
    azure_client = AzureClient()
    context = azure_client.get_environment_context()
    context["subscription_name"] = st.session_state.subscription
    context["landing_zone"] = st.session_state.landing_zone
    orchestrator = ArchitectureReviewOrchestrator()
    return orchestrator.run_review(context, waf_pillar=pillar_key, tier=tier_key)

if st.session_state.review_result is None:
    with st.spinner("🔍 Running 4 specialist agents in parallel..."):
        st.session_state.review_result = run_review()

result = st.session_state.review_result

# ── Helper data ────────────────────────────────────────────────────────────
score = result["overall_risk_score"]
savings = result["total_estimated_savings"]
top5 = result["top5_risks"]
agent_results = result["agent_results"]
bp = result.get("blueprint", {})
active_tier = bp.get("tier", "enterprise")

all_risks_flat = top5
critical_count = sum(1 for r in all_risks_flat if r["severity"] == "Critical")
high_count = sum(1 for r in all_risks_flat if r["severity"] == "High")
medium_count = sum(1 for r in all_risks_flat if r["severity"] == "Medium")
low_count = sum(1 for r in all_risks_flat if r["severity"] == "Low")

agent_icons_html = {"Security": "🛡️", "Cost": "💲", "Identity": "👤", "Reliability": "☁️"}
agent_icon_class = {"Security": "agent-icon-sec", "Cost": "agent-icon-cost",
                    "Identity": "agent-icon-idn", "Reliability": "agent-icon-rel"}
sev_class = {"Critical": "sev-critical", "High": "sev-high", "Medium": "sev-medium", "Low": "sev-low"}
risk_badge_class = {"High": "risk-high", "Critical": "risk-critical",
                    "Medium": "risk-medium", "Low": "risk-low"}
fill_class = {"Critical": "fill-critical", "High": "fill-high",
              "Medium": "fill-medium", "Low": "fill-low"}

def score_to_risk_level(s):
    if s < 60: return "Critical Risk", "risk-critical"
    if s < 75: return "High Risk", "risk-high"
    if s < 90: return "Medium Risk", "risk-medium"
    return "Low Risk", "risk-low"

# ── LAYOUT: sidebar | main | chat ──────────────────────────────────────────
sidebar_col, main_col, chat_col = st.columns([1.1, 4.2, 1.7])

# ════════════════════════ SIDEBAR ════════════════════════
with sidebar_col:
    st.markdown("""
    <div style="padding:20px 8px 8px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <div style="background:linear-gradient(135deg,#0078d4,#6f42c1);width:40px;height:40px;
          border-radius:10px;display:flex;align-items:center;justify-content:center;
          font-size:20px;font-weight:900;color:white;">A</div>
        <div>
          <div style="font-size:13px;font-weight:700;color:#e6edf3;line-height:1.2;">
            Azure Architecture<br><span style="color:#3b82f6;">Review</span> Copilot</div>
          <div style="font-size:10px;color:#8b949e;">Multi-Agent AI Copilot</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("🏠", "Overview"), ("⚠️", "Risk Dashboard"), ("📋", "Findings"),
        ("💡", "Recommendations"), ("🏗️", "Blueprints"),
        ("🏛️", "Well-Architected Pillars"), ("📊", "Reports"), ("⚙️", "Settings"),
    ]
    for icon, label in nav_items:
        is_active = st.session_state.active_nav == label
        cls = "nav-item active" if is_active else "nav-item"
        if st.button(f"{icon}  {label}", key=f"nav_{label}",
                     use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.active_nav = label
            st.rerun()

    st.markdown("<hr style='border-color:#1c2a35;margin:10px 8px;'>", unsafe_allow_html=True)

    # Environment card
    st.markdown(f"""
    <div class="env-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span style="font-size:13px;font-weight:700;color:#e6edf3;">Environment</span>
        <span><span class="connected-dot"></span>
          <span style="font-size:11px;color:#3fb950;">Connected</span></span>
      </div>
      <div class="env-label">Subscription</div>
      <div class="env-value">{st.session_state.subscription}</div>
      <div class="env-label" style="margin-top:8px;">Landing Zone</div>
      <div class="env-value">{st.session_state.landing_zone}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 View Details →", use_container_width=True):
        pass

    # Settings expander in sidebar
    with st.expander("⚙️ Review Settings"):
        new_sub = st.text_input("Subscription", value=st.session_state.subscription, key="sub_inp")
        new_lz = st.text_input("Landing Zone", value=st.session_state.landing_zone, key="lz_inp")
        tier_sel = st.selectbox("Tier", ["Auto-Detect", "SMB", "Mid-Market", "Enterprise"], key="tier_sel")
        pillar_sel = st.selectbox("WAF Pillar", ["None"] + [v["name"] for v in WAF_PILLARS.values()], key="pillar_sel")
        if st.button("🚀 Run New Review", type="primary", use_container_width=True):
            st.session_state.subscription = new_sub
            st.session_state.landing_zone = new_lz
            tier_map = {"Auto-Detect": None, "SMB": "smb", "Mid-Market": "midmarket", "Enterprise": "enterprise"}
            pillar_map = {v["name"]: k for k, v in WAF_PILLARS.items()}
            with st.spinner("Running review..."):
                st.session_state.review_result = run_review(
                    tier_key=tier_map[tier_sel],
                    pillar_key=pillar_map.get(pillar_sel)
                )
            st.rerun()

# ════════════════════════ MAIN CONTENT ════════════════════════
with main_col:
    # Top header
    now = datetime.now().strftime("%b %d, %Y at %I:%M %p")
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
      padding:16px 4px 0;margin-bottom:4px;">
      <div>
        <div class="greeting-title">Hello, Architect 👋</div>
        <div class="greeting-sub">AI-powered review of your Azure environment</div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;">
        <button class="new-review-btn" onclick="">＋ New Review</button>
        <span style="font-size:20px;cursor:pointer;">🔔</span>
        <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#0078d4,#6f42c1);
          display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:14px;">A</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary Banner ──
    score_color_hex = "#ef4444" if score < 60 else "#f59e0b" if score < 80 else "#10b981"
    st.markdown(f"""
    <div class="summary-banner">
      <div>
        <div class="banner-title">Architecture Review Summary</div>
        <div class="banner-sub">Completed on {now}</div>
        <div style="display:flex;align-items:center;gap:30px;margin-top:16px;">
          <div class="score-ring-wrap">
            <div class="score-ring-num" style="color:{score_color_hex};">{score}</div>
            <div style="font-size:28px;color:{score_color_hex};line-height:0.8;">/100</div>
            <div class="score-ring-label">Overall Risk<br>Score</div>
          </div>
          <div class="stat-box"><div class="stat-num stat-critical">{critical_count}</div>
            <div class="stat-label">Critical Risks</div></div>
          <div class="stat-box"><div class="stat-num stat-high">{high_count}</div>
            <div class="stat-label">High Risks</div></div>
          <div class="stat-box"><div class="stat-num stat-medium">{medium_count}</div>
            <div class="stat-label">Medium Risks</div></div>
          <div class="stat-box"><div class="stat-num stat-low">{low_count}</div>
            <div class="stat-label">Low Risks</div></div>
        </div>
        <div style="margin-top:16px;">
          <button class="view-report-btn">📄 View Full Report</button>
        </div>
      </div>
      <div style="font-size:80px;opacity:0.6;">🤖</div>
    </div>
    """, unsafe_allow_html=True)

    # ── AI Agent Analysis ──
    st.markdown("""
    <div class="section-header" style="margin-top:20px;">
      <span class="section-title">AI Agent Analysis</span>
      <span class="section-link">View all agents →</span>
    </div>
    """, unsafe_allow_html=True)

    agent_cols = st.columns(4)
    for i, (cat, data) in enumerate(agent_results.items()):
        s = data["risk_score"]
        rlabel, rclass = score_to_risk_level(s)
        icon = agent_icons_html.get(cat, "🔷")
        icls = agent_icon_class.get(cat, "")
        with agent_cols[i]:
            st.markdown(f"""
            <div class="agent-card">
              <div class="agent-header">
                <div class="agent-icon {icls}">{icon}</div>
                <div class="agent-name">{cat} Agent</div>
              </div>
              <div class="agent-stat">Scanned {data['resources_scanned']} resources</div>
              <div class="agent-stat">Identified {data['risk_count']} risks</div>
              <div><span class="risk-badge {rclass}">{rlabel}</span></div>
              <div class="progress-bar-wrap">
                <div class="progress-bar-fill {fill_class.get(rlabel.split()[0],'fill-medium')}"
                  style="width:{s}%;"></div>
              </div>
              <div style="font-size:11px;color:#6b7280;text-align:right;margin-top:2px;">{s}%</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Top 5 Risks + Donut Chart ──
    risks_col, chart_col = st.columns([3, 2])

    with risks_col:
        st.markdown("""
        <div class="section-header" style="margin-top:20px;">
          <span class="section-title">Top 5 Risks</span>
          <span class="section-link">View all</span>
        </div>
        <div class="card" style="padding:8px 16px;">
        """, unsafe_allow_html=True)

        for i, r in enumerate(top5, 1):
            scls = sev_class.get(r["severity"], "sev-medium")
            st.markdown(f"""
            <div class="risk-row">
              <div class="risk-num">{i}</div>
              <div style="flex:1;">
                <div class="risk-title">{r['title']}</div>
                <div class="risk-desc">{r['description'][:70]}...</div>
              </div>
              <span class="sev-badge {scls}">{r['severity']}</span>
              <span style="font-size:16px;color:#9ca3af;cursor:pointer;">📋</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Expandable details
        for i, r in enumerate(top5, 1):
            with st.expander(f"Details: {r['title']}", expanded=False):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Category:** {r['category']}")
                c2.markdown(f"**Effort:** {r['effort']}")
                c3.markdown(f"**Impact:** {r['impact']}")
                st.markdown(f"**Remediation:** {r['remediation']}")
                if r.get("reference_url"):
                    st.markdown(f"[📖 Microsoft Reference]({r['reference_url']})")
                if r.get("estimated_savings", 0) > 0:
                    st.success(f"💰 Est. savings: ${r['estimated_savings']:,.0f}/mo")

    with chart_col:
        st.markdown("""
        <div class="section-header" style="margin-top:20px;">
          <span class="section-title">Risk by Category</span>
          <span class="section-link">View details</span>
        </div>
        """, unsafe_allow_html=True)

        cats = list(agent_results.keys())
        counts = [agent_results[c]["risk_count"] for c in cats]
        total_risks = sum(counts)

        fig = go.Figure(data=[go.Pie(
            labels=cats, values=counts, hole=0.62,
            marker=dict(colors=["#6f42c1", "#10b981", "#3b82f6", "#f59e0b"],
                        line=dict(color='#ffffff', width=2)),
            textinfo="none",
            hovertemplate="%{label}<br>%{value} risks (%{percent})<extra></extra>",
        )])
        fig.add_annotation(text=f"<b>{total_risks}</b>", x=0.5, y=0.55,
                           font_size=24, font_color="#1a1a2e", showarrow=False)
        fig.add_annotation(text="Total Risks", x=0.5, y=0.42,
                           font_size=11, font_color="#6b7280", showarrow=False)
        fig.update_layout(
            margin=dict(t=10, b=0, l=0, r=0), height=240,
            showlegend=True,
            legend=dict(orientation="v", x=0.75, y=0.5,
                        font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Recommended Blueprints ──
    st.markdown("""
    <div class="section-header" style="margin-top:8px;">
      <span class="section-title">Recommended Blueprint</span>
      <span style="font-size:12px;color:#6b7280;">Based on your environment profile</span>
    </div>
    """, unsafe_allow_html=True)

    bp_cols = st.columns(3)
    tiers_info = [
        ("🏪", "SMB Blueprint", "smb", "Optimized for small teams", "75%", False),
        ("🏢", "Mid-Market Blueprint", "midmarket", "Balanced scale & governance", "92%", True),
        ("🏙️", "Enterprise Blueprint", "enterprise", "Advanced scale & compliance", "80%", False),
    ]
    for col, (icon, name, key, desc, match, highlighted) in zip(bp_cols, tiers_info):
        is_active = key == active_tier or highlighted
        match_color = "#16a34a" if highlighted else "#0078d4"
        border_style = "border: 2px solid #0078d4; background:#f0f7ff;" if is_active else "border: 1px solid #e8ecf0;"
        with col:
            st.markdown(f"""
            <div style="{border_style} border-radius:12px;padding:16px;text-align:center;">
              <div style="font-size:28px;margin-bottom:6px;">{icon}</div>
              <div style="font-size:13px;font-weight:700;color:#1a1a2e;">{name}</div>
              <div style="font-size:11px;color:#6b7280;margin:4px 0;">{desc}</div>
              <div style="font-size:12px;font-weight:700;color:{match_color};margin-top:6px;">{match} Match</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Export ──
    st.markdown("<div style='margin-top:20px;'>", unsafe_allow_html=True)
    report_gen = ReportGenerator()
    exp_col1, exp_col2, _ = st.columns([1, 1, 2])
    with exp_col1:
        json_report = report_gen.generate_json(result)
        st.download_button("⬇️ Download ADR (JSON)", data=json_report,
                           file_name="azure_adr_report.json", mime="application/json",
                           use_container_width=True)
    with exp_col2:
        md_report = report_gen.generate_markdown(result)
        st.download_button("⬇️ Download ADR (Markdown)", data=md_report,
                           file_name="azure_adr_report.md", mime="text/markdown",
                           use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════ RIGHT CHAT PANEL ════════════════════════
with chat_col:
    waf_pillar_data = WAF_PILLARS.get(st.session_state.waf_focus, WAF_PILLARS["security"])

    st.markdown("""
    <div style="border-left:1px solid #e8ecf0;height:100%;padding:0;">
      <div style="display:flex;justify-content:space-between;align-items:center;
        padding:14px 12px;border-bottom:1px solid #e8ecf0;background:white;
        position:sticky;top:0;z-index:10;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:20px;">🤖</span>
          <span style="font-size:14px;font-weight:700;color:#1a1a2e;">Architecture Copilot</span>
        </div>
        <span style="font-size:16px;color:#9ca3af;cursor:pointer;">✕</span>
      </div>
    """, unsafe_allow_html=True)

    # Initial message
    st.markdown("""
    <div style="background:#f9fafb;border-radius:8px;padding:12px;margin:12px;
      font-size:13px;color:#374151;line-height:1.5;">
      Hi Architect! I've completed the review of your Azure environment. Here are the key insights.
    </div>
    <div style="font-size:13px;font-weight:600;color:#374151;margin:12px 12px 6px;">
      What would you like to do next?
    </div>
    """, unsafe_allow_html=True)

    quick_actions = [
        ("⚠️", "Show me the top risks"),
        ("💡", "Give me remediation plan"),
        ("🏛️", "Map to CAF framework"),
        ("📊", "Focus on Well-Architected pillars"),
    ]
    for icon, label in quick_actions:
        if st.button(f"{icon}  {label}", key=f"qa_{label}", use_container_width=True):
            st.session_state.chat_query = label

    # Chat response
    query = st.session_state.chat_query
    st.markdown("<hr style='margin:10px 12px;border-color:#f3f4f6;'>", unsafe_allow_html=True)

    with st.container():
        if "top risks" in query.lower():
            st.markdown("**🚨 Top Critical Risks:**")
            for r in top5[:3]:
                scls = sev_class.get(r["severity"], "sev-medium")
                st.markdown(f"""<div style="font-size:12px;padding:4px 0;border-bottom:1px solid #f3f4f6;">
                  <span class="sev-badge {scls}" style="padding:1px 6px;border-radius:3px;
                  font-size:10px;">{r['severity']}</span>&nbsp;{r['title']}</div>""",
                            unsafe_allow_html=True)
        elif "remediation" in query.lower():
            st.markdown("**🛠️ Prioritized Remediation:**")
            for i, r in enumerate(top5, 1):
                st.markdown(f"<div style='font-size:12px;padding:3px 0;'>{i}. <b>{r['title']}</b><br>"
                            f"<span style='color:#6b7280;'>{r['remediation'][:80]}...</span></div>",
                            unsafe_allow_html=True)
        elif "caf" in query.lower():
            st.markdown("**🏛️ CAF Alignment:**")
            st.markdown("""<div style='font-size:12px;color:#374151;'>Your environment maps to
              <b>Enterprise Scale Landing Zone</b>. Key areas: Management Groups,
              Policy-driven governance, Hub-Spoke networking.</div>""", unsafe_allow_html=True)
            st.markdown("[📖 CAF Enterprise Scale →](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/)")
        elif "well-architected" in query.lower():
            st.markdown("**🏛️ WAF Pillar Summary:**")
            for pk, pd in WAF_PILLARS.items():
                st.markdown(f"<div style='font-size:11px;padding:3px 0;'>{pd['icon']} <b>{pd['name']}</b></div>",
                            unsafe_allow_html=True)

    # Chat input
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    chat_input = st.chat_input("Ask me anything...", key="main_chat")
    if chat_input:
        st.session_state.chat_query = chat_input
        st.rerun()

    # WAF Pillars section
    st.markdown(f"""
    <div style="padding:14px 12px;border-top:1px solid #e8ecf0;margin-top:8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:13px;font-weight:700;color:#1a1a2e;">Well-Architected Pillars</span>
        <span style="font-size:12px;color:#0078d4;cursor:pointer;">Change</span>
      </div>
      <div style="font-size:11px;color:#6b7280;margin:4px 0 10px;">
        Current Focus: <b>{waf_pillar_data['name']}</b>
      </div>
      <div style="display:flex;gap:8px;">
    """, unsafe_allow_html=True)

    waf_cols = st.columns(5)
    waf_items = [
        ("reliability", "🛡️"), ("security", "🔐"),
        ("cost", "💰"), ("operational_excellence", "⚙️"), ("performance", "⚡"),
    ]
    for col, (pk, icon) in zip(waf_cols, waf_items):
        with col:
            is_active = pk == st.session_state.waf_focus
            bg = "background:#e8f4ff;border:2px solid #0078d4;" if is_active else "border:1px solid #e8ecf0;"
            if st.button(icon, key=f"waf_{pk}",
                         help=WAF_PILLARS[pk]["name"]):
                st.session_state.waf_focus = pk
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
