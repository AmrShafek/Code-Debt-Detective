"""
Diff viewer component for displaying code changes
"""

import streamlit as st
import difflib


def render_diff_viewer(old_text: str, new_text: str, language: str = "python"):
    """Render a side-by-side diff of code changes

    Args:
        old_text: Original code
        new_text: Modified code
        language: Programming language for syntax highlighting
    """
    if not old_text and not new_text:
        st.info("No diff to display")
        return

    diff = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile="original",
        tofile="modified"
    )

    diff_text = "".join(diff)
    if not diff_text:
        st.success("No differences found")
        return

    st.code(diff_text, language="diff")


def render_inline_diff(old_text: str, new_text: str):
    """Render an inline, word-level diff

    Args:
        old_text: Original text
        new_text: Modified text
    """
    if old_text == new_text:
        st.caption("No changes")
        return

    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    html_parts = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            html_parts.append(old_text[i1:i2])
        elif op == "replace":
            html_parts.append(
                f'<span style="background: #ff444444; text-decoration: line-through;">'
                f'{old_text[i1:i2]}</span>'
            )
            html_parts.append(
                f'<span style="background: #44ff4444;">{new_text[j1:j2]}</span>'
            )
        elif op == "delete":
            html_parts.append(
                f'<span style="background: #ff444444; text-decoration: line-through;">'
                f'{old_text[i1:i2]}</span>'
            )
        elif op == "insert":
            html_parts.append(
                f'<span style="background: #44ff4444;">{new_text[j1:j2]}</span>'
            )

    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_diff_summary(changes: list):
    """Render a summary of changes from analysis

    Args:
        changes: List of change dicts with 'file', 'type', 'description'
    """
    if not changes:
        st.caption("No changes to display")
        return

    for change in changes:
        cols = st.columns([1, 3, 6])
        with cols[0]:
            change_type = change.get("type", "modify")
            if change_type == "add":
                st.markdown(":green[**+ ADD**]")
            elif change_type == "delete":
                st.markdown(":red[**- DEL**]")
            else:
                st.markdown(":blue[**~ MOD**]")
        with cols[1]:
            st.code(change.get("file", ""), language="")
        with cols[2]:
            st.caption(change.get("description", ""))
