
# EquiPilot AI - Streamlit Frontend
# Production dashboard (thin API client, no business logic in Streamlit)

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

import requests
import streamlit as st

# Streamlit Community Cloud may not add the repo root to sys.path.
# Ensure `import frontend...` and other absolute imports work reliably.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from frontend.components.progress_tracker import render_progress
from frontend.components.report_display import render_report
from frontend.components.sidebar import render_sidebar
from frontend.components.design_system_ui import inject_global_styles, safe_html_escape, title_brand

# API configuration — configurable via environment variable for production deployment
API_BASE_URL = os.environ.get("EQUIPILOT_API_URL", "").rstrip("/")
API_HEALTH_URL = os.environ.get("EQUIPILOT_HEALTH_URL", "").rstrip("/")


def build_backend_url(path: str, *, request_id: str | None = None) -> str:
    """
    Canonical backend URL builder for all frontend API calls.

    Handles EQUIPILOT_API_URL with or without '/api/v1' suffix.
    Avoids:
      - '/api/v1/api/v1'
      - missing '/api/v1'
      - manual string replacements spread across the codebase.

    This is intentionally a thin URL normalizer only (no business logic).
    """
    base = (API_BASE_URL or "").rstrip("/")
    if not base:
        return ""

    normalized_base = base
    # If base already contains '/api/v1' (anywhere at the end), keep it.
    if "/api/v1" in normalized_base:
        # Prevent duplicate '/api/v1' when callers pass '/api/v1/..' style paths.
        normalized_base = normalized_base.split("/api/v1", 1)[0] + "/api/v1"

    # Normalize path input.
    p = (path or "").lstrip("/")
    if request_id is not None:
        # Caller expects .../{request_id}
        # Ensure request_id is safe as a path segment (no schema changes).
        rid = str(request_id).strip().strip("/")
        p = f"{p}/{rid}"

    # If base doesn't include '/api/v1', ensure we add it exactly once.
    if "/api/v1" not in normalized_base:
        # Only add prefix when building non-empty API paths.
        normalized_base = normalized_base + "/api/v1"

    # Avoid double slashes.
    return f"{normalized_base}/{p}"

T = TypeVar("T")


def _get_logger() -> logging.Logger:
    """Create a production-safe logger (never crash Streamlit)."""
    try:
        logger_ = logging.getLogger("frontend")
        if not logger_.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            handler.setFormatter(formatter)
            logger_.addHandler(handler)
        logger_.setLevel(logging.INFO)
        return logger_
    except Exception:
        # As a last resort, return root logger; never fail import.
        return logging.getLogger()


_LOGGER = _get_logger()


def run_safely(
    fn: Callable[[], T],
    context: str,
    fallback: T,
    *,
    error_placeholder=None,
) -> T:
    """
    Execute fn() safely:
    - logs full stack trace on exception
    - shows friendly inline error (no traceback) near the failing component
    - returns provided fallback to keep the dashboard functional
    """
    try:
        return fn()
    except Exception as e:
        try:
            _LOGGER.exception("Frontend runtime failure in %s: %s", context, e)
        except Exception:
            # Never allow logging failure to break the UI
            pass

        # Inline friendly error near the component that failed.
        try:
            if error_placeholder is not None:
                error_placeholder.error(f"Something went wrong while {context}. Please try again.")
            else:
                st.error(f"Something went wrong while {context}. Please try again.")
        except Exception:
            pass

        return fallback


