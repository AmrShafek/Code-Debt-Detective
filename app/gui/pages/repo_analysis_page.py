"""
Repository Analysis page - Detailed code analysis and dependency visualization
"""

import json
import streamlit as st
from app.gui.components.graph_viewer import render_dependency_graph


def render():
    st.markdown('<p class="main-header">\U0001F50D Repository Analysis</p>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.analysis_results:
        st.info("No analysis results available. Run an analysis from the Dashboard first.")
        return

    results = st.session_state.analysis_results
    details = results.get("details", {})

    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001F4CA Overview", "\U0001F517 Dependencies",
        "\U0001F50D Code Smells", "\U0001F3D7\uFE0F Architecture"
    ])

    with tab1:
        render_overview_tab(results, details)

    with tab2:
        render_dependencies_tab(details)

    with tab3:
        render_smells_tab(details)

    with tab4:
        render_architecture_tab(details)


def render_overview_tab(results, details):
    st.markdown("### File Structure")
    fs = details.get("file_structure", {})

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Files", fs.get("total_files", 0))
        st.metric("Total Lines", fs.get("total_lines", 0))

    with col2:
        st.metric("Max File Size", f"{fs.get('max_file_size', 0)} lines")
        largest = fs.get("largest_files", [])
        if largest:
            st.markdown("**Largest Files:**")
            for f in largest[:5]:
                st.caption(f"- {f.get('path', '')} ({f.get('lines', 0)} lines)")

    st.markdown("### Language Distribution")
    languages = fs.get("languages", {})
    if languages:
        lang_data = {lang: info.get("count", 0) for lang, info in languages.items()}
        st.bar_chart(lang_data)

    cm = details.get("code_metrics", {})
    st.markdown("### Code Metrics")
    mcols = st.columns(3)
    with mcols[0]:
        st.metric("Code Lines", cm.get("total_code_lines", 0))
    with mcols[1]:
        st.metric("Comment Lines", cm.get("total_comment_lines", 0))
    with mcols[2]:
        st.metric("Blank Lines", cm.get("total_blank_lines", 0))

    st.markdown("### Complexity Indicators")
    ci = cm.get("complexity_indicators", {})
    ccols = st.columns(3)
    with ccols[0]:
        st.metric("Long Functions", ci.get("long_functions", 0))
    with ccols[1]:
        st.metric("Many Branches", ci.get("many_branches", 0))
    with ccols[2]:
        st.metric("Duplication Candidates", len(cm.get("duplication_candidates", [])))

    funcs = details.get("functions", {})
    if funcs.get("complex_functions"):
        st.markdown("### Most Complex Functions")
        complex_items = funcs.get("complex_functions", [])[:5]
        for f in complex_items:
            st.markdown(
                f"- `{f.get('name', '')}` in _{f.get('file', '')}_ "
                f"(complexity: {f.get('cyclomatic_complexity', 0)})"
            )


def render_dependencies_tab(details):
    st.markdown("### Dependency Graph")
    st.caption("Interactive graph showing module dependencies. Nodes are modules, edges show import relationships.")

    graph_json = details.get("graph_json", {})
    graph = graph_json.get("graph", {})

    if graph.get("nodes"):
        vis_nodes = []
        for node in graph.get("nodes", []):
            vis_nodes.append({
                "id": node.get("id"),
                "label": node.get("name", "").split(".")[-1][:20],
                "title": node.get("name", ""),
                "group": node.get("group", "unknown"),
                "value": node.get("size", 10)
            })

        vis_edges = []
        for edge in graph.get("edges", []):
            vis_edges.append({
                "from": edge.get("source"),
                "to": edge.get("target"),
                "arrows": "to"
            })

        render_dependency_graph({"nodes": vis_nodes, "edges": vis_edges})
    else:
        st.info("No dependency graph available")

    st.markdown("### Cyclic Dependencies")
    cycles = details.get("cyclic_dependencies", {})
    if cycles.get("cycles"):
        st.warning(f"Found {cycles.get('total_cycles', 0)} cyclic dependencies")
        for cycle in cycles.get("cycles", []):
            severity = cycle.get("severity", "low")
            badge = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}.get(severity, "badge-low")
            st.markdown(
                f'<span class="badge {badge}">{severity.upper()}</span> '
                f'Cycle: {" \u2192 ".join(cycle.get("cycle", []))}',
                unsafe_allow_html=True
            )
    else:
        st.success("No cyclic dependencies detected")

    st.markdown("### Coupling Metrics")
    coupling = details.get("coupling_metrics", {})
    metrics_list = coupling.get("module_metrics", {})
    if metrics_list:
        data = []
        for module, m in sorted(metrics_list.items(), key=lambda x: x[1].get("instability", 0), reverse=True)[:10]:
            data.append({
                "module": module,
                "instability": m.get("instability", 0),
                "afferent": m.get("afferent_coupling", 0),
                "efferent": m.get("efferent_coupling", 0)
            })
        st.dataframe(data, use_container_width=True)


