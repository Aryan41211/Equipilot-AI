
from __future__ import annotations

from typing import Any

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root{
  /* === Design Tokens === */

  /* Typography */
  --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;

  --font-size-xs: 0.75rem;
  --font-size-sm: 0.8125rem;
  --font-size-base: 0.9375rem;
  --font-size-lg: 1.0625rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  --font-size-4xl: 2.25rem;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  --tracking-tight: -0.025em;
  --tracking-normal: 0em;
  --tracking-wide: 0.025em;

  /* Light Mode — Enterprise Neutral */
  --bg: #f6f8fa;
  --panel: #ffffff;
  --text: #0f172a;
  --muted: #64748b;
  --border: #e2e8f0;
  --border-dark: #cbd5e1;

  --shadow-xs: 0 1px 2px rgba(0,0,0,0.03);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.03);
  --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.06), 0 10px 10px -5px rgba(0,0,0,0.03);
  --transition: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 250ms cubic-bezier(0.4, 0, 0.2, 1);

  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --primary-light: rgba(37, 99, 235, 0.08);
  --secondary: #64748b;
  --secondary-hover: #475569;

  --accent: #0b3d91;
  --accent-2: #06b6d4;

  --success: #059669;
  --success-light: rgba(5, 150, 105, 0.08);
  --warning: #d97706;
  --warning-light: rgba(217, 119, 6, 0.08);
  --danger: #dc2626;
  --danger-light: rgba(220, 38, 38, 0.08);
  --info: #0891b2;
  --info-light: rgba(8, 145, 178, 0.08);

  --info-bg: rgba(8, 145, 178, 0.05);
  --success-bg: rgba(5, 150, 105, 0.05);
  --warning-bg: rgba(217, 119, 6, 0.05);
  --error-bg: rgba(220, 38, 38, 0.05);

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-full: 9999px;

  --focus-ring: rgba(37, 99, 235, 0.25);

  /* Spacing (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
}

/* === Reset & Base === */
*{
  box-sizing: border-box;
}
html, body{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--font-sans) !important;
  font-size: var(--font-size-base);
  line-height: var(--leading-normal);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* === Layout === */
.block-container{
  padding: var(--space-8) var(--space-6) var(--space-12) var(--space-6) !important;
  max-width: 1280px;
  margin: 0 auto;
}

/* === Sidebar === */
[data-testid="stSidebar"]{
  background: var(--panel) !important;
  border-right: 1px solid var(--border) !important;
  transition: var(--transition);
}
[data-testid="stSidebar"] > div:first-child{
  padding: var(--space-6) var(--space-5) !important;
}
[data-testid="stSidebar"] .stMarkdown{
  margin-bottom: var(--space-2);
}
[data-testid="stSidebar"] hr{
  margin: var(--space-5) 0 !important;
  border-color: var(--border);
  opacity: 0.6;
}

/* === Typography === */
h1, h2, h3, h4, h5, h6{
  color: var(--text);
  font-weight: var(--font-weight-semibold);
  line-height: var(--leading-snug);
  letter-spacing: var(--tracking-tight);
  margin-top: 0;
  margin-bottom: var(--space-2);
}
h1{ font-size: var(--font-size-3xl); letter-spacing: -0.03em; }
h2{ font-size: var(--font-size-2xl); letter-spacing: -0.02em; }
h3{ font-size: var(--font-size-xl); letter-spacing: -0.015em; }
h4{ font-size: var(--font-size-lg); }
h5{ font-size: var(--font-size-base); }
h6{ font-size: var(--font-size-sm); }

p{
  margin-bottom: var(--space-4);
  color: var(--text);
  line-height: var(--leading-relaxed);
}
.caption, .stCaption{
  font-size: var(--font-size-sm);
  color: var(--muted);
  line-height: var(--leading-normal);
}

