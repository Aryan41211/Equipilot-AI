
# EquiPilot AI - Sidebar Component
# Navigation, research inputs, system status, and history

import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

import streamlit as st

from frontend.components.research_form_helpers import looks_like_ticker

from frontend.components.design_system_ui import (
    section_header,
    title_brand,
    status_badge,
)

API_BASE_URL = os.environ.get("EQUIPILOT_API_URL", "").rstrip("/")


_SECTION_ICONS = {
    "research": "🔬",
    "quick": "⚡",
    "model": "🧠",
    "status": "🖥",
    "history": "📋",
    "about": "ℹ️",
}


def _sidebar_section(icon: str, title: str, subtitle: str | None = None) -> str:
    """Compact sidebar section header with icon."""
    subtitle_html = f'<div style="font-size:var(--font-size-xs);color:var(--muted);margin-top:1px;line-height:1.3;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
      <span style="font-size:14px;width:20px;flex-shrink:0;">{icon}</span>
      <div>
        <div style="font-size:var(--font-size-xs);font-weight:var(--font-weight-semibold);color:var(--text);letter-spacing:-0.01em;text-transform:uppercase;opacity:0.7;">{title}</div>
        {subtitle_html}
      </div>
    </div>
    """


def render_sidebar(on_analyze: Callable[[dict[str, Any]], None] | None = None):
    """Render sidebar with analysis inputs, system status, and recent reports."""
    st.markdown(title_brand(), unsafe_allow_html=True)

    st.markdown(f'<hr style="margin:1rem 0 !important;" />', unsafe_allow_html=True)

    # --- Research (primary CTA) ---
    st.markdown(_sidebar_section(_SECTION_ICONS["research"], "Research", "Configure and run analysis"), unsafe_allow_html=True)

    with st.form("analysis_form"):
        company_or_ticker = st.text_input(
            "Company or Ticker *",
            placeholder="e.g., AAPL, MSFT, or Apple Inc.",
            key="company_ticker_input",
            help="Enter a stock ticker (e.g., AAPL) or company name for entity resolution.",
        )

        query = st.text_area(
            "Research Question *",
            placeholder='e.g., "What are the key growth drivers and margin trends?"',
            height=90,
            key="query_input",
            help="Describe what you want to research. Be specific for better results.",
        )

        analysis_type = st.selectbox(
            "Analysis Scope",
            options=["Full Research", "Fundamentals", "News", "Sentiment"],
            index=0,
            key="analysis_type",
            help="Full Research combines all data sources. Narrower scopes focus on specific areas.",
        )

        submitted = st.form_submit_button("Run Analysis", type="primary", use_container_width=True)

    if submitted:
        company_or_ticker_val = (company_or_ticker or "").strip()
        query_val = (query or "").strip()

        if not company_or_ticker_val:
            st.error("Please enter a Company / Ticker.")
            return
        if not query_val:
            st.error("Please enter a Query.")
            return

        include_news = analysis_type in ("News", "Full Research")
        include_sentiment = analysis_type in ("Sentiment", "Full Research")
        include_fundamentals = analysis_type in ("Fundamentals", "Full Research")

        normalized = company_or_ticker_val.strip().upper()
        tickers = [normalized] if looks_like_ticker(company_or_ticker_val) else None

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
            st.session_state["_last_analysis_form_data"] = form_data

    st.markdown(f'<hr style="margin:1.25rem 0 !important;" />', unsafe_allow_html=True)

    # --- Quick Actions ---
    st.markdown(_sidebar_section(_SECTION_ICONS["quick"], "Quick Actions", "One-click examples"), unsafe_allow_html=True)
    quick_examples = [
        ("AAPL", "Market snapshot with fundamentals, news, and valuation"),
        ("MSFT", "Recent news, sentiment, and competitive positioning"),
        ("NVDA", "Growth drivers, risks, and financial health"),
    ]
    for t, q in quick_examples:
        if st.button(f"{t}", key=f"qa_{t}", use_container_width=True):
            if on_analyze:
                on_analyze(
                    {
                        "company_or_ticker": t,
                        "query": q,
                        "tickers": [t],
                        "include_news": True,
                        "include_sentiment": True,
                        "include_fundamentals": True,
                        "include_technicals": False,
                        "analysis_type": "Full Research",
                        "max_report_length": st.session_state.get("max_report_length", 5000),
                    }
                )
            else:
                st.session_state["_last_analysis_form_data"] = {
                    "company_or_ticker": t,
                    "query": q,
                    "tickers": [t],
                    "include_news": True,
                    "include_sentiment": True,
                    "include_fundamentals": True,
                    "include_technicals": False,
                    "analysis_type": "Full Research",
                    "max_report_length": st.session_state.get("max_report_length", 5000),
                }

    st.markdown(f'<hr style="margin:1.25rem 0 !important;" />', unsafe_allow_html=True)

    # --- System Status ---
    st.markdown(_sidebar_section(_SECTION_ICONS["status"], "System Status", "Backend health & integrations"), unsafe_allow_html=True)
    render_system_status()

    st.markdown(f'<hr style="margin:1.25rem 0 !important;" />', unsafe_allow_html=True)

    # --- Recent Reports ---
    st.markdown(_sidebar_section(_SECTION_ICONS["history"], "Recent Reports", "Session research history"), unsafe_allow_html=True)
    render_recent_reports()

    st.markdown(f'<hr style="margin:1.25rem 0 !important;" />', unsafe_allow_html=True)

    # --- About ---
    st.markdown(_sidebar_section(_SECTION_ICONS["about"], "About"), unsafe_allow_html=True)
    st.caption(
        "EquiPilot AI is an **informational equity research assistant** built with LangGraph orchestration. "
        "It combines market data, news, and LLM synthesis — but does not provide investment advice."
    )


def render_system_status():
    """Render backend health status."""
    try:
        if not API_BASE_URL:
            st.caption("API not configured (set EQUIPILOT_API_URL).")
            return

        import requests

        from frontend.app import build_backend_url

        health_url = build_backend_url("health")
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            health = response.json()

            # Status indicator row
            c1, c2 = st.columns([1, 3])
            with c1:
                st.markdown(
                    '<span style="display:inline-flex;align-items:center;gap:4px;font-size:var(--font-size-xs);color:var(--success);">'
                    '<span style="width:6px;height:6px;border-radius:50%;background:var(--success);display:inline-block;"></span>'
                    "Connected</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<span style="font-size:var(--font-size-xs);color:var(--muted);">{API_BASE_URL}</span>',
                    unsafe_allow_html=True,
                )

            services = health.get("services", {})
            svc_status = []
            if services.get("openai"):
                svc_status.append(
                    '<span style="color:var(--success)">●</span> OpenAI'
                )
            else:
                svc_status.append(
                    '<span style="color:var(--muted)">○</span> OpenAI'
                )
            if services.get("news_api"):
                svc_status.append(
                    '<span style="color:var(--success)">●</span> News'
                )
            else:
                svc_status.append(
                    '<span style="color:var(--muted)">○</span> News'
                )

            st.markdown(
                f'<div style="display:flex;gap:12px;margin-top:4px;font-size:var(--font-size-xs);">{ "".join(svc_status) }</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:4px;font-size:var(--font-size-xs);color:var(--danger);">'
                '<span style="width:6px;height:6px;border-radius:50%;background:var(--danger);display:inline-block;"></span>'
                "Error</span>",
                unsafe_allow_html=True,
            )
    except Exception:
        st.markdown(
            '<span style="display:inline-flex;align-items:center;gap:4px;font-size:var(--font-size-xs);color:var(--danger);">'
            '<span style="width:6px;height:6px;border-radius:50%;background:var(--danger);display:inline-block;"></span>'
            "Unreachable</span>",
            unsafe_allow_html=True,
        )
        if API_BASE_URL:
            try:
                from frontend.app import build_backend_url

                st.caption(f"Checked: {build_backend_url('health')}")
            except Exception:
                st.caption("Checked: /health")


def render_recent_reports():
    """Render session-only report history in sidebar."""
    history = st.session_state.get("research_history", [])

    if not history:
        st.caption("No recent reports")
        return

    for item in history[-5:]:
        req_id = item.get("request_id", "")[:8]
        query = item.get("query", "Unknown")[:40]
        if st.button(f"{query}...", key=f"sidebar_report_{req_id}", use_container_width=True):
            st.session_state.current_request_id = item.get("request_id")
            st.session_state.is_processing = True
            st.session_state.current_report = None
            st.session_state.execution_trace = None
            st.session_state.poll_count = 0
            st.session_state.poll_started_at = datetime.utcnow().timestamp()
            st.rerun()