def main():
    initialize_session_state()
    st.set_page_config(
        page_title="EquiPilot AI — Equity Research Assistant",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_global_styles()

    render_header()
    render_disclaimer_bar()

    with st.sidebar:
        render_sidebar(on_analyze=handle_sidebar_submit)

    render_main_page()


def initialize_session_state():
    if "research_history" not in st.session_state:
        st.session_state.research_history = []

    if "current_request_id" not in st.session_state:
        st.session_state.current_request_id = None

    if "current_report" not in st.session_state:
        st.session_state.current_report = None

    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

    if "execution_trace" not in st.session_state:
        st.session_state.execution_trace = None

    if "show_tool_data" not in st.session_state:
        st.session_state.show_tool_data = {}

    if "max_report_length" not in st.session_state:
        st.session_state.max_report_length = 5000

    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = None

    # Request de-duplication + polling guards
    if "last_submit_fingerprint" not in st.session_state:
        st.session_state.last_submit_fingerprint = None
    if "poll_count" not in st.session_state:
        st.session_state.poll_count = 0
    if "poll_started_at" not in st.session_state:
        st.session_state.poll_started_at = None


def render_header():
    """Premium header with title, subtitle, and connection status."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">'
            '<div style="width:40px;height:40px;border-radius:var(--radius-lg);background:linear-gradient(135deg,var(--primary),var(--primary-hover));display:flex;align-items:center;justify-content:center;color:white;font-weight:var(--font-weight-bold);font-size:var(--font-size-sm);flex-shrink:0;">EP</div>'
            '<div><div style="font-size:var(--font-size-2xl);font-weight:var(--font-weight-semibold);letter-spacing:-0.03em;line-height:1.2;color:var(--text);">EquiPilot AI</div>'
            '<div style="font-size:var(--font-size-sm);color:var(--muted);margin-top:1px;">Agentic Equity Research Assistant</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div style="text-align:right;font-size:var(--font-size-xs);color:var(--muted);">'
            f'{datetime.utcnow().strftime("%b %d, %Y — %H:%M")} UTC</div>',
            unsafe_allow_html=True,
        )
        check_backend_connection()


def check_backend_connection() -> None:
    """Verify backend connectivity and display status indicator."""
    if st.session_state.backend_connected is None:
        # Streamlit Cloud cannot reach Railway via localhost; don't block rendering
        # unless the API URL is explicitly configured.
        if not API_HEALTH_URL:
            st.session_state.backend_connected = False
        else:
            try:
                # Preserve behavior: if EQUIPILOT_HEALTH_URL is explicitly provided, use it as-is.
                resp = requests.get(API_HEALTH_URL, timeout=3)
                st.session_state.backend_connected = (resp.status_code == 200)
            except requests.exceptions.RequestException:
                st.session_state.backend_connected = False

    if st.session_state.backend_connected is True:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:flex-end;gap:4px;font-size:var(--font-size-xs);color:var(--success);">'
            '<span style="width:6px;height:6px;border-radius:50%;background:var(--success);display:inline-block;"></span>'
            "API Connected</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:flex-end;gap:4px;font-size:var(--font-size-xs);color:var(--danger);">'
            '<span style="width:6px;height:6px;border-radius:50%;background:var(--danger);display:inline-block;"></span>'
            "API Disconnected</div>",
            unsafe_allow_html=True,
        )
        if API_BASE_URL:
            st.caption(f"URL: {API_BASE_URL}")
        else:
            st.caption("EQUIPILOT_API_URL not configured for this deployment.")


def render_disclaimer_bar():
    """Compact disclaimer bar at top of main content."""
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:var(--radius-md);background:var(--warning-light);border:1px solid var(--border);margin-bottom:var(--space-5);font-size:var(--font-size-xs);color:var(--muted);line-height:1.4;">
        <span style="font-size:14px;flex-shrink:0;">⚠️</span>
        <span>EquiPilot AI is an <strong>informational equity research assistant</strong>. Not investment advice. Always do your own due diligence.</span>
        </div>""",
        unsafe_allow_html=True,
    )


def _suggestion_card(icon: str, ticker: str, title: str, desc: str, query: str, analysis_type: str = "Full Research") -> str:
    """Interactive suggestion card that pre-fills sidebar form on click."""
    return f"""
    <div class="ds-suggestion" onclick="
      var inp = window.parent.document.querySelector('[data-testid=\\'stTextInput\\'] input');
      if(inp){{ var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; nativeInputValueSetter.call(inp, '{ticker}'); inp.dispatchEvent(new Event('input', {{ bubbles:true }})); }}
    " style="cursor:pointer;">
      <div class="ds-suggestion__icon">{icon}</div>
      <div class="ds-suggestion__title">{ticker} — {title}</div>
      <div class="ds-suggestion__desc">{desc}</div>
    </div>
    """