/* === Links === */
a{
  color: var(--primary);
  text-decoration: none;
  transition: var(--transition);
}
a:hover{
  color: var(--primary-hover);
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* === Buttons === */
.stButton > button{
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  transition: var(--transition);
  border: 1px solid transparent;
  padding: 0.5rem 1rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.stButton > button::after{
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0);
  transition: var(--transition);
}
.stButton > button:hover::after{
  background: rgba(255,255,255,0.08);
}
.stButton > button:active:not(:disabled)::after{
  background: rgba(0,0,0,0.06);
}
.stButton > button[kind="primary"]{
  background-color: var(--primary);
  color: white;
  border: none;
  box-shadow: 0 1px 2px rgba(37,99,235,0.2);
}
.stButton > button[kind="primary"]:hover:not(:disabled){
  background-color: var(--primary-hover);
  box-shadow: 0 2px 8px rgba(37,99,235,0.3);
  transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active:not(:disabled){
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(37,99,235,0.2);
}
.stButton > button[kind="primary"]:disabled{
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
.stButton > button[kind="secondary"]{
  background-color: transparent;
  color: var(--text);
  border: 1px solid var(--border);
}
.stButton > button[kind="secondary"]:hover:not(:disabled){
  background-color: var(--bg);
  border-color: var(--border-dark);
}
.stButton > button[kind="secondaryFormSubmit"]{
  background-color: var(--primary);
  color: white;
  border: none;
  box-shadow: 0 1px 2px rgba(37,99,235,0.2);
}
.stButton > button[kind="secondaryFormSubmit"]:hover:not(:disabled){
  background-color: var(--primary-hover);
  box-shadow: 0 2px 8px rgba(37,99,235,0.3);
  transform: translateY(-1px);
}
.stButton > button:focus-visible{
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

/* Sidebar buttons (quick actions, history) */
[data-testid="stSidebar"] .stButton > button{
  font-size: var(--font-size-sm);
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-sm);
  text-align: left;
  justify-content: flex-start;
}
[data-testid="stSidebar"] .stButton > button:hover:not(:disabled){
  background-color: var(--primary-light);
  border-color: transparent;
}

/* === Form Elements === */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stMultiSelect > div > div > div{
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  padding: 0.5rem 0.75rem !important;
  font-size: var(--font-size-sm) !important;
  background-color: var(--panel) !important;
  color: var(--text) !important;
  transition: var(--transition) !important;
  line-height: var(--leading-normal);
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > div:focus,
.stMultiSelect > div > div > div:focus{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px var(--focus-ring) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder{
  color: var(--muted) !important;
  opacity: 0.6;
}

/* Form labels */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stMultiSelect label, .stCheckbox label, .stRadio label{
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  color: var(--text);
  margin-bottom: var(--space-1);
}

/* Checkbox & Radio */
.stCheckbox, .stRadio{
  gap: var(--space-2);
}
.stCheckbox label, .stRadio label{
  font-size: var(--font-size-sm);
}

/* Select slider */
.stSlider label{
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
}

/* === Metrics === */
[data-testid="stMetric"]{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-xs);
  transition: var(--transition);
}
[data-testid="stMetric"]:hover{
  box-shadow: var(--shadow);
  border-color: var(--border-dark);
}
[data-testid="stMetric"] label{
  font-size: var(--font-size-xs);
  color: var(--muted);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}
[data-testid="stMetric"] [data-testid="stMetricValue"]{
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text);
  line-height: var(--leading-snug);
}
[data-testid="stMetric"] [data-testid="stMetricDelta"]{
  font-size: var(--font-size-sm);
}

/* === Progress Bar === */
.stProgress > div > div > div > div {
  background-color: var(--primary);
  height: 6px;
  border-radius: var(--radius-full);
}
.stProgress > div > div {
  background-color: rgba(37, 99, 235, 0.12);
  border-radius: var(--radius-full);
  height: 6px;
}
.stProgress{
  margin: var(--space-4) 0;
}

/* === Divider === */
hr, .stDivider, div[data-testid="stVerticalBlockBorder"]{
  border: 0 !important;
  border-top: 1px solid var(--border) !important;
  margin: var(--space-6) 0 !important;
  opacity: 0.7;
}

/* === Expander === */
.stExpander{
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-4);
  overflow: hidden;
  transition: var(--transition);
}
.stExpander:hover{
  border-color: var(--border-dark);
}
.stExpander > details > summary{
  padding: var(--space-3) var(--space-4);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--text);
  background-color: transparent;
  cursor: pointer;
  transition: var(--transition);
}
.stExpander > details > summary:hover{
  background-color: var(--bg);
}
.stExpander > details > .content{
  padding: var(--space-4);
  padding-top: 0;
}
.stExpander > details[open] > summary{
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-3);
}

