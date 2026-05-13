"""
Dashboard page - Overview of repository health and analysis status
"""

import streamlit as st
from app.services.repo_scanner import RepoScanner
from app.services.graph_service import GraphService


def render():
    st.markdown('<p class="main-header">\U0001F4CA Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        render_repo_selection()

    with col2:
        render_quick_stats()

    if st.session_state.analysis_results:
        st.markdown("---")
        render_analysis_summary()
        render_quality_metrics()
        render_recent_hotspots()


def render_repo_selection():
    st.markdown("### \U0001F4E5 Repository Selection")
    scanner = st.session_state.repo_scanner
    local_repos = scanner.list_local_repos()

    tab1, tab2 = st.tabs(["Local Repositories", "Clone Remote"])

    with tab1:
        if local_repos:
            repo_names = [r["name"] for r in local_repos]
            selected = st.selectbox("Select a repository", repo_names)

            if st.button("\U0001F50D Analyze Selected Repo", use_container_width=True, type="primary"):
                repo = next(r for r in local_repos if r["name"] == selected)
                st.session_state.session_memory.new_session(selected)
                run_analysis_direct(repo["name"], repo["path"])
        else:
            st.info("No repositories found. Add one by scanning or cloning.")

    with tab2:
        repo_url = st.text_input("Git repository URL",
            placeholder="https://github.com/user/repo.git")
        branch = st.text_input("Branch (optional)", placeholder="main")

        if st.button("\U0001F500 Clone & Analyze", use_container_width=True, type="primary"):
            if repo_url:
                with st.spinner("Cloning repository..."):
                    result = scanner.clone_repository(repo_url, branch or None)
                    if result["success"]:
                        st.session_state.session_memory.new_session(result["name"])
                        run_analysis_direct(result["name"], result["path"])
                    else:
                        st.error(f"Clone failed: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please enter a repository URL")

    uploaded = st.file_uploader("Or upload a local directory path", type=None)
    if uploaded:
        st.info("File upload not supported. Use local path input below.")

    local_path = st.text_input("Local directory path",
        placeholder="C:/path/to/your/project")
    if st.button("\U0001F4C2 Scan Directory", use_container_width=True):
        if local_path:
            import os
            if os.path.isdir(local_path):
                result = scanner.scan_directory(local_path)
                if result["success"]:
                    st.session_state.session_memory.new_session(result["name"])
                    run_analysis_direct(result["name"], result["path"])
                else:
                    st.error(f"Scan failed: {result.get('error', 'Unknown error')}")
            else:
                st.error("Invalid directory path")
        else:
            st.warning("Please enter a directory path")


def run_analysis_direct(repo_name: str, repo_path: str):
    """Run analysis directly and update session state"""
    import asyncio
    from app.workflows.analysis_workflow import AnalysisWorkflow

    st.session_state.running = True

    async def run():
        workflow = AnalysisWorkflow(repo_path, use_llm=False)
        results = await workflow.run_full_analysis()

        st.session_state.analysis_results = results
        st.session_state.session_memory.save_analysis(results)

        graph_service = st.session_state.graph_service
        graph_service.load_from_analysis(results)

        st.session_state.running = False

    try:
        asyncio.run(run())
        if st.session_state.analysis_results:
            st.success(f"Analysis complete for {repo_name}!")
            st.rerun()
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        st.session_state.running = False


def render_quick_stats():
    st.markdown("### \U0001F4CA Quick Stats")
    session = st.session_state.session_memory.get_current()
    if session:
        st.metric("Active Session", session.get("repo_name", "N/A"))
        st.caption(f"State: {session.get('state', 'N/A')}")
    else:
        st.metric("Active Session", "None")

    if st.session_state.analysis_results:
        summary = st.session_state.analysis_results.get("summary", {})
        st.metric("Quality Grade", summary.get("quality_rating", "N/A"))
        st.metric("Code Smells", summary.get("total_smells", 0))
        st.metric("Arch Issues", summary.get("arch_issues", 0))
    else:
        st.metric("Quality Grade", "--")
        st.metric("Code Smells", "--")
        st.metric("Arch Issues", "--")

    if st.session_state.running:
        st.info("Analysis running...")


def render_analysis_summary():
    st.markdown("### \U0001F4CB Analysis Summary")
    results = st.session_state.analysis_results
    summary = results.get("summary", {})

    cols = st.columns(5)
    with cols[0]:
        st.metric("Files", summary.get("total_files", 0))
    with cols[1]:
        st.metric("Lines of Code", summary.get("total_lines", 0))
    with cols[2]:
        st.metric("Functions", summary.get("total_functions", 0))
    with cols[3]:
        st.metric("Classes", summary.get("total_classes", 0))
    with cols[4]:
        st.metric("Avg Complexity", summary.get("avg_complexity", 0))


def render_quality_metrics():
    st.markdown("### \U0001F3AF Quality Metrics")
    results = st.session_state.analysis_results
    details = results.get("details", {})
    cm = details.get("code_metrics", {})
    cs = details.get("code_smells", {})
    ai = details.get("architectural_issues", {})

    cols = st.columns(3)

    with cols[0]:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        quality = cm.get("quality_score", 0)
        rating = cm.get("quality_rating", "N/A")
        color = "green" if quality >= 75 else "orange" if quality >= 50 else "red"
        st.markdown(f'<p class="metric-value" style="color:{color}">{rating}</p>',
            unsafe_allow_html=True)
        st.markdown(f'<p class="metric-label">Quality Score: {quality}/100</p>',
            unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cols[1]:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        smells = cs.get("smells", {})
        total = cs.get("total_smells", 0)
        st.markdown(f'<p class="metric-value">{total}</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="metric-label">'
            f'Critical: {cs.get("critical_count", 0)} | '
            f'High: {cs.get("high_count", 0)} | '
            f'Medium: {cs.get("medium_count", 0)}'
            f'</p>',
            unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cols[2]:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        arch = ai.get("issues", [])
        st.markdown(f'<p class="metric-value">{len(arch)}</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="metric-label">'
            f'High: {ai.get("high_severity", 0)} | '
            f'Medium: {ai.get("medium_severity", 0)}'
            f'</p>',
            unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_recent_hotspots():
    st.markdown("### \U0001F525 Top Technical Debt Hotspots")
    results = st.session_state.analysis_results
    modules = results.get("details", {}).get("modules", {})
    hotspots = modules.get("debt_hotspots", [])

    if not hotspots:
        st.caption("No hotspots detected")
        return

    for hotspot in hotspots[:5]:
        cols = st.columns([3, 1, 1, 2])

        with cols[0]:
            st.markdown(f"**{hotspot.get('module', 'Unknown')}**")

        with cols[1]:
            score = hotspot.get("debt_score", 0)
            if score > 5:
                st.markdown(f'<span class="badge badge-critical">{score}</span>',
                    unsafe_allow_html=True)
            elif score > 3:
                st.markdown(f'<span class="badge badge-high">{score}</span>',
                    unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="badge badge-medium">{score}</span>',
                    unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"_{hotspot.get('file_count', 0)} files_")

        with cols[3]:
            issues = hotspot.get("issues", [])
            if issues:
                st.caption(", ".join(issues[:3]))
