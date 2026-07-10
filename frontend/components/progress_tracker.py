# EquiPilot AI - Progress Tracker Component
# Real-time research progress display

import time
from collections.abc import Callable
from typing import Any

import streamlit as st

from frontend.components.design_system_ui import alert_markdown

RESEARCH_STEPS = [
    # (step_id, step_name, phase_label_for_ui)
    ("router", "Entity Resolution", "Resolving entity"),
    ("market_data_tool", "Market Data", "Fetching market data"),
    ("news_tool", "News", "Fetching news"),
    ("sentiment_tool", "Sentiment", "Running sentiment analysis"),
    ("research", "Research", "Generating research report"),
    ("completed", "Completed", "Finalizing"),
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
    is_running = status in ("pending", "in_progress")

    st.markdown(
        '<div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4);">'
        '<div style="width:36px;height:36px;border-radius:var(--radius-md);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:1rem;">🔄</div>'
        '<div><div style="font-size:var(--font-size-xl);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Generating Research</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);">Running multi-agent analysis pipeline</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if is_running and show_spinner:
        st.markdown(
            '<div class="ds-state-card ds-state-card--info" style="margin-bottom:var(--space-5);">'
            '<div class="ds-state-card__icon">⏳</div>'
            '<div class="ds-state-card__body">'
            f'<div class="ds-state-card__title">Processing</div>'
            f'<div class="ds-state-card__detail" style="font-size:var(--font-size-sm);">{message or "Research in progress..."}</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    if show_steps:
        _render_step_progress(current_step)

    step_index = _get_step_index(current_step)
    progress = (step_index + 1) / len(RESEARCH_STEPS)
    st.progress(min(progress, 1.0))


def _render_step_progress(current_step: str):
    """Render visual step progress as a lightweight responsive stepper."""
    step_index = _get_step_index(current_step)

    cols = st.columns(len(RESEARCH_STEPS))
    for i, (step_id, step_name, _phase_label) in enumerate(RESEARCH_STEPS):
        with cols[i]:
            state_class = "ds-step"
            icon = str(i + 1)
            if i < step_index:
                state_class += " ds-step--done"
                icon = "✓"
            elif i == step_index:
                state_class += " ds-step--active"
                icon = "•"

            # Use design-system stepper classes (from design_system_ui.py)
            st.markdown(
                f"""
                <div class="{state_class}" style="text-align:center;">
                  <div class="ds-step__icon" aria-label="step {step_name}">{icon}</div>
                  <div class="ds-step__title">{step_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _get_step_index(step_id: str) -> int:
    """Get index of step in RESEARCH_STEPS."""
    for i, (sid, _step_name, _phase_label) in enumerate(RESEARCH_STEPS):
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