def render_empty_dashboard():
    """Render premium empty dashboard with guidance and quick actions."""
    from frontend.components.design_system_ui import (
        alert_markdown,
        quick_action_card,
    )

    # === Hero Section ===
    st.markdown(
        '<div class="ds-hero">'
        '<div class="ds-hero__title">Equity Research,<br>Reimagined with AI</div>'
        '<div class="ds-hero__subtitle">'
        "Enterprise-grade equity research powered by multi-agent orchestration. "
        "Analyze market data, news, sentiment, and fundamentals — all in one place."
        '</div>'
        '<div class="ds-hero__stats">'
        '<div class="ds-hero-stat"><span class="ds-hero-stat__value">📈</span> Real-time Market Data</div>'
        '<div class="ds-hero-stat"><span class="ds-hero-stat__value">📰</span> News &amp; Sentiment</div>'
        '<div class="ds-hero-stat"><span class="ds-hero-stat__value">🧠</span> AI-Powered Analysis</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # === Onboarding CTA ===
    st.markdown(
        '<div style="background:var(--panel);border:1px solid var(--border);border-radius:var(--radius-xl);padding:var(--space-6) var(--space-8);margin-bottom:var(--space-8);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-4);">'
        '<div><div style="font-size:var(--font-size-lg);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Get started in seconds</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);margin-top:2px;">Enter a ticker and question in the sidebar, or pick an example below.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # === Quick Start Examples (Interactive Suggestion Cards) ===
    st.markdown(
        '<div style="margin-bottom:var(--space-5);">'
        '<div style="font-size:var(--font-size-lg);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Quick Start Examples</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);margin-top:2px;">Click any example to pre-fill the sidebar and begin analysis</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="ds-suggestion">'
            '<div class="ds-suggestion__icon">📊</div>'
            '<div class="ds-suggestion__title">AAPL — Market Snapshot</div>'
            '<div class="ds-suggestion__desc">Fundamentals, valuation metrics, and competitive positioning in the tech sector.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Run AAPL Analysis", key="ex_aapl", use_container_width=True, type="secondary"):
            st.session_state["company_ticker_input"] = "AAPL"
            st.session_state["query_input"] = "Provide a comprehensive market overview with key metrics, valuation, and competitive positioning"
            st.session_state["analysis_type"] = "Full Research"
            st.rerun()

    with c2:
        st.markdown(
            '<div class="ds-suggestion">'
            '<div class="ds-suggestion__icon">📰</div>'
            '<div class="ds-suggestion__title">TSLA — News Catalysts</div>'
            '<div class="ds-suggestion__desc">Latest news headlines, sentiment analysis, and market-moving catalyst identification.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Run TSLA Analysis", key="ex_tsla", use_container_width=True, type="secondary"):
            st.session_state["company_ticker_input"] = "TSLA"
            st.session_state["query_input"] = "What are the latest news catalysts, sentiment drivers, and market-moving events?"
            st.session_state["analysis_type"] = "News"
            st.rerun()

    with c3:
        st.markdown(
            '<div class="ds-suggestion">'
            '<div class="ds-suggestion__icon">⚠️</div>'
            '<div class="ds-suggestion__title">MSFT — Risk Assessment</div>'
            '<div class="ds-suggestion__desc">Key investment risks, competitive threats, and regulatory challenges facing Microsoft.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Run MSFT Analysis", key="ex_msft", use_container_width=True, type="secondary"):
            st.session_state["company_ticker_input"] = "MSFT"
            st.session_state["query_input"] = "Identify key investment risks, competitive threats, and challenges to growth"
            st.session_state["analysis_type"] = "Full Research"
            st.rerun()

    st.markdown(f'<hr style="margin:var(--space-8) 0 !important;" />', unsafe_allow_html=True)

    # === Tip ===
    st.markdown(alert_markdown(
        '💡 Pro tip: Be specific in your queries. Instead of "Analyze AAPL", try "What are AAPL\'s key growth drivers and margin trends?"',
        kind="info",
    ), unsafe_allow_html=True)

    st.markdown(f'<hr style="margin:var(--space-8) 0 !important;" />', unsafe_allow_html=True)

    # === What You Get ===
    st.markdown(
        '<div style="margin-bottom:var(--space-5);">'
        '<div style="font-size:var(--font-size-lg);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Powered By</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);margin-top:2px;">Each analysis is generated through a multi-agent research pipeline</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(quick_action_card(
            icon="📈",
            title="Market Intelligence",
            description="Real-time price data, fundamentals, valuation ratios, and technical indicators from yfinance.",
            cta="Live market data",
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(quick_action_card(
            icon="📰",
            title="News & Sentiment",
            description="Aggregated headlines, entity-level sentiment scoring, and catalyst detection across major sources.",
            cta="News API integration",
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(quick_action_card(
            icon="🤖",
            title="AI Synthesis",
            description="Structured reports with executive summaries, risk analysis, and cited sources via LangGraph orchestration.",
            cta="GPT-4o powered",
        ), unsafe_allow_html=True)


def handle_sidebar_submit(form_data: dict[str, Any]) -> None:
    """
    Thin-client callback invoked by sidebar. Starts research on backend and
    triggers polling rendering in the main page.
    """

    def _impl() -> None:
        # Store for UI/debug
        st.session_state.analysis_form_data = form_data

        # Session state hardening (avoid missing-key crashes)
        current_max_length = st.session_state.get("max_report_length", 5000)
        max_length = form_data.get("max_report_length", current_max_length)
        st.session_state.max_report_length = max_length

        with st.spinner("Submitting research request..."):
            request_data = submit_research(
                query=form_data.get("query", ""),
                tickers=form_data.get("tickers"),
                include_news=form_data.get("include_news", True),
                include_sentiment=form_data.get("include_sentiment", True),
                include_fundamentals=form_data.get("include_fundamentals", True),
                include_technicals=form_data.get("include_technicals", False),
                max_length=max_length,
            )

        if not request_data:
            return

        req_id = request_data.get('request_id', 'N/A')[:12]
        st.markdown(
            f'<div class="ds-state-card ds-state-card--success" style="margin-bottom:var(--space-4);">'
            f'<div class="ds-state-card__icon">🚀</div>'
            f'<div class="ds-state-card__body">'
            f'<div class="ds-state-card__title">Research Started</div>'
            f'<div class="ds-state-card__detail">Request ID: {req_id}... — The analysis pipeline is now running.</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # New workflow: reset polling guards for this request
        st.session_state.poll_count = 0
        st.session_state.poll_started_at = datetime.utcnow().timestamp()

        st.session_state.current_request_id = request_data.get("request_id")
        st.session_state.is_processing = True
        st.session_state.current_report = None
        st.session_state.execution_trace = None

        history = st.session_state.get("research_history", [])
        if isinstance(history, list):
            history.append(
                {
                    "request_id": request_data.get("request_id"),
                    "query": form_data.get("query"),
                    "tickers": form_data.get("tickers") or [],
                    "status": request_data.get("status"),
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            st.session_state.research_history = history

        st.rerun()

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "sidebar submission", fallback=None, error_placeholder=error_ph)  # type: ignore[return-value]


def render_main_page():
    request_id = st.session_state.get("current_request_id")
    report = st.session_state.get("current_report")

    if st.session_state.get("is_processing") and request_id:
        render_loading_workflow(request_id)
        return

    if report:
        render_dashboard_sections(report)
        return

    render_empty_dashboard()


def render_loading_workflow(request_id: str) -> None:
    """
    Poll backend and render stage-based loading UI + execution trace live.

    Repair goals:
    - Prevent infinite rerun loops
    - Prevent duplicate polling bursts
    - Cap polling attempts
    """

    def _impl() -> None:
        from frontend.components.design_system_ui import alert_markdown, safe_html_escape

        # Polling guards (avoid infinite reruns)
        max_polls = 60  # ~2 minutes at 2s interval
        poll_interval_s = 2.0

        st.session_state.poll_count = int(st.session_state.get("poll_count", 0)) + 1
        poll_started_at = st.session_state.get("poll_started_at")
        if poll_started_at is not None:
            elapsed_s = max(0.0, time.time() - float(poll_started_at))
            if st.session_state.poll_count > max_polls or elapsed_s > (max_polls * poll_interval_s):
                st.session_state.is_processing = False
                st.markdown(
                    '<div class="ds-state-card ds-state-card--warning" style="margin-bottom:var(--space-4);">'
                    '<div class="ds-state-card__icon">⏱️</div>'
                    '<div class="ds-state-card__body">'
                    '<div class="ds-state-card__title">Research Timeout</div>'
                    '<div class="ds-state-card__detail">The research is taking longer than expected. You can submit a new request or check the backend status.</div>'
                    '</div></div>',
                    unsafe_allow_html=True,
                )
                return

        status_data = check_status(request_id)
        if not status_data:
            st.markdown(
                '<div class="ds-state-card ds-state-card--warning" style="margin-bottom:var(--space-4);">'
                '<div class="ds-state-card__icon">⏳</div>'
                '<div class="ds-state-card__body">'
                '<div class="ds-state-card__title">Waiting for backend</div>'
                '<div class="ds-state-card__detail">The research service is initializing. Retrying...</div>'
                '</div></div>',
                unsafe_allow_html=True,
            )
            time.sleep(1)
            st.rerun()
            return

        status = status_data.get("status", "unknown")
        execution_metadata = status_data.get("execution_metadata", {}) or {}
        current_step = status_data.get("current_step") or execution_metadata.get("current_step") or "router"

        stage_label = map_trace_step_to_stage(current_step)

        render_progress(
            current_step=current_step,
            status="in_progress" if status in ("pending", "in_progress") else status,
            message=f"Stage: {stage_label}",
            show_steps=True,
            show_spinner=True,
        )

        st.divider()
        render_execution_trace_explicit_partial(status_data)

        if status in ("completed", "success"):
            st.session_state.is_processing = False
            st.session_state.current_report = status_data
            st.session_state.execution_trace = execution_metadata
            st.rerun()
            return

        if status == "failed":
            st.session_state.is_processing = False
            err = status_data.get("error", status_data.get("message", "Unknown error"))
            st.markdown(
                '<div class="ds-state-card ds-state-card--error" style="margin-bottom:var(--space-4);">'
                '<div class="ds-state-card__icon">❌</div>'
                '<div class="ds-state-card__body">'
                '<div class="ds-state-card__title">Research Failed</div>'
                f'<div class="ds-state-card__detail">{safe_html_escape(str(err))}</div>'
                '</div></div>',
                unsafe_allow_html=True,
            )
            st.rerun()
            return

        time.sleep(poll_interval_s)
        st.rerun()

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "loading workflow", fallback=None, error_placeholder=error_ph)  # type: ignore[return-value]


def map_trace_step_to_stage(step_id: str) -> str:
    mapping = {
        "router": "Resolving entity",
        "entity_resolution_tool": "Resolving entity",
        "market_data_tool": "Fetching market data",
        "news_tool": "Fetching news",
        "sentiment_tool": "Running sentiment analysis",
        "research": "Generating research report",
        "completed": "Finalizing",
    }
    return mapping.get(step_id, "Processing")


def _data_section_card(title: str, icon: str, data: Any, empty_msg: str) -> None:
    """Render a premium collapsible data section card."""
    has_data = data is not None
    with st.container():
        st.markdown(
            f'<div class="ds-card" style="padding:var(--space-4);margin-bottom:var(--space-5);">'
            f'<div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-3);">'
            f'<div style="width:32px;height:32px;border-radius:var(--radius-md);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:1rem;">{icon}</div>'
            f'<div><div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);">{title}</div>'
            f'<div style="font-size:var(--font-size-xs);color:var(--muted);">{ "Structured data available" if has_data else "Not available" }</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if has_data:
            with st.expander("View Raw Data", expanded=False):
                st.json(data)
        else:
            st.markdown(
                f'<div style="font-size:var(--font-size-sm);color:var(--muted);padding:var(--space-3);text-align:center;">{empty_msg}</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


def render_dashboard_sections(report: dict[str, Any]) -> None:
    """
    Main page sections (required layout):
      - Market Data
      - News Headlines
      - Sentiment Analysis
      - AI Research Report
    """

    # === Report Header ===
    request_id = report.get("request_id", "N/A")[:12]
    status = str(report.get("status", "unknown")).title()
    tickers = report.get("tickers", [])
    created = report.get("created_at", "")
    if created:
        created = created[:16].replace("T", " ")

    st.markdown(
        '<div style="margin-bottom:var(--space-6);">'
        '<div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4);">'
        '<div style="width:36px;height:36px;border-radius:var(--radius-md);background:linear-gradient(135deg,var(--success),rgba(5,150,105,0.8));display:flex;align-items:center;justify-content:center;color:white;font-weight:var(--font-weight-bold);font-size:1rem;">✓</div>'
        '<div><div style="font-size:var(--font-size-xl);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Research Complete</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);">AI-generated equity research report</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # === KPI Row ===
    kpi_cols = st.columns(4)
    metrics_data = [
        ("Request ID", request_id + "...", ""),
        ("Status", status, ""),
        ("Tickers", str(len(tickers)) if tickers else "0", ""),
        ("Generated", created if created else "—", ""),
    ]
    for i, (label, value, _sublabel) in enumerate(metrics_data):
        with kpi_cols[i]:
            st.markdown(
                f'<div class="ds-kpi">'
                f'<div class="ds-kpi__label">{label}</div>'
                f'<div class="ds-kpi__value" style="font-size:var(--font-size-lg);">{value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(f'<hr style="margin:var(--space-6) 0 !important;" />', unsafe_allow_html=True)

    # === AI Research Report ===
    st.markdown(
        '<div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4);">'
        '<div style="width:32px;height:32px;border-radius:var(--radius-md);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:1rem;">🧠</div>'
        '<div><div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-base);">AI Research Report</div>'
        '<div style="font-size:var(--font-size-xs);color:var(--muted);">Full analysis generated by multi-agent pipeline</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    render_report(report, show_metadata=False, show_citations=True, expandable=False)

    st.markdown(f'<hr style="margin:var(--space-8) 0 !important;" />', unsafe_allow_html=True)

    # === Market Data ===
    market_data = report.get("market_data") or report.get("market_data_summary")
    _data_section_card("Market Data", "📈", market_data, "No market data available for this analysis.")

    # === News Headlines ===
    news_data = report.get("news_data") or report.get("news_summary")
    _data_section_card("News Headlines", "📰", news_data, "No news headlines available for this analysis.")

    # === Sentiment Analysis ===
    sentiment_data = report.get("sentiment_data") or report.get("sentiment_summary")
    _data_section_card("Sentiment Analysis", "🧾", sentiment_data, "No sentiment analysis available for this analysis.")


def _extract_execution_metadata_fields(report: dict[str, Any]) -> dict[str, Any]:
    execution_metadata = report.get("execution_metadata", {}) or {}
    traces = execution_metadata.get("traces", []) or []

    detected_intent = execution_metadata.get("detected_intent") or execution_metadata.get("intent") or None
    resolved_entity = execution_metadata.get("resolved_entity") or execution_metadata.get("entity") or None

    selected_tools = execution_metadata.get("selected_tools")
    skipped_tools = execution_metadata.get("skipped_tools")

    # Infer from trace node names if structured fields are missing
    if selected_tools is None:
        selected_tools = [t.get("node_name") for t in traces if t.get("success")]

    if skipped_tools is None:
        known_tools = {"router", "entity_resolution_tool", "market_data_tool", "news_tool", "sentiment_tool", "research"}
        selected_set = set(selected_tools or [])
        skipped_tools = sorted(list(known_tools - selected_set))

    execution_status = report.get("status") or execution_metadata.get("execution_status") or "unknown"

    total_ms = execution_metadata.get("execution_time_ms")
    if total_ms is None:
        total_ms = sum((t.get("duration_ms", 0) or 0) for t in traces)

    errors = execution_metadata.get("errors")
    if errors is None:
        errors = [t.get("error") for t in traces if t.get("error")]

    if isinstance(errors, list):
        errors = [e for e in errors if e]

    return {
        "detected_intent": detected_intent,
        "resolved_entity": resolved_entity,
        "selected_tools": selected_tools,
        "skipped_tools": skipped_tools,
        "execution_time_ms": total_ms,
        "execution_status": execution_status,
        "errors": errors,
    }


def _trace_timeline_item(icon: str, label: str, value: str, state: str = "default") -> str:
    """Render a single timeline item for the execution trace."""
    state_class = ""
    if state == "active":
        state_class = " ds-timeline__item--active"
    elif state == "done":
        state_class = " ds-timeline__item--done"
    elif state == "error":
        state_class = " ds-timeline__item--error"

    return f"""
    <div class="ds-timeline__item{state_class}">
      <div class="ds-timeline__dot">{icon}</div>
      <div class="ds-timeline__content">
        <div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);">{safe_html_escape(label)}</div>
        <div style="font-size:var(--font-size-xs);color:var(--muted);margin-top:2px;">{safe_html_escape(str(value))}</div>
      </div>
    </div>
    """


def render_execution_trace_explicit(report: dict[str, Any]) -> None:
    fields = _extract_execution_metadata_fields(report)

    with st.expander("🔍 Execution Trace", expanded=False):
        st.markdown(
            '<div class="ds-timeline">',
            unsafe_allow_html=True,
        )

        items = [
            ("🧠", "Detected Intent", fields["detected_intent"] or "Not available", "done" if fields["detected_intent"] else "default"),
            ("🏢", "Resolved Entity", fields["resolved_entity"] or "Not available", "done" if fields["resolved_entity"] else "default"),
        ]

        tools = fields.get("selected_tools", [])
        if tools:
            items.append(("🛠️", "Selected Tools", ", ".join(tools), "done"))

        skipped = fields.get("skipped_tools", [])
        if skipped:
            items.append(("⏭️", "Skipped Tools", ", ".join(skipped), "default"))

        status = fields.get("execution_status", "unknown")
        status_state = "done" if status in ("completed", "success") else ("error" if status in ("failed", "error") else "active")
        items.append(("📊", "Execution Status", str(status).title(), status_state))

        ms = fields.get("execution_time_ms")
        time_display = f"{float(ms)/1000:.2f}s" if ms is not None else "Not available"
        items.append(("⏱️", "Execution Time", time_display, "done" if ms else "default"))

        errs = fields.get("errors", [])
        if errs:
            items.append(("❌", "Errors", "; ".join(str(e) for e in errs), "error"))
        else:
            items.append(("✅", "Errors", "No errors", "done"))

        for icon, label, value, state in items:
            st.markdown(_trace_timeline_item(icon, label, value, state), unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def _render_timing_report_from_metadata(execution_metadata: dict[str, Any]) -> None:
    """
    Render a stage timing report from execution metadata.
    """
    nodes = execution_metadata.get("nodes", {}) or {}
    tools = execution_metadata.get("tools", {}) or {}
    traces = execution_metadata.get("traces", []) or []

    def _duration_ms(v: Any) -> float | None:
        try:
            if v is None:
                return None
            return float(v)
        except Exception:
            return None

    def _sum_node_like(keys: list[str]) -> float:
        total = 0.0
        for k in keys:
            n = nodes.get(k) or {}
            d = _duration_ms(n.get("duration_ms"))
            if d is not None:
                total += d
        return total

    router_ms = _sum_node_like(["router"])
    research_ms = _sum_node_like(["research"])
    merge_ms = _sum_node_like(["merge_results"])

    def _tool_ms(tool_name: str) -> float:
        t = tools.get(tool_name) or {}
        d = _duration_ms(t.get("duration_ms"))
        if d is not None:
            return d
        return 0.0

    market_ms = _tool_ms("market_data_tool")
    news_ms = _tool_ms("news_tool")
    sentiment_ms = _tool_ms("sentiment_tool")

    trace_total = 0.0
    for tr in traces:
        dur = _duration_ms(tr.get("duration_ms"))
        trace_total += dur or 0.0

    st.markdown(
        '<div style="display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-3);">'
        '<span style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);">⏱️ Timing Report</span>'
        '<span style="font-size:var(--font-size-xs);color:var(--muted);">Stage durations from execution metadata</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    rows = [
        ("Router / Entity Resolution", router_ms, "🔍"),
        ("Market Data Retrieval", market_ms, "📈"),
        ("News Collection", news_ms, "📰"),
        ("Sentiment Analysis", sentiment_ms, "🧾"),
        ("LLM Research", research_ms, "🧠"),
        ("Merge Results", merge_ms, "🔗"),
    ]

    # Sort by duration descending for better scanning
    rows_sorted = sorted(rows, key=lambda r: r[1], reverse=True)
    max_ms = max((r[1] for r in rows_sorted), default=1)

    for stage, ms, icon in rows_sorted:
        pct = (ms / max_ms * 100) if max_ms > 0 else 0
        bar_color = "var(--primary)" if ms > 0 else "var(--border)"
        st.markdown(
            f'<div style="margin-bottom:var(--space-2);">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">'
            f'<span style="font-size:var(--font-size-xs);color:var(--text);">{icon} {stage}</span>'
            f'<span style="font-size:var(--font-size-xs);font-weight:var(--font-weight-medium);color:var(--text);font-variant-numeric:tabular-nums;">{ms:.1f} ms</span>'
            f'</div>'
            f'<div style="height:4px;background:var(--border);border-radius:var(--radius-full);overflow:hidden;">'
            f'<div style="height:100%;width:{pct:.0f}%;background:{bar_color};border-radius:var(--radius-full);transition:width 0.5s ease;"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    total_backend_ms = execution_metadata.get("execution_time_ms")
    if total_backend_ms is not None or trace_total > 0:
        st.markdown(
            f'<div style="display:flex;gap:var(--space-6);margin-top:var(--space-3);padding-top:var(--space-3);border-top:1px solid var(--border);font-size:var(--font-size-xs);color:var(--muted);">'
            + (f'<span>Total: <strong>{float(total_backend_ms):.1f} ms</strong></span>' if total_backend_ms is not None else "")
            + (f'<span>Traces: <strong>{trace_total:.1f} ms</strong></span>' if trace_total > 0 else "")
            + f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()


def render_execution_trace_explicit_partial(status_data: dict[str, Any]) -> None:
    def _impl() -> None:
        fields = _extract_execution_metadata_fields(status_data)

        execution_metadata = status_data.get("execution_metadata", {}) or {}
        with st.expander("⏱️ Timing Report (Live)", expanded=False):
            _render_timing_report_from_metadata(execution_metadata)

        with st.expander("🔍 Execution Trace (Live)", expanded=False):
            st.markdown(
                '<div class="ds-timeline">',
                unsafe_allow_html=True,
            )

            items = [
                ("🧠", "Detected Intent", fields["detected_intent"] or "Not available", "done" if fields["detected_intent"] else "default"),
                ("🏢", "Resolved Entity", fields["resolved_entity"] or "Not available", "done" if fields["resolved_entity"] else "default"),
            ]

            tools = fields.get("selected_tools", [])
            if tools:
                items.append(("🛠️", "Selected Tools", ", ".join(str(x) for x in tools), "done"))

            skipped = fields.get("skipped_tools", [])
            if skipped:
                items.append(("⏭️", "Skipped Tools", ", ".join(str(x) for x in skipped), "default"))

            status = fields.get("execution_status", "unknown")
            status_state = "done" if status in ("completed", "success") else ("error" if status in ("failed", "error") else "active")
            items.append(("📊", "Execution Status", str(status).title(), status_state))

            ms = fields.get("execution_time_ms")
            time_display = f"{float(ms)/1000:.2f}s" if ms is not None else "Not available"
            items.append(("⏱️", "Execution Time", time_display, "done" if ms else "default"))

            errs = fields.get("errors", [])
            if errs:
                items.append(("❌", "Errors", "; ".join(str(e) for e in errs), "error"))
            else:
                items.append(("✅", "Errors", "No errors", "done"))

            for icon, label, value, state in items:
                st.markdown(_trace_timeline_item(icon, label, value, state), unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "execution trace", fallback=None, error_placeholder=error_ph)  # type: ignore[return-value]


def submit_research(
    query: str,
    tickers: list[str] | None = None,
    include_news: bool = True,
    include_sentiment: bool = True,
    include_fundamentals: bool = True,
    include_technicals: bool = False,
    max_length: int = 5000,
) -> dict[str, Any] | None:
    """
    Submit research request to backend API.
    Thin client: no business logic here.

    Repair goal: de-duplicate repeated submits that can happen from Streamlit reruns.
    """

    def _impl() -> dict[str, Any] | None:
        payload = {
            "query": (query or "").strip(),
            "tickers": tickers,
            "include_news": include_news,
            "include_sentiment": include_sentiment,
            "include_fundamentals": include_fundamentals,
            "include_technicals": include_technicals,
            "max_report_length": max_length,
        }

        if not API_BASE_URL:
            st.error("Backend API URL is not configured for this deployment.")
            return None

        # Fingerprint for dedup
        fingerprint = str(
            (
                payload.get("query"),
                payload.get("tickers"),
                payload.get("include_news"),
                payload.get("include_sentiment"),
                payload.get("include_fundamentals"),
                payload.get("include_technicals"),
                payload.get("max_report_length"),
            )
        )

        # If we're already processing the same payload, block duplicate POST.
        if st.session_state.get("is_processing") and st.session_state.get("last_submit_fingerprint") == fingerprint:
            st.info("Request is already in progress; skipping duplicate submit.")
            return None

        # If we have a current in-flight request, also avoid submitting again for same fingerprint.
        st.session_state.last_submit_fingerprint = fingerprint

        url = build_backend_url("research")
        last_exc: Exception | None = None
        last_response: requests.Response | None = None

        try:
            response = requests.post(url, json=payload, timeout=30)
            last_response = response
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            last_exc = e

        if last_response is not None:
            st.markdown(
                f'<div class="ds-state-card ds-state-card--error ds-animate-slide-up" style="margin-bottom:var(--space-4);">'
                f'<div class="ds-state-card__icon">❌</div>'
                f'<div class="ds-state-card__body">'
                f'<div class="ds-state-card__title">API Error ({last_response.status_code})</div>'
                f'<div class="ds-state-card__detail">{safe_html_escape(last_response.text[:500])}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            err_msg = f"{last_exc!s}" if last_exc else "API Error"
            st.markdown(
                f'<div class="ds-state-card ds-state-card--error ds-animate-slide-up" style="margin-bottom:var(--space-4);">'
                f'<div class="ds-state-card__icon">❌</div>'
                f'<div class="ds-state-card__body">'
                f'<div class="ds-state-card__title">API Error</div>'
                f'<div class="ds-state-card__detail">{safe_html_escape(err_msg)}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        return None

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "submit research", fallback=None, error_placeholder=error_ph)


def check_status(request_id: str) -> dict[str, Any] | None:
    """Check research status (thin client)."""

    def _impl() -> dict[str, Any] | None:
        url = build_backend_url("research", request_id=request_id)

        last_response: requests.Response | None = None
        last_exc: Exception | None = None

        try:
            response = requests.get(url, timeout=5)
            last_response = response
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            last_exc = e

        if last_response is not None:
            st.markdown(
                f'<div class="ds-state-card ds-state-card--error ds-animate-slide-up" style="margin-bottom:var(--space-4);">'
                f'<div class="ds-state-card__icon">❌</div>'
                f'<div class="ds-state-card__body">'
                f'<div class="ds-state-card__title">Status API Error ({last_response.status_code})</div>'
                f'<div class="ds-state-card__detail">{safe_html_escape(last_response.text[:500])}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            err_msg = f"{last_exc!s}" if last_exc else "Status API Error"
            st.markdown(
                f'<div class="ds-state-card ds-state-card--error ds-animate-slide-up" style="margin-bottom:var(--space-4);">'
                f'<div class="ds-state-card__icon">❌</div>'
                f'<div class="ds-state-card__body">'
                f'<div class="ds-state-card__title">Status API Error</div>'
                f'<div class="ds-state-card__detail">{safe_html_escape(err_msg)}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        return None

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "check status", fallback=None, error_placeholder=error_ph)


if __name__ == "__main__":
    main()
