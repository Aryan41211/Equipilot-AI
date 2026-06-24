# EquiPilot AI - Streamlit Frontend
# Main Streamlit application entry point

import streamlit as st
import requests
import uuid
from datetime import datetime

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
    # Header
    st.title("📊 EquiPilot AI")
    st.caption("Agentic Equity Research Assistant")

    # Disclaimer
    st.warning(
        "⚠️ **Disclaimer**: EquiPilot AI is an informational equity research assistant "
        "and does not provide investment advice. All outputs are for informational "
        "and educational purposes only.",
        icon="⚠️"
    )

    # Sidebar
    with st.sidebar:
        render_sidebar()

    # Main content
    tab1, tab2, tab3 = st.tabs(["🔍 Research", "📋 History", "⚙️ Settings"])

    with tab1:
        render_research_tab()

    with tab2:
        render_history_tab()

    with tab3:
        render_settings_tab()


def render_sidebar():
    """Render sidebar with navigation and status."""
    st.header("Navigation")

    # API Status
    st.subheader("Backend Status")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            st.success("🟢 Backend Connected")
            st.json(health.get("services", {}))
        else:
            st.error("🔴 Backend Error")
    except Exception:
        st.error("🔴 Backend Unreachable")
        st.caption("Start backend with: `uvicorn backend.app:app --reload`")

    st.divider()

    # Quick Actions
    st.subheader("Quick Actions")
    if st.button("🔄 Clear History", use_container_width=True):
        st.session_state.research_history = []
        st.rerun()

    st.divider()

    # Info
    st.subheader("About")
    st.caption(
        "EquiPilot AI uses LangGraph orchestration to combine "
        "market data (yfinance), news, and LLM synthesis "
        "into comprehensive research reports."
    )


