# EquiPilot AI - Streamlit Frontend
# Main Streamlit application entry point

import streamlit as st
import requests
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="EquiPilot AI - Equity Research Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Render header
    render_header()

    # Disclaimer
    render_disclaimer()

    # Sidebar
    with st.sidebar:
        render_sidebar()

    # Main content area
    tab1, tab2, tab3 = st.tabs(["🔍 Research", "📋 History", "⚙️ Settings"])

    with tab1:
        render_research_tab()

    with tab2:
        render_history_tab()

    with tab3:
        render_settings_tab()


def initialize_session_state():
    """Initialize session state variables."""
    if "research_history" not in st.session_state:
        st.session_state.research_history = []
    if "current_request_id" not in st.session_state:
        st.session_state.current_request_id = None
    if "current_report" not in st.session_state:
        st.session_state.current_report = None
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "show_tool_data" not in st.session_state:
        st.session_state.show_tool_data = {}


def render_header():
    """Render application header."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 EquiPilot AI")
        st.caption("Agentic Equity Research Assistant")
    with col2:
        st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")


def render_disclaimer():
    """Render disclaimer banner."""
    st.warning(
        "⚠️ **Disclaimer**: EquiPilot AI is an informational equity research assistant "
        "and does not provide investment advice. All outputs are for informational "
        "and educational purposes only.",
        icon="⚠️"
    )


def render_sidebar():
    """Render sidebar with navigation and status."""
    st.header("Navigation")

    # Current Model
    st.subheader("Current Model")
    model_name = st.session_state.get("model_name", "gpt-4o")
    st.caption(model_name)

    st.divider()

    # System Status
    st.subheader("System Status")
    render_system_status()

    st.divider()

    # Recent Reports
    st.subheader("Recent Reports")
    render_recent_reports()

    st.divider()

    # About
    st.subheader("About EquiPilot AI")
    st.caption(
        "Agentic equity research system using LangGraph orchestration "
        "to combine market data, news, and LLM synthesis."
    )


def render_system_status():
    """Render backend health status."""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            st.success("🟢 Connected")
            services = health.get("services", {})
            if services.get("openai"):
                st.caption("✓ OpenAI API")
            else:
                st.caption("○ OpenAI API (optional)")
            if services.get("news_api"):
                st.caption("✓ News API")
            else:
                st.caption("○ News API (optional)")
        else:
            st.error("🔴 Error")
    except Exception:
        st.error("🔴 Unreachable")
        st.caption("Start backend: `uvicorn backend.app:app --reload`")


def render_recent_reports():
    """Render session-only report history in sidebar."""
    history = st.session_state.get("research_history", [])

    if not history:
        st.caption("No recent reports")
        return

    for item in history[-5:]:
        req_id = item.get("request_id", "")[:8]
        query = item.get("query", "Unknown")[:40]
        if st.button(f"📄 {query}...", key=f"history_sidebar_{req_id}", use_container_width=True):
            st.session_state.current_request_id = item.get("request_id")
            st.session_state.is_processing = False
            st.session_state.current_report = None
            st.rerun()


def render_research_tab():
    """Render the main research query tab."""
    st.header("New Research Query")

    # Query input form
    with st.form("research_form", clear_on_submit=True):
        query = st.text_area(
            "Research Query",
            placeholder="e.g., Analyze AAPL's competitive position and upcoming catalysts",
            height=100,
            key="query_input",
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            include_news = st.checkbox("Include News", value=True, key="include_news")
            include_sentiment = st.checkbox("Include Sentiment", value=True, key="include_sentiment")

        with col2:
            include_fundamentals = st.checkbox("Include Fundamentals", value=True, key="include_fundamentals")
            include_technicals = st.checkbox("Include Technicals", value=False, key="include_technicals")

        # Explicit tickers (optional)
        explicit_tickers = st.text_input(
            "Explicit Tickers (optional, comma-separated)",
            placeholder="AAPL, MSFT, GOOGL",
            key="explicit_tickers",
        )

        # Max report length
        max_length = st.slider(
            "Max Report Length",
            min_value=1000,
            max_value=10000,
            value=5000,
            step=500,
            key="max_length",
        )

        submitted = st.form_submit_button("🚀 Start Research", type="primary", use_container_width=True)

    # Handle submission
    if submitted:
        if not query.strip():
            st.error("Please enter a research query")
            return

        # Parse tickers
        tickers = [t.strip().upper() for t in explicit_tickers.split(",") if t.strip()]

        # Submit to backend
        with st.spinner("Submitting research request..."):
            request_data = submit_research(
                query=query,
                tickers=tickers if tickers else None,
                include_news=include_news,
                include_sentiment=include_sentiment,
                include_fundamentals=include_fundamentals,
                include_technicals=include_technicals,
                max_length=max_length,
            )

        if request_data:
            st.success(f"Research started! Request ID: {request_data.get('request_id', 'N/A')[:12]}...")
            st.session_state.current_request_id = request_data.get("request_id")
            st.session_state.is_processing = True
            st.session_state.current_report = None
            st.rerun()

    # Poll for results if processing
    if st.session_state.get("is_processing") and st.session_state.get("current_request_id"):
        render_progress_and_results()


def render_progress_and_results():
    """Render progress polling and final results."""
    request_id = st.session_state.current_request_id

    status_data = check_status(request_id)

    if not status_data:
        st.warning("Waiting for backend response...")
        time.sleep(2)
        st.rerun()
        return

    status = status_data.get("status", "unknown")

    if status in ("completed", "success"):
        st.session_state.is_processing = False
        st.session_state.current_report = status_data
        report = status_data
        render_report(report)
    elif status == "failed":
        st.session_state.is_processing = False
        error_msg = status_data.get("error", status_data.get("message", "Unknown error"))
        st.error(f"Research failed: {error_msg}")
    elif status in ("pending", "in_progress"):
        render_agent_timeline(status_data)

        # Auto-rerun to poll again
        time.sleep(2)
        st.rerun()


def render_agent_timeline(status_data: Dict[str, Any]):
    """Render agent execution timeline."""
    st.subheader("Agent Execution Timeline")

    execution_metadata = status_data.get("execution_metadata", {})
    traces = execution_metadata.get("traces", [])

    # Define steps based on GraphState nodes
    steps = [
        ("router", "Entity Resolution", "🎯"),
        ("market_data_tool", "Market Data", "📊"),
        ("news_tool", "News", "📰"),
        ("sentiment_tool", "Sentiment", "😊"),
        ("research", "Research", "📝"),
    ]

    # Calculate step durations from traces
    step_times = {}
    for trace in traces:
        node_name = trace.get("node_name", "")
        duration = trace.get("duration_ms", 0)
        step_times[node_name] = duration

    # Get current step and build progress
    col_count = len(steps)
    cols = st.columns(col_count)

    for i, (step_id, step_name, icon) in enumerate(steps):
        with cols[i]:
            duration = step_times.get(step_id, 0)
            # Check if step is completed or in progress
            trace = next((t for t in traces if t.get("node_name") == step_id), None)
            if trace:
                status_icon = "✅" if trace.get("success") else "❌"
                st.markdown(f"""
                <div style="text-align: center; padding: 10px;">
                    <div style="font-size: 24px;">{icon}</div>
                    <div style="font-size: 12px; font-weight: bold;">{step_name}</div>
                    <div style="font-size: 10px; color: gray;">{duration:.0f}ms {status_icon}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; opacity: 0.5;">
                    <div style="font-size: 24px;">{icon}</div>
                    <div style="font-size: 12px;">{step_name}</div>
                </div>
                """, unsafe_allow_html=True)

    # Total execution time
    total_time = sum(step_times.values()) / 1000 if step_times else 0
    if total_time > 0:
        st.markdown(f"**Total Execution Time: {total_time:.2f}s**")

    st.divider()


def render_history_tab():
    """Render research history tab."""
    st.header("Research History")

    history = st.session_state.get("research_history", [])

    if not history:
        st.info("No research history yet. Submit a query to get started!")
        return

    for item in reversed(history):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Query:** {item.get('query')}")
            if item.get("tickers"):
                st.write(f"**Tickers:** {', '.join(item.get('tickers'))}")
            st.write(f"**Status:** {item.get('status')}")
        with col2:
            st.write(f"**ID:** {item.get('request_id')[:12]}...")
            st.write(f"**Time:** {item.get('created_at')}")
            if st.button("View Report", key=f"view_history_{item.get('request_id')}"):
                st.session_state.current_request_id = item.get("request_id")
                st.session_state.is_processing = False
                st.session_state.current_report = None
                st.rerun()

    # Clear history button
    if st.button("🗑️ Clear History", type="secondary"):
        st.session_state.research_history = []
        st.rerun()


def render_settings_tab():
    """Render settings tab."""
    st.header("Settings")

    st.subheader("API Configuration")
    st.text_input("Backend URL", value=API_BASE_URL, disabled=True)
    st.caption("Configure via environment variables or .env file")

    st.divider()

    st.subheader("Display Options")
    st.checkbox("Show raw JSON responses", value=False, key="show_raw_json")
    st.checkbox("Auto-scroll to results", value=True, key="auto_scroll")
    st.selectbox("Theme", ["Light", "Dark", "System"], key="theme")

    st.divider()

    st.subheader("Data Sources")
    st.checkbox("yfinance (Market Data)", value=True, disabled=True)
    st.checkbox("News API", value=True, disabled=True)
    st.checkbox("OpenAI (LLM)", value=True, disabled=True)


def submit_research(
    query: str,
    tickers: Optional[List[str]] = None,
    include_news: bool = True,
    include_sentiment: bool = True,
    include_fundamentals: bool = True,
    include_technicals: bool = False,
    max_length: int = 5000,
) -> Optional[Dict[str, Any]]:
    """Submit research request to backend API."""
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

        response = requests.post(
            f"{API_BASE_URL}/research",
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            request_id = result.get("request_id")

            # Add to history
            st.session_state.research_history.append({
                "request_id": request_id,
                "query": query,
                "tickers": tickers or [],
                "status": result.get("status"),
                "created_at": datetime.utcnow().isoformat(),
            })

            return result
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is it running on port 8000?")
        return None
    except Exception as e:
        st.error(f"Error submitting request: {str(e)}")
        return None


def check_status(request_id: str) -> Optional[Dict[str, Any]]:
    """Check research status."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/research/{request_id}",
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception:
        return None


