# EquiPilot AI - Report Display Component
# Reusable research report rendering

from typing import Any, Callable

import streamlit as st

from frontend.components.design_system_ui import section_header, status_badge, safe_html_escape


def _premium_card(icon: str, title: str, content: str, badge: str | None = None):
    badge_html = f"""
      <span style="
        display:inline-flex;
        align-items:center;
        gap:0.4rem;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(37, 99, 235, 0.06);
        color: var(--accent);
        font-weight: var(--font-weight-semibold);
        font-size: var(--font-size-xs);
      ">{badge}</span>
    """ if badge else ""

    return f"""
    <div class="ds-card ds-card--premium" style="padding: 1rem 1rem; margin-bottom: 1rem;">
      <div style="display:flex; align-items:flex-start; justify-content: space-between; gap: 1rem;">
        <div style="display:flex; align-items:flex-start; gap: .75rem;">
          <div style="width:34px;height:34px;border-radius: var(--radius-md);background: rgba(59,130,246,0.12);display:flex;align-items:center;justify-content:center;font-size: 1.1rem;">
            {icon}
          </div>
          <div>
            <div style="font-weight: var(--font-weight-bold); font-size: var(--font-size-base);">{safe_html_escape(title)}</div>
            {badge_html}
          </div>
        </div>
      </div>
      <div style="margin-top: .75rem;">
        {content}
      </div>
    </div>
    """


