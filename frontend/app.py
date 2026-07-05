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
from frontend.components.design_system_ui import inject_global_styles, title_brand

# API configuration — configurable via environment variable for production deployment
API_BASE_URL = os.environ.get("EQUIPILOT_API_URL", "").rstrip("/")
API_HEALTH_URL = os.environ.get("EQUIPILOT_HEALTH_URL", "").rstrip("/")

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
        page_title="EquiPilot AI - Equity Research Assistant",
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
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 EquiPilot AI")
        st.caption("Agentic Equity Research Assistant")
    with col2:
        st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
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
                resp = requests.get(API_HEALTH_URL, timeout=3)
                st.session_state.backend_connected = (resp.status_code == 200)
            except requests.exceptions.RequestException:
                st.session_state.backend_connected = False

    if st.session_state.backend_connected is True:
        st.markdown("🟢 **API Connected**")
    else:
        st.markdown("🔴 **API Disconnected**")
        if API_BASE_URL:
            st.caption(f"URL: {API_BASE_URL}")
        else:
            st.caption("EQUIPILOT_API_URL not configured for this deployment.")


def render_disclaimer_bar():
    """Compact disclaimer bar at top of main content."""
    st.markdown(
        f"""<div style="padding: 0.5rem 0.75rem; border-radius: var(--radius-md); background: var(--error-bg); border: 1px solid var(--border); margin-bottom: 1rem; font-size: var(--font-size-sm); color: var(--muted);">
        <span style="color: var(--danger); font-weight: var(--font-weight-semibold);">⚠️ Disclaimer:</span> EquiPilot AI is an informational equity research assistant. Not investment advice.
        </div>""",
        unsafe_allow_html=True,
    )


