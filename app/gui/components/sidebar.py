"""
Sidebar navigation component for the Streamlit GUI
"""

import streamlit as st
from app.config.settings import settings
from app.services.llm_service import LLMService


def render_sidebar():
    """Render the sidebar with navigation and app controls"""
    llm = LLMService()

    with st.sidebar:
        st.markdown("# \U0001F50D Code Debt Detective")
        st.markdown("---")

        st.markdown("### Navigation")

        if st.button(
            "\U0001F4CA Dashboard",
            width="stretch",
            type="secondary" if st.session_state.current_page != "Dashboard" else "primary"
        ):
            st.session_state.current_page = "Dashboard"
            st.rerun()

        if st.button(
            "\U0001F50D Repository Analysis",
            width="stretch",
            type="secondary" if st.session_state.current_page != "Repository Analysis" else "primary"
        ):
            st.session_state.current_page = "Repository Analysis"
            st.rerun()

        if st.button(
            "\U0001F527 Refactoring",
            width="stretch",
            type="secondary" if st.session_state.current_page != "Refactoring" else "primary"
        ):
            st.session_state.current_page = "Refactoring"
            st.rerun()

        if st.button(
            "\u26A0\uFE0F Risk Assessment",
            width="stretch",
            type="secondary" if st.session_state.current_page != "Risk Assessment" else "primary"
        ):
            st.session_state.current_page = "Risk Assessment"
            st.rerun()

        st.markdown("---")

        st.markdown("### Active Session")
        session = st.session_state.session_memory.get_current()
        if session:
            st.info(f"**Repo:** {session.get('repo_name', 'N/A')}\n\n"
                    f"**State:** {session.get('state', 'N/A')}")
        else:
            st.caption("No active session")

        st.markdown("---")

        st.markdown("### LLM Configuration")

        ca_cfg = llm.get_code_analyzer_config()
        ca_ok = llm.is_code_analyzer_configured()
        st.caption(f"\U0001F50D **Code Analyzer:** {ca_cfg.get('model', 'N/A')}")
        st.caption(f"{'✅ Configured' if ca_ok else '❌ No API key'}")

        rf_cfg = llm.get_refactor_config()
        rf_ok = llm.is_refactor_configured()
        st.caption(f"\U0001F527 **Strategist/Risk/Explainer:** {rf_cfg.get('model', 'N/A')}")
        st.caption(f"{'✅ Configured' if rf_ok else '❌ No API key'}")

        if st.button("\U0001F504 Reset Session", width="stretch"):
            st.session_state.session_memory.clear_current()
            st.session_state.analysis_results = None
            st.session_state.refactoring_results = None
            st.rerun()

        st.markdown("---")
        st.caption(f"v{settings.APP_VERSION}")