def render_report(report: Dict[str, Any]):
    """Render a research report with all sections."""
    if not report:
        st.warning("No report data available")
        return

    st.success("✅ Research Complete!")

    # Report metadata
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Request ID", report.get("request_id", "N/A")[:12] + "...")
    with col2:
        st.metric("Status", report.get("status", "unknown").title())
    with col3:
        st.metric("Tickers", len(report.get("tickers", [])))
    with col4:
        created = report.get("created_at", "")
        if created:
            st.metric("Generated", created[:16].replace("T", " "))

    st.divider()

    # Tool Output Panels
    render_tool_panels(report)

    st.divider()

    # Report content - structured sections
    render_report_sections(report)

    st.divider()

    # Execution trace
    render_execution_trace(report)


def render_tool_panels(report: Dict[str, Any]):
    """Render expandable tool output panels."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Market Data", use_container_width=True):
            key = "show_market_data"
            st.session_state.show_tool_data[key] = not st.session_state.show_tool_data.get(key, False)

    with col2:
        if st.button("📰 News", use_container_width=True):
            key = "show_news_data"
            st.session_state.show_tool_data[key] = not st.session_state.show_tool_data.get(key, False)

    with col3:
        if st.button("😊 Sentiment", use_container_width=True):
            key = "show_sentiment_data"
            st.session_state.show_tool_data[key] = not st.session_state.show_tool_data.get(key, False)

    with col4:
        if st.button("🔍 Execution Trace", use_container_width=True):
            key = "show_execution_trace"
            st.session_state.show_tool_data[key] = not st.session_state.show_tool_data.get(key, False)

    # Market Data panel
    if st.session_state.show_tool_data.get("show_market_data"):
        with st.expander("📊 Market Data Output", expanded=True):
            market_data = report.get("market_data") or report.get("market_data_summary")
            if market_data:
                st.json(market_data)
            else:
                st.info("No market data available")

    # News panel
    if st.session_state.show_tool_data.get("show_news_data"):
        with st.expander("📰 News Output", expanded=True):
            news_data = report.get("news_data") or report.get("news_summary")
            if news_data:
                st.json(news_data)
            else:
                st.info("No news data available")

    # Sentiment panel
    if st.session_state.show_tool_data.get("show_sentiment_data"):
        with st.expander("😊 Sentiment Output", expanded=True):
            sentiment_data = report.get("sentiment_data") or report.get("sentiment_summary")
            if sentiment_data:
                st.json(sentiment_data)
            else:
                st.info("No sentiment data available")


def render_report_sections(report: Dict[str, Any]):
    """Render structured report sections."""
    sections = report.get("sections")

    if not sections:
        # Fallback to plain report
        if report.get("report"):
            st.markdown(report["report"])
        elif report.get("executive_summary"):
            # Handle SynthesizedReport format
            st.subheader("📋 Executive Summary")
            st.markdown(report.get("executive_summary", ""))
            if report.get("market_snapshot"):
                st.subheader("📈 Market Snapshot")
                st.markdown(report["market_snapshot"])
            if report.get("news_summary"):
                st.subheader("📰 News Summary")
                st.markdown(report["news_summary"])
            if report.get("sentiment_summary"):
                st.subheader("😊 Sentiment Summary")
                st.markdown(report["sentiment_summary"])
            if report.get("risks"):
                st.subheader("⚠️ Risks")
                st.markdown(report["risks"])
            if report.get("opportunities"):
                st.subheader("📈 Opportunities")
                st.markdown(report["opportunities"])
            st.caption(report.get("disclaimer", "This is not investment advice."))
        return

    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")

        if title == "Executive Summary":
            st.subheader("📋 Executive Summary")
            st.markdown(content)
        elif title == "Market Snapshot":
            st.subheader("📈 Market Snapshot")
            st.markdown(content)
        elif title == "News Summary":
            st.subheader("📰 News Summary")
            st.markdown(content)
        elif title == "Sentiment Analysis" or title == "Sentiment Summary":
            st.subheader("😊 Sentiment Summary")
            st.markdown(content)
        elif title == "Risk Factors" or title == "Risks":
            st.subheader("⚠️ Risks")
            st.markdown(content)
        elif title == "Opportunities":
            st.subheader("📈 Opportunities")
            st.markdown(content)
        elif title == "Disclaimer":
            st.caption(f"*{content}*")
        else:
            st.markdown(f"**{title}**")
            st.markdown(content)


def render_execution_trace(report: Dict[str, Any]):
    """Render detailed execution trace."""
    execution_metadata = report.get("execution_metadata", {})
    traces = execution_metadata.get("traces", [])

    if not traces:
        return

    with st.expander("🔍 Execution Trace", expanded=False):
        for trace in traces:
            step = trace.get("node_name", "unknown")
            duration = trace.get("duration_ms", 0)
            status = "✅" if trace.get("success") else "❌"
            timestamp = trace.get("start_time", "")[:19]
            error = trace.get("error")

            st.markdown(f"- **{step}**: {duration:.0f}ms {status} - {timestamp}")
            if error:
                st.caption(f"  Error: {error}")


if __name__ == "__main__":
    main()