def render_empty_dashboard():
    """Render empty dashboard with guidance and quick actions."""
    from frontend.components.design_system_ui import (
        alert_markdown,
        section_header,
        quick_action_card,
    )

    st.markdown(section_header("AI Research Dashboard", "Enterprise-grade equity research platform."), unsafe_allow_html=True)

    # Primary CTA Card
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1rem 0 1.5rem 0;
    ">
        <div style="font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); color: white; margin-bottom: 0.5rem;">
            🚀 Start Your First Analysis
        </div>
        <div style="font-size: var(--font-size-sm); color: rgba(255,255,255,0.9); margin-bottom: 1rem;">
            Enter a company name or ticker and your research question in the sidebar to generate a comprehensive AI-powered equity report.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(alert_markdown(
        "💡 Tip: Try queries like \"What are AAPL's key growth drivers?\" or \"Analyze TSLA's competitive risks\"",
        kind="info",
    ), unsafe_allow_html=True)

    st.divider()

    # Example queries with direct sidebar pre-fill buttons
    st.markdown(section_header("Quick Start Examples", "Click any example to pre-fill the sidebar form"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📈 AAPL Market Snapshot", key="ex_aapl", use_container_width=True):
            st.session_state["company_ticker_input"] = "AAPL"
            st.session_state["query_input"] = "Provide a comprehensive market overview with key metrics and valuation"
            st.session_state["analysis_type"] = "Full Research"
            st.rerun()
        st.caption("Full fundamentals + market data + news")

    with col2:
        if st.button("📰 TSLA News Catalysts", key="ex_tsla", use_container_width=True):
            st.session_state["company_ticker_input"] = "TSLA"
            st.session_state["query_input"] = "What are the latest news catalysts and sentiment drivers?"
            st.session_state["analysis_type"] = "News"
            st.rerun()
        st.caption("News-focused analysis with sentiment")

    with col3:
        if st.button("📊 MSFT Investment Risks", key="ex_msft", use_container_width=True):
            st.session_state["company_ticker_input"] = "MSFT"
            st.session_state["query_input"] = "Identify key investment risks and competitive threats"
            st.session_state["analysis_type"] = "Full Research"
            st.rerun()
        st.caption("Risk-focused comprehensive analysis")

    st.divider()

    # Feature cards below examples
    st.markdown(section_header("What You Get", "Each analysis delivers"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(quick_action_card(
            icon="📈",
            title="Market Data",
            description="Real-time price, volume, fundamentals, and valuation metrics",
            cta="Live data from yfinance",
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(quick_action_card(
            icon="📰",
            title="News & Sentiment",
            description="Latest headlines, sentiment scoring, and catalyst identification",
            cta="News API integration",
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(quick_action_card(
            icon="🤖",
            title="AI Synthesis",
            description="Structured report: executive summary, risks, opportunities, citations",
            cta="LangGraph orchestration",
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

        st.success(f"Research started! Request ID: {request_data.get('request_id', 'N/A')[:12]}...")

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
        from frontend.components.design_system_ui import alert_markdown

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
                    alert_markdown(
                        "⏱️ Research is taking longer than expected. Stop polling.",
                        kind="warning",
                    ),
                    unsafe_allow_html=True,
                )
                return

        status_data = check_status(request_id)
        if not status_data:
            st.markdown(alert_markdown("Waiting for backend response...", kind="warning"), unsafe_allow_html=True)
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
            st.markdown(alert_markdown(str(err), kind="danger"), unsafe_allow_html=True)
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


def render_dashboard_sections(report: dict[str, Any]) -> None:
    """
    Main page sections (required layout):
      - Market Data
      - News Headlines
      - Sentiment Analysis
      - AI Research Report
    """
    # AI Research Report
    st.write("## AI Research Report")
    render_report(report, show_metadata=True, show_citations=True, expandable=False)
    st.divider()

    # Market Data
    st.write("## Market Data")
    market_data = report.get("market_data") or report.get("market_data_summary")
    if market_data:
        st.json(market_data)
    else:
        st.caption("No market data available.")
    st.divider()

    # News Headlines
    st.write("## News Headlines")
    news_data = report.get("news_data") or report.get("news_summary")
    if news_data:
        st.json(news_data)
    else:
        st.caption("No news data available.")
    st.divider()

    # Sentiment Analysis
    st.write("## Sentiment Analysis")
    sentiment_data = report.get("sentiment_data") or report.get("sentiment_summary")
    if sentiment_data:
        st.json(sentiment_data)
    else:
        st.caption("No sentiment analysis available.")


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


def render_execution_trace_explicit(report: dict[str, Any]) -> None:
    fields = _extract_execution_metadata_fields(report)

    with st.expander("🔍 Execution Trace", expanded=True):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Detected Intent**")
            st.write(fields["detected_intent"] or "Not available")

            st.markdown("**Resolved Entity**")
            st.write(fields["resolved_entity"] or "Not available")

            st.markdown("**Execution Status**")
            st.write(str(fields["execution_status"]).title())

        with c2:
            st.markdown("**Selected Tools**")
            st.write(", ".join(fields["selected_tools"]) if fields["selected_tools"] else "Not available")

            st.markdown("**Skipped Tools**")
            st.write(", ".join(fields["skipped_tools"]) if fields["skipped_tools"] else "Not available")

            st.markdown("**Execution Time**")
            ms = fields.get("execution_time_ms")
            if ms is None:
                st.write("Not available")
            else:
                st.write(f"{float(ms)/1000:.2f}s")

        st.markdown("**Errors**")
        errs = fields["errors"]
        if errs:
            for e in errs:
                st.error(str(e))
        else:
            st.write("No errors")


def render_execution_trace_explicit_partial(status_data: dict[str, Any]) -> None:
    def _impl() -> None:
        fields = _extract_execution_metadata_fields(status_data)

        with st.expander("🔍 Execution Trace (Live)", expanded=False):
            st.markdown("**Detected Intent**")
            st.write(fields["detected_intent"] or "Not available")

            st.markdown("**Resolved Entity**")
            st.write(fields["resolved_entity"] or "Not available")

            st.markdown("**Selected Tools**")
            st.write(", ".join([str(x) for x in (fields["selected_tools"] or [])]) if fields["selected_tools"] else "Not available")

            st.markdown("**Skipped Tools**")
            st.write(", ".join([str(x) for x in (fields["skipped_tools"] or [])]) if fields["skipped_tools"] else "Not available")

            st.markdown("**Execution Status**")
            st.write(str(fields["execution_status"]).title())

            st.markdown("**Execution Time**")
            ms = fields.get("execution_time_ms")
            if ms is None:
                st.write("Not available")
            else:
                st.write(f"{float(ms)/1000:.2f}s")

            st.markdown("**Errors**")
            errs = fields["errors"]
            if errs:
                for e in errs:
                    st.error(str(e))
            else:
                st.write("No errors")

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

        # Backend routes are under settings.api_prefix (default: /api/v1).
        # API_BASE_URL may or may not already include that prefix.
        candidate_posts = [
            f"{API_BASE_URL}/research",
            f"{API_BASE_URL}/api/v1/research",
        ]

        last_exc: Exception | None = None
        last_response: requests.Response | None = None

        for url in candidate_posts:
            try:
                response = requests.post(url, json=payload, timeout=30)
                last_response = response
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                last_exc = e

        if last_response is not None:
            st.error(f"API Error: {last_response.status_code} - {last_response.text}")
        else:
            st.error(f"API Error: {last_exc!s}" if last_exc else "API Error")
        return None

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "submit research", fallback=None, error_placeholder=error_ph)


def check_status(request_id: str) -> dict[str, Any] | None:
    """Check research status (thin client)."""

    def _impl() -> dict[str, Any] | None:
        if not API_BASE_URL:
            return None

        candidate_gets = [
            f"{API_BASE_URL}/research/{request_id}",
            f"{API_BASE_URL}/api/v1/research/{request_id}",
        ]

        last_response: requests.Response | None = None
        last_exc: Exception | None = None

        for url in candidate_gets:
            try:
                response = requests.get(url, timeout=5)
                last_response = response
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                last_exc = e

        if last_response is not None:
            st.error(f"API Error: {last_response.status_code} - {last_response.text}")
        else:
            st.error(f"API Error: {last_exc!s}" if last_exc else "API Error")

        return None

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "check status", fallback=None, error_placeholder=error_ph)


if __name__ == "__main__":
    main()
