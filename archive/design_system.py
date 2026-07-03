from __future__ import annotations

from typing import Any

THEME_CSS = """
:root{
  --bg: #f7f8fb;
  --panel: #ffffff;
  --text: #1f2937;
  --muted: #6b7280;
  --border: #e5e7eb;
  --shadow: 0 6px 20px rgba(17, 24, 39, 0.06);

  --accent: #0b3d91;
  --accent-2: #06b6d4;

  --success: #16a34a;
  --warning: #f59e0b;
  --danger: #ef4444;

  --radius-xl: 18px;
  --radius-lg: 14px;
  --radius-md: 12px;

  --focus: rgba(11, 61, 145, .35);

  --font-sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
}

html, body{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--font-sans) !important;
}

.block-container{
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}

.stApp [data-testid="stSidebar"]{
  background: #ffffff !important;
  border-right: 1px solid var(--border) !important;
}

.stAlert{
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02) !important;
}

.stExpander section{
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  background: #fff !important;
}

[data-testid="stMetric"]{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 0.75rem 0.9rem;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}

.ds-card{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow);
}

.ds-flex{
  display:flex;
  align-items:center;
  gap: .6rem;
}

:focus{
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}

a{ color: var(--accent) !important; text-decoration: none !important; }
a:hover{ text-decoration: underline !important; }
"""


def inject_global_styles() -> None:
    import streamlit as st

    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def title_brand() -> str:
    return """
    <div class="ds-flex" style="gap: .85rem;">
      <div style="width:38px;height:38px;border-radius:12px;background:linear-gradient(180deg, rgba(11,61,145,1) 0%, rgba(11,61,145,.86) 100%);display:flex;align-items:center;justify-content:center;color:white;font-weight:800;">
        EP
      </div>
      <div>
        <div style="font-size: 28px; line-height: 1.15; font-weight: 800; letter-spacing: -0.02em;">EquiPilot AI</div>
        <div style="margin-top: 2px; font-size: 13px; color: var(--muted); font-weight: 600;">Agentic Equity Research Assistant</div>
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
        <div style="margin: 10px 0 14px 0;">
          <div style="font-size: 18px; font-weight: 800; letter-spacing: -0.01em;">{title}</div>
          <div style="margin-top: 4px; font-size: 13px; color: var(--muted); font-weight: 600;">{subtitle}</div>
        </div>
        """
    return f"""
    <div style="margin: 10px 0 14px 0;">
      <div style="font-size: 18px; font-weight: 800; letter-spacing: -0.01em;">{title}</div>
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
      gap:8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(0,0,0,0.03);
      border: 1px solid var(--border);
      color: var(--text);
      font-weight: 700;
      font-size: 12px;
    ">
      <span style="width:8px;height:8px;border-radius:99px;background:{color};display:inline-block;"></span>
      {label}
    </span>
    """


def alert_markdown(message: str, kind: str = "info") -> str:
    kind_map = {
        "info": "var(--accent-2)",
        "success": "var(--success)",
        "warning": "var(--warning)",
        "danger": "var(--danger)",
    }
    color = kind_map.get(kind, "var(--accent-2)")
    return f"""
    <div class="ds-card" style="
      padding: 14px 16px;
      border-radius: var(--radius-lg);
      box-shadow: none;
      border: 1px solid var(--border);
      background: rgba(6,182,212,0.04);
    ">
      <div style="display:flex; align-items:flex-start; gap: 10px;">
        <div style="width:10px;height:10px;border-radius:99px;background:{color};margin-top: 6px;"></div>
        <div style="font-weight: 700; line-height: 1.35;">{message}</div>
      </div>
    </div>
    """


def safe_html_escape(text: Any) -> str:
    s = "" if text is None else str(text)
    return (
        s.replace("&", "&amp;")
        .replace("<", "<")
        .replace(">", ">")
        .replace('"', """)
        .replace("'", "&#x27;")
    )