/* === Tabs === */
.stTabs [data-baseweb="tab-list"]{
  gap: var(--space-1);
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}
.stTabs [data-baseweb="tab"]{
  background-color: transparent;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  padding: var(--space-2) var(--space-4);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  color: var(--muted);
  transition: var(--transition);
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.stTabs [data-baseweb="tab"]:hover{
  color: var(--text);
  background-color: var(--bg);
}
.stTabs [data-baseweb="tab"][aria-selected="true"]{
  color: var(--primary);
  border-bottom-color: var(--primary);
  background-color: transparent;
}

/* === Alerts === */
.stAlert{
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
}
.stAlert[data-baseweb="notification"]{
  border-left: 4px solid var(--primary);
  background-color: var(--info-light);
}
.stAlert[data-baseweb="notification"][kind="info"]{
  border-left-color: var(--info);
  background-color: var(--info-light);
}
.stAlert[data-baseweb="notification"][kind="success"]{
  border-left-color: var(--success);
  background-color: var(--success-light);
}
.stAlert[data-baseweb="notification"][kind="warning"]{
  border-left-color: var(--warning);
  background-color: var(--warning-light);
}
.stAlert[data-baseweb="notification"][kind="error"]{
  border-left-color: var(--danger);
  background-color: var(--danger-light);
}

/* === Cards === */
.ds-card{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xs);
  transition: var(--transition-slow);
}
.ds-card:hover{
  box-shadow: var(--shadow);
  border-color: var(--border-dark);
}
.ds-card--premium{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xs);
  transition: var(--transition-slow);
}
.ds-card--premium:hover{
  box-shadow: var(--shadow-lg);
  border-color: var(--border-dark);
  transform: translateY(-2px);
}

/* === Stepper === */
.ds-stepper{
  display:flex;
  gap: 0.75rem;
  width: 100%;
  flex-wrap: wrap;
}
.ds-step{
  flex: 1 1 140px;
  min-width: 140px;
  padding: 0.75rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: var(--panel);
  transition: var(--transition);
}
.ds-step--done{
  border-color: rgba(34,197,94,0.3);
  background: rgba(34,197,94,0.04);
}
.ds-step--active{
  border-color: rgba(59,130,246,0.45);
  background: rgba(59,130,246,0.06);
  box-shadow: 0 0 0 2px rgba(59,130,246,0.15);
}
.ds-step__icon{
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-sm);
  background: rgba(59,130,246,0.1);
  color: var(--primary);
  margin: 0 auto;
}
.ds-step--done .ds-step__icon{
  background: rgba(34,197,94,0.12);
  color: var(--success);
}
.ds-step__title{
  margin-top: var(--space-2);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  text-align: center;
}
.ds-step__sub{
  margin-top: 0.25rem;
  font-size: var(--font-size-xs);
  color: var(--muted);
  line-height: 1.25;
  text-align: center;
}

/* === Code & Pre === */
code{
  background-color: rgba(0,0,0,0.05);
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.875em;
}
pre{
  background-color: rgba(0,0,0,0.03);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  border: 1px solid var(--border);
}
pre code{
  background: none;
  padding: 0;
}

