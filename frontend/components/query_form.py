# EquiPilot AI - Query Form Component
# Reusable research query input form

from typing import Any, Callable, Optional

import streamlit as st


def render_query_form(
    key: str = "query_form",
    default_query: str = "",
    default_tickers: list[str] | None = None,
    on_submit: Callable | None = None,
) -> dict[str, Any] | None:
    """
    Render a research query form.

    Args:
        key: Unique key for the form
        default_query: Pre-filled query text
        default_tickers: Pre-filled ticker list
        on_submit: Callback function(form_data) -> None

    Returns:
        Form data dict if submitted, None otherwise
    """
    with st.form(key):
        query = st.text_area(
            "Research Query",
            value=default_query,
            placeholder="e.g., Analyze AAPL's competitive position and upcoming catalysts",
            height=100,
            key=f"{key}_query",
        )

        col1, col2 = st.columns(2)

        with col1:
            include_news = st.checkbox("Include News", value=True, key=f"{key}_news")
            include_fundamentals = st.checkbox("Include Fundamentals", value=True, key=f"{key}_fundamentals")

        with col2:
            include_sentiment = st.checkbox("Include Sentiment", value=True, key=f"{key}_sentiment")
            include_technicals = st.checkbox("Include Technicals", value=False, key=f"{key}_technicals")

        ticker_input = st.text_input(
            "Explicit Tickers (optional, comma-separated)",
            value=", ".join(default_tickers) if default_tickers else "",
            placeholder="AAPL, MSFT, GOOGL",
            key=f"{key}_tickers",
        )

        with st.expander("Advanced Options"):
            max_length = st.slider(
                "Max Report Length",
                min_value=1000,
                max_value=10000,
                value=5000,
                step=500,
                key=f"{key}_max_length",
            )

        submitted = st.form_submit_button("🚀 Start Research", type="primary", use_container_width=True)

        if submitted:
            if not query.strip():
                st.error("Please enter a research query")
                return None

            tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

            form_data = {
                "query": query,
                "tickers": tickers if tickers else None,
                "include_news": include_news,
                "include_sentiment": include_sentiment,
                "include_fundamentals": include_fundamentals,
                "include_technicals": include_technicals,
                "max_report_length": max_length,
            }

            if on_submit:
                on_submit(form_data)

            return form_data

    return None


def render_quick_stats(tickers: list[str], status: str, execution_time: float | None = None):
    """Render quick statistics for a research request."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tickers", len(tickers))
    with col2:
        st.metric("Status", status.title())
    with col3:
        if execution_time:
            st.metric("Time", f"{execution_time:.2f}s")
        else:
            st.metric("Time", "N/A")
