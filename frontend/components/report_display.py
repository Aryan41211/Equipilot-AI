# EquiPilot AI - Report Display Component
# Reusable research report rendering

import streamlit as st
from typing import Optional, Dict, Any, List


def render_report(
    report: Dict[str, Any],
    show_metadata: bool = True,
    show_citations: bool = True,
    expandable: bool = True,
):
    """
    Render a research report.

    Args:
        report: Report dictionary from API
        show_metadata: Show request metadata
        show_citations: Show citations section
        expandable: Make sections expandable
    """
    if not report:
        st.warning("No report data available")
        return

    # Metadata
    if show_metadata:
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

    # Main report content
    if report.get("report"):
        # Single markdown report
        if expandable:
            with st.expander("📄 Full Report", expanded=True):
                st.markdown(report["report"])
        else:
            st.markdown(report["report"])

    elif report.get("sections"):
        # Structured sections
        for i, section in enumerate(report["sections"]):
            level = section.get("level", 2)
            title = section.get("title", f"Section {i+1}")
            content = section.get("content", "")

            if expandable:
                with st.expander(f"{'#' * level} {title}", expanded=(i == 0)):
                    st.markdown(content)
            else:
                st.markdown(f"{'#' * level} {title}")
                st.markdown(content)

    else:
        st.info("Report content not available in expected format")
        with st.expander("Raw Report Data"):
            st.json(report)

    # Citations
    if show_citations and report.get("citations"):
        with st.expander("📚 Sources & Citations"):
            for i, cite in enumerate(report["citations"]):
                _render_citation(cite, i)

    # Market data summary
    if report.get("market_data_summary"):
        with st.expander("📈 Market Data Summary"):
            st.json(report["market_data_summary"])

    # News summary
    if report.get("news_summary"):
        with st.expander("📰 News Summary"):
            st.json(report["news_summary"])

    # Sentiment summary
    if report.get("sentiment_summary"):
        with st.expander("😊 Sentiment Summary"):
            st.json(report["sentiment_summary"])


def _render_citation(citation: Dict[str, Any], index: int):
    """Render a single citation."""
    cite_type = citation.get("type", "unknown")
    title = citation.get("title", "Untitled")
    source = citation.get("source", "Unknown")
    url = citation.get("url")
    date = citation.get("date")

    # Type icon
    type_icons = {
        "market_data": "📊",
        "news": "📰",
        "sentiment": "😊",
        "llm": "🤖",
    }
    icon = type_icons.get(cite_type, "📄")

    st.markdown(f"**{index + 1}. {icon} {title}**")
    st.caption(f"Source: {source} | Type: {cite_type}" + (f" | Date: {date}" if date else ""))

    if url:
        st.markdown(f"[🔗 View Source]({url})")

    if citation.get("snippet"):
        st.caption(f"> {citation['snippet'][:200]}...")

    st.divider()


def render_report_card(
    report: Dict[str, Any],
    on_click: Optional[callable] = None,
):
    """Render a compact report card for history view."""
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"**{report.get('query', 'Unknown Query')[:80]}...**")
            st.caption(f"Tickers: {', '.join(report.get('tickers', [])) or 'None'}")
            st.caption(f"Status: {report.get('status', 'unknown').title()}")

        with col2:
            if st.button("View", key=f"view_{report.get('request_id')}", use_container_width=True):
                if on_click:
                    on_click(report.get("request_id"))

        st.caption(f"ID: {report.get('request_id', 'N/A')[:12]}... | {report.get('created_at', '')[:16]}")