/* === Blockquote === */
blockquote{
  border-left: 3px solid var(--border-dark);
  padding-left: var(--space-4);
  margin: var(--space-4) 0;
  color: var(--muted);
  font-style: italic;
}

/* === Image === */
img{
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
}

/* === Table === */
table{
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-4) 0;
}
th, td{
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border);
  text-align: left;
  font-size: var(--font-size-sm);
}
th{
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  background: var(--bg);
}
tr:last-child td{
  border-bottom: none;
}

/* === Focus Styles === */
:focus-visible{
  outline: 2px solid var(--focus-ring) !important;
  outline-offset: 2px !important;
}
button:focus-visible,
[role="button"]:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible{
  outline: 2px solid var(--focus-ring) !important;
  outline-offset: 2px !important;
}

/* === Scrollbar === */
::-webkit-scrollbar{
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track{
  background: transparent;
}
::-webkit-scrollbar-thumb{
  background: var(--border-dark);
  border-radius: var(--radius-full);
}
::-webkit-scrollbar-thumb:hover{
  background: var(--muted);
}

/* === Utility Classes === */
.ds-flex{
  display:flex;
  align-items:center;
  gap: 0.75rem;
}
.ds-grid{
  display: grid;
  gap: var(--space-4);
}

/* === Animations === */
@keyframes fadeIn{
  from{ opacity: 0; transform: translateY(8px); }
  to{ opacity: 1; transform: translateY(0); }
}
.fade-in{
  animation: fadeIn 0.25s ease-out forwards;
}

@keyframes dsPulse{
  0%{ box-shadow: 0 0 0 rgba(59,130,246,0); }
  40%{ box-shadow: 0 0 0 6px rgba(59,130,246,0.15); }
  100%{ box-shadow: 0 0 0 rgba(59,130,246,0); }
}

@keyframes dsShimmer{
  0%{ background-position: -200% 0; }
  100%{ background-position: 200% 0; }
}
.ds-skeleton{
  background: linear-gradient(90deg, rgba(0,0,0,0.04) 25%, rgba(0,0,0,0.07) 37%, rgba(0,0,0,0.04) 63%);
  background-size: 400% 100%;
  animation: dsShimmer 1.2s ease-in-out infinite;
  border-radius: var(--radius-md);
}

/* === Status Badge === */
.ds-badge{
  display:inline-flex;
  align-items:center;
  gap: 0.4rem;
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-full);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-xs);
  line-height: 1.25;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
}

/* === KPI / Metric Card === */
.ds-kpi{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-xs);
  transition: var(--transition);
}
.ds-kpi:hover{
  box-shadow: var(--shadow);
  border-color: var(--border-dark);
}
.ds-kpi__label{
  font-size: var(--font-size-xs);
  color: var(--muted);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  margin-bottom: var(--space-1);
  line-height: var(--leading-normal);
}
.ds-kpi__value{
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text);
  line-height: var(--leading-snug);
  letter-spacing: -0.02em;
}
.ds-kpi__sublabel{
  font-size: var(--font-size-xs);
  color: var(--muted);
  margin-top: var(--space-1);
  line-height: var(--leading-normal);
}

/* === Interactive Suggestion Card === */
.ds-suggestion{
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--panel);
  transition: var(--transition-slow);
  cursor: default;
  position: relative;
}
.ds-suggestion:hover{
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
  transform: translateY(-1px);
}
.ds-suggestion__icon{
  font-size: 1.25rem;
  margin-bottom: var(--space-2);
}
.ds-suggestion__title{
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--text);
  margin-bottom: var(--space-1);
}
.ds-suggestion__desc{
  font-size: var(--font-size-xs);
  color: var(--muted);
  line-height: var(--leading-normal);
}

