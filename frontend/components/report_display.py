
# EquiPilot AI - Report Display Component
# Premium enterprise report rendering

from collections.abc import Callable
from typing import Any

import streamlit as st

from frontend.components.design_system_ui import safe_html_escape, status_badge


def _report_section_card(icon: str, title: str, content: str, badge: str | None = None) -> str:
    """Premium report section card with icon, header, badge, and content."""
    badge_html = ""
    if badge:
        badge_html = f"""
        <span style="
          display:inline-flex;align-items:center;gap:3px;
          padding:2px 8px;border-radius:var(--radius-full);
          background:var(--primary-light);
          color:var(--primary);font-weight:var(--font-weight-medium);
          font-size:10px;line-height:1.4;letter-spacing:0.01em;
          text-transform:uppercase;
        ">{safe_html_escape(badge)}</span>
        """

    return f"""
    <div class="ds-card" style="padding:1.25rem;margin-bottom:1rem;border-left:3px solid var(--primary);">
      <div style="display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:0.75rem;">
        <div style="
          width:32px;height:32px;border-radius:var(--radius-md);
          background:var(--primary-light);
          display:flex;align-items:center;justify-content:center;
          font-size:1rem;flex-shrink:0;
        ">{icon}</div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
            <span style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);color:var(--text);">
              {safe_html_escape(title)}
            </span>
            {badge_html}
          </div>
        </div>
      </div>
      <div style="font-size:var(--font-size-sm);color:var(--text);line-height:var(--leading-relaxed);">
        {content}
      </div>
    </div>
    """