def render_smells_tab(details):
    st.markdown("### Code Smells")
    cs = details.get("code_smells", {})

    total = cs.get("total_smells", 0)
    critical = cs.get("critical_count", 0)
    high = cs.get("high_count", 0)
    medium = cs.get("medium_count", 0)
    low = cs.get("low_count", 0)

    mcols = st.columns(4)
    with mcols[0]:
        st.metric("Total", total)
    with mcols[1]:
        st.metric("Critical", critical)
    with mcols[2]:
        st.metric("High", high)
    with mcols[3]:
        st.metric("Medium", medium)

    smells = cs.get("smells", {})

    if smells.get("critical"):
        st.markdown("#### Critical")
        for s in smells["critical"]:
            st.error(f"**{s.get('type', 'Unknown')}** in `{s.get('file', '')}`:{s.get('line', '')}")
            st.caption(f"{s.get('message', '')}")
            st.caption(f"Suggestion: {s.get('suggestion', '')}")

    if smells.get("high"):
        st.markdown("#### High")
        for s in smells["high"]:
            st.warning(f"**{s.get('type', 'Unknown')}** in `{s.get('file', '')}`:{s.get('line', '')}")
            st.caption(f"{s.get('message', '')}")

    if smells.get("medium"):
        st.markdown("#### Medium")
        for s in smells["medium"]:
            st.info(f"**{s.get('type', 'Unknown')}** in `{s.get('file', '')}`")

    if smells.get("low"):
        with st.expander(f"Low severity ({len(smells['low'])} items)"):
            for s in smells["low"]:
                st.caption(f"- {s.get('message', '')} (`{s.get('file', '')}`:{s.get('line', '')})")


def render_architecture_tab(details):
    st.markdown("### Architectural Issues")
    ai = details.get("architectural_issues", {})

    total = ai.get("total_issues", 0)
    high = ai.get("high_severity", 0)
    medium = ai.get("medium_severity", 0)
    low = ai.get("low_severity", 0)

    mcols = st.columns(4)
    with mcols[0]:
        st.metric("Total Issues", total)
    with mcols[1]:
        st.metric("High", high)
    with mcols[2]:
        st.metric("Medium", medium)
    with mcols[3]:
        st.metric("Low", low)

    issues = ai.get("issues", [])
    if issues:
        for issue in issues:
            sev = issue.get("severity", "low")
            icon = { "high": "\u26A0\uFE0F", "medium": "\u26A0\uFE0F", "low": "\u2139\uFE0F" }.get(sev, "")
            with st.container():
                cols = st.columns([1, 5, 4])
                with cols[0]:
                    badge_cls = f"badge-{sev}"
                    st.markdown(f'<span class="badge {badge_cls}">{sev.upper()}</span>',
                        unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"**{issue.get('type', 'Unknown').replace('_', ' ').title()}**")
                    if issue.get('message'):
                        st.caption(issue.get('message', ''))
                with cols[2]:
                    if issue.get('suggestion'):
                        st.caption(f":bulb: {issue.get('suggestion', '')}")
                st.divider()

    modules = details.get("modules", {})
    st.markdown("### Module Classification")
    class_data = {
        "Service Modules": modules.get("service_modules", []),
        "API Modules": modules.get("api_modules", []),
        "Core Modules": modules.get("core_modules", []),
        "Data Modules": modules.get("data_modules", []),
        "Utility Modules": modules.get("utility_modules", []),
        "Test Modules": modules.get("test_modules", []),
    }

    dc_cols = st.columns(3)
    for i, (label, mods) in enumerate(class_data.items()):
        with dc_cols[i % 3]:
            st.markdown(f"**{label}:** {len(mods)}")
            if mods:
                st.caption(", ".join(mods[:5]))