/* === Error / Warning / Success Cards === */
.ds-state-card{
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  line-height: var(--leading-normal);
}
.ds-state-card--error{
  border: 1px solid var(--danger);
  background: var(--danger-light);
  border-left: 4px solid var(--danger);
}
.ds-state-card--success{
  border: 1px solid var(--success);
  background: var(--success-light);
  border-left: 4px solid var(--success);
}
.ds-state-card--warning{
  border: 1px solid var(--warning);
  background: var(--warning-light);
  border-left: 4px solid var(--warning);
}
.ds-state-card--info{
  border: 1px solid var(--info);
  background: var(--info-light);
  border-left: 4px solid var(--info);
}
.ds-state-card__icon{
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 1px;
}
.ds-state-card__body{
  font-size: var(--font-size-sm);
  color: var(--text);
}
.ds-state-card__title{
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-1);
}
.ds-state-card__detail{
  font-size: var(--font-size-xs);
  color: var(--muted);
  margin-top: var(--space-1);
}

/* === Completion Badge === */
.ds-completion-badge{
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  background: var(--success-light);
  border: 1px solid rgba(5,150,105,0.2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--success);
}

/* === Hero Section === */
.ds-hero{
  margin-bottom: var(--space-8);
}
.ds-hero__title{
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.03em;
  line-height: 1.15;
  color: var(--text);
  margin-bottom: var(--space-2);
}
.ds-hero__subtitle{
  font-size: var(--font-size-base);
  color: var(--muted);
  line-height: var(--leading-relaxed);
  max-width: 640px;
}
.ds-hero__stats{
  display: flex;
  gap: var(--space-6);
  margin-top: var(--space-4);
  flex-wrap: wrap;
}
.ds-hero-stat{
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--muted);
}
.ds-hero-stat__value{
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  font-size: var(--font-size-base);
}

/* === Section Header === */
.ds-section-header{
  margin: var(--space-1) 0 var(--space-3) 0;
}
.ds-section-header__title{
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  color: var(--text);
  line-height: var(--leading-snug);
}
.ds-section-header__subtitle{
  margin-top: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--muted);
  font-weight: var(--font-weight-normal);
  line-height: var(--leading-normal);
}

