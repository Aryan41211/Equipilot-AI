# EquiPilot AI - Streamlit Frontend
# Production dashboard (thin API client, no business logic in Streamlit)

import time
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.progress_tracker import render_progress
from frontend.components.report_display import render_report

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def main():
    initialize_session_state()
    st.set_page_config(
        page_title="EquiPilot AI - Equity Research Assistant",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    render_header()
    render_disclaimer()

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


def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 EquiPilot AI")
        st.caption("Agentic Equity Research Assistant")
    with col2:
        st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")


def render_disclaimer():
    st.warning(
        "⚠️ **Disclaimer**: EquiPilot AI is an informational equity research assistant "
        "and does not provide investment advice. All outputs are for informational "
        "and educational purposes only.",
        icon="⚠️",
    )


def handle_sidebar_submit(form_data: Dict[str, Any]) -> None:
    """
    Thin-client callback invoked by sidebar. Starts research on backend and
    triggers polling rendering in the main page.
    """
    # Store for UI/debug
    st.session_state.analysis_form_data = form_data

    max_length = form_data.get("max_report_length", st.session_state.get("max_report_length", 5000))
    st.session_state.max_report_length = max_length

    with st.spinner("Submitting research request..."):
        request_data = submit_research(
            query=form_data["query"],
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
    st.session_state.current_request_id = request_data.get("request_id")
    st.session_state.is_processing = True
    st.session_state.current_report = None
    st.session_state.execution_trace = None

    st.session_state.research_history.append(
        {
            "request_id": request_data.get("request_id"),
            "query": form_data.get("query"),
            "tickers": form_data.get("tickers") or [],
            "status": request_data.get("status"),
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    st.rerun()


def render_main_page():
    st.subheader("EquiPilot AI Dashboard")

    request_id = st.session_state.get("current_request_id")
    report = st.session_state.get("current_report")

    if st.session_state.get("is_processing") and request_id:
        render_loading_workflow(request_id)
        return

    if report:
        render_dashboard_sections(report)
        render_execution_trace_explicit(report)
        return

    # Empty state placeholders
    st.info("Submit a query from the sidebar to generate an AI research report.")

    st.write("### Market Data")
    st.caption("No data yet.")

    st.write("### News Headlines")
    st.caption("No headlines yet.")

    st.write("### Sentiment Analysis")
    st.caption("No sentiment analysis yet.")

    st.write("### AI Research Report")
    st.caption("No report generated yet.")


def render_loading_workflow(request_id: str) -> None:
    """
    Poll backend and render stage-based loading UI + execution trace live.
    """
    status_data = check_status(request_id)
    if not status_data:
        st.warning("Waiting for backend response...")
        time.sleep(1)
        st.rerun()
        return

    status = status_data.get("status", "unknown")
    execution_metadata = status_data.get("execution_metadata", {}) or {}
    current_step = status_data.get("current_step") or execution_metadata.get("current_step") or "router"

    stage_label = map_trace_step_to_stage(current_step)

    render_progress(
        current_step=current_step,
        status="in_progress" if status in ("pending", "in_progress", "in_progress") else status,
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
        st.error(status_data.get("error", status_data.get("message", "Unknown error")))
        st.rerun()
        return

    time.sleep(2)
    st.rerun()


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


def render_dashboard_sections(report: Dict[str, Any]) -> None:
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


def _extract_execution_metadata_fields(report: Dict[str, Any]) -> Dict[str, Any]:
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


def render_execution_trace_explicit(report: Dict[str, Any]) -> None:
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


def render_execution_trace_explicit_partial(status_data: Dict[str, Any]) -> None:
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


def submit_research(
    query: str,
    tickers: Optional[List[str]] = None,
    include_news: bool = True,
    include_sentiment: bool = True,
    include_fundamentals: bool = True,
    include_technicals: bool = False,
    max_length: int = 5000,
) -> Optional[Dict[str, Any]]:
    """
    Submit research request to backend API.
    Thin client: no business logic here.
    """
    try:
        payload = {
            "query": query,
            "tickers": tickers,
            "include_news": include_news,
            "include_sentiment": include_sentiment,
            "include_fundamentals": include_fundamentals,
            "include_technicals": include_technicals,
            "max_report_length": max_length,
        }

        response = requests.post(f"{API_BASE_URL}/research", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()

        st.error(f"API Error: {response.status_code} - {response.text}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is it running on port 8000?")
        return None
    except Exception as e:
        st.error(f"Error submitting request: {str(e)}")
        return None


def check_status(request_id: str) -> Optional[Dict[str, Any]]:
    """Check research status (thin client)."""
    try:
        response = requests.get(f"{API_BASE_URL}/research/{request_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


if __name__ == "__main__":
    main()