def render_report(
    report: dict[str, Any] | None,
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
        st.markdown(section_header("AI Research Report", "No report data available."), unsafe_allow_html=True)
        st.warning("No report data available")
        return

    if show_metadata:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Request ID", report.get("request_id", "N/A")[:12] + "...")
        with col2:
            st.metric("Status", str(report.get("status", "unknown")).title())
        with col3:
            st.metric("Tickers", len(report.get("tickers", [])))
        with col4:
            created = report.get("created_at", "")
            if created:
                st.metric("Generated", created[:16].replace("T", " "))

        st.divider()

    def _premium_card(icon: str, title: str, content: str, badge: str | None = None):
        badge_html = f"""
          <span style="
            display:inline-flex;
            align-items:center;
            gap:0.4rem;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: rgba(37, 99, 235, 0.06);
            color: var(--accent);
            font-weight: var(--font-weight-semibold);
            font-size: var(--font-size-xs);
          ">{badge}</span>
        """ if badge else ""

        return f"""
        <div class="ds-card ds-card--premium" style="padding: 1rem 1rem; margin-bottom: 1rem;">
          <div style="display:flex; align-items:flex-start; justify-content: space-between; gap: 1rem;">
            <div style="display:flex; align-items:flex-start; gap: .75rem;">
              <div style="width:34px;height:34px;border-radius: var(--radius-md);background: rgba(59,130,246,0.12);display:flex;align-items:center;justify-content:center;font-size: 1.1rem;">
                {icon}
              </div>
              <div>
                <div style="font-weight: var(--font-weight-bold); font-size: var(--font-size-base);">{safe_html_escape(title)}</div>
                {badge_html}
              </div>
            </div>
          </div>
          <div style="margin-top: .75rem;">
            {content}
          </div>
        </div>
        """

    # Legacy payload support:
    # - `report["report"]` contains raw LLM text
    # - `report["sections"]` contains structured sections
    if report.get("report"):
        if expandable:
            with st.expander("Full Report", expanded=True):
                st.markdown(report["report"])
        else:
            st.markdown(report["report"])

    elif report.get("sections"):
        render_structured_sections(report["sections"], expandable)

    elif report.get("executive_summary"):
        render_synthesized_report(report)

    else:
        st.info("Report content not available in expected format")

    if show_citations and report.get("citations"):
        with st.expander("Sources & Citations"):
            for i, cite in enumerate(report["citations"]):
                _render_citation(cite, i)


def render_structured_sections(sections: list[dict[str, Any]], expandable: bool = True):
    """Render structured report sections."""
    SECTION_ICON = {
        "Executive Summary": "🧠",
        "Key Insights": "🔎",
        "Market Snapshot": "📈",
        "Market Data": "📊",
        "News Summary": "📰",
        "News": "📰",
        "Sentiment Summary": "🧾",
        "Sentiment Analysis": "🧾",
        "Risk Factors": "⚠️",
        "Risks": "⚠️",
        "Opportunities": "🚀",
        "Recommendation": "✅",
        "Sources": "🔗",
        "Sources & Citations": "🔗",
        "Disclaimer": "🛡️",
    }

    def section_title_to_key(t: str) -> str:
        # Normalize to known keys (best-effort, keeps contract)
        tt = (t or "").strip()
        return tt

    for i, section in enumerate(sections):
        title = section.get("title", f"Section {i+1}")
        content = section.get("content", "")

        icon = SECTION_ICON.get(section_title_to_key(title), "📌")
        badge = None
        if "sentiment" in (title or "").lower():
            badge = "Sentiment"
        elif "news" in (title or "").lower():
            badge = "News"
        elif "market" in (title or "").lower():
            badge = "Market"
        elif "risk" in (title or "").lower():
            badge = "Risks"
        elif "opportun" in (title or "").lower():
            badge = "Opportunities"

        body = f"<div style='white-space: pre-wrap;'>{content}</div>"
        card_html = _premium_card(icon=icon, title=title, content=body, badge=badge)

        if expandable and title != "Disclaimer":
            with st.expander(title, expanded=False):
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.markdown(card_html, unsafe_allow_html=True)

        if title == "Disclaimer":
            st.caption(f"*{content}*")


def render_synthesized_report(report: dict[str, Any]):
    """Render a synthesized report (LLM output format)."""
    if report.get("executive_summary"):
        st.markdown(section_header("Executive Summary", None), unsafe_allow_html=True)
        st.markdown(report["executive_summary"])

    if report.get("market_snapshot"):
        st.markdown(section_header("Market Snapshot", None), unsafe_allow_html=True)
        st.markdown(report["market_snapshot"])

    if report.get("news_summary"):
        st.markdown(section_header("News Summary", None), unsafe_allow_html=True)
        st.markdown(report["news_summary"])

    if report.get("sentiment_summary"):
        st.markdown(section_header("Sentiment Summary", None), unsafe_allow_html=True)
        st.markdown(report["sentiment_summary"])

    if report.get("risks"):
        st.markdown(section_header("Risks", None), unsafe_allow_html=True)
        if isinstance(report["risks"], list):
            for risk in report["risks"]:
                st.markdown(f"- {risk}")
        else:
            st.markdown(report["risks"])

    if report.get("opportunities"):
        st.markdown(section_header("Opportunities", None), unsafe_allow_html=True)
        if isinstance(report["opportunities"], list):
            for opp in report["opportunities"]:
                st.markdown(f"- {opp}")
        else:
            st.markdown(report["opportunities"])

    st.caption(report.get("disclaimer", "This is not investment advice."))


def _render_citation(citation: dict[str, Any], index: int):
    """Render a single citation."""
    cite_type = citation.get("type", "unknown")
    title = str(citation.get("title", "Untitled"))
    source = citation.get("source", "Unknown")
    url = citation.get("url")
    date = citation.get("date")

    st.markdown(f"**{index + 1}. {safe_html_escape(title)}**", unsafe_allow_html=False)
    st.caption(
        f"Source: {source} | Type: {cite_type}" + (f" | Date: {date}" if date else "")
    )

    if url:
        st.markdown(f"[🔗 View Source]({url})")

    if citation.get("snippet"):
        st.caption(f"> {citation['snippet'][:200]}...")

    st.divider()


def render_report_card(
    report: dict[str, Any],
    on_click: Callable[[str], None] | None = None,
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
                    request_id_val = report.get("request_id")
                    if isinstance(request_id_val, str) and request_id_val:
                        on_click(request_id_val)
