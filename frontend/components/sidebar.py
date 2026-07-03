# EquiPilot AI - Sidebar Component
# Navigation, recent reports, and system status

import os
from collections.abc import Callable
from typing import Any

import streamlit as st

from frontend.components.design_system_ui import (
    section_header,
    title_brand,
    status_badge,
)

API_BASE_URL = os.environ.get("EQUIPILOT_API_URL", "").rstrip("/")


def render_sidebar(on_analyze: Callable[[dict[str, Any]], None] | None = None):
    """Render sidebar with analysis inputs, system status, and recent reports."""
    st.markdown(title_brand(), unsafe_allow_html=True)
    st.caption("Agentic Equity Research Assistant")
    st.divider()

    # --- Analysis Inputs (required by spec) ---
    st.markdown(section_header("Research Setup", "Configure the research you want."), unsafe_allow_html=True)

    with st.form("analysis_form"):
        company_or_ticker = st.text_input(
            "Company / Ticker",
            placeholder="e.g., AAPL or Apple Inc.",
            key="company_ticker_input",
        )

        query = st.text_area(
            "Query",
            placeholder="What do you want to research? (e.g., fundamentals, catalysts, risks)",
            height=120,
            key="query_input",
        )

        analysis_type = st.selectbox(
            "Analysis Type",
            options=["Fundamentals", "News", "Sentiment", "Full Research"],
            index=3,  # default to Full Research
            key="analysis_type",
        )

        submitted = st.form_submit_button("🔎 Analyze", type="primary", use_container_width=True)

    if submitted:
        company_or_ticker_val = (company_or_ticker or "").strip()
        query_val = (query or "").strip()

        if not company_or_ticker_val:
            st.error("Please enter a Company / Ticker.")
            return
        if not query_val:
            st.error("Please enter a Query.")
            return

        # Convert analysis type into backend boolean flags.
        include_news = analysis_type in ("News", "Full Research")
        include_sentiment = analysis_type in ("Sentiment", "Full Research")
        include_fundamentals = analysis_type in ("Fundamentals", "Full Research")

        # Backend accepts tickers; when user enters a name, entity resolution
        # can map it. We pass tickers only when it looks like a ticker.
        normalized = company_or_ticker_val.strip().upper()
        looks_like_ticker = normalized.replace(".", "", 1).isalnum() and len(normalized) <= 12
        tickers = [normalized] if looks_like_ticker else None

        form_data = {
            "company_or_ticker": company_or_ticker_val,
            "query": query_val,
            "tickers": tickers,
            "include_news": include_news,
            "include_sentiment": include_sentiment,
            "include_fundamentals": include_fundamentals,
            "include_technicals": False,
            "analysis_type": analysis_type,
            "max_report_length": st.session_state.get("max_report_length", 5000),
        }

        if on_analyze:
            on_analyze(form_data)
        else:
            # Fallback for cases where parent didn't pass callback.
            st.session_state["_last_analysis_form_data"] = form_data

    st.divider()

    # --- Current Model ---
    st.markdown(section_header("Current Model"), unsafe_allow_html=True)
    model_name = st.session_state.get("model_name", "gpt-4o")
    st.caption(model_name)

    st.divider()

    # --- System Status ---
    st.markdown(section_header("System Status", "Backend health & integration."), unsafe_allow_html=True)
    render_system_status()

    st.divider()

    # --- Recent Reports ---
    st.markdown(section_header("Recent Reports", "Session history for quick re-runs."), unsafe_allow_html=True)
    render_recent_reports()

    st.divider()

    # --- About ---
    st.markdown(section_header("About EquiPilot AI", "Informational equity research assistant."), unsafe_allow_html=True)
    st.caption(
        "Agentic equity research system using LangGraph orchestration "
        "to combine market data, news, and LLM synthesis."
    )


def render_system_status():
    """Render backend health status."""
    try:
        if not API_BASE_URL:
            st.info("API not configured (set EQUIPILOT_API_URL).")
            return

        import requests

        health_url = f"{API_BASE_URL.replace('/api/v1', '')}/health"
        response = requests.get(health_url, timeout=5)
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
        if API_BASE_URL:
            st.caption(f"Checked: {API_BASE_URL.replace('/api/v1', '')}/health")


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
