# Equipilot AI - Streamlit Production Dashboard TODO

## Step 1: Sidebar spec compliance
- [ ] Update `frontend/components/sidebar.py` to include:
  - Company / Ticker input
  - Query input
  - Analysis Type selector (Fundamentals, News, Sentiment, Full Research)
  - Analyze button
- [ ] On submit, store required values in `st.session_state` and trigger backend request via a callback passed from `frontend/app.py`.

## Step 2: Refactor Streamlit layout
- [ ] Refactor `frontend/app.py` to replace tabs with production-style main-page sections:
  - Market Data
  - News Headlines
  - Sentiment Analysis
  - AI Research Report

## Step 3: Execution trace panel
- [ ] Implement an Execution Trace panel that explicitly shows:
  - Detected Intent
  - Resolved Entity
  - Selected Tools
  - Skipped Tools
  - Execution Time
  - Execution Status
  - Errors (if any)

## Step 4: Loading workflow / progress stages
- [ ] Implement a clear loading workflow with progress stages matching backend traces when available:
  - Resolving entity
  - Routing request
  - Fetching market data
  - Fetching news
  - Running sentiment analysis
  - Generating research report

## Step 5: Reuse existing components
- [ ] Reuse existing components:
  - `frontend/components/progress_tracker.py`
  - `frontend/components/report_display.py`
  - (extend sidebar only; no duplicates)

## Step 6: Manual verification
- [ ] Run the Streamlit frontend manually.
- [ ] Verify backend connectivity.
- [ ] Verify loading states and error handling.
- [ ] Verify empty-state placeholders.
- [ ] Verify report sections render.

## Step 7: Final reporting
- [ ] Provide final task status + technical/user explanations + created/modified files + manual testing instructions + remaining TODOs + recommended git commit message.
