
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


def render_empty_dashboard():
    """Render premium empty dashboard with guidance and quick actions."""
    from frontend.components.design_system_ui import (
        alert_markdown,
        section_header,
        quick_action_card,
    )

    # === Hero Section ===
    st.markdown(
        '<div style="margin-bottom:var(--space-6);">'
        '<div style="font-size:var(--font-size-3xl);font-weight:var(--font-weight-semibold);letter-spacing:-0.03em;line-height:1.25;color:var(--text);">AI Research Dashboard</div>'
        '<div style="font-size:var(--font-size-base);color:var(--muted);margin-top:4px;">Enterprise-grade equity research powered by multi-agent orchestration.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # === Primary CTA Card ===
    st.markdown(
        '<div style="'
        'background:linear-gradient(135deg,var(--primary) 0%,var(--primary-hover) 100%);'
        'border-radius:var(--radius-xl);padding:var(--space-8);'
        'margin:0 0 var(--space-6) 0;position:relative;overflow:hidden;'
        '">'
        '<div style="position:absolute;top:-50%;right:-20%;width:300px;height:300px;border-radius:50%;background:rgba(255,255,255,0.05);"></div>'
        '<div style="position:absolute;bottom:-30%;left:-10%;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,0.03);"></div>'
        '<div style="font-size:var(--font-size-xl);font-weight:var(--font-weight-semibold);color:white;margin-bottom:var(--space-2);letter-spacing:-0.02em;position:relative;z-index:1;">Start Your First Analysis</div>'
        '<div style="font-size:var(--font-size-sm);color:rgba(255,255,255,0.85);line-height:1.5;margin-bottom:var(--space-4);position:relative;z-index:1;max-width:80%;">'
        "Enter a company name or ticker and your research question in the sidebar to generate a comprehensive AI-powered equity report."
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # === Tip ===
    st.markdown(alert_markdown(
        'Tip: Try queries like "What are AAPL\'s key growth drivers?" or "Analyze TSLA\'s competitive risks"',
        kind="info",
    ), unsafe_allow_html=True)

    st.markdown(f'<hr style="margin:var(--space-8) 0 !important;" />', unsafe_allow_html=True)

    # === Quick Start Examples ===
    st.markdown(
        '<div style="margin-bottom:var(--space-5);">'
        '<div style="font-size:var(--font-size-lg);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">Quick Start Examples</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);margin-top:2px;">Click any example to pre-fill the sidebar form</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div style="border:1px solid var(--border);border-radius:var(--radius-lg);padding:var(--space-4);background:var(--panel);">',
            unsafe_allow_html=True,
        )
        if st.button("AAPL Market Snapshot", key="ex_aapl", use_container_width=True):
            st.session_state["company_ticker_input"] = "AAPL"
            st.session_state["query_input"] = "Provide a comprehensive market overview with key metrics and valuation"
            st.session_state["analysis_type"] = "Full Research"
            st.rerun()
        st.caption("Fundamentals + market data + news")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(
            '<div style="border:1px solid var(--border);border-radius:var(--radius-lg);padding:var(--space-4);background:var(--panel);">',
            unsafe_allow_html=True,
        )
        if st.button("TSLA News Catalysts", key="ex_tsla", use_container_width=True):
            st.session_state["company_ticker_input"] = "TSLA"
            st.session_state["query_input"] = "What are the latest news catalysts and sentiment drivers?"
            st.session_state["analysis_type"] = "News"
            st.rerun()
        st.caption("News-focused analysis with sentiment")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown(
            '<div style="border:1px solid var(--border);border-radius:var(--radius-lg);padding:var(--space-4);background:var(--panel);">',
            unsafe_allow_html=True,
        )
        if st.button("MSFT Investment Risks", key="ex_msft", use_container_width=True):
            st.session_state["company_ticker_input"] = "MSFT"
            st.session_state["query_input"] = "Identify key investment risks and competitive threats"
            st.session_state["analysis_type"] = "Full Research"
            st.rerun()
        st.caption("Risk-focused comprehensive analysis")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<hr style="margin:var(--space-8) 0 !important;" />', unsafe_allow_html=True)

    # === What You Get ===
    st.markdown(
        '<div style="margin-bottom:var(--space-5);">'
        '<div style="font-size:var(--font-size-lg);font-weight:var(--font-weight-semibold);letter-spacing:-0.02em;">What You Get</div>'
        '<div style="font-size:var(--font-size-sm);color:var(--muted);margin-top:2px;">Each analysis delivers structured, actionable insights</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(quick_action_card(
            icon="📈",
            title="Market Data",
            description="Real-time price, volume, fundamentals, and valuation metrics",
            cta="Powered by yfinance",
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


def _render_timing_report_from_metadata(execution_metadata: dict[str, Any]) -> None:
    """
    Render a stage timing report from execution metadata.

    Contract:
    - Does not mutate API responses
    - Uses only execution_metadata.nodes/tools/traces when present
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

    # Node timing (best-effort)
    router_ms = _sum_node_like(["router"])
    research_ms = _sum_node_like(["research"])
    merge_ms = _sum_node_like(["merge_results"])

    # Tool timing (best-effort)
    def _tool_ms(tool_name: str) -> float:
        t = tools.get(tool_name) or {}
        d = _duration_ms(t.get("duration_ms"))
        if d is not None:
            return d
        # fallback: some implementations may store timings via started_at/finished_at only
        return 0.0

    market_ms = _tool_ms("market_data_tool")
    news_ms = _tool_ms("news_tool")
    sentiment_ms = _tool_ms("sentiment_tool")

    # Trace timing (best-effort) — if traces contain duration_ms per node_name
    trace_total = 0.0
    for tr in traces:
        dur = _duration_ms(tr.get("duration_ms"))
        trace_total += dur or 0.0

    st.markdown("### Timing Report")
    st.caption("Best-effort timings from backend execution metadata (per node/tool).")

    # Show a compact timing table
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: .5rem; margin-top: .5rem;">
              <div><b>Stage</b></div><div><b>Duration (ms)</b></div>
            """,
            unsafe_allow_html=True,
        )

        rows = [
            ("Router / Entity Resolution", router_ms),
            ("Market Data Retrieval", market_ms),
            ("News Collection", news_ms),
            ("Sentiment Analysis", sentiment_ms),
            ("LLM Research", research_ms),
            ("Merge Results", merge_ms),
        ]

        for stage, ms in rows:
            st.markdown(
                f"""
                <div style="display: contents;">
                  <div style="opacity: .95;">{stage}</div>
                  <div style="text-align:right; font-variant-numeric: tabular-nums;">{ms:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("**Trace Total (sum of traces)**")
        st.write(f"{trace_total:.2f} ms")

        total_backend_ms = execution_metadata.get("execution_time_ms")
        if total_backend_ms is not None:
            try:
                st.markdown("**Execution Total (execution_time_ms)**")
                st.write(f"{float(total_backend_ms):.2f} ms")
            except Exception:
                pass

    # Tools missing a duration_ms field may show as 0; keep report non-blocking.

    st.divider()


def render_execution_trace_explicit_partial(status_data: dict[str, Any]) -> None:
    def _impl() -> None:
        fields = _extract_execution_metadata_fields(status_data)

        execution_metadata = status_data.get("execution_metadata", {}) or {}
        with st.expander("🔍 Timing Report (Live)", expanded=False):
            _render_timing_report_from_metadata(execution_metadata)

        with st.expander("🔍 Execution Trace (Live)", expanded=False):
            st.markdown("**Detected Intent**")
            st.write(fields["detected_intent"] or "Not available")

            st.markdown("**Resolved Entity**")
            st.write(fields["resolved_entity"] or "Not available")

            st.markdown("**Selected Tools**")
            st.write(
                ", ".join([str(x) for x in (fields["selected_tools"] or [])])
                if fields["selected_tools"]
                else "Not available"
            )

            st.markdown("**Skipped Tools**")
            st.write(
                ", ".join([str(x) for x in (fields["skipped_tools"] or [])])
                if fields["skipped_tools"]
                else "Not available"
            )

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
            st.error(f"API Error: {last_response.status_code} - {last_response.text}")
        else:
            st.error(f"API Error: {last_exc!s}" if last_exc else "API Error")
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
            st.error(f"API Error: {last_response.status_code} - {last_response.text}")
        else:
            st.error(f"API Error: {last_exc!s}" if last_exc else "API Error")

        return None

    error_ph = st.empty()
    return run_safely(lambda: _impl(), "check status", fallback=None, error_placeholder=error_ph)


if __name__ == "__main__":
    main()
