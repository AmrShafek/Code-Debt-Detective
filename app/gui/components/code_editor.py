"""
Code editor component for viewing and editing source code
"""

import streamlit as st


def render_code_editor(code: str, language: str = "python", height: int = 400, key: str = "code_editor"):
    """Render a read-only code viewer with syntax highlighting

    Args:
        code: Source code to display
        language: Programming language
        height: Editor height in pixels
        key: Unique key for the component
    """
    st.code(code, language=language, line_numbers=True)


def render_file_browser(files: list, on_select=None):
    """Render a file browser tree

    Args:
        files: List of file path strings
        on_select: Callback when a file is selected
    """
    tree = {}
    for filepath in files:
        parts = filepath.split("/")
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    def _render_tree(node, path=""):
        items = list(node.items())
        items.sort(key=lambda x: (not bool(x[1]), x[0]))

        for name, children in items:
            full_path = f"{path}/{name}" if path else name
            if children:
                with st.expander(f"\U0001F4C1 {name}", expanded=False):
                    _render_tree(children, full_path)
            else:
                if st.button(f"\U0001F4C4 {name}", key=full_path, use_container_width=True):
                    if on_select:
                        on_select(full_path)

    _render_tree(tree)


def render_code_metrics(metrics: dict):
    """Render code metrics visualization

    Args:
        metrics: Dict with code metrics (lines, complexity, etc.)
    """
    if not metrics:
        st.caption("No metrics available")
        return

    cols = st.columns(4)
    metrics_display = [
        ("Lines", metrics.get("lines", 0)),
        ("Code", metrics.get("code_lines", 0)),
        ("Comments", metrics.get("comment_lines", 0)),
        ("Blank", metrics.get("blank_lines", 0)),
    ]

    for col, (label, value) in zip(cols, metrics_display):
        with col:
            st.metric(label, value)
