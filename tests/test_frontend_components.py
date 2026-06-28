# EquiPilot AI - Frontend Component Tests
# Tests for Streamlit UI components

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st


class TestQueryForm:
    """Tests for query form component."""

    def test_render_query_form_returns_none_when_not_submitted(self):
        """Form returns None when not submitted."""
        from frontend.components.query_form import render_query_form

        with patch.object(st, 'form') as mock_form:
            mock_form.return_value.__enter__ = Mock(return_value=None)
            mock_form.return_value.__exit__ = Mock(return_value=None)
            with patch.object(st, 'text_area', return_value=""):
                with patch.object(st, 'form_submit_button', return_value=False):
                    result = render_query_form()
                    assert result is None

    def test_render_query_form_validates_empty_query(self):
        """Form shows error for empty query."""
        from frontend.components.query_form import render_query_form

        with patch.object(st, 'form') as mock_form:
            mock_form.return_value.__enter__ = Mock(return_value=None)
            mock_form.return_value.__exit__ = Mock(return_value=None)
            with patch.object(st, 'text_area', return_value=""):
                with patch.object(st, 'form_submit_button', return_value=True):
                    with patch.object(st, 'error') as mock_error:
                        result = render_query_form()
                        assert result is None
                        mock_error.assert_called()

    def test_render_query_form_parses_tickers_correctly(self):
        """Form parses comma-separated tickers correctly."""
        from frontend.components.query_form import render_query_form

        with patch.object(st, 'form') as mock_form:
            mock_form.return_value.__enter__ = Mock(return_value=None)
            mock_form.return_value.__exit__ = Mock(return_value=None)
            with patch.object(st, 'text_area', return_value="Analyze AAPL"):
                with patch.object(st, 'text_input', return_value="AAPL, MSFT"):
                    with patch.object(st, 'form_submit_button', return_value=True):
                        with patch.object(st, 'checkbox', return_value=True):
                            with patch.object(st, 'expander'):
                                with patch.object(st, 'slider', return_value=5000):
                                    result = render_query_form()
                                    assert result is not None
                                    assert result['tickers'] == ['AAPL', 'MSFT']

    def test_render_query_form_normalizes_ticker_case(self):
        """Form normalizes ticker symbols to uppercase."""
        from frontend.components.query_form import render_query_form

        with patch.object(st, 'form') as mock_form:
            mock_form.return_value.__enter__ = Mock(return_value=None)
            mock_form.return_value.__exit__ = Mock(return_value=None)
            with patch.object(st, 'text_area', return_value="Analyze Apple"):
                with patch.object(st, 'text_input', return_value="aapl, msft"):
                    with patch.object(st, 'form_submit_button', return_value=True):
                        with patch.object(st, 'checkbox', return_value=True):
                            with patch.object(st, 'expander'):
                                with patch.object(st, 'slider', return_value=5000):
                                    result = render_query_form()
                                    assert result is not None
                                    assert result['tickers'] == ['AAPL', 'MSFT']


class TestReportDisplay:
    """Tests for report display component."""

    def test_render_report_handles_none_input(self):
        """Report display handles None gracefully."""
        from frontend.components.report_display import render_report

        with patch.object(st, 'warning') as mock_warning:
            render_report(None)
            mock_warning.assert_called_with("No report data available")

    def test_render_report_shows_metadata(self):
        """Report display shows request metadata."""
        from frontend.components.report_display import render_report

        report = {
            "request_id": "test-123",
            "tickers": ["AAPL"],
            "created_at": "2024-01-01T12:00:00",
        }

        with patch.object(st, 'success'):
            with patch.object(st, 'metric') as mock_metric:
                render_report(report, show_metadata=True)
                assert mock_metric.call_count >= 3

    def test_render_report_shows_markdown_content(self):
        """Report display shows markdown report content."""
        from frontend.components.report_display import render_report

        report = {
            "request_id": "test-123",
            "report": "# Test Report\n\nThis is test content.",
        }

        with patch.object(st, 'success'):
            with patch.object(st, 'markdown') as mock_markdown:
                render_report(report)
                mock_markdown.assert_called()

    def test_render_report_shows_structured_sections(self):
        """Report display shows structured sections."""
        from frontend.components.report_display import render_report

        report = {
            "request_id": "test-123",
            "sections": [
                {"title": "Executive Summary", "content": "Summary content", "level": 2},
                {"title": "Risks", "content": "Risk content", "level": 2},
            ],
        }

        with patch.object(st, 'success'):
            with patch.object(st, 'expander'):
                with patch.object(st, 'subheader'):
                    with patch.object(st, 'markdown'):
                        render_report(report, show_metadata=False)