def render_research_tab():
    """Render the main research query tab."""
    st.header("New Research Query")

    # Query input
    with st.form("research_form"):
        col1, col2 = st.columns([3, 1])

        with col1:
            query = st.text_area(
                "Research Query",
                placeholder="e.g., Analyze AAPL's competitive position in the smartphone market and upcoming catalysts",
                height=100,
                help="Describe what you want to research. Include tickers or company names.",
            )

        with col2:
            st.subheader("Options")
            include_news = st.checkbox("Include News", value=True)
            include_sentiment = st.checkbox("Include Sentiment", value=True)
            include_fundamentals = st.checkbox("Include Fundamentals", value=True)
            include_technicals = st.checkbox("Include Technicals", value=False)

            max_length = st.slider(
                "Max Report Length",
                min_value=1000,
                max_value=10000,
                value=5000,
                step=500,
            )

        # Explicit tickers (optional)
        explicit_tickers = st.text_input(
            "Explicit Tickers (optional, comma-separated)",
            placeholder="AAPL, MSFT, GOOGL",
            help="Override automatic ticker extraction",
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
            request_id = submit_research(
                query=query,
                tickers=tickers if tickers else None,
                include_news=include_news,
                include_sentiment=include_sentiment,
                include_fundamentals=include_fundamentals,
                include_technicals=include_technicals,
                max_length=max_length,
            )

        if request_id:
            st.success(f"Research started! Request ID: {request_id}")
            st.session_state.current_request_id = request_id
            st.session_state.polling = True
            st.rerun()

    # Poll for results if we have a request ID
    if st.session_state.get("polling") and st.session_state.get("current_request_id"):
        render_progress_poller()


def render_progress_poller():
    """Render progress polling for active research."""
    request_id = st.session_state.current_request_id

    # Progress container
    progress_container = st.container()

    with progress_container:
        st.subheader("Research in Progress...")

        # Progress bar placeholder
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Poll for status
        import time
        max_polls = 60  # 60 seconds max
        poll_interval = 2

        for i in range(max_polls):
            status = check_status(request_id)

            if status:
                progress = min((i + 1) / max_polls, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Status: {status.get('status', 'unknown')}")

                if status.get("status") == "completed":
                    st.session_state.polling = False
                    render_report(status.get("report"))
                    break
                elif status.get("status") == "failed":
                    st.session_state.polling = False
                    st.error(f"Research failed: {status.get('error', 'Unknown error')}")
                    break

            time.sleep(poll_interval)
        else:
            st.warning("Research is taking longer than expected. Check History tab for results.")
            st.session_state.polling = False


def render_report(report: dict):
    """Render a research report."""
    if not report:
        st.warning("No report data available")
        return

    st.success("✅ Research Complete!")

    # Report metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Request ID", report.get("request_id", "N/A")[:12] + "...")
    with col2:
        st.metric("Tickers", ", ".join(report.get("tickers", [])))
    with col3:
        st.metric("Generated", report.get("created_at", "N/A")[:19])

    st.divider()

    # Report content
    if report.get("report"):
        st.markdown(report["report"])
    elif report.get("sections"):
        for section in report["sections"]:
            level = "#" * section.get("level", 2)
            st.markdown(f"{level} {section.get('title', 'Section')}")
            st.markdown(section.get("content", ""))

    # Citations
    if report.get("citations"):
        with st.expander("📚 Sources & Citations"):
            for cite in report["citations"]:
                st.markdown(f"- **{cite.get('title', 'Source')}** ({cite.get('source', 'Unknown')})")
                if cite.get("url"):
                    st.markdown(f"  [{cite['url']}]({cite['url']})")


def render_history_tab():
    """Render research history tab."""
    st.header("Research History")

    history = st.session_state.get("research_history", [])

    if not history:
        st.info("No research history yet. Submit a query to get started!")
        return

    for item in reversed(history):
        with st.expander(f"{item.get('query', 'Unknown')[:80]}... ({item.get('request_id', '')[:8]})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Query:** {item.get('query')}")
                st.write(f"**Tickers:** {', '.join(item.get('tickers', []))}")
                st.write(f"**Status:** {item.get('status')}")
            with col2:
                st.write(f"**ID:** {item.get('request_id')}")
                st.write(f"**Time:** {item.get('created_at')}")
                if st.button("View Report", key=f"view_{item.get('request_id')}"):
                    st.session_state.current_request_id = item.get("request_id")
                    st.session_state.polling = True
                    st.rerun()


def render_settings_tab():
    """Render settings tab."""
    st.header("Settings")

    st.subheader("API Configuration")
    st.text_input("Backend URL", value=API_BASE_URL, disabled=True)
    st.caption("Configure via environment variables or .env file")

    st.divider()

    st.subheader("Display Options")
    st.checkbox("Show raw JSON responses", value=False)
    st.checkbox("Auto-scroll to results", value=True)
    st.selectbox("Theme", ["Light", "Dark", "System"])

    st.divider()

    st.subheader("Data Sources")
    st.checkbox("yfinance (Market Data)", value=True, disabled=True)
    st.checkbox("News API", value=True, disabled=True)
    st.checkbox("OpenAI (LLM)", value=True, disabled=True)


def submit_research(
    query: str,
    tickers: list = None,
    include_news: bool = True,
    include_sentiment: bool = True,
    include_fundamentals: bool = True,
    include_technicals: bool = False,
    max_length: int = 5000,
) -> str:
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
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            request_id = result.get("request_id")

            # Add to history
            if "research_history" not in st.session_state:
                st.session_state.research_history = []

            st.session_state.research_history.append({
                "request_id": request_id,
                "query": query,
                "tickers": tickers or [],
                "status": result.get("status"),
                "created_at": datetime.utcnow().isoformat(),
            })

            return request_id
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is it running on port 8000?")
        return None
    except Exception as e:
        st.error(f"Error submitting request: {str(e)}")
        return None


def check_status(request_id: str) -> dict:
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


if __name__ == "__main__":
    main()