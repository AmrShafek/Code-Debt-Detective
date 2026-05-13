"""
Refactoring page - View and explore refactoring strategies
"""

import asyncio
import streamlit as st
from app.workflows.refactor_workflow import RefactorWorkflow


def render():
    st.markdown('<p class="main-header">\U0001F527 Refactoring Plans</p>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.analysis_results:
        st.info("No analysis results available. Run an analysis from the Dashboard first.")
        return

    analyses = st.session_state.analysis_results
    details = analyses.get("details", {})

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Generate Refactoring Plan")

        use_llm = st.checkbox("Use LLM for deeper analysis", value=False,
            help="Requires LLM API key to be configured")

        if st.button("\U0001F9F0 Generate Refactoring Strategy", use_container_width=True, type="primary"):
            with st.spinner("Generating refactoring plan..."):
                workflow = RefactorWorkflow(analyses, use_llm=use_llm)

                async def run():
                    return await workflow.run_full_refactoring_pipeline()

                try:
                    results = asyncio.run(run())
                    st.session_state.refactoring_results = results
                    st.session_state.session_memory.save_refactoring(results)
                    st.success("Refactoring plan generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {str(e)}")

        if st.button("\U0001F504 Regenerate (local only)", use_container_width=True):
            workflow = RefactorWorkflow(analyses, use_llm=False)

            async def run():
                return await workflow.run_full_refactoring_pipeline()

            try:
                results = asyncio.run(run())
                st.session_state.refactoring_results = results
                st.session_state.session_memory.save_refactoring(results)
                st.success("Refactoring plan regenerated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {str(e)}")

    with col2:
        st.markdown("### Input Summary")
        summary = analyses.get("summary", {})
        st.metric("Quality", summary.get("quality_rating", "N/A"))
        st.metric("Smells", summary.get("total_smells", 0))
        st.metric("Arch Issues", summary.get("arch_issues", 0))

    if st.session_state.refactoring_results:
        ref_results = st.session_state.refactoring_results
        render_refactoring_plan(ref_results)
        render_refactoring_details(ref_results)


def render_refactoring_plan(ref_results):
    st.markdown("---")
    st.markdown("### \U0001F4CB Refactoring Plan")

    plan = ref_results.get("refactoring_plan", {})
    if isinstance(plan, str):
        st.markdown(plan)
        return

    st.metric("Total Effort", f"{plan.get('total_effort_days', 0)} days")

    phases = plan.get("refactoring_phases", [])
    if not phases:
        st.caption("No phases defined")
        return

    for phase in phases:
        risk = phase.get("risk_level", "LOW")
        badge = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(risk, "badge-low")

        with st.container():
            st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
            cols = st.columns([4, 1, 1, 2])

            with cols[0]:
                st.markdown(f"**Phase {phase.get('phase', '?')}: {phase.get('name', 'Unknown')}**")

            with cols[1]:
                st.markdown(f'<span class="badge {badge}">{risk}</span>',
                    unsafe_allow_html=True)

            with cols[2]:
                st.markdown(f"_{phase.get('duration_days', 0)}d_")

            with cols[3]:
                modules = phase.get("modules_to_extract", [])
                if modules:
                    st.caption(", ".join(modules))

            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Extraction Opportunities")
    opportunities = plan.get("extraction_opportunities", [])
    if opportunities:
        opp_data = []
        for opp in opportunities:
            opp_data.append({
                "Module": opp.get("module", ""),
                "Priority": opp.get("priority_rank", 0),
                "Effort": opp.get("effort_score", 0),
                "Risk": opp.get("risk_score", 0),
                "Impact": opp.get("impact_score", 0),
            })
        st.dataframe(opp_data, use_container_width=True)


def render_refactoring_details(ref_results):
    st.markdown("---")
    st.markdown("### \U0001F4DD Detailed Plan")

    tab1, tab2 = st.tabs(["Phases Detail", "Explanation"])

    with tab1:
        plan = ref_results.get("refactoring_plan", {})
        if isinstance(plan, dict):
            phases = plan.get("refactoring_phases", [])
            for phase in phases:
                with st.expander(f"Phase {phase.get('phase')}: {phase.get('name')}"):
                    st.markdown(f"**Duration:** {phase.get('duration_days', 0)} days")
                    st.markdown(f"**Risk:** {phase.get('risk_level', 'LOW')}")

                    modules = phase.get("modules_to_extract", [])
                    if modules:
                        st.markdown(f"**Modules:** {', '.join(modules)}")

                    criteria = phase.get("success_criteria", [])
                    if criteria:
                        st.markdown("**Success Criteria:**")
                        for c in criteria:
                            st.markdown(f"- {c}")

                    breaking = phase.get("breaking_changes", [])
                    if breaking:
                        st.markdown("**Breaking Changes:**")
                        for b in breaking:
                            st.markdown(f"- {b}")

                    st.markdown(f"**Rollback:** {phase.get('rollback_plan', 'N/A')}")

    with tab2:
        explanation = ref_results.get("diff_explanation", {})
        if isinstance(explanation, dict):
            summary = explanation.get("executive_summary", "")
            if summary:
                st.markdown(f"**Executive Summary:** {summary}")

            phases = explanation.get("phases", [])
            for phase in phases:
                with st.expander(phase.get("name", "Phase")):
                    guide = phase.get("guide", "")
                    if guide:
                        st.markdown(guide)

                    checklist = phase.get("testing_checklist", [])
                    if checklist:
                        st.markdown("**Testing Checklist:**")
                        for item in checklist:
                            st.markdown(f"- [ ] {item}")
        elif isinstance(explanation, str):
            st.markdown(explanation)
