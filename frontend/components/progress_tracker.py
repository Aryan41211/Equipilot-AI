# EquiPilot AI - Progress Tracker Component
# Real-time research progress display

import time
from collections.abc import Callable
from typing import Any

import streamlit as st

from frontend.components.design_system_ui import alert_markdown

RESEARCH_STEPS = [
    ("router", "Entity Resolution"),
    ("market_data_tool", "Market Data"),
    ("news_tool", "News"),
    ("sentiment_tool", "Sentiment"),
    ("research", "Research"),
    ("completed", "Completed"),
]


def render_progress(
    current_step: str,
    status: str = "in_progress",
    message: str = "",
    show_steps: bool = True,
    show_spinner: bool = True,
):
    """
    Render progress tracker for research workflow.

    Args:
        current_step: Current step identifier
        status: "pending", "in_progress", "completed", "failed"
        message: Optional status message
        show_steps: Show step progress bar
        show_spinner: Show spinner for in-progress
    """
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## Research {status.replace('_', ' ').title()}")
    with col2:
        if status == "in_progress" and show_spinner:
            st.spinner("Processing…")

    if message:
        st.markdown(alert_markdown(message, kind="info"), unsafe_allow_html=True)

    if show_steps:
        _render_step_progress(current_step)

    step_index = _get_step_index(current_step)
    progress = (step_index + 1) / len(RESEARCH_STEPS)
    st.progress(min(progress, 1.0))


def _render_step_progress(current_step: str):
    """Render visual step progress."""
    step_index = _get_step_index(current_step)

    cols = st.columns(len(RESEARCH_STEPS))
    for i, (step_id, step_name) in enumerate(RESEARCH_STEPS):
        with cols[i]:
            if i < step_index:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 10px;">
                        <div style="font-weight: 800;">✓</div>
                        <div style="font-size: 12px; color: gray;">{step_name}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif i == step_index:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 10px;">
                        <div style="font-weight: 800; color: var(--accent-2);">•</div>
                        <div style="font-size: 12px; font-weight: 800;">{step_name}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 10px; opacity: 0.3;">
                        <div style="font-weight: 800;">•</div>
                        <div style="font-size: 12px; color: lightgray;">{step_name}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _get_step_index(step_id: str) -> int:
    """Get index of step in RESEARCH_STEPS."""
    for i, (sid, _step_name) in enumerate(RESEARCH_STEPS):
        if sid == step_id:
            return i
    return -1


def render_polling_progress(
    check_status_fn: Callable[[str], dict[str, Any] | None],
    request_id: str,
    poll_interval: float = 2.0,
    max_polls: int = 60,
    on_complete: Callable[[dict[str, Any]], None] | None = None,
    on_error: Callable[[str], None] | None = None,
):
    """
    Render auto-polling progress tracker.

    Args:
        check_status_fn: Function that takes request_id and returns status dict or None
        request_id: Request identifier
        poll_interval: Seconds between polls
        max_polls: Maximum number of polls
        on_complete: Callback(report_dict) when completed
        on_error: Callback(error_message) when failed
    """
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    error_placeholder = st.empty()

    for _ in range(max_polls):
        status_data = check_status_fn(request_id)

        if status_data:
            current_step = status_data.get("current_step", "router")
            status = status_data.get("status", "in_progress")

            with progress_placeholder.container():
                render_progress(current_step, status)

            if status in ("completed", "success"):
                status_placeholder.success("✅ Research completed!")
                if on_complete:
                    on_complete(status_data)
                return status_data

            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                status_placeholder.error(f"❌ Research failed: {error}")
                if on_error:
                    on_error(error)
                return status_data

        else:
            with status_placeholder.container():
                st.warning("Waiting for status...")

        time.sleep(poll_interval)

    error_placeholder.warning("⏱️ Research is taking longer than expected. Check History tab.")
    return None


def render_simple_progress(
    completed_steps: int,
    total_steps: int,
    current_step_name: str = "",
):
    """Render simple progress bar with step info."""
    progress = completed_steps / total_steps if total_steps > 0 else 0
    st.progress(progress)

    if current_step_name:
        st.caption(f"Step {completed_steps}/{total_steps}: {current_step_name}")
    else:
        st.caption(f"Progress: {completed_steps}/{total_steps} steps")
