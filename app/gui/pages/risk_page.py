"""
Risk Assessment page - View and explore change risk analysis
"""

import streamlit as st


def render():
    st.markdown('<p class="main-header">\u26A0\uFE0F Risk Assessment</p>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.refactoring_results:
        if st.session_state.analysis_results:
            st.info("No refactoring results yet. Go to the Refactoring page to generate a plan first.")
        else:
            st.info("No analysis results available. Run an analysis from the Dashboard first.")
        return

    ref_results = st.session_state.refactoring_results
    risk = ref_results.get("risk_assessment", {})

    if isinstance(risk, str):
        st.markdown(risk)
        return

    render_risk_overview(risk)
    render_risk_details(risk)
    render_breaking_changes(risk)
    render_mitigation(risk)


def render_risk_overview(risk):
    st.markdown("### \U0001F4CA Risk Overview")

    phase_risks = risk.get("phase_risks", [])
    total_risk = risk.get("total_risk_score", 0)

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Risk Score", f"{total_risk:.1f}")
    with cols[1]:
        st.metric("Phases Assessed", len(phase_risks))
    with cols[2]:
        breaking = risk.get("has_breaking_changes", False)
        st.metric("Breaking Changes", ":warning: Yes" if breaking else ":white_check_mark: No")

    if phase_risks:
        st.markdown("#### Per-Phase Risk Breakdown")

        for phase in phase_risks:
            overall = phase.get("overall_risk", 0)
            color = "red" if overall > 5 else "orange" if overall > 3 else "green"

            with st.container():
                cols = st.columns([2, 1, 1, 1, 1])

                with cols[0]:
                    st.markdown(f"**Phase {phase.get('phase')}: {phase.get('name')}**")

                with cols[1]:
                    st.markdown(f'<span style="color:{color}; font-weight:bold;">Risk: {overall}</span>',
                        unsafe_allow_html=True)

                with cols[2]:
                    st.caption(f"Impact: {phase.get('impact_score', 0)}")

                with cols[3]:
                    st.caption(f"Prob: {phase.get('probability_score', 0)}")

                with cols[4]:
                    st.caption(f"Detect: {phase.get('detection_score', 0)}")

                if overall > 5:
                    st.progress(min(overall / 10, 1.0))
                else:
                    st.progress(min(overall / 10, 1.0))

                st.divider()


def render_risk_details(risk):
    st.markdown("---")
    st.markdown("### \U0001F4CA Detailed Risk Matrix")

    phase_risks = risk.get("phase_risks", [])
    if phase_risks:
        risk_data = []
        for p in phase_risks:
            impact = p.get("impact_score", 1)
            probability = p.get("probability_score", 1)
            detection = p.get("detection_score", 1)
            overall = (impact * probability) / max(detection, 1)

            risk_data.append({
                "Phase": p.get("name", f"Phase {p.get('phase')}"),
                "Impact (1-10)": impact,
                "Probability (1-10)": probability,
                "Detection (1-10)": detection,
                "Overall Risk": round(overall, 2),
                "Level": (
                    "\U0001F534 High" if overall > 5 else
                    "\U0001F7E1 Medium" if overall > 3 else
                    "\U0001F7E2 Low"
                )
            })

        st.dataframe(risk_data, use_container_width=True, hide_index=True)

    st.markdown("#### Risk Score Formula")
    st.caption("Overall Risk = (Impact x Probability) / Detection")
    st.caption("Where Impact = how many modules affected, Probability = likelihood of breakage, Detection = how easily caught")


def render_breaking_changes(risk):
    st.markdown("---")
    st.markdown("### \U0001F4A5 Breaking Changes Analysis")

    breaking = risk.get("has_breaking_changes", False)

    if breaking:
        st.warning("Breaking changes detected in the refactoring plan")

        blast_radius = risk.get("blast_radius", 0)
        if blast_radius:
            st.metric("Blast Radius", f"{blast_radius} modules affected")

        suggestions = risk.get("mitigation_suggestions", [])
        if suggestions:
            st.markdown("#### Suggested Mitigations")
            for s in suggestions:
                st.markdown(f"- {s}")
    else:
        st.success("No breaking changes detected in the current plan")

    cycles = st.session_state.analysis_results.get("details", {}).get("cyclic_dependencies", {})
    if cycles.get("has_cycles"):
        st.info("Cyclic dependencies exist but may not be directly affected by the current refactoring plan")


def render_mitigation(risk):
    st.markdown("---")
    st.markdown("### \U0001F6E1\uFE0F Mitigation Strategies")

    suggestions = risk.get("mitigation_suggestions", [])
    if not suggestions:
        st.info(risk.get("mitigation", "No specific mitigation strategies in current assessment"))
        return

    for s in suggestions:
        with st.container():
            st.markdown(f'- <span style="font-size:1.1rem;">{s}</span>',
                unsafe_allow_html=True)
            st.divider()

    st.markdown("#### General Best Practices")
    st.markdown("""
    - **Feature Flags**: Wrap risky changes behind feature flags for safe rollout
    - **Canary Deployments**: Roll out to 5-10% of users first
    - **Automated Rollback**: Ensure rollback scripts are tested and ready
    - **Integration Tests**: Run full integration test suite before merge
    - **Code Review**: All refactoring PRs require at least 2 approvals
    - **Staging Validation**: Deploy to staging for minimum 24 hours
    - **Monitoring**: Set up dashboards for error rates and latency
    """)