class TestProgressTracker:
    """Tests for progress tracker component."""

    def test_render_progress_shows_in_progress_status(self):
        """Progress tracker shows in_progress status correctly."""
        # Test the step index function and status colors
        from frontend.components.progress_tracker import _get_step_index, RESEARCH_STEPS

        for i, (step_id, step_name, icon) in enumerate(RESEARCH_STEPS):
            assert _get_step_index(step_id) == i

    def test_render_progress_shows_completed_status(self):
        """Progress tracker shows completed status correctly."""
        from frontend.components.progress_tracker import _get_step_index, RESEARCH_STEPS

        assert _get_step_index("completed") == len(RESEARCH_STEPS) - 1

    def test_get_step_index_returns_correct_index(self):
        """Get step index returns correct position."""
        from frontend.components.progress_tracker import _get_step_index, RESEARCH_STEPS

        for i, (step_id, _, _) in enumerate(RESEARCH_STEPS):
            assert _get_step_index(step_id) == i

    def test_get_step_index_returns_minus_one_for_unknown(self):
        """Get step index returns -1 for unknown step."""
        from frontend.components.progress_tracker import _get_step_index

        assert _get_step_index("unknown_step") == -1


class TestSidebar:
    """Tests for sidebar component."""

    def test_render_sidebar_shows_navigation(self):
        """Sidebar renders navigation header."""
        from frontend.components.sidebar import render_sidebar

        with patch.object(st, 'header'):
            with patch.object(st, 'subheader'):
                with patch.object(st, 'caption'):
                    with patch.object(st, 'divider'):
                        with patch.object(st, 'error'):
                            render_sidebar()

    def test_render_recent_reports_empty_state(self):
        """Recent reports shows empty state correctly."""
        from frontend.components.sidebar import render_recent_reports

        with patch.object(st, 'session_state', {"research_history": []}):
            with patch.object(st, 'caption') as mock_caption:
                render_recent_reports()
                mock_caption.assert_called_with("No recent reports")


class TestExecutionTrace:
    """Tests for execution trace display in app.py."""

    def test_render_execution_timeline_no_traces(self):
        """Timeline handles missing traces gracefully."""
        from frontend.app import render_execution_timeline

        report = {}

        with patch.object(st, 'subheader'):
            with patch.object(st, 'columns'):
                with patch.object(st, 'markdown'):
                    render_execution_timeline(report)

    def test_render_execution_timeline_with_traces(self):
        """Timeline displays traces correctly."""
        from frontend.app import render_execution_timeline

        report = {
            "execution_metadata": {
                "traces": [
                    {"step": "router", "duration_ms": 100.5, "status": "completed", "timestamp": "2024-01-01T12:00:00"},
                    {"step": "market_data", "duration_ms": 2500.0, "status": "completed", "timestamp": "2024-01-01T12:00:01"},
                ]
            }
        }

        with patch.object(st, 'subheader'):
            with patch.object(st, 'columns'):
                with patch.object(st, 'expander') as mock_expander:
                    render_execution_timeline(report)

    def test_render_structured_sections_all_types(self):
        """Structured sections renders all section types correctly."""
        from frontend.app import render_structured_sections

        sections = [
            {"title": "Executive Summary", "content": "Summary", "level": 2},
            {"title": "Market Snapshot", "content": "Snapshot", "level": 2},
            {"title": "News Summary", "content": "News", "level": 2},
            {"title": "Sentiment Summary", "content": "Sentiment", "level": 2},
            {"title": "Risks", "content": "Risks", "level": 2},
            {"title": "Opportunities", "content": "Opportunities", "level": 2},
            {"title": "Disclaimer", "content": "Disclaimer", "level": 2},
        ]

        with patch.object(st, 'subheader'):
            with patch.object(st, 'markdown'):
                with patch.object(st, 'caption'):
                    render_structured_sections(sections)


class TestBackendIntegration:
    """Tests for backend API integration."""

    def test_check_status_success(self, monkeypatch):
        """Check status handles successful API response."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed", "report": {}}

        def mock_get(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(requests, 'get', mock_get)

        from frontend.app import check_status
        result = check_status("test-id")
        assert result["status"] == "completed"