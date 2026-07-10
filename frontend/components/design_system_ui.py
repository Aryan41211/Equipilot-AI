
from __future__ import annotations

from typing import Any

THEME_CSS = """
:root{
  /* Light Mode (Professional Neutral) */
  --bg: #f8fafc;
  --panel: #ffffff;
  --text: #0f172a;   /* dark blue-gray */
  --muted: #64748b;   /* slate */
  --border: #e2e8f0;  /* light gray */
  --border-dark: #cbd5e1;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
  --transition: all 0.2s ease;

  --primary: #2563eb;   /* blue-600 */
  --primary-hover: #1d4ed8;
  --secondary: #64748b;
  --accent: #0b3d91;   /* deep blue */
  --accent-2: #06b6d4; /* cyan */

  --success: #059669;
  --warning: #d97706;
  --danger: #dc2626;

  --info-bg: rgba(6, 182, 212, 0.04);
  --success-bg: rgba(5, 150, 105, 0.05);
  --warning-bg: rgba(217, 119, 6, 0.05);
  --error-bg: rgba(220, 38, 38, 0.05);

  --radius-xl: 1rem;
  --radius-lg: 0.75rem;
  --radius-md: 0.5rem;
  --radius-sm: 0.25rem;

  --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;

  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --focus-ring: rgba(37, 99, 235, 0.25);
}

/* Base */
html, body{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--font-sans) !important;
  font-size: var(--font-size-base);
  line-height: 1.6;
}

/* Containers */
.block-container{
  padding-top: 2rem;
  padding-bottom: 3rem;
  max-width: 1200px;
}

/* Sidebar */
.stApp [data-testid="stSidebar"]{
  background: var(--panel) !important;
  border-right: 1px solid var(--border) !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6{
  color: var(--text);
  font-weight: var(--font-weight-bold);
  line-height: 1.2;
  margin-top: 0;
  margin-bottom: 0.5rem;
}
h1{ font-size: var(--font-size-3xl); }
h2{ font-size: var(--font-size-2xl); }
h3{ font-size: var(--font-size-xl); }
h4{ font-size: var(--font-size-lg); }
h5{ font-size: var(--font-size-base); }
h6{ font-size: var(--font-size-sm); }

/* Text */
p{
  margin-bottom: 1rem;
  color: var(--text);
}

/* Links */
a{
  color: var(--primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}
a:hover{
  color: var(--primary-hover);
  text-decoration: underline;
}

/* Buttons */
.stButton > button{
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  transition: var(--transition);
  border: 1px solid transparent;
  padding: 0.5rem 1rem;
}
.stButton > button[kind="primary"]{
  background-color: var(--primary);
  color: white;
  border: none;
}
.stButton > button[kind="primary"]:hover{
  background-color: var(--primary-hover);
  box-shadow: var(--shadow-sm);
}
.stButton > button[kind="secondary"]{
  background-color: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
}
.stButton > button[kind="secondary"]:hover{
  background-color: rgba(37, 99, 235, 0.08);
  border-color: var(--primary-hover);
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select{
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.5rem 0.75rem;
  font-size: var(--font-size-base);
  background-color: var(--panel);
  color: var(--text);
  transition: var(--transition);
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus{
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--focus-ring);
  outline: none;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder{
  color: var(--muted);
  opacity: 0.7;
}

/* Metrics */
[data-testid="stMetric"]{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1rem;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}
[data-testid="stMetric"]:hover{
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

/* Progress bar */
.stProgress > div > div > div > div {
  background-color: var(--primary);
  height: 0.5rem;
  border-radius: var(--radius-sm);
}
.stProgress > div > div {
  background-color: rgba(37, 99, 235, 0.2);
  border-radius: var(--radius-sm);
  height: 0.5rem;
}

/* Ensure progress bar container has proper spacing */
.stProgress {
  margin: 1rem 0;
}

/* Expander */
.stExpander{
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
}
.stExpander > details > summary{
  padding: 0.75rem 1rem;
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  background-color: transparent;
  cursor: pointer;
}
.stExpander > details > summary:hover{
  background-color: rgba(0,0,0,0.02);
}
.stExpander > details > .content{
  padding: 1rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{
  gap: 0.5rem;
}
.stTabs [data-baseweb="tab"]{
  background-color: transparent;
  border-radius: var(--radius-md);
  padding: 0.5rem 0.75rem;
  font-weight: var(--font-weight-medium);
  transition: var(--transition);
}
.stTabs [data-baseweb="tab"][aria-selected="true"]{
  background-color: var(--primary);
  color: white;
}

/* Alerts */
.stAlert{
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1rem;
  margin-bottom: 1rem;
}
.stAlert[data-baseweb="notification"]{
  background-color: rgba(13, 110, 253, 0.05);
  border-left: 4px solid var(--primary);
}
.stAlert[data-baseweb="notification"][kind="info"]{
  background-color: rgba(13, 110, 253, 0.05);
  border-left-color: var(--primary);
}
.stAlert[data-baseweb="notification"][kind="success"]{
  background-color: rgba(5, 150, 105, 0.05);
  border-left-color: var(--success);
}
.stAlert[data-baseweb="notification"][kind="warning"]{
  background-color: rgba(217, 119, 6, 0.05);
  border-left-color: var(--warning);
}
.stAlert[data-baseweb="notification"][kind="error"]{
  background-color: rgba(220, 38, 38, 0.05);
  border-left-color: var(--danger);
}

/* Cards */
.ds-card{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}
.ds-card:hover{
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

/* Layout utilities */
.ds-flex{
  display:flex;
  align-items:center;
  gap: .75rem;
}
.ds-grid{
  display: grid;
  gap: 1rem;
}

/* Misc */
:focus-visible{
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
hr{
  border: 0;
  border-top: 1px solid var(--border);
  margin: 1.5rem 0;
}
code{
  background-color: rgba(0,0,0,0.04);
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}
pre{
  background-color: rgba(0,0,0,0.04);
  padding: 1rem;
  border-radius: var(--radius-lg);
  overflow-x: auto;
}
blockquote{
  border-left: 4px solid var(--border);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--muted);
}
img{
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
}

/* Dark mode adjustments (Enterprise palette) */
@media (prefers-color-scheme: dark){
  :root{
    --bg: #0B1220;
    --panel: #111827;
    --text: #f8fafc;
    --muted: #9CA3AF;
    --border: #1F2937;
    --border-dark: #334155;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow: 0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -1px rgba(0,0,0,0.2);
    --primary: #3B82F6;
    --primary-hover: #2563eb;
    --success: #22C55E;
    --warning: #F59E0B;
    --danger: #EF4444;
    --info-bg: rgba(59, 130, 246, 0.14);
    --success-bg: rgba(34, 197, 94, 0.14);
    --warning-bg: rgba(245, 158, 11, 0.14);
    --error-bg: rgba(239, 68, 68, 0.14);

    --accent: #3B82F6;
    --accent-2: #60A5FA;

    --shadow-sm: 0 1px 3px rgba(0,0,0,0.35);
    --shadow: 0 8px 18px rgba(0,0,0,0.35);
  }
}

/* Premium micro-interactions */
@keyframes dsPulse {
  0%{ box-shadow: 0 0 0 rgba(59,130,246,0.0); }
  40%{ box-shadow: 0 0 0 6px rgba(59,130,246,0.18); }
  100%{ box-shadow: 0 0 0 rgba(59,130,246,0.0); }
}
.ds-card--premium{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}
.ds-card--premium:hover{
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

/* Lightweight shimmer skeleton */
@keyframes dsShimmer{
  0%{ background-position: -200% 0; }
  100%{ background-position: 200% 0; }
}
.ds-skeleton{
  background: linear-gradient(90deg, rgba(255,255,255,0.06) 25%, rgba(255,255,255,0.12) 37%, rgba(255,255,255,0.06) 63%);
  background-size: 400% 100%;
  animation: dsShimmer 1.2s ease-in-out infinite;
  border-radius: var(--radius-md);
}

/* Accessible focus improvements */
button:focus-visible, [role="button"]:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible{
  outline: 2px solid var(--focus-ring) !important;
  outline-offset: 2px !important;
}

/* Animated stepper */
.ds-stepper{
  display:flex;
  gap: 0.75rem;
  width: 100%;
  flex-wrap: wrap;
}
.ds-step{
  flex: 1 1 140px;
  min-width: 140px;
  padding: 0.75rem 0.75rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: rgba(0,0,0,0.01);
  transition: var(--transition);
}
.ds-step--done{
  border-color: rgba(34,197,94,0.35);
  animation: dsPulse 0.8s ease-out 1;
}
.ds-step--active{
  border-color: rgba(59,130,246,0.55);
  background: rgba(59,130,246,0.08);
}
.ds-step__icon{
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight: var(--font-weight-bold);
  background: rgba(59,130,246,0.12);
  color: var(--primary);
}
.ds-step--done .ds-step__icon{
  background: rgba(34,197,94,0.14);
  color: var(--success);
}
.ds-step__title{
  margin-top: 0.5rem;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
}
.ds-step__sub{
  margin-top: 0.25rem;
  font-size: var(--font-size-xs);
  color: var(--muted);
  line-height: 1.25;
}

/* Fade animations */
@keyframes fadeIn{
  from{ opacity: 0; transform: translateY(10px); }
  to{ opacity: 1; transform: translateY(0); }
}
.fade-in{
  animation: fadeIn 0.3s ease-out forwards;
}


"""


