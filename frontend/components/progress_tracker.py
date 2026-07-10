
# EquiPilot AI - Progress Tracker Component
# Animated research timeline with stage indicators

import time
from collections.abc import Callable
from typing import Any

import streamlit as st

from frontend.components.design_system_ui import safe_html_escape

RESEARCH_STEPS = [
    ("router", "Entity Resolution", "🔍", "Identifying company and resolving ticker"),
    ("market_data_tool", "Market Data", "📈", "Fetching real-time price and fundamentals"),
    ("news_tool", "News", "📰", "Aggregating latest headlines and press releases"),
    ("sentiment_tool", "Sentiment", "🧾", "Analyzing market sentiment and舆论 scoring"),
    ("research", "Research", "🧠", "Generating comprehensive AI report"),
    ("completed", "Completed", "✅", "Finalizing and structuring results"),
]


def _step_icon(step_id: str) -> str:
    for sid, _, icon, _ in RESEARCH_STEPS:
        if sid == step_id:
            return icon
    return "🔄"


def _step_desc(step_id: str) -> str:
    for sid, _, _, desc in RESEARCH_STEPS:
        if sid == step_id:
            return desc
    return "Processing..."


def _step_name(step_id: str) -> str:
    for sid, name, _, _ in RESEARCH_STEPS:
        if sid == step_id:
            return name
    return step_id.replace("_", " ").title()


def _get_step_index(step_id: str) -> int:
    for i, (sid, _, _, _) in enumerate(RESEARCH_STEPS):
        if sid == step_id:
            return i
    return -1


def render_progress(
    current_step: str,
    status: str = "in_progress",
    message: str = "",
    show_steps: bool = True,
    show_spinner: bool = True,
):
    """
    Render animated research progress timeline.
    """
    is_running = status in ("pending", "in_progress")
    step_index = _get_step_index(current_step)

    st.markdown(
        '<div class="ds-animate-slide-up" style="margin-bottom:var(--space-5);">'
        '<div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4);">'
        '<div style="width:36px;height:36px;border-radius:var(--radius-md);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:1rem;animation:spin 2s linear infinite;">🔄</div>'
        '<div><div style="font-size:var(--font-size-xl);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Generating Research</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);">Running multi-agent analysis pipeline</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Current stage card
    if is_running and current_step and current_step != "completed":
        stage_desc = _step_desc(current_step)
        stage_name = _step_name(current_step)
        stage_icon = _step_icon(current_step)
        pct = min(((step_index + 1) / len(RESEARCH_STEPS)) * 100, 100)

        st.markdown(
            f'<div class="ds-card ds-animate-scale-in" style="padding:var(--space-4);margin-bottom:var(--space-5);border-left:3px solid var(--primary);">'
            f'<div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-3);">'
            f'<div style="width:40px;height:40px;border-radius:var(--radius-md);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:1.25rem;animation:dsPulse 2s ease-in-out infinite;">{stage_icon}</div>'
            f'<div style="flex:1;">'
            f'<div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-base);">{safe_html_escape(stage_name)}</div>'
            f'<div style="font-size:var(--font-size-sm);color:var(--muted);">{safe_html_escape(stage_desc)}</div>'
            f'</div>'
            f'<div style="font-size:var(--font-size-sm);font-weight:var(--font-weight-semibold);color:var(--primary);">{pct:.0f}%</div>'
            f'</div>'
            f'<div style="height:4px;background:var(--border);border-radius:var(--radius-full);overflow:hidden;">'
            f'<div style="height:100%;width:{pct:.0f}%;background:linear-gradient(90deg,var(--primary),var(--primary-hover));border-radius:var(--radius-full);transition:width 0.5s ease;"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if is_running and show_spinner and message:
        st.markdown(
            f'<div class="ds-state-card ds-state-card--info" style="margin-bottom:var(--space-5);">'
            f'<div class="ds-state-card__icon ds-animate-spin" style="display:inline-block;">⏳</div>'
            f'<div class="ds-state-card__body">'
            f'<div class="ds-state-card__detail" style="font-size:var(--font-size-sm);color:var(--text);">{safe_html_escape(message)}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    if show_steps and step_index >= 0:
        _render_timeline_progress(current_step, step_index)

    progress = (step_index + 1) / len(RESEARCH_STEPS)
    st.progress(min(progress, 1.0))


def _render_timeline_progress(_current_step: str, step_index: int):
    """Render animated step progress as a visual timeline."""
    st.markdown(
        '<div style="font-weight:var(--font-weight-medium);font-size:var(--font-size-xs);color:var(--muted);'
        'text-transform:uppercase;letter-spacing:0.04em;margin-bottom:var(--space-3);margin-top:var(--space-4);">'
        'Research Pipeline</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(RESEARCH_STEPS))
    for i, (step_id, step_name, icon, desc) in enumerate(RESEARCH_STEPS):
        with cols[i]:
            state_class = "ds-step"
            display_icon = icon
            if i < step_index:
                state_class += " ds-step--done"
                display_icon = "✓"
            elif i == step_index:
                state_class += " ds-step--active"
                display_icon = icon

            anim = 'style="animation:scaleIn 0.3s ease-out forwards;"' if i <= step_index else ""

            st.markdown(
                f'<div class="{state_class}" {anim}>'
                f'<div class="ds-step__icon" aria-label="step {step_name}">{display_icon}</div>'
                f'<div class="ds-step__title">{step_name}</div>'
                f'<div class="ds-step__sub">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_polling_progress(
    check_status_fn: Callable[[str], dict[str, Any] | None],
    request_id: str,
    poll_interval: float = 2.0,
    max_polls: int = 60,
    on_complete: Callable[[dict[str, Any]], None] | None = None,
    on_error: Callable[[str], None] | None = None,
):
    """Render auto-polling progress tracker with live updates."""
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
                with status_placeholder.container():
                    st.markdown(
                        '<div class="ds-completion-badge ds-animate-scale-in" style="margin-bottom:var(--space-4);">'
                        "✅ Research completed successfully"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                if on_complete:
                    on_complete(status_data)
                return status_data

            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                with status_placeholder.container():
                    st.markdown(
                        f'<div class="ds-state-card ds-state-card--error ds-animate-slide-up" style="margin-bottom:var(--space-4);">'
                        f'<div class="ds-state-card__icon">❌</div>'
                        f'<div class="ds-state-card__body">'
                        f'<div class="ds-state-card__title">Research Failed</div>'
                        f'<div class="ds-state-card__detail">{safe_html_escape(str(error))}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                if on_error:
                    on_error(error)
                return status_data

        else:
            with status_placeholder.container():
                st.markdown(
                    '<div class="ds-state-card ds-state-card--warning" style="margin-bottom:var(--space-4);">'
                    '<div class="ds-state-card__icon">⏳</div>'
                    '<div class="ds-state-card__body">'
                    '<div class="ds-state-card__title">Waiting for Status</div>'
                    '<div class="ds-state-card__detail">Connecting to research service...</div>'
                    '</div></div>',
                    unsafe_allow_html=True,
                )

        time.sleep(poll_interval)

    error_placeholder.markdown(
        '<div class="ds-state-card ds-state-card--warning" style="margin-bottom:var(--space-4);">'
        '<div class="ds-state-card__icon">⏱️</div>'
        '<div class="ds-state-card__body">'
        '<div class="ds-state-card__title">Research Taking Longer Than Expected</div>'
        '<div class="ds-state-card__detail">The analysis is still running. You can check back later or submit a new request.</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
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
