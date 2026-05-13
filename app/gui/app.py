"""
Main Streamlit Application
Interactive dashboard for code analysis, refactoring, and risk visualization
"""

import sys
import asyncio
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
.main-header { font-size: 2rem; font-weight: 700; margin-bottom: 0; }
.sub-header { font-size: 1.2rem; color: #888; margin-bottom: 2rem; }
.metric-card {
    background: #1e1e1e; border-radius: 10px; padding: 1.5rem;
    border: 1px solid #333; margin-bottom: 1rem;
}
.metric-value { font-size: 2.5rem; font-weight: 700; }
.metric-label { font-size: 0.9rem; color: #888; }
.stButton>button { width: 100%; }
.badge {
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
    font-size: 0.8rem; font-weight: 600;
}
.badge-high { background: #ff4444; color: white; }
.badge-medium { background: #ffaa00; color: black; }
.badge-low { background: #00cc66; color: white; }
.badge-critical { background: #cc0000; color: white; }
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
