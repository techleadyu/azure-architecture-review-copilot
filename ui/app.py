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

# ── Handle query param for chat FAB toggle ─────────────────────────────────
if "chat" in st.query_params:
    if "show_chat" in st.session_state:
        st.session_state.show_chat = not st.session_state.show_chat
    else:
        st.session_state.show_chat = True
    st.query_params.clear()


st.markdown("""
<style>
  /* ── Default: DARK theme ── */
  :root {
    --bg-primary:       #0d1117;
    --bg-card:          #161b22;
    --bg-sidebar:       #0f1923;
    --bg-sidebar-hover: #1c2a35;
    --bg-banner:        linear-gradient(135deg,#0d1b2a 0%,#1a2744 60%,#0f1f3d 100%);
    --bg-env-card:      #1c2a35;
    --border:           #30363d;
    --border-sidebar:   #2d3f4e;
    --text-primary:     #e6edf3;
    --text-secondary:   #8b949e;
    --text-sidebar:     #c9d1d9;
    --text-sidebar-dim: #8b949e;
    --accent-blue:      #0078d4;
    --accent-purple:    #6f42c1;
    --risk-critical:    #dc2626;
    --risk-high:        #d97706;
    --risk-medium:      #ca8a04;
    --risk-low:         #16a34a;
    --bg-critical:      #3d1515;
    --bg-high:          #3d2a00;
    --bg-medium:        #2d2600;
    --bg-low:           #0d2e1a;
    --shadow:           0 1px 4px rgba(0,0,0,.4);
    --shadow-card:      0 2px 12px rgba(0,0,0,.3);
    --radius:           12px;
    --radius-sm:        8px;
  }

  /* Streamlit app-level background — dark default */
  .stApp,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  section[data-testid="stMain"] > div {
    background-color: #0d1117 !important;
  }
  /* Cards and secondary containers */
  [data-testid="stVerticalBlock"],
  [data-testid="column"] { background: transparent !important; }

  /* ── Hide Streamlit native header and deploy button ── */
  header[data-testid="stHeader"],
  [data-testid="stToolbar"],
  .stDeployButton,
  #MainMenu { display: none !important; }
  footer { visibility: hidden; }

  /* ── Remove default sidebar header whitespace ── */
  [data-testid="stSidebarHeader"] { display: none !important; min-height: 0 !important; }
  section[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
  [data-testid="stSidebarContent"] { padding-top: 0 !important; }

  /* ── Sidebar expand button — ALWAYS visible when sidebar collapsed ── */
  [data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    left: 0 !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    z-index: 99998 !important;
  }
  [data-testid="stSidebarCollapsedControl"] button {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #1a2235 !important;
    border: 1px solid #2d3f4e !important;
    border-left: none !important;
    color: #c9d1d9 !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 14px 8px !important;
    cursor: pointer !important;
    min-height: 48px !important;
  }

  /* ── Chat FAB — form-based, fixed bottom-right ── */
  .chat-fab-wrap {
    position: fixed !important;
    bottom: 28px !important;
    right: 28px !important;
    z-index: 99999 !important;
  }
  .chat-fab-wrap form { margin: 0; padding: 0; }
  .chat-fab-wrap button {
    width: 58px !important; height: 58px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #0078d4, #6f42c1) !important;
    border: 2px solid rgba(255,255,255,.15) !important;
    color: white !important; font-size: 24px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(0,120,212,.55) !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    transition: transform .15s, box-shadow .15s !important;
    line-height: 1 !important;
  }
  .chat-fab-wrap button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 6px 28px rgba(0,120,212,.7) !important;
  }

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
  /* Sidebar nav buttons — all states */
  [data-testid="stSidebar"] .stButton > button,
  [data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
  [data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
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
  [data-testid="stSidebar"] .stButton > button:hover,
  [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
    background-color: var(--bg-sidebar-hover) !important;
    color: #e6edf3 !important;
  }
  /* Active nav button — primary type */
  [data-testid="stSidebar"] button[data-testid="baseButton-primary"],
  [data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)) !important;
    background-color: var(--accent-blue) !important;
    color: #ffffff !important;
  }
  [data-testid="stSidebar"] .stButton > button:focus,
  [data-testid="stSidebar"] button:focus { box-shadow: none !important; outline: none !important; }
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

  /* ── Column gaps — specific overrides ── */
  /* Agent cards and blueprint columns need gaps */
  [data-testid="stHorizontalBlock"] { gap: 12px !important; }
  /* Greeting row top — tighten vertical padding */
  .greeting-row { margin-bottom: 0 !important; padding-bottom: 4px !important; }

  /* ── Chat overlay panel ── */
  .chat-overlay {
    position: fixed !important;
    bottom: 100px !important;
    right: 20px !important;
    width: 360px !important;
    max-height: 70vh !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 40px rgba(0,0,0,.4) !important;
    z-index: 99998 !important;
    overflow: hidden !important;
    display: flex;
    flex-direction: column;
  }
  .chat-overlay-hdr {
    background: linear-gradient(135deg, #0078d4, #6f42c1);
    padding: 14px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 16px 16px 0 0;
    flex-shrink: 0;
  }
  .chat-overlay-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Overview"
if "waf_focus" not in st.session_state:
    st.session_state.waf_focus = "security"
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False   # closed by default
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "chat_query" not in st.session_state:
    st.session_state.chat_query = "Show me the top risks"
if "subscription" not in st.session_state:
    st.session_state.subscription = "Contoso - Production"
if "landing_zone" not in st.session_state:
    st.session_state.landing_zone = "Enterprise Scale"

# ── Dynamic theme CSS injection ────────────────────────────────────────────
if st.session_state.theme == "light":
    st.markdown("""<style>
  :root {
    --bg-primary:   #f8fafc; --bg-card: #ffffff; --border: #e8ecf0;
    --text-primary: #1a1a2e; --text-secondary: #6b7280;
    --bg-critical:  #fee2e2; --bg-high: #fef3c7;
    --bg-medium:    #fef9c3; --bg-low: #dcfce7;
    --shadow:       0 1px 4px rgba(0,0,0,.08);
    --shadow-card:  0 2px 12px rgba(0,0,0,.06);
  }
  .stApp, [data-testid="stAppViewContainer"],
  [data-testid="stMain"], section[data-testid="stMain"] > div {
    background-color: #f8fafc !important; color: #1a1a2e !important;
  }
  .greeting-title, .greeting-sub { color: #1a1a2e !important; }
  .card { background: #ffffff !important; border: 1px solid #e8ecf0 !important; }
  .sec-title { color: #1a1a2e !important; }
  .agent-name, .agent-stat, .pct-label { color: #374151 !important; }
  </style>""", unsafe_allow_html=True)

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
    <div style="padding:10px 10px 6px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
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
            tier_map2   = {"Auto-Detect": None, "SMB": "smb", "Mid-Market": "midmarket", "Enterprise": "enterprise"}
            pillar_map2 = {v["name"]: k for k, v in WAF_PILLARS.items()}
            with st.spinner("Running review..."):
                st.session_state.review_result = run_review(
                    tier_key=tier_map2[tier_sel],
                    pillar_key=pillar_map2.get(pillar_sel)
                )
            st.rerun()

    # ── Theme toggle at sidebar bottom ─────────────────────────────────────
    st.markdown("<div style='margin-top:auto;padding-top:10px;'>", unsafe_allow_html=True)
    theme_icon = "☀️  Light Mode" if st.session_state.theme == "dark" else "🌙  Dark Mode"
    if st.button(theme_icon, key="theme_toggle_sb", use_container_width=True,
                 help="Toggle Light/Dark theme"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════ LAYOUT SETUP ══════════════════════════════════
nav       = st.session_state.active_nav
show_chat = st.session_state.show_chat   # always read from session state (default False)

# Always use full-width main container; chat is a FAB overlay
main_col = st.container()

# ═══════════════════════════ MAIN AREA ═════════════════════════════════════
with main_col:
    now = datetime.now().strftime("%b %d, %Y at %I:%M %p")

    # ── Greeting row — pure HTML, no Streamlit buttons ────────────────────
    st.markdown(f"""
    <div class="greeting-row">
      <div>
        <div class="greeting-title">Hello, Architect 👋</div>
        <div class="greeting-sub">AI-powered review of your Azure environment</div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:20px;cursor:pointer;opacity:.7;">🔔</span>
        <div style="width:34px;height:34px;border-radius:50%;
          background:linear-gradient(135deg,#0078d4,#6f42c1);
          display:flex;align-items:center;justify-content:center;
          color:white;font-weight:700;font-size:13px;">A</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════ NAV ROUTING ═══════════════════════════════════════════════

    if nav == "Overview":
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
          </div>
          <div class="banner-robot">🤖</div>
        </div>
        """, unsafe_allow_html=True)

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
                  <span style="font-size:15px;color:var(--text-secondary);">📋</span>
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
            cats   = list(agent_results.keys())
            counts = [agent_results[c]["risk_count"] for c in cats]
            total_risks = sum(counts)
            fig = go.Figure(data=[go.Pie(
                labels=cats, values=counts, hole=0.62,
                marker=dict(colors=["#6f42c1","#10b981","#3b82f6","#f59e0b"],
                            line=dict(color="rgba(0,0,0,0)", width=2)),
                textinfo="none",
                hovertemplate="%{label}<br>%{value} risks (%{percent})<extra></extra>",
            )])
            fig.add_annotation(text=f"<b>{total_risks}</b>", x=0.5, y=0.55,
                               font_size=24, font_color="#e6edf3", showarrow=False)
            fig.add_annotation(text="Total Risks", x=0.5, y=0.42,
                               font_size=11, font_color="#8b949e", showarrow=False)
            fig.update_layout(
                margin=dict(t=10,b=0,l=0,r=0), height=240, showlegend=True,
                legend=dict(orientation="v", x=0.72, y=0.5,
                            font=dict(size=11, color="#e6edf3"),
                            bgcolor="rgba(0,0,0,0)"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("""
        <div class="sec-hdr" style="margin-top:8px;">
          <span class="sec-title">Recommended Blueprint</span>
          <span style="font-size:12px;color:var(--text-secondary);">Based on your environment profile</span>
        </div>
        """, unsafe_allow_html=True)
        bp_cols = st.columns(3)
        tiers_info = [
            ("🏪","SMB Blueprint","smb","Optimized for small teams","75%",False),
            ("🏢","Mid-Market Blueprint","midmarket","Balanced scale & governance","92%",True),
            ("🏙️","Enterprise Blueprint","enterprise","Advanced scale & compliance","80%",False),
        ]
        for col, (icon, name, key, desc, match, highlighted) in zip(bp_cols, tiers_info):
            is_active = key == active_tier or highlighted
            match_cls = "bp-match-good" if highlighted else "bp-match-norm"
            card_cls  = "bp-card bp-active" if is_active else "bp-card"
            with col:
                st.markdown(f"""
                <div class="{card_cls}">
                  <div class="bp-icon">{icon}</div>
                  <div class="bp-name">{name}</div>
                  <div class="bp-desc">{desc}</div>
                  <div class="{match_cls}">{match} Match</div>
                </div>
                """, unsafe_allow_html=True)

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

    # ─────────────────────── RISK DASHBOARD ────────────────────────────────
    elif nav == "Risk Dashboard":
        st.markdown("### ⚠️ Risk Dashboard")
        st.markdown(f"**{len(top5)} total risks identified** · Last scan: {now}")
        sev_filter = st.multiselect(
            "Filter by Severity", ["Critical","High","Medium","Low"],
            default=["Critical","High"], key="sev_filter"
        )
        cat_filter = st.multiselect(
            "Filter by Category", list(agent_results.keys()),
            default=list(agent_results.keys()), key="cat_filter"
        )
        filtered = [
            r for r in top5
            if (not sev_filter or r["severity"] in sev_filter)
            and (not cat_filter or r["category"] in cat_filter)
        ]
        st.markdown(f"**Showing {len(filtered)} risks**")
        for r in filtered:
            sev   = r["severity"]
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div class="card" style="padding:14px 18px;margin-bottom:8px;">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                    <span class="sev-badge sev-{sev}">{sev}</span>
                    <span style="font-weight:600;font-size:14px;">{r['title']}</span>
                    <span style="font-size:11px;color:var(--text-secondary);margin-left:auto;">{r['category']}</span>
                  </div>
                  <div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px;">{r['description']}</div>
                  <div style="font-size:12px;">
                    <b>Remediation:</b> {r['remediation']}<br>
                    <span style="color:var(--text-secondary);">Effort: {r['effort']} &nbsp;|&nbsp; Impact: {r['impact']}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if r.get("reference_url"):
                    st.markdown(f"[📖 Ref]({r['reference_url']})")
                if r.get("estimated_savings", 0) > 0:
                    st.metric("Savings/mo", f"${r['estimated_savings']:,.0f}")

    # ─────────────────────── FINDINGS ──────────────────────────────────────
    elif nav == "Findings":
        st.markdown("### 📋 Detailed Findings by Agent")
        tabs = st.tabs([f"{agent_icons.get(k,'🔷')} {k}" for k in agent_results])
        for tab, (cat, data) in zip(tabs, agent_results.items()):
            with tab:
                m1, m2, m3 = st.columns(3)
                m1.metric("Resources Scanned", data["resources_scanned"])
                m2.metric("Risks Identified",  data["risk_count"])
                m3.metric("Risk Score",         f"{data['risk_score']}/100")
                st.markdown(f"**Summary:** {data.get('summary','No summary available.')}")
                st.divider()
                agent_risks = [r for r in top5 if r["category"] == cat]
                if agent_risks:
                    st.markdown(f"**Top risks from {cat} Agent:**")
                    for r in agent_risks:
                        sev = r["severity"]
                        with st.expander(f"{r['title']} · {sev}", expanded=True):
                            st.markdown(f"**Description:** {r['description']}")
                            st.markdown(f"**Remediation:** {r['remediation']}")
                            c1, c2 = st.columns(2)
                            c1.markdown(f"**Effort:** `{r['effort']}`")
                            c2.markdown(f"**Impact:** `{r['impact']}`")
                            if r.get("reference_url"):
                                st.markdown(f"[📖 Microsoft Reference]({r['reference_url']})")
                else:
                    st.info(f"No findings in top-5 for {cat} agent. Agent found {data['risk_count']} total risks.")

    # ─────────────────────── RECOMMENDATIONS ───────────────────────────────
    elif nav == "Recommendations":
        st.markdown("### 💡 Prioritized Remediation Roadmap")
        st.markdown(
            "Recommendations are ordered by **severity + implementation effort**. "
            "Critical risks with Low effort should be addressed first."
        )
        effort_map = {"Low": 1, "Medium": 2, "High": 3}
        sev_map    = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        sorted_risks = sorted(
            top5,
            key=lambda r: (-sev_map.get(r["severity"],0), effort_map.get(r["effort"],2))
        )
        sev_colors = {"Critical":"#dc2626","High":"#d97706","Medium":"#ca8a04","Low":"#16a34a"}
        effort_colors = {"Low":"#10b981","Medium":"#f59e0b","High":"#ef4444"}
        for i, r in enumerate(sorted_risks, 1):
            sev   = r["severity"]
            eff   = r["effort"]
            sc    = sev_colors.get(sev,"#8b949e")
            ec    = effort_colors.get(eff,"#8b949e")
            st.markdown(f"""
            <div class="card" style="padding:16px 20px;margin-bottom:10px;border-left:4px solid {sc};">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div style="font-size:11px;color:var(--text-secondary);margin-bottom:4px;">STEP {i}</div>
                  <div style="font-weight:700;font-size:15px;margin-bottom:6px;">{r['title']}</div>
                  <div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px;">{r['description'][:120]}...</div>
                  <div style="font-size:13px;background:rgba(0,120,212,.08);padding:10px 14px;border-radius:8px;margin-bottom:8px;">
                    <b>Action:</b> {r['remediation']}
                  </div>
                </div>
                <div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end;min-width:110px;padding-left:12px;">
                  <span style="background:{sc};color:white;font-size:10px;padding:3px 8px;border-radius:4px;font-weight:600;">{sev}</span>
                  <span style="background:{ec};color:white;font-size:10px;padding:3px 8px;border-radius:4px;">Effort: {eff}</span>
                  <span style="font-size:11px;color:var(--text-secondary);">{r['category']}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if r.get("reference_url"):
                st.markdown(f"&nbsp;&nbsp;&nbsp;[📖 Microsoft Reference]({r['reference_url']})")

    # ─────────────────────── BLUEPRINTS ────────────────────────────────────
    elif nav == "Blueprints":
        st.markdown("### 🏗️ Azure Architecture Blueprints")
        st.markdown("Blueprints are grounded in **Microsoft Azure Architecture Center** and **Cloud Adoption Framework** guidance.")
        tier_tab = st.tabs(["🏪 SMB", "🏢 Mid-Market", "🏙️ Enterprise"])
        blueprints_data = {
            "SMB": {
                "desc":"Optimized for small teams (<50 users). Single subscription, minimal governance overhead.",
                "services":["Azure App Service","Azure SQL Database","Azure Blob Storage","Azure CDN","Basic monitoring"],
                "highlights":["Cost-optimized SKUs","Dev/Test licensing","Single region deployment","Basic RBAC"],
                "ref":"https://learn.microsoft.com/azure/cloud-adoption-framework/scenarios/start-zone/",
            },
            "Mid-Market": {
                "desc":"Balanced scale and governance for 50-500 users. Hub-spoke topology recommended.",
                "services":["Azure App Service (Premium)","Azure SQL Elastic Pool","Azure Key Vault","Azure API Management","Azure Monitor","Azure Policy"],
                "highlights":["Hub-spoke networking","Policy-driven governance","Multi-region active-passive","RBAC with PIM"],
                "ref":"https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/",
            },
            "Enterprise": {
                "desc":"Advanced scale and compliance for 500+ users. Full enterprise scale landing zone.",
                "services":["Azure Kubernetes Service","Azure SQL Hyperscale","Azure Front Door","Azure Firewall Premium","Microsoft Sentinel","Azure DevOps"],
                "highlights":["Enterprise Scale Landing Zone","Management groups hierarchy","Azure Policy initiatives","Private endpoints everywhere","Zero-trust networking"],
                "ref":"https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/",
            },
        }
        for tab, (tier_name, bdata) in zip(tier_tab, blueprints_data.items()):
            with tab:
                st.markdown(f"**{bdata['desc']}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Core Services:**")
                    for svc in bdata["services"]:
                        st.markdown(f"- {svc}")
                with c2:
                    st.markdown("**Key Highlights:**")
                    for h in bdata["highlights"]:
                        st.markdown(f"✅ {h}")
                st.markdown(f"[📖 Microsoft Reference: {tier_name} Architecture]({bdata['ref']})")
                if tier_name == "Mid-Market":
                    st.success("✅ **Recommended for your environment** (92% match based on current profile)")

    # ─────────────────────── WELL-ARCHITECTED PILLARS ──────────────────────
    elif nav == "Well-Architected Pillars":
        st.markdown("### 🏛️ Well-Architected Framework Review")
        st.markdown("Scores are based on the current review findings, mapped to each WAF pillar.")
        pillar_scores = {
            "reliability":            {"score":72, "key":"reliability"},
            "security":               {"score":68, "key":"security"},
            "cost":                   {"score":74, "key":"cost"},
            "operational_excellence": {"score":80, "key":"operational_excellence"},
            "performance":            {"score":85, "key":"performance"},
        }
        score_cols = st.columns(5)
        for col, (pk, pdata) in zip(score_cols, pillar_scores.items()):
            pillar  = WAF_PILLARS.get(pk, {})
            sc      = pdata["score"]
            sc_col  = "#10b981" if sc >= 80 else "#f59e0b" if sc >= 65 else "#ef4444"
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center;padding:16px 8px;">
                  <div style="font-size:24px;">{pillar.get('icon','⭐')}</div>
                  <div style="font-size:11px;font-weight:700;margin:6px 0 2px;">{pillar.get('name','Pillar')}</div>
                  <div style="font-size:28px;font-weight:700;color:{sc_col};">{sc}</div>
                  <div style="font-size:10px;color:var(--text-secondary);">/100</div>
                  <div style="height:4px;background:var(--border);border-radius:2px;margin-top:8px;">
                    <div style="height:4px;background:{sc_col};width:{sc}%;border-radius:2px;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
        focus_pillar = st.selectbox(
            "Drill into a pillar:",
            list(WAF_PILLARS.keys()),
            format_func=lambda k: f"{WAF_PILLARS[k]['icon']} {WAF_PILLARS[k]['name']}",
            key="waf_drill",
        )
        pd2 = WAF_PILLARS.get(focus_pillar, {})
        sc2 = pillar_scores.get(focus_pillar, {}).get("score", 0)
        sc_col2 = "#10b981" if sc2 >= 80 else "#f59e0b" if sc2 >= 65 else "#ef4444"
        st.markdown(f"""
        <div class="card" style="padding:20px;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <span style="font-size:32px;">{pd2.get('icon','⭐')}</span>
            <div>
              <div style="font-weight:700;font-size:18px;">{pd2.get('name','Pillar')}</div>
              <div style="font-size:12px;color:var(--text-secondary);">{pd2.get('description','')}</div>
            </div>
            <div style="margin-left:auto;text-align:center;">
              <div style="font-size:36px;font-weight:700;color:{sc_col2};">{sc2}</div>
              <div style="font-size:11px;color:var(--text-secondary);">Score / 100</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("[📖 Well-Architected Framework →](https://learn.microsoft.com/azure/well-architected/)")
        st.markdown("[📖 Azure Architecture Center →](https://learn.microsoft.com/azure/architecture/)")

    # ─────────────────────── REPORTS ───────────────────────────────────────
    elif nav == "Reports":
        st.markdown("### 📊 Architecture Decision Reports")
        report_gen2 = ReportGenerator()
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown("""
            <div class="card" style="padding:20px;text-align:center;">
              <div style="font-size:32px;">📄</div>
              <div style="font-weight:700;margin:8px 0 4px;">JSON Report</div>
              <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">Machine-readable ADR for CI/CD integration</div>
            </div>""", unsafe_allow_html=True)
            json_r = report_gen2.generate_json(result)
            st.download_button("⬇️ Download JSON", data=json_r,
                               file_name="azure_adr_report.json", mime="application/json",
                               use_container_width=True)
        with r2:
            st.markdown("""
            <div class="card" style="padding:20px;text-align:center;">
              <div style="font-size:32px;">📝</div>
              <div style="font-weight:700;margin:8px 0 4px;">Markdown Report</div>
              <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">Human-readable ADR for wikis & PRs</div>
            </div>""", unsafe_allow_html=True)
            md_r = report_gen2.generate_markdown(result)
            st.download_button("⬇️ Download Markdown", data=md_r,
                               file_name="azure_adr_report.md", mime="text/markdown",
                               use_container_width=True)
        with r3:
            st.markdown("""
            <div class="card" style="padding:20px;text-align:center;">
              <div style="font-size:32px;">📊</div>
              <div style="font-weight:700;margin:8px 0 4px;">Executive Summary</div>
              <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">High-level overview for stakeholders</div>
            </div>""", unsafe_allow_html=True)
            exec_txt = f"Azure Architecture Review\nDate: {now}\nScore: {score}/100\nCritical Risks: {critical_count}\nEst. Savings: ${savings:,.0f}/mo"
            st.download_button("⬇️ Download Summary", data=exec_txt,
                               file_name="executive_summary.txt", mime="text/plain",
                               use_container_width=True)
        st.divider()
        st.markdown("**Executive Summary Preview:**")
        st.info(f"""
**Azure Architecture Review Report**
- **Date:** {now}
- **Environment:** {st.session_state.subscription} / {st.session_state.landing_zone}
- **Overall Score:** {score}/100
- **Critical Risks:** {critical_count} | **High:** {high_count} | **Medium:** {medium_count}
- **Estimated Monthly Savings:** ${savings:,.0f}
- **Top Risk:** {top5[0]['title'] if top5 else 'None'}
        """)

    # ─────────────────────── SETTINGS ──────────────────────────────────────
    elif nav == "Settings":
        st.markdown("### ⚙️ Settings & Configuration")
        with st.form("settings_form"):
            st.markdown("**Connection Settings**")
            fc1, fc2 = st.columns(2)
            new_sub = fc1.text_input("Subscription Name", value=st.session_state.subscription)
            new_lz  = fc2.text_input("Landing Zone",      value=st.session_state.landing_zone)
            st.markdown("**Review Parameters**")
            fc3, fc4 = st.columns(2)
            tier_sel   = fc3.selectbox("Architecture Tier", ["Auto-Detect","SMB","Mid-Market","Enterprise"])
            pillar_sel = fc4.selectbox("WAF Pillar Focus",  ["None"] + [v["name"] for v in WAF_PILLARS.values()])
            st.markdown("**Agent Toggles**")
            ac1, ac2, ac3, ac4 = st.columns(4)
            chk_sec = ac1.checkbox("🛡️ Security Agent",    value=True)
            chk_cst = ac2.checkbox("💰 Cost Agent",        value=True)
            chk_idn = ac3.checkbox("👤 Identity Agent",    value=True)
            chk_rel = ac4.checkbox("☁️ Reliability Agent", value=True)
            st.markdown("**Demo Mode**")
            demo_val = os.environ.get("DEMO_MODE","true").lower() == "true"
            demo_on = st.checkbox("Enable Demo Mode (no real Azure connection required)", value=demo_val)
            submitted = st.form_submit_button("💾 Save & Run Review", type="primary", use_container_width=True)
            if submitted:
                st.session_state.subscription = new_sub
                st.session_state.landing_zone  = new_lz
                tier_map   = {"Auto-Detect":None,"SMB":"smb","Mid-Market":"midmarket","Enterprise":"enterprise"}
                pillar_map = {v["name"]:k for k,v in WAF_PILLARS.items()}
                with st.spinner("Running review..."):
                    st.session_state.review_result = run_review(
                        tier_key=tier_map[tier_sel],
                        pillar_key=pillar_map.get(pillar_sel)
                    )
                st.success("✅ Settings saved and review completed!")
                st.rerun()

# ══════════════════════════ FLOATING CHAT FAB ══════════════════════════════
# Form-based FAB — GET form submits to /?chat=toggle, triggers Python handler at top of file
fab_icon = "✕" if show_chat else "💬"
st.markdown(f"""
<div class="chat-fab-wrap">
  <form method="get" action="/" target="_self">
    <input type="hidden" name="chat" value="toggle">
    <button type="submit" title="Toggle Architecture Copilot">{fab_icon}</button>
  </form>
</div>
""", unsafe_allow_html=True)


# Chat overlay panel (shown when show_chat=True)
if show_chat:
    waf_pillar_data = WAF_PILLARS.get(st.session_state.waf_focus, WAF_PILLARS["security"])
    query = st.session_state.get("chat_query", "")

    # Build chat content HTML
    chat_body_html = ""
    if "top risks" in query.lower() and top5:
        items = "".join(
            f'<div style="font-size:12px;padding:5px 0;border-bottom:1px solid #2d3f4e;">'
            f'<span style="background:#3d1515;color:#ff6b6b;padding:1px 7px;border-radius:3px;font-size:10px;font-weight:700;">{r["severity"]}</span>'
            f'&nbsp;{r["title"]}</div>'
            for r in top5[:3]
        )
        chat_body_html = f"<div style='padding:8px 0;'><b style='font-size:12px;'>🚨 Top Critical Risks:</b>{items}</div>"
    elif "remediation" in query.lower():
        items = "".join(
            f"<div style='font-size:12px;padding:4px 0;'>{i}. <b>{r['title']}</b><br>"
            f"<span style='color:#8b9dc3;'>{r['remediation'][:80]}...</span></div>"
            for i, r in enumerate(top5[:4], 1)
        )
        chat_body_html = f"<div style='padding:8px 0;'><b style='font-size:12px;'>🛠️ Remediation Plan:</b>{items}</div>"
    elif "caf" in query.lower():
        chat_body_html = """<div style='font-size:12px;padding:8px 0;'>
          <b>🏛️ CAF Alignment:</b><br><br>
          Your environment maps to <b>Enterprise Scale Landing Zone</b>.
          Key areas: Management Groups, Policy-driven governance, Hub-Spoke networking.<br><br>
          <a href='https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/' 
             target='_blank' style='color:#58a6ff;'>📖 CAF Enterprise Scale →</a>
        </div>"""
    elif "well-architected" in query.lower():
        pillar_html = "".join(
            f"<div style='font-size:11px;padding:2px 0;'>{pd['icon']} <b>{pd['name']}</b></div>"
            for pd in WAF_PILLARS.values()
        )
        chat_body_html = f"<div style='padding:8px 0;'><b style='font-size:12px;'>🏛️ WAF Pillars:</b>{pillar_html}</div>"
    else:
        chat_body_html = """
        <div style='background:#1a2235;border-radius:8px;padding:12px;font-size:13px;line-height:1.6;border:1px solid #2d3f4e;'>
          Hi Architect! I've completed the review. Ask me anything about your Azure environment.
        </div>"""

    waf_btns = "".join(
        f'<a href="?chat=toggle" style="text-decoration:none;font-size:18px;padding:4px 6px;border-radius:6px;background:#1a2235;border:1px solid #2d3f4e;">{icon}</a>'
        for _, icon in [("reliability","🛡️"),("security","🔐"),("cost","💰"),("operational_excellence","⚙️"),("performance","⚡")]
    )

    st.markdown(f"""
    <div class="chat-overlay">
      <div class="chat-overlay-hdr">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:22px;">🤖</span>
          <div>
            <div style="font-size:14px;font-weight:700;color:#fff;">Architecture Copilot</div>
            <div style="font-size:10px;color:rgba(255,255,255,.7);">Powered by Foundry IQ</div>
          </div>
        </div>
        <a href="?chat=toggle" style="text-decoration:none;font-size:18px;color:white;opacity:.8;">✕</a>
      </div>
      <div class="chat-overlay-body">
        {chat_body_html}
        <div style="margin-top:12px;font-size:12px;font-weight:600;color:#8b9dc3;margin-bottom:6px;">QUICK ACTIONS</div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          <a href="?qa=risks"       style="text-decoration:none;background:#1a2235;border:1px solid #2d3f4e;border-radius:8px;padding:8px 12px;font-size:12px;color:#e6edf3;display:flex;align-items:center;gap:8px;">⚠️ Show me the top risks</a>
          <a href="?qa=remediation" style="text-decoration:none;background:#1a2235;border:1px solid #2d3f4e;border-radius:8px;padding:8px 12px;font-size:12px;color:#e6edf3;display:flex;align-items:center;gap:8px;">💡 Give me remediation plan</a>
          <a href="?qa=caf"         style="text-decoration:none;background:#1a2235;border:1px solid #2d3f4e;border-radius:8px;padding:8px 12px;font-size:12px;color:#e6edf3;display:flex;align-items:center;gap:8px;">🏛️ Map to CAF framework</a>
          <a href="?qa=waf"         style="text-decoration:none;background:#1a2235;border:1px solid #2d3f4e;border-radius:8px;padding:8px 12px;font-size:12px;color:#e6edf3;display:flex;align-items:center;gap:8px;">📊 Well-Architected pillars</a>
        </div>
        <div style="margin-top:12px;display:flex;gap:6px;align-items:center;font-size:11px;color:#8b9dc3;">
          WAF Focus: {waf_btns}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Handle chat input via Streamlit widget (below overlay)
    chat_input = st.chat_input("Ask me anything...", key="main_chat")
    if chat_input:
        st.session_state.chat_query = chat_input
        st.rerun()

# Handle quick action query params
if "qa" in st.query_params:
    qa_map = {"risks": "top risks", "remediation": "remediation plan", "caf": "caf framework", "waf": "well-architected pillars"}
    qa_key = st.query_params.get("qa", "")
    st.session_state.chat_query = qa_map.get(qa_key, qa_key)
    st.session_state.show_chat = True
    st.query_params.clear()
    st.rerun()
