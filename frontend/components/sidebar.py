# EquiPilot AI - Sidebar Component
# Navigation, recent reports, and system status

import streamlit as st

API_BASE_URL = "http://localhost:8000/api/v1"


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
        import requests
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
        if st.button(f"📄 {query}...", key=f"sidebar_report_{req_id}", use_container_width=True):
            st.session_state.current_request_id = item.get("request_id")
            st.session_state.is_processing = False
            st.session_state.current_report = None
            st.rerun()