def _format_content(text: str) -> str:
    """Convert plain text into HTML paragraphs for better readability."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    paragraphs = []
    for line in lines:
        if line.startswith("•") or line.startswith("-") or line.startswith("*"):
            paragraphs.append(
                f'<div style="display:flex;gap:0.5rem;padding:0.25rem 0;align-items:flex-start;">'
                f'<span style="color:var(--primary);flex-shrink:0;font-size:0.75rem;">▸</span>'
                f'<span>{safe_html_escape(line.lstrip("•-* ").strip())}</span></div>'
            )
        elif line.startswith("#"):
            heading = line.lstrip("# ").strip()
            paragraphs.append(
                f'<div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-base);'
                f'margin:0.75rem 0 0.25rem;color:var(--text);">{safe_html_escape(heading)}</div>'
            )
        else:
            paragraphs.append(f"<p style='margin:0 0 0.5rem;'>{safe_html_escape(line)}</p>")
    if not paragraphs:
        return f"<p style='margin:0;'>{safe_html_escape(text)}</p>"
    return "".join(paragraphs)


def render_report(
    report: dict[str, Any] | None,
    show_metadata: bool = True,
    show_citations: bool = True,
    expandable: bool = True,
):
    """
    Render a research report with premium card-based layout.
    """
    if not report:
        st.markdown(
            '<div class="ds-state-card ds-state-card--warning" style="margin-bottom:var(--space-4);">'
            '<div class="ds-state-card__icon">📋</div>'
            '<div class="ds-state-card__body">'
            '<div class="ds-state-card__title">No Report Available</div>'
            '<div class="ds-state-card__detail">The report data could not be loaded. Submit a new research request to generate a report.</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        return

    if report.get("report"):
        content = report["report"]
        card = _report_section_card("📄", "Full Report", _format_content(content))
        if expandable:
            with st.expander("View Full Report", expanded=True):
                st.markdown(card, unsafe_allow_html=True)
        else:
            st.markdown(card, unsafe_allow_html=True)

    elif report.get("sections"):
        render_structured_sections(report["sections"], expandable)

    elif report.get("executive_summary"):
        render_synthesized_report(report)

    else:
        st.markdown(
            '<div class="ds-state-card ds-state-card--info" style="margin-bottom:var(--space-4);">'
            '<div class="ds-state-card__icon">📋</div>'
            '<div class="ds-state-card__body">'
            '<div class="ds-state-card__title">Report Format Not Recognized</div>'
            '<div class="ds-state-card__detail">The report data is in an unexpected format. Try viewing the raw data below.</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    if show_citations and report.get("citations"):
        st.markdown(
            '<div style="display:flex;align-items:center;gap:var(--space-2);margin:var(--space-5) 0 var(--space-3);">'
            '<div style="width:24px;height:24px;border-radius:var(--radius-sm);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:0.75rem;">🔗</div>'
            '<span style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);">Sources &amp; Citations</span>'
            '<span class="ds-badge">{}</span>'.format(len(report["citations"])) + ' cited</div>',
            unsafe_allow_html=True,
        )
        for i, cite in enumerate(report["citations"]):
            _render_citation(cite, i)


def render_structured_sections(sections: list[dict[str, Any]], expandable: bool = True):
    """Render structured report sections as premium expandable cards."""
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

    def _badge_for(title: str) -> str | None:
        t = (title or "").lower()
        if "sentiment" in t:
            return "Sentiment"
        if "news" in t:
            return "News"
        if "market" in t:
            return "Market"
        if "risk" in t:
            return "Risks"
        if "opportun" in t:
            return "Opportunity"
        if "summary" in t:
            return "Summary"
        return None

    for i, section in enumerate(sections):
        title = section.get("title", f"Section {i+1}")
        content = section.get("content", "")
        icon = SECTION_ICON.get(title, "📌")
        badge = _badge_for(title)

        body = _format_content(content)
        card_html = _report_section_card(icon=icon, title=title, content=body, badge=badge)

        if expandable and title != "Disclaimer":
            with st.expander(title, expanded=True if i == 0 else False):
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.markdown(card_html, unsafe_allow_html=True)

        if title == "Disclaimer":
            st.markdown(
                f'<div style="font-size:var(--font-size-xs);color:var(--muted);font-style:italic;padding:var(--space-2) 0;">{safe_html_escape(content)}</div>',
                unsafe_allow_html=True,
            )


def render_synthesized_report(report: dict[str, Any]):
    """Render a synthesized report with premium section cards."""
    sections_config = [
        ("executive_summary", "🧠", "Executive Summary", None),
        ("market_snapshot", "📈", "Market Snapshot", "Market"),
        ("news_summary", "📰", "News Summary", "News"),
        ("sentiment_summary", "🧾", "Sentiment Summary", "Sentiment"),
        ("risks", "⚠️", "Risks", "Risks"),
        ("opportunities", "🚀", "Opportunities", "Opportunity"),
    ]

    for key, icon, label, badge in sections_config:
        val = report.get(key)
        if not val:
            continue

        if isinstance(val, list):
            items = []
            for item in val:
                items.append(
                    f'<div style="display:flex;gap:0.5rem;padding:0.25rem 0;align-items:flex-start;">'
                    f'<span style="color:var(--primary);flex-shrink:0;font-size:0.75rem;margin-top:0.25rem;">▸</span>'
                    f'<span>{safe_html_escape(str(item))}</span></div>'
                )
            content = "".join(items)
        else:
            content = _format_content(str(val))

        st.markdown(_report_section_card(icon, label, content, badge), unsafe_allow_html=True)

    disclaimer = report.get("disclaimer", "This is not investment advice.")
    st.markdown(
        f'<div style="font-size:var(--font-size-xs);color:var(--muted);font-style:italic;padding:var(--space-2) 0;text-align:center;">{safe_html_escape(disclaimer)}</div>',
        unsafe_allow_html=True,
    )


def _render_citation(citation: dict[str, Any], index: int):
    """Render a single citation as a premium card."""
    title = str(citation.get("title", "Untitled"))
    source = citation.get("source", "Unknown")
    url = citation.get("url")
    date = citation.get("date")
    cite_type = citation.get("type", "unknown")
    snippet = citation.get("snippet", "")

    st.markdown(
        f'<div class="ds-card" style="padding:var(--space-4);margin-bottom:var(--space-3);border-left:3px solid var(--border-dark);">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:var(--space-3);margin-bottom:var(--space-2);">'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);color:var(--text);">'
        f'{index + 1}. {safe_html_escape(title)}</div>'
        f'</div>'
        f'<span class="ds-badge" style="flex-shrink:0;">{safe_html_escape(cite_type)}</span>'
        f'</div>'
        f'<div style="display:flex;gap:var(--space-4);font-size:var(--font-size-xs);color:var(--muted);margin-bottom:var(--space-2);flex-wrap:wrap;">'
        f'<span>📰 {safe_html_escape(source)}</span>'
        + (f'<span>📅 {safe_html_escape(date)}</span>' if date else "")
        + '</div>'
        + (f'<div style="font-size:var(--font-size-xs);color:var(--muted);line-height:var(--leading-normal);margin-bottom:var(--space-2);">"{safe_html_escape(snippet[:200])}"{"..." if len(snippet) > 200 else ""}</div>'
           if snippet else "")
        + (f'<a href="{safe_html_escape(url)}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:4px;font-size:var(--font-size-xs);color:var(--primary);font-weight:var(--font-weight-medium);">🔗 View Source →</a>'
           if url else "")
        + '</div>',
        unsafe_allow_html=True,
    )


def render_report_card(
    report: dict[str, Any],
    on_click: Callable[[str], None] | None = None,
):
    """Render a compact premium report card for history view."""
    query = report.get("query", "Unknown Query")[:60]
    tickers = report.get("tickers", [])
    status = report.get("status", "unknown")

    st.markdown(
        f'<div class="ds-card" style="padding:var(--space-4);margin-bottom:var(--space-3);display:flex;align-items:center;justify-content:space-between;gap:var(--space-4);">'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-weight:var(--font-weight-semibold);font-size:var(--font-size-sm);color:var(--text);margin-bottom:2px;">{safe_html_escape(query)}</div>'
        f'<div style="display:flex;gap:var(--space-3);font-size:var(--font-size-xs);color:var(--muted);">'
        f'<span>📊 {", ".join(tickers) if tickers else "No tickers"}</span>'
        f'<span>{status_badge(status)}</span>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    req_id = report.get("request_id", "")
    if isinstance(req_id, str) and req_id and on_click:
        if st.button("View Report", key=f"view_{req_id}", use_container_width=True, type="secondary"):
            on_click(req_id)