def inject_global_styles() -> None:
    import streamlit as st

    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def title_brand() -> str:
    # Keep to simple HTML (used with st.markdown(..., unsafe_allow_html=True)).
    return """
    <div class="ds-flex" style="gap: .85rem;">
      <div style="width:38px;height:38px;border-radius:var(--radius-md);background:linear-gradient(180deg, rgba(11,61,145,1) 0%, rgba(11,61,145,.86) 100%);display:flex;align-items:center;justify-content:center;color:white;font-weight:var(--font-weight-bold);">
        EP
      </div>
      <div>
        <div style="font-size: var(--font-size-2xl); line-height: 1.15; font-weight: var(--font-weight-bold); letter-spacing: -0.02em;">EquiPilot AI</div>
        <div style="margin-top: 0.125rem; font-size: var(--font-size-sm); color: var(--muted); font-weight: var(--font-weight-medium);">Agentic Equity Research Assistant</div>
      </div>
    </div>
    """


def ds_card_start(style: str = "") -> str:
    return f'<div class="ds-card" style="{style}">'


def ds_card_end() -> str:
    return "</div>"


def section_header(title: str, subtitle: str | None = None) -> str:
    if subtitle:
        return f"""
        <div style="margin: 0.5rem 0 0.75rem 0;">
          <div style="font-size: var(--font-size-lg); font-weight: var(--font-weight-bold); letter-spacing: -0.01em;">{safe_html_escape(title)}</div>
          <div style="margin-top: 0.25rem; font-size: var(--font-size-xs); color: var(--muted); font-weight: var(--font-weight-medium);">{safe_html_escape(subtitle)}</div>
        </div>
        """
    return f"""
    <div style="margin: 0.5rem 0 0.75rem 0;">
      <div style="font-size: var(--font-size-lg); font-weight: var(--font-weight-bold); letter-spacing: -0.01em;">{safe_html_escape(title)}</div>
    </div>
    """


