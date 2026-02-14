"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Test suite for demo_rate_limited_http script
 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import pytest
import sys
from unittest.mock import Mock, patch

# =============================================================================
# PHASE 1: Validation Tests
# =============================================================================


class TestUrlValidation:
    """Tests for URL validation."""

    def test_validate_url_accepts_https(self) -> None:
        """Test valid HTTPS URL is accepted."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_url

        url = "https://httpbin.org/delay/0"

        # ACT
        result = validate_url(url)

        # ASSERT
        assert result == url

    def test_validate_url_accepts_http(self) -> None:
        """Test valid HTTP URL is accepted."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_url

        url = "http://example.com"

        # ACT
        result = validate_url(url)

        # ASSERT
        assert result == url

    def test_validate_url_rejects_invalid_scheme(self) -> None:
        """Test URL without http/https raises ValueError."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_url

        url = "ftp://example.com"

        # ACT & ASSERT
        with pytest.raises(ValueError):
            validate_url(url)

    def test_validate_url_rejects_empty(self) -> None:
        """Test empty URL raises ValueError."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_url

        url = ""

        # ACT & ASSERT
        with pytest.raises(ValueError):
            validate_url(url)


# =============================================================================
# PHASE 2: RPM Validation Tests
# =============================================================================


class TestRpmValidation:
    """Tests for RPM validation."""

    def test_validate_rpm_accepts_valid_range(self) -> None:
        """Test valid RPM in range is accepted."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_rpm

        rpm = 600

        # ACT
        result = validate_rpm(rpm)

        # ASSERT
        assert result == 600

    def test_validate_rpm_rejects_below_minimum(self) -> None:
        """Test RPM below minimum raises ValueError."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_rpm

        rpm = 0

        # ACT & ASSERT
        with pytest.raises(ValueError):
            validate_rpm(rpm)

    def test_validate_rpm_rejects_above_maximum(self) -> None:
        """Test RPM above maximum raises ValueError."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_rpm

        rpm = 20000

        # ACT & ASSERT
        with pytest.raises(ValueError):
            validate_rpm(rpm)

    def test_validate_rpm_accepts_minimum(self) -> None:
        """Test minimum valid RPM is accepted."""
        # ARRANGE
        from demos.demo_rate_limited_http import validate_rpm

        rpm = 1

        # ACT
        result = validate_rpm(rpm)

        # ASSERT
        assert result == 1


# =============================================================================
# PHASE 3: CLI Parser Tests
# =============================================================================


class TestParseArguments:
    """Tests for CLI argument parsing."""

    def test_parse_arguments_with_required_url(self) -> None:
        """Test parsing with required URL argument."""
        # ARRANGE
        from demos.demo_rate_limited_http import parse_arguments

        sys.argv = ["demo.py", "--url", "https://example.com"]

        # ACT
        args = parse_arguments()

        # ASSERT
        assert args["url"] == "https://example.com"

    def test_parse_arguments_uses_default_rpm(self) -> None:
        """Test default RPM is 600."""
        # ARRANGE
        from demos.demo_rate_limited_http import parse_arguments

        sys.argv = ["demo.py", "--url", "https://example.com"]

        # ACT
        args = parse_arguments()

        # ASSERT
        assert args["rpm"] == 600

    def test_parse_arguments_uses_default_duration(self) -> None:
        """Test default duration is 60."""
        # ARRANGE
        from demos.demo_rate_limited_http import parse_arguments

        sys.argv = ["demo.py", "--url", "https://example.com"]

        # ACT
        args = parse_arguments()

        # ASSERT
        assert args["duration"] == 60

    def test_parse_arguments_uses_default_burst(self) -> None:
        """Test default burst is 50."""
        # ARRANGE
        from demos.demo_rate_limited_http import parse_arguments

        sys.argv = ["demo.py", "--url", "https://example.com"]

        # ACT
        args = parse_arguments()

        # ASSERT
        assert args["burst"] == 50

    def test_parse_arguments_with_all_options(self) -> None:
        """Test parsing with all custom options."""
        # ARRANGE
        from demos.demo_rate_limited_http import parse_arguments

        sys.argv = [
            "demo.py",
            "--url", "https://api.example.com",
            "--rpm", "1000",
            "--duration", "30",
            "--burst", "100"
        ]

        # ACT
        args = parse_arguments()

        # ASSERT
        assert args["url"] == "https://api.example.com"
        assert args["rpm"] == 1000
        assert args["duration"] == 30
        assert args["burst"] == 100


# =============================================================================
# PHASE 4: Event Creation Tests
# =============================================================================


class TestCreateEvents:
    """Tests for HTTP event creation."""

    def test_create_events_returns_list(self) -> None:
        """Test create_events returns list of events."""
        # ARRANGE
        from demos.demo_rate_limited_http import create_events

        url = "https://example.com"
        count = 5

        # ACT
        events = create_events(url, count)

        # ASSERT
        assert isinstance(events, list)
        assert len(events) == 5

    def test_create_events_with_valid_url(self) -> None:
        """Test created events contain valid URL."""
        # ARRANGE
        import basefunctions
        from demos.demo_rate_limited_http import create_events

        url = "https://httpbin.org/get"
        count = 3

        # ACT
        events = create_events(url, count)

        # ASSERT
        for event in events:
            assert isinstance(event, basefunctions.Event)
            assert event.event_data["url"] == url

    def test_create_events_zero_count(self) -> None:
        """Test zero count returns empty list."""
        # ARRANGE
        from demos.demo_rate_limited_http import create_events

        url = "https://example.com"
        count = 0

        # ACT
        events = create_events(url, count)

        # ASSERT
        assert len(events) == 0


# =============================================================================
# PHASE 5: Handler Configuration Tests
# =============================================================================


class TestSendEvents:
    """Tests for _send_events helper function."""

    def test_send_events_returns_count_and_timestamps(self) -> None:
        """Test _send_events returns sent count and timestamps list."""
        # ARRANGE
        from demos.demo_rate_limited_http import _send_events, create_events
        from unittest.mock import MagicMock

        handler = MagicMock()
        handler.handle.return_value = MagicMock()

        events = create_events("https://example.com", 5)

        # ACT
        sent_count, timestamps = _send_events(handler, events, batch_size=2, batch_delay=0.01)

        # ASSERT
        assert sent_count == 5
        assert isinstance(timestamps, list)
        assert len(timestamps) == 5

    def test_send_events_handles_batch_size(self) -> None:
        """Test _send_events respects batch size."""
        # ARRANGE
        from demos.demo_rate_limited_http import _send_events, create_events
        from unittest.mock import MagicMock
        import time

        handler = MagicMock()
        handler.handle.return_value = MagicMock()

        events = create_events("https://example.com", 5)

        # ACT
        start = time.time()
        sent_count, _ = _send_events(handler, events, batch_size=2, batch_delay=0.05)
        elapsed = time.time() - start

        # ASSERT
        assert sent_count == 5
        # Two batches (2+2+1) with delay between = ~0.1s
        assert elapsed >= 0.04  # At least one batch delay


class TestWaitForResults:
    """Tests for _wait_for_results helper function."""

    def test_wait_for_results_returns_wait_time(self) -> None:
        """Test _wait_for_results returns elapsed time."""
        # ARRANGE
        from demos.demo_rate_limited_http import _wait_for_results
        from unittest.mock import MagicMock

        handler = MagicMock()
        handler.get_results.return_value = {"event_1": MagicMock(), "event_2": MagicMock()}

        # ACT
        wait_time = _wait_for_results(handler, 2, timeout=5)

        # ASSERT
        assert isinstance(wait_time, float)
        assert wait_time >= 0


class TestExecuteDemo:
    """Tests for demo execution."""

    @patch("demos.demo_rate_limited_http.print_results")
    def test_execute_demo_calls_print_results(self, mock_print: Mock) -> None:
        """Test execute_demo calls print_results."""
        # ARRANGE
        from demos.demo_rate_limited_http import execute_demo

        url = "https://httpbin.org/status/200"
        rpm = 600
        duration = 1  # Short duration for test
        burst = 50

        # ACT
        execute_demo(url, rpm, duration, burst)

        # ASSERT
        assert mock_print.called

    @patch("demos.demo_rate_limited_http.print_results")
    def test_execute_demo_with_valid_params(self, mock_print: Mock) -> None:
        """Test execute_demo accepts valid parameters."""
        # ARRANGE
        from demos.demo_rate_limited_http import execute_demo

        url = "https://httpbin.org/status/200"
        rpm = 300
        duration = 1
        burst = 25

        # ACT & ASSERT - should not raise
        try:
            execute_demo(url, rpm, duration, burst)
            # Verify print_results was called with results dict
            assert mock_print.called
        except Exception:
            pytest.fail("execute_demo raised exception")


# =============================================================================
# PHASE 6: Results Formatting Tests
# =============================================================================


class TestPrintResults:
    """Tests for results formatting."""

    def test_print_results_accepts_dict(self) -> None:
        """Test print_results accepts results dictionary."""
        # ARRANGE
        from demos.demo_rate_limited_http import print_results

        results = {
            "sent": 600,
            "success": 596,
            "failure": 4,
            "total_duration": 60.0,
            "actual_rpm": 9.87,
            "success_rate": 99.3,
            "failure_rate": 0.7,
            "min_time": 0.12,
            "max_time": 2.45,
            "avg_time": 0.68,
        }

        # ACT & ASSERT - should not raise
        try:
            print_results(results)
        except Exception:
            pytest.fail("print_results raised exception")

    def test_print_results_formats_output(self, capsys) -> None:
        """Test print_results produces output."""
        # ARRANGE
        from demos.demo_rate_limited_http import print_results

        results = {
            "sent": 600,
            "success": 596,
            "failure": 4,
            "total_duration": 60.0,
            "actual_rpm": 9.87,
            "success_rate": 99.3,
            "failure_rate": 0.7,
            "min_time": 0.12,
            "max_time": 2.45,
            "avg_time": 0.68,
        }

        # ACT
        print_results(results)

        # ASSERT
        captured = capsys.readouterr()
        assert "RateLimitedHttpHandler" in captured.out
        assert "Results:" in captured.out