/* === Data Table (st.dataframe) === */
[data-testid="stDataFrame"]{
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* === JSON Output === */
[data-testid="stJson"]{
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

/* === Timeline === */
.ds-timeline{
  position: relative;
  padding-left: var(--space-8);
}
.ds-timeline::before{
  content: '';
  position: absolute;
  left: 15px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: var(--border);
  border-radius: var(--radius-full);
}
.ds-timeline__item{
  position: relative;
  padding-bottom: var(--space-5);
}
.ds-timeline__item:last-child{
  padding-bottom: 0;
}
.ds-timeline__dot{
  position: absolute;
  left: calc(-1 * var(--space-8) + 6px);
  top: 4px;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: var(--panel);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  z-index: 1;
  transition: var(--transition);
}
.ds-timeline__item--active .ds-timeline__dot{
  border-color: var(--primary);
  background: var(--primary);
  color: white;
  box-shadow: 0 0 0 4px var(--focus-ring);
}
.ds-timeline__item--done .ds-timeline__dot{
  border-color: var(--success);
  background: var(--success);
  color: white;
}
.ds-timeline__item--error .ds-timeline__dot{
  border-color: var(--danger);
  background: var(--danger);
  color: white;
}
.ds-timeline__content{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  transition: var(--transition);
}
.ds-timeline__item--active .ds-timeline__content{
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
}
.ds-timeline__time{
  font-size: var(--font-size-xs);
  color: var(--muted);
  margin-top: var(--space-1);
}

/* === Animations & Micro-interactions === */
@keyframes slideUp{
  from{ opacity: 0; transform: translateY(12px); }
  to{ opacity: 1; transform: translateY(0); }
}
@keyframes slideDown{
  from{ opacity: 0; transform: translateY(-8px); }
  to{ opacity: 1; transform: translateY(0); }
}
@keyframes scaleIn{
  from{ opacity: 0; transform: scale(0.95); }
  to{ opacity: 1; transform: scale(1); }
}
@keyframes spin{
  to{ transform: rotate(360deg); }
}
@keyframes progressPulse{
  0%{ opacity: 0.6; }
  50%{ opacity: 1; }
  100%{ opacity: 0.6; }
}
.ds-animate-slide-up{
  animation: slideUp 0.3s ease-out forwards;
}
.ds-animate-slide-down{
  animation: slideDown 0.25s ease-out forwards;
}
.ds-animate-scale-in{
  animation: scaleIn 0.2s ease-out forwards;
}
.ds-animate-spin{
  animation: spin 1s linear infinite;
}
.ds-animate-pulse{
  animation: progressPulse 1.5s ease-in-out infinite;
}
.stApp [data-testid="stExpander"] .content{
  animation: slideDown 0.2s ease-out;
}

/* Responsive breakpoints */
@media (max-width: 1200px){
  .block-container{
    max-width: 100%;
    padding: var(--space-6) var(--space-4) !important;
  }
}
@media (max-width: 992px){
  .ds-hero__title{
    font-size: var(--font-size-3xl);
  }
  .ds-hero__stats{
    flex-direction: column;
    gap: var(--space-2);
  }
}
@media (max-width: 768px){
  .block-container{
    padding: var(--space-4) var(--space-3) !important;
  }
  [data-testid="stSidebar"] > div:first-child{
    padding: var(--space-4) var(--space-3) !important;
  }
  .ds-kpi{
    padding: var(--space-3);
  }
  .ds-kpi__value{
    font-size: var(--font-size-xl);
  }
  .ds-card{
    border-radius: var(--radius-lg);
  }
}
@media (max-width: 576px){
  .block-container{
    padding: var(--space-3) var(--space-2) !important;
  }
  h1{ font-size: var(--font-size-2xl); }
  h2{ font-size: var(--font-size-xl); }
  h3{ font-size: var(--font-size-lg); }
}

/* Accessibility: prefers-reduced-motion */
@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Accessibility: high contrast */
@media (prefers-contrast: high){
  :root{
    --border: #94a3b8;
    --border-dark: #64748b;
    --text: #000000;
    --muted: #334155;
  }
  .ds-state-card--error{
    border-width: 2px;
  }
  .ds-state-card--success{
    border-width: 2px;
  }
}

/* Accessibility: focus within for cards */
.ds-suggestion:focus-within{
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--focus-ring);
}

/* === Dark Mode — Vercel-inspired dark === */
@media (prefers-color-scheme: dark){
  :root{
    --bg: #0a0a0f;
    --panel: #121216;
    --text: #f5f5f5;
    --muted: #8a8a9a;
    --border: #1e1e26;
    --border-dark: #2a2a35;

    --shadow-xs: 0 1px 2px rgba(0,0,0,0.25);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
    --shadow: 0 4px 6px rgba(0,0,0,0.35), 0 2px 4px rgba(0,0,0,0.25);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.4), 0 4px 6px rgba(0,0,0,0.3);
    --shadow-xl: 0 20px 25px rgba(0,0,0,0.5), 0 10px 10px rgba(0,0,0,0.35);

    --primary: #3b82f6;
    --primary-hover: #60a5fa;
    --primary-light: rgba(59, 130, 246, 0.12);

    --accent: #60a5fa;
    --accent-2: #22d3ee;

    --success: #22c55e;
    --success-light: rgba(34, 197, 94, 0.12);
    --warning: #f59e0b;
    --warning-light: rgba(245, 158, 11, 0.12);
    --danger: #ef4444;
    --danger-light: rgba(239, 68, 68, 0.12);
    --info: #22d3ee;
    --info-light: rgba(34, 211, 238, 0.12);

    --info-bg: rgba(34, 211, 238, 0.06);
    --success-bg: rgba(34, 197, 94, 0.06);
    --warning-bg: rgba(245, 158, 11, 0.06);
    --error-bg: rgba(239, 68, 68, 0.06);

    --focus-ring: rgba(59, 130, 246, 0.35);
  }

  .ds-skeleton{
    background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 37%, rgba(255,255,255,0.04) 63%);
    background-size: 400% 100%;
  }

  code{
    background-color: rgba(255,255,255,0.06);
  }
  pre{
    background-color: rgba(255,255,255,0.04);
  }
}
"""


def inject_global_styles() -> None:
    import streamlit as st

    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def title_brand() -> str:
    return """
    <div class="ds-flex" style="gap: 0.75rem;">
      <div style="
        width: 36px; height: 36px;
        border-radius: var(--radius-md);
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: var(--font-weight-bold);
        font-size: var(--font-size-sm); letter-spacing: -0.02em;
        flex-shrink: 0;
      ">EP</div>
      <div>
        <div style="
          font-size: var(--font-size-base);
          line-height: var(--leading-snug);
          font-weight: var(--font-weight-semibold);
          letter-spacing: -0.02em;
          color: var(--text);
        ">EquiPilot AI</div>
        <div style="
          margin-top: 1px;
          font-size: var(--font-size-xs);
          color: var(--muted);
          font-weight: var(--font-weight-normal);
        ">Agentic Equity Research</div>
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
        <div class="ds-section-header">
          <div class="ds-section-header__title">{safe_html_escape(title)}</div>
          <div class="ds-section-header__subtitle">{safe_html_escape(subtitle)}</div>
        </div>
        """
    return f"""
    <div class="ds-section-header">
      <div class="ds-section-header__title">{safe_html_escape(title)}</div>
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
        color = "var(--primary)"
        label = "In Progress"
    else:
        color = "var(--muted)"
        label = status.title() if status else "Status"

    return f"""
    <span class="ds-badge">
      <span style="width:6px;height:6px;border-radius:var(--radius-full);background:{color};display:inline-block;flex-shrink:0;"></span>
      {safe_html_escape(label)}
    </span>
    """


def alert_markdown(message: str, kind: str = "info") -> str:
    color_map = {
        "info": "var(--info)",
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
    color = color_map.get(kind, "var(--info)")
    bg = bg_map.get(kind, "var(--info-bg)")

    return f"""
    <div class="ds-card" style="
      padding: 0.75rem 1rem;
      border-radius: var(--radius-md);
      box-shadow: none;
      border: 1px solid var(--border);
      border-left: 3px solid {color};
      background: {bg};
    ">
      <div style="display:flex; align-items:center; gap: 0.5rem;">
        <div style="font-weight: var(--font-weight-medium); font-size: var(--font-size-sm); line-height: var(--leading-normal);">{safe_html_escape(message)}</div>
      </div>
    </div>
    """


def quick_action_card(icon: str, title: str, description: str, cta: str) -> str:
    """Render a quick action card for empty dashboard."""
    return f"""
    <div style="
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: var(--space-5);
        box-shadow: var(--shadow-xs);
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
        transition: var(--transition-slow);
    ">
        <div style="
          width: 40px; height: 40px;
          border-radius: var(--radius-md);
          background: var(--primary-light);
          display: flex; align-items: center; justify-content: center;
          font-size: 1.25rem;
        ">{icon}</div>
        <div style="font-weight: var(--font-weight-semibold); font-size: var(--font-size-sm); color: var(--text);">{safe_html_escape(title)}</div>
        <div style="font-size: var(--font-size-xs); color: var(--muted); line-height: var(--leading-normal);">{safe_html_escape(description)}</div>
        <div style="font-size: var(--font-size-xs); color: var(--primary); font-weight: var(--font-weight-medium); margin-top: auto;">{safe_html_escape(cta)}</div>
    </div>
    """


def safe_html_escape(text: Any) -> str:
    """
    Escape HTML special characters for safe insertion into unsafe_allow_html templates.
    """
    import html

    s = "" if text is None else str(text)
    return html.escape(s, quote=True)
