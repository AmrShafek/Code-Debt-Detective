"""
Main Streamlit Application
Detective-themed code analysis dashboard
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.config.settings import settings
from app.memory.session_memory import SessionMemory
from app.services.repo_scanner import RepoScanner
from app.services.graph_service import GraphService
from app.gui.components.sidebar import render_sidebar
from app.gui.pages.dashboard import render as render_dashboard
from app.gui.pages.repo_analysis_page import render as render_analysis
from app.gui.pages.refactor_page import render as render_refactor
from app.gui.pages.risk_page import render as render_risk

st.set_page_config(
    page_title="Code Debt Detective",
    page_icon="\U0001F50D",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    if "session_memory" not in st.session_state:
        st.session_state.session_memory = SessionMemory()
    if "repo_scanner" not in st.session_state:
        st.session_state.repo_scanner = RepoScanner()
    if "graph_service" not in st.session_state:
        st.session_state.graph_service = GraphService()
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "refactoring_results" not in st.session_state:
        st.session_state.refactoring_results = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    if "running" not in st.session_state:
        st.session_state.running = False


def apply_custom_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: #1a1f2e;
    --bg-card-hover: #1e2537;
    --border-color: #2a3040;
    --border-glow: rgba(74, 144, 226, 0.15);
    --text-primary: #e8edf5;
    --text-secondary: #8892a8;
    --text-muted: #5a6478;
    --accent-blue: #4a90e2;
    --accent-cyan: #00d4ff;
    --accent-gold: #f0c040;
    --accent-red: #ff4757;
    --accent-green: #2ed573;
    --accent-orange: #ffa502;
    --glow-blue: rgba(74, 144, 226, 0.3);
    --glow-cyan: rgba(0, 212, 255, 0.2);
}

.stApp {
    background: var(--bg-primary);
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(74, 144, 226, 0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(0, 212, 255, 0.02) 0%, transparent 50%);
}

.main-header {
    font-family: 'Inter', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.main-header::before {
    content: "\\1F50D";
    font-size: 1.4rem;
}

.sub-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 1.5rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
}

.case-divider {
    height: 1px;
    background: linear-gradient(90deg, var(--border-color), var(--accent-blue), var(--border-color));
    margin: 1.5rem 0;
    opacity: 0.5;
}

.evidence-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    transition: all 0.2s ease;
    position: relative;
}
.evidence-card:hover {
    border-color: var(--accent-blue);
    box-shadow: 0 0 20px var(--border-glow);
    background: var(--bg-card-hover);
}
.evidence-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 3px;
    height: 100%;
    background: var(--accent-blue);
    border-radius: 3px 0 0 3px;
    opacity: 0;
    transition: opacity 0.2s;
}
.evidence-card:hover::before {
    opacity: 1;
}

.metric-value {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1;
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.25rem;
}

.badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-critical { background: rgba(255, 71, 87, 0.15); color: var(--accent-red); border: 1px solid rgba(255, 71, 87, 0.3); }
.badge-high { background: rgba(255, 165, 2, 0.15); color: var(--accent-orange); border: 1px solid rgba(255, 165, 2, 0.3); }
.badge-medium { background: rgba(240, 192, 64, 0.15); color: var(--accent-gold); border: 1px solid rgba(240, 192, 64, 0.3); }
.badge-low { background: rgba(46, 213, 115, 0.15); color: var(--accent-green); border: 1px solid rgba(46, 213, 115, 0.3); }

.evidence-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.1rem 0.4rem;
    border: 1px solid var(--border-color);
    border-radius: 2px;
    display: inline-block;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: var(--bg-secondary);
    border-radius: 6px;
    padding: 3px;
    border: 1px solid var(--border-color);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 4px;
    padding: 0.5rem 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
}
.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--accent-cyan) !important;
    border: 1px solid var(--border-color) !important;
}

.stButton > button {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-radius: 4px;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 25px var(--glow-blue);
    transform: translateY(-1px);
}

.stTextInput input, .stSelectbox div, .stTextArea textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 4px !important;
    color: var(--text-primary) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTextInput input:focus, .stSelectbox div:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 10px var(--border-glow) !important;
}

.stCheckbox label {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.stDataFrame {
    border: 1px solid var(--border-color) !important;
    border-radius: 6px !important;
    overflow: hidden;
}

div[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace;
    color: var(--text-primary);
}

.stAlert {
    border-radius: 6px;
    border-left: 3px solid;
}
.stAlert[data-baseweb="notification"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
}

.stExpander {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    margin-bottom: 0.5rem;
}
.stExpander:hover {
    border-color: var(--accent-blue);
}
.stExpander details > summary {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: var(--text-primary);
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan)) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-primary);
    border-right: 1px solid var(--border-color);
    background-image:
        linear-gradient(rgba(74, 144, 226, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(74, 144, 226, 0.02) 1px, transparent 1px);
    background-size: 20px 20px;
}

[data-testid="stSidebar"] .sidebar-header {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
}
[data-testid="stSidebar"] .sidebar-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
}
[data-testid="stSidebar"] .section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    padding: 1rem 0 0.25rem 0;
    border-top: 1px solid var(--border-color);
    margin-top: 0.75rem;
}

.nav-btn {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 4px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--text-muted) !important;
    transition: all 0.2s;
}
.nav-btn:hover {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}
.nav-btn.active {
    background: var(--bg-card) !important;
    border-color: var(--accent-blue) !important;
    color: var(--accent-cyan) !important;
    box-shadow: 0 0 15px var(--border-glow);
}
</style>
""", unsafe_allow_html=True)


def main():
    settings.ensure_dirs()
    init_session_state()
    apply_custom_css()

    render_sidebar()

    pages = {
        "Dashboard": render_dashboard,
        "Repository Analysis": render_analysis,
        "Refactoring": render_refactor,
        "Risk Assessment": render_risk,
    }

    page = st.session_state.get("current_page", "Dashboard")
    if page in pages:
        pages[page]()


if __name__ == "__main__":
    main()