def status_badge(status: str) -> str:
    s = (status or "").lower().strip()
    if s in ("completed", "success", "done"):
        color = "var(--success)"
        label = "Completed"
    elif s in ("failed", "error"):
        color = "var(--danger)"
        label = "Failed"
    elif s in ("in_progress", "in progress", "running", "processing"):
        color = "var(--accent-2)"
        label = "In Progress"
    else:
        color = "var(--accent)"
        label = status.title() if status else "Status"

    return f"""
    <span style="
      display:inline-flex;
      align-items:center;
      gap:0.5rem;
      padding: 0.375rem 0.625rem;
      border-radius: 999px;
      background: rgba(0,0,0,0.03);
      border: 1px solid var(--border);
      color: var(--text);
      font-weight: var(--font-weight-semibold);
      font-size: var(--font-size-xs);
    ">
      <span style="width:0.5rem;height:0.5rem;border-radius:99px;background:{color};display:inline-block;"></span>
      {safe_html_escape(label)}
    </span>
    """


def alert_markdown(message: str, kind: str = "info") -> str:
    color_map = {
        "info": "var(--accent-2)",
        "success": "var(--success)",
        "warning": "var(--warning)",
        "danger": "var(--danger)",
    }
    bg_map = {
        "info": "var(--info-bg)",
        "success": "var(--success-bg)",
        "warning": "var(--warning-bg)",
        "danger": "var(--error-bg)",
    }
    color = color_map.get(kind, "var(--accent-2)")
    bg = bg_map.get(kind, "var(--info-bg)")

    return f"""
    <div class="ds-card" style="
      padding: 0.875rem 1rem;
      border-radius: var(--radius-lg);
      box-shadow: none;
      border: 1px solid var(--border);
      background: {bg};
    ">
      <div style="display:flex; align-items:flex-start; gap: 0.5rem;">
        <div style="width:0.625rem;height:0.625rem;border-radius:99px;background:{color};display:inline-block;"></div>
        <div style="font-weight: var(--font-weight-bold); line-height: 1.35;">{safe_html_escape(message)}</div>
      </div>
    </div>
    """


def quick_action_card(icon: str, title: str, description: str, cta: str) -> str:
    """Render a quick action card for empty dashboard."""
    return f"""
    <div style="
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1rem;
        box-shadow: var(--shadow);
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    ">
        <div style="font-size: 1.5rem;">{icon}</div>
        <div style="font-weight: var(--font-weight-bold); font-size: var(--font-size-sm); color: var(--text);">{safe_html_escape(title)}</div>
        <div style="font-size: var(--font-size-xs); color: var(--muted); line-height: 1.4;">{safe_html_escape(description)}</div>
        <div style="font-size: var(--font-size-xs); color: var(--accent); font-weight: var(--font-weight-medium); margin-top: auto;">{safe_html_escape(cta)}</div>
    </div>
    """


def safe_html_escape(text: Any) -> str:
    """
    Escape HTML special characters for safe insertion into unsafe_allow_html templates.

    Must escape at least: &, <, >.
    We also escape quotes to prevent breaking attributes in HTML templates.
    """
    import html

    s = "" if text is None else str(text)
    # html.escape escapes &, <, >
    return html.escape(s, quote=True)
