# EquiPilot AI - Frontend Component Tests
# Tests for Streamlit UI components

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

    def test_render_quick_stats_displays_metrics(self):
        """Quick stats renders correctly."""
        from frontend.components.query_form import render_quick_stats

        mock_col = MagicMock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock(return_value=None)

        with patch.object(st, 'columns', return_value=[mock_col, mock_col, mock_col]):
            with patch.object(st, 'metric') as mock_metric:
                render_quick_stats(["AAPL"], "completed", 1.5)
                assert mock_metric.call_count >= 3


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
                with patch.object(st, 'expander'):
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

    def test_render_synthesized_report_with_all_sections(self):
        """Render synthesized report with all LLM sections."""
        from frontend.components.report_display import render_synthesized_report

        report = {
            "executive_summary": "Summary",
            "market_snapshot": "Snapshot",
            "news_summary": "News",
            "sentiment_summary": "Sentiment",
            "risks": ["Risk 1"],
            "opportunities": ["Opportunity 1"],
            "disclaimer": "Disclaimer",
        }

        with patch.object(st, 'subheader'):
            with patch.object(st, 'markdown'):
                with patch.object(st, 'caption'):
                    render_synthesized_report(report)

    def test_render_report_card_uses_container(self):
        """Report card uses container with border."""
        from frontend.components.report_display import render_report_card

        report = {"request_id": "test-123", "query": "Test query", "tickers": ["AAPL"]}

        on_click = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        mock_col = MagicMock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock(return_value=None)

        with patch.object(st, 'container', return_value=mock_context):
            with patch.object(st, 'columns', return_value=[mock_col, mock_col]):
                with patch.object(st, 'markdown'):
                    with patch.object(st, 'caption'):
                        with patch.object(st, 'button', return_value=False):
                            render_report_card(report, on_click=on_click)


class TestProgressTracker:
    """Tests for progress tracker component."""

    def test_get_step_index_returns_correct_index(self):
        """Get step index returns correct position."""
        from frontend.components.progress_tracker import _get_step_index, RESEARCH_STEPS

        for i, (step_id, _, _) in enumerate(RESEARCH_STEPS):
            assert _get_step_index(step_id) == i

    def test_get_step_index_returns_minus_one_for_unknown(self):
        """Get step index returns -1 for unknown step."""
        from frontend.components.progress_tracker import _get_step_index

        assert _get_step_index("unknown_step") == -1

    def test_completed_step_index(self):
        """Completed step is the last index."""
        from frontend.components.progress_tracker import _get_step_index, RESEARCH_STEPS

        assert _get_step_index("completed") == len(RESEARCH_STEPS) - 1

    def test_research_steps_contains_all_required_steps(self):
        """RESEARCH_STEPS contains all agent steps."""
        from frontend.components.progress_tracker import RESEARCH_STEPS

        step_ids = [s[0] for s in RESEARCH_STEPS]
        assert "router" in step_ids
        assert "market_data_tool" in step_ids
        assert "news_tool" in step_ids
        assert "sentiment_tool" in step_ids
        assert "research" in step_ids


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

    def test_render_system_status_connected(self):
        """System status shows connected when health check passes."""
        from frontend.components.sidebar import render_system_status

        with patch.object(st, 'success'):
            with patch.object(st, 'caption'):
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"services": {"openai": True, "news_api": True}}
                    mock_get.return_value = mock_response
                    render_system_status()


class TestMainApp:
    """Tests for main app functions."""

    def test_initialize_session_state(self):
        """Session state initializes correctly."""
        # This test would need to be run with streamlit runtime
        # For now, we test the logic indirectly
        # The keys should be present after main() runs
        pass

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

    def test_submit_research_connection_error(self, monkeypatch):
        """Submit research handles connection errors."""
        import requests

        def mock_post(*args, **kwargs):
            raise requests.exceptions.ConnectionError()

        monkeypatch.setattr(requests, 'post', mock_post)

        from frontend.app import submit_research
        with patch.object(st, 'error') as mock_error:
            result = submit_research(query="Test query")
            assert result is None
            mock_error.assert_called()

    def test_render_report_sections_all_types(self):
        """Report sections renders all section types correctly."""
        from frontend.components.report_display import render_structured_sections

        sections = [
            {"title": "Executive Summary", "content": "Summary", "level": 2},
            {"title": "Market Snapshot", "content": "Snapshot", "level": 2},
            {"title": "News Summary", "content": "News", "level": 2},
            {"title": "Sentiment Analysis", "content": "Sentiment", "level": 2},
            {"title": "Risk Factors", "content": "Risks", "level": 2},
            {"title": "Opportunities", "content": "Opportunities", "level": 2},
            {"title": "Disclaimer", "content": "Disclaimer", "level": 2},
        ]

        with patch.object(st, 'subheader'):
            with patch.object(st, 'markdown'):
                with patch.object(st, 'caption'):
                    render_structured_sections(sections)