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

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  :root {
    --bg-primary:       #f8fafc;
    --bg-card:          #ffffff;
    --bg-sidebar:       #0f1923;
    --bg-sidebar-hover: #1c2a35;
    --bg-banner:        linear-gradient(135deg,#0d1b2a 0%,#1a2744 60%,#0f1f3d 100%);
    --bg-env-card:      #1c2a35;
    --border:           #e8ecf0;
    --border-sidebar:   #2d3f4e;
    --text-primary:     #1a1a2e;
    --text-secondary:   #6b7280;
    --text-sidebar:     #c9d1d9;
    --text-sidebar-dim: #8b949e;
    --accent-blue:      #0078d4;
    --accent-purple:    #6f42c1;
    --risk-critical:    #dc2626;
    --risk-high:        #d97706;
    --risk-medium:      #ca8a04;
    --risk-low:         #16a34a;
    --bg-critical:      #fee2e2;
    --bg-high:          #fef3c7;
    --bg-medium:        #fef9c3;
    --bg-low:           #dcfce7;
    --shadow:           0 1px 4px rgba(0,0,0,.08);
    --shadow-card:      0 2px 12px rgba(0,0,0,.06);
    --radius:           12px;
    --radius-sm:        8px;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --bg-primary:     #0d1117;
      --bg-card:        #161b22;
      --border:         #30363d;
      --text-primary:   #e6edf3;
      --text-secondary: #8b949e;
      --bg-critical:    #3d1515;
      --bg-high:        #3d2a00;
      --bg-medium:      #2d2600;
      --bg-low:         #0d2e1a;
      --shadow:         0 1px 4px rgba(0,0,0,.4);
      --shadow-card:    0 2px 12px rgba(0,0,0,.3);
    }
  }

  /* ── Hide Streamlit native header and deploy button ── */
  header[data-testid="stHeader"],
  [data-testid="stToolbar"],
  .stDeployButton,
  #MainMenu { display: none !important; }
  footer { visibility: hidden; }

  /* ── Base ── */
  html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
  }
  .block-container { padding: 1rem 1.5rem 2rem !important; max-width: 100% !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    min-width: 240px !important;
    max-width: 260px !important;
    border-right: 1px solid var(--border-sidebar) !important;
    padding-top: 0 !important;
  }
  [data-testid="stSidebar"] > div { padding-top: 0 !important; }
  [data-testid="stSidebar"] * { color: var(--text-sidebar) !important; }
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {
    color: #ffffff !important; font-size: 14px !important; font-weight: 700 !important;
  }
  /* Sidebar nav buttons */
  [data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: var(--text-sidebar-dim) !important;
    text-align: left !important;
    font-size: 13px !important;
    padding: 9px 12px !important;
    border-radius: 8px !important;
    width: 100% !important;
    justify-content: flex-start !important;
    transition: background 0.15s, color 0.15s !important;
    margin: 1px 0 !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    background: var(--bg-sidebar-hover) !important;
    color: #e6edf3 !important;
  }
  [data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)) !important;
    color: #ffffff !important;
  }
  [data-testid="stSidebar"] .stButton > button:focus { box-shadow: none !important; }
  [data-testid="stSidebar"] hr { border-color: var(--border-sidebar) !important; }
  [data-testid="stSidebar"] .stExpander {
    border-color: var(--border-sidebar) !important;
    background: transparent !important;
  }
  [data-testid="stSidebar"] .stTextInput input,
  [data-testid="stSidebar"] .stSelectbox select {
    background: var(--bg-env-card) !important;
    color: #e6edf3 !important;
    border-color: var(--border-sidebar) !important;
    font-size: 12px !important;
  }
  [data-testid="stSidebar"] label { color: var(--text-sidebar-dim) !important; font-size: 11px !important; }

  /* Environment card */
  .env-card {
    background: var(--bg-env-card); border-radius: var(--radius);
    padding: 14px; margin: 6px 4px;
    border: 1px solid var(--border-sidebar);
  }
  .env-label { font-size: 10px; color: var(--text-sidebar-dim); margin-bottom: 2px;
    text-transform: uppercase; letter-spacing: .5px; }
  .env-value { font-size: 13px; color: #e6edf3 !important; font-weight: 600; }
  .dot-connected { display:inline-block; width:7px; height:7px; border-radius:50%;
    background:#3fb950; margin-right:5px; vertical-align:middle; }

  /* ── Main area ── */
  .main-wrap { background: var(--bg-primary); }

  /* Greeting */
  .greeting-row {
    display:flex; justify-content:space-between; align-items:center;
    padding: 8px 0 10px; flex-wrap: wrap; gap: 10px; margin-bottom: 4px;
  }
  .greeting-title { font-size: clamp(18px,2.5vw,26px); font-weight: 800;
    color: var(--text-primary); margin:0; }
  .greeting-sub { font-size: 13px; color: var(--text-secondary); margin:0; }
  .action-btn {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    color: #fff !important; border: none; border-radius: var(--radius-sm);
    padding: 9px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
    white-space: nowrap; box-shadow: 0 2px 8px rgba(0,120,212,.3);
    transition: opacity .15s;
  }
  .action-btn:hover { opacity: .9; }

  /* ── Summary banner ── */
  .summary-banner {
    background: var(--bg-banner);
    border-radius: var(--radius); padding: clamp(16px,3vw,28px);
    margin: 4px 0 16px; position: relative; overflow: hidden;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,.25);
  }
  .banner-left { flex: 1; min-width: 260px; }
  .banner-title { font-size: 15px; font-weight: 700; color: #ffffff; }
  .banner-sub { font-size: 11px; color: #8b9dc3; margin-bottom: 16px; }
  .banner-stats { display: flex; align-items: center; gap: clamp(10px,2.5vw,24px); flex-wrap: nowrap; overflow-x: auto; }
  .score-block { text-align:center; }
  .score-num { font-size: clamp(28px,4vw,42px); font-weight: 900; line-height:1; }
  .score-denom { font-size: 16px; color: #8b9dc3; }
  .score-label { font-size: 10px; color: #8b9dc3; margin-top:2px;
    text-transform: uppercase; letter-spacing: .5px; }
  .stat-blk { text-align:center; padding: 0 6px; }
  .stat-n { font-size: clamp(18px,3vw,26px); font-weight: 800; line-height:1.1; }
  .stat-l { font-size: 10px; color: #8b9dc3; margin-top:2px;
    text-transform: uppercase; letter-spacing: .4px; }
  .n-crit { color: #ff6b6b; }
  .n-high { color: #ffa94d; }
  .n-med  { color: #ffd43b; }
  .n-low  { color: #69db7c; }
  .divider-v { width: 1px; height: 40px; background: rgba(255,255,255,.12); }
  .banner-robot { font-size: clamp(50px,8vw,90px); opacity:.7; flex-shrink:0; }

  /* ── Cards ── */
  .card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px;
    box-shadow: var(--shadow-card);
    transition: box-shadow .2s, transform .2s;
  }
  .card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.1); transform: translateY(-1px); }

  /* ── Section headers ── */
  .sec-hdr { display:flex; justify-content:space-between; align-items:center;
    margin: 16px 0 10px; }
  .sec-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
  .sec-link { font-size: 12px; color: var(--accent-blue); cursor: pointer; }

  /* ── Agent cards ── */
  .agent-card {
    background: #1a2235; border: 1px solid #2d3f4e;
    border-radius: var(--radius); padding: 16px;
    box-shadow: var(--shadow); transition: all .2s; height: 100%;
  }
  .agent-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.25); transform: translateY(-2px); }
  .agent-hdr { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
  .agent-ico {
    width:38px; height:38px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:18px; flex-shrink:0;
  }
  .ico-sec  { background: #1a2a4a; }
  .ico-cost { background: #0d2e20; }
  .ico-idn  { background: #2a1a4a; }
  .ico-rel  { background: #0d2030; }
  .agent-name { font-size: 14px; font-weight: 700; color: #e6edf3; }
  .agent-stat { font-size: 11px; color: #8b949e; margin: 2px 0; }

  /* Risk level labels inside agent cards */
  .risk-lbl {
    display:inline-block; padding: 3px 10px; border-radius: 4px;
    font-size: 11px; font-weight: 700; margin: 8px 0 4px;
  }
  .lbl-critical { background:#3d1515; color:#ff6b6b; }
  .lbl-high     { background:#3d2a00; color:#ffa94d; }
  .lbl-medium   { background:#2d2600; color:#ffd43b; }
  .lbl-low      { background:#0d2e1a; color:#69db7c; }

  .pbar-bg { background:#2d3748; border-radius:4px; height:6px; margin-top:8px; overflow:hidden; }
  .pbar-fill { height:6px; border-radius:4px; transition: width .6s ease; }
  .pbar-critical { background: #dc2626; }
  .pbar-high     { background: #d97706; }
  .pbar-medium   { background: #ca8a04; }
  .pbar-low      { background: #16a34a; }
  .pbar-blue     { background: var(--accent-blue); }
  .pct-label { font-size:10px; color:#8b949e; text-align:right; margin-top:2px; }

  /* ── Risk rows ── */
  .risk-row {
    display:flex; align-items:center; gap:10px; padding:10px 0;
    border-bottom: 1px solid var(--border);
  }
  .risk-row:last-child { border-bottom: none; }
  .risk-num {
    width:26px; height:26px; border-radius:50%;
    background:var(--bg-primary); border:1px solid var(--border);
    display:flex; align-items:center; justify-content:center;
    font-size:12px; font-weight:700; color:var(--text-primary); flex-shrink:0;
  }
  .risk-info { flex:1; min-width:0; }
  .risk-title { font-size:13px; font-weight:600; color:var(--text-primary);
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .risk-desc  { font-size:11px; color:var(--text-secondary); margin-top:1px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .sev-badge { padding:2px 10px; border-radius:4px; font-size:11px;
    font-weight:700; flex-shrink:0; white-space:nowrap; }
  .sev-Critical { background:var(--bg-critical); color:var(--risk-critical); }
  .sev-High     { background:var(--bg-high);     color:var(--risk-high); }
  .sev-Medium   { background:var(--bg-medium);   color:var(--risk-medium); }
  .sev-Low      { background:var(--bg-low);       color:var(--risk-low); }

  /* ── Blueprint cards ── */
  .bp-card {
    border: 1px solid var(--border); border-radius: var(--radius);
    padding: 16px; text-align:center;
    background: var(--bg-card); transition: all .2s;
  }
  .bp-card:hover { border-color: var(--accent-blue); transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,120,212,.12); }
  .bp-active { border: 2px solid var(--accent-blue) !important; background: #f0f7ff; }
  @media (prefers-color-scheme: dark) { .bp-active { background: #0d1e35 !important; } }
  .bp-icon { font-size: 28px; margin-bottom: 6px; }
  .bp-name { font-size: 13px; font-weight: 700; color: var(--text-primary); }
  .bp-desc { font-size: 11px; color: var(--text-secondary); margin: 4px 0; }
  .bp-match-good { font-size:12px; font-weight:700; color:var(--risk-low); }
  .bp-match-norm { font-size:12px; font-weight:700; color:var(--accent-blue); }

  /* ── Chat panel ── */
  .chat-panel {
    border-left: 1px solid var(--border); height: 100%;
    background: var(--bg-card);
  }
  .chat-panel-hdr {
    display:flex; justify-content:space-between; align-items:center;
    padding: 14px 12px; border-bottom: 1px solid var(--border);
    background: var(--bg-card); position: sticky; top: 0; z-index: 10;
    border-radius: var(--radius) var(--radius) 0 0;
  }
  .chat-hdr-title { font-size:14px; font-weight:700; color:var(--text-primary); }
  .chat-bubble {
    background: var(--bg-primary); border-radius: var(--radius-sm);
    padding:12px; margin:12px; font-size:13px; color:var(--text-primary);
    line-height:1.5; border: 1px solid var(--border);
  }
  .chat-prompt-hdr { font-size:13px; font-weight:600; color:var(--text-primary); margin:8px 12px 6px; }
  .waf-section { padding:12px; border-top:1px solid var(--border); }
  .waf-section-title { font-size:13px; font-weight:700; color:var(--text-primary); }
  .waf-focus-text { font-size:11px; color:var(--text-secondary); margin:2px 0 8px; }

  /* ── Responsive ── */
  @media (max-width: 1100px) {
    [data-testid="stSidebar"] { min-width: 200px !important; max-width: 200px !important; }
    .banner-robot { display: none; }
  }
  @media (max-width: 768px) {
    .banner-stats { gap: 8px; }
    .score-num { font-size: 24px; }
    .stat-n { font-size: 18px; }
    .greeting-title { font-size: 18px; }
    .block-container { padding: 0.5rem !important; }
  }

  /* ── Streamlit component overrides ── */
  .stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)) !important;
    color: white !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important; font-size: 13px !important;
    padding: 10px 16px !important;
    box-shadow: 0 2px 8px rgba(0,120,212,.25) !important;
    transition: opacity .15s !important; width: 100% !important;
  }
  .stDownloadButton > button:hover { opacity: .88 !important; }

  .streamlit-expanderHeader {
    font-size: 13px !important; color: var(--text-primary) !important;
    background: var(--bg-primary) !important;
    border-radius: var(--radius-sm) !important;
  }
  .stChatInput { border-radius: var(--radius-sm) !important; }
  .stChatInput > div { border-color: var(--border) !important; }

  /* Main area vertical column gap */
  [data-testid="stHorizontalBlock"] { gap: 0 !important; }
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

agent_icons = {"Security": "🛡️", "Cost": "💰", "Identity": "👤", "Reliability": "☁️"}
agent_ico_cls = {"Security": "ico-sec", "Cost": "ico-cost", "Identity": "ico-idn", "Reliability": "ico-rel"}

def score_to_risk_level(s):
    if s < 60: return "Critical Risk", "critical"
    if s < 75: return "High Risk", "high"
    if s < 90: return "Medium Risk", "medium"
    return "Low Risk", "low"

# ════════════════════════ SIDEBAR (st.sidebar) ════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 10px 8px;">
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

    st.markdown("<hr style='border-color:#2d3f4e;margin:4px 0 6px;'>", unsafe_allow_html=True)

    nav_items = [
        ("🏠", "Overview"), ("⚠️", "Risk Dashboard"), ("📋", "Findings"),
        ("💡", "Recommendations"), ("🏗️", "Blueprints"),
        ("🏛️", "Well-Architected Pillars"), ("📊", "Reports"), ("⚙️", "Settings"),
    ]
    for icon, label in nav_items:
        is_active = st.session_state.active_nav == label
        if st.button(f"{icon}  {label}", key=f"nav_{label}",
                     use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.active_nav = label
            st.rerun()

    st.markdown("<hr style='border-color:#2d3f4e;margin:10px 0 6px;'>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="env-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span style="font-size:13px;font-weight:700;color:#e6edf3;">Environment</span>
        <span><span class="dot-connected"></span>
          <span style="font-size:11px;color:#3fb950;">Connected</span></span>
      </div>
      <div class="env-label">SUBSCRIPTION</div>
      <div class="env-value">{st.session_state.subscription}</div>
      <div class="env-label" style="margin-top:8px;">LANDING ZONE</div>
      <div class="env-value">{st.session_state.landing_zone}</div>
    </div>
    """, unsafe_allow_html=True)

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

# ════════════════════════ MAIN + CHAT COLUMNS ════════════════════════
main_col, chat_col = st.columns([3.2, 1.3])

# ════════════════════════ MAIN CONTENT ════════════════════════
with main_col:
    now = datetime.now().strftime("%b %d, %Y at %I:%M %p")

    # ── Greeting row ──
    st.markdown(f"""
    <div class="greeting-row">
      <div>
        <div class="greeting-title">Hello, Architect 👋</div>
        <div class="greeting-sub">AI-powered review of your Azure environment</div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <button class="action-btn">＋ New Review</button>
        <span style="font-size:20px;cursor:pointer;opacity:.7;">🔔</span>
        <div style="width:34px;height:34px;border-radius:50%;
          background:linear-gradient(135deg,#0078d4,#6f42c1);
          display:flex;align-items:center;justify-content:center;
          color:white;font-weight:700;font-size:13px;">A</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary Banner ──
    score_hex = "#ef4444" if score < 60 else "#f59e0b" if score < 80 else "#10b981"
    st.markdown(f"""
    <div class="summary-banner">
      <div class="banner-left">
        <div class="banner-title">Architecture Review Summary</div>
        <div class="banner-sub">Completed on {now}</div>
        <div class="banner-stats">
          <div class="score-block">
            <div class="score-num" style="color:{score_hex};">{score}<span class="score-denom">/100</span></div>
            <div class="score-label">Overall Risk Score</div>
          </div>
          <div class="divider-v"></div>
          <div class="stat-blk"><div class="stat-n n-crit">{critical_count}</div><div class="stat-l">Critical</div></div>
          <div class="stat-blk"><div class="stat-n n-high">{high_count}</div><div class="stat-l">High</div></div>
          <div class="stat-blk"><div class="stat-n n-med">{medium_count}</div><div class="stat-l">Medium</div></div>
          <div class="stat-blk"><div class="stat-n n-low">{low_count}</div><div class="stat-l">Low</div></div>
          <div class="divider-v"></div>
          <div class="stat-blk">
            <div class="stat-n" style="color:#51cf66;">${savings:,.0f}</div>
            <div class="stat-l">Est. Monthly Savings</div>
          </div>
        </div>
        <div style="margin-top:16px;">
          <button style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
            color:white;border-radius:8px;padding:8px 16px;font-size:12px;cursor:pointer;">
            📄 View Full Report
          </button>
        </div>
      </div>
      <div class="banner-robot">🤖</div>
    </div>
    """, unsafe_allow_html=True)

    # ── AI Agent Analysis ──
    st.markdown("""
    <div class="sec-hdr">
      <span class="sec-title">AI Agent Analysis</span>
      <span class="sec-link">View all agents →</span>
    </div>
    """, unsafe_allow_html=True)

    agent_cols = st.columns(4)
    for i, (cat, data) in enumerate(agent_results.items()):
        s = data["risk_score"]
        rlabel, rkey = score_to_risk_level(s)
        icon = agent_icons.get(cat, "🔷")
        icls = agent_ico_cls.get(cat, "")
        with agent_cols[i]:
            st.markdown(f"""
            <div class="agent-card">
              <div class="agent-hdr">
                <div class="agent-ico {icls}">{icon}</div>
                <span class="agent-name">{cat} Agent</span>
              </div>
              <div class="agent-stat">Scanned {data['resources_scanned']} resources</div>
              <div class="agent-stat">Identified {data['risk_count']} risks</div>
              <div><span class="risk-lbl lbl-{rkey}">{rlabel}</span></div>
              <div class="pbar-bg"><div class="pbar-fill pbar-{rkey}" style="width:{s}%;"></div></div>
              <div class="pct-label">{s}%</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Top 5 Risks + Chart ──
    risks_col, chart_col2 = st.columns([3, 2])

    with risks_col:
        st.markdown("""
        <div class="sec-hdr">
          <span class="sec-title">Top 5 Risks</span>
          <span class="sec-link">View all</span>
        </div>
        <div class="card" style="padding:4px 16px;">
        """, unsafe_allow_html=True)

        for i, r in enumerate(top5, 1):
            sev = r["severity"]
            st.markdown(f"""
            <div class="risk-row">
              <div class="risk-num">{i}</div>
              <div class="risk-info">
                <div class="risk-title">{r['title']}</div>
                <div class="risk-desc">{r['description'][:72]}...</div>
              </div>
              <span class="sev-badge sev-{sev}">{sev}</span>
              <span style="font-size:15px;color:var(--text-secondary);cursor:pointer;">📋</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

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

    with chart_col2:
        st.markdown("""
        <div class="sec-hdr">
          <span class="sec-title">Risk by Category</span>
          <span class="sec-link">View details</span>
        </div>
        """, unsafe_allow_html=True)

        cats = list(agent_results.keys())
        counts = [agent_results[c]["risk_count"] for c in cats]
        total_risks = sum(counts)

        fig = go.Figure(data=[go.Pie(
            labels=cats, values=counts, hole=0.62,
            marker=dict(colors=["#6f42c1", "#10b981", "#3b82f6", "#f59e0b"],
                        line=dict(color='rgba(0,0,0,0)', width=2)),
            textinfo="none",
            hovertemplate="%{label}<br>%{value} risks (%{percent})<extra></extra>",
        )])
        fig.add_annotation(text=f"<b>{total_risks}</b>", x=0.5, y=0.55,
                           font_size=24, font_color="#e6edf3", showarrow=False)
        fig.add_annotation(text="Total Risks", x=0.5, y=0.42,
                           font_size=11, font_color="#8b949e", showarrow=False)
        fig.update_layout(
            margin=dict(t=10, b=0, l=0, r=0), height=240,
            showlegend=True,
            legend=dict(orientation="v", x=0.72, y=0.5,
                        font=dict(size=11, color="#e6edf3"),
                        bgcolor="rgba(0,0,0,0)"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Recommended Blueprints ──
    st.markdown("""
    <div class="sec-hdr" style="margin-top:8px;">
      <span class="sec-title">Recommended Blueprint</span>
      <span style="font-size:12px;color:var(--text-secondary);">Based on your environment profile</span>
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
        match_cls = "bp-match-good" if highlighted else "bp-match-norm"
        card_cls = "bp-card bp-active" if is_active else "bp-card"
        with col:
            st.markdown(f"""
            <div class="{card_cls}">
              <div class="bp-icon">{icon}</div>
              <div class="bp-name">{name}</div>
              <div class="bp-desc">{desc}</div>
              <div class="{match_cls}">{match} Match</div>
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
    <div class="chat-panel-hdr">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:20px;">🤖</span>
        <span class="chat-hdr-title">Architecture Copilot</span>
      </div>
      <span style="font-size:16px;color:#9ca3af;cursor:pointer;">✕</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="chat-bubble">
      Hi Architect! I've completed the review of your Azure environment. Here are the key insights.
    </div>
    <div class="chat-prompt-hdr">What would you like to do next?</div>
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

    st.markdown("<hr style='margin:8px 0;border-color:var(--border);'>", unsafe_allow_html=True)

    query = st.session_state.chat_query
    if "top risks" in query.lower():
        st.markdown("**🚨 Top Critical Risks:**")
        for r in top5[:3]:
            sev = r["severity"]
            st.markdown(
                f'<div style="font-size:12px;padding:4px 0;border-bottom:1px solid var(--border);">'
                f'<span class="sev-badge sev-{sev}" style="padding:1px 6px;font-size:10px;">{sev}</span>'
                f'&nbsp;{r["title"]}</div>',
                unsafe_allow_html=True)
    elif "remediation" in query.lower():
        st.markdown("**🛠️ Prioritized Remediation:**")
        for i, r in enumerate(top5, 1):
            st.markdown(
                f"<div style='font-size:12px;padding:3px 0;'>{i}. <b>{r['title']}</b><br>"
                f"<span style='color:var(--text-secondary);'>{r['remediation'][:80]}...</span></div>",
                unsafe_allow_html=True)
    elif "caf" in query.lower():
        st.markdown("**🏛️ CAF Alignment:**")
        st.markdown(
            "<div style='font-size:12px;'>Your environment maps to <b>Enterprise Scale Landing Zone</b>. "
            "Key areas: Management Groups, Policy-driven governance, Hub-Spoke networking.</div>",
            unsafe_allow_html=True)
        st.markdown("[📖 CAF Enterprise Scale →](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/)")
    elif "well-architected" in query.lower():
        st.markdown("**🏛️ WAF Pillar Summary:**")
        for pk, pd in WAF_PILLARS.items():
            st.markdown(
                f"<div style='font-size:11px;padding:3px 0;'>{pd['icon']} <b>{pd['name']}</b></div>",
                unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    chat_input = st.chat_input("Ask me anything...", key="main_chat")
    if chat_input:
        st.session_state.chat_query = chat_input
        st.rerun()

    # WAF Pillars section
    st.markdown(f"""
    <div class="waf-section">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="waf-section-title">Well-Architected Pillars</span>
        <span style="font-size:12px;color:var(--accent-blue);cursor:pointer;">Change</span>
      </div>
      <div class="waf-focus-text">Current Focus: <b>{waf_pillar_data['name']}</b></div>
    </div>
    """, unsafe_allow_html=True)

    waf_cols = st.columns(5)
    waf_items = [
        ("reliability", "🛡️"), ("security", "🔐"),
        ("cost", "💰"), ("operational_excellence", "⚙️"), ("performance", "⚡"),
    ]
    for col, (pk, icon) in zip(waf_cols, waf_items):
        with col:
            is_active = pk == st.session_state.waf_focus
            if st.button(icon, key=f"waf_{pk}", help=WAF_PILLARS[pk]["name"]):
                st.session_state.waf_focus = pk
                st.rerun()
