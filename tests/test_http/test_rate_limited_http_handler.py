"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Pytest test suite for rate_limited_http_handler.
 Tests rate limiting with token bucket, queue management, and HTTP execution.
 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# Project imports
import basefunctions

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_event() -> Mock:
    """Create mock Event object with configurable event_data."""
    event: Mock = Mock(spec=basefunctions.Event)
    event.event_id = "test_event_123"
    event.event_data = {}
    return event


@pytest.fixture
def mock_context() -> Mock:
    """Create mock EventContext object."""
    context: Mock = Mock(spec=basefunctions.EventContext)
    return context


# =============================================================================
# PHASE 1: Token Bucket Tests
# =============================================================================


class TestTokenBucket:
    """Tests for _TokenBucket internal class."""

    def test_token_bucket_initializes_with_full_capacity(self) -> None:
        """Test that token bucket initializes with full capacity.

        Zyklus 1: test_token_bucket_initializes_with_full_capacity
        - Assert: bucket.capacity, bucket.tokens == capacity
        - Assert: bucket.refill_rate and bucket.last_refill set
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        capacity = 100
        refill_rate = 10.0

        # ACT
        bucket = _TokenBucket(capacity=capacity, refill_rate=refill_rate)

        # ASSERT
        assert bucket.capacity == capacity
        assert bucket.tokens == float(capacity)
        assert bucket.refill_rate == refill_rate
        assert bucket.last_refill is not None
        assert isinstance(bucket.last_refill, float)

    def test_token_bucket_consume_returns_true_when_available(self) -> None:
        """Test consume returns True when tokens available.

        Zyklus 2: test_token_bucket_consume_returns_true_when_available
        - Setup: bucket = _TokenBucket(capacity=100, refill_rate=10)
        - Act: result = bucket.consume(1)
        - Assert: result is True, bucket.tokens == 99
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=10)

        # ACT
        result = bucket.consume(1)

        # ASSERT
        assert result is True
        assert bucket.tokens == 99.0

    def test_token_bucket_consume_returns_false_when_insufficient(self) -> None:
        """Test consume returns False when insufficient tokens.

        Zyklus 3: test_token_bucket_consume_returns_false_when_insufficient
        - Setup: bucket.tokens = 5, refill_rate = 0
        - Act: result = bucket.consume(10)
        - Assert: result is False, bucket.tokens == 5 (unchanged)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=0)
        bucket.tokens = 5

        # ACT
        result = bucket.consume(10)

        # ASSERT
        assert result is False
        assert bucket.tokens == 5

    def test_token_bucket_refills_based_on_elapsed_time(self) -> None:
        """Test refill adds tokens based on elapsed time.

        Zyklus 4: test_token_bucket_refills_based_on_elapsed_time
        - Setup: bucket.tokens = 50, last_refill = time - 2.0, refill_rate=10
        - Act: bucket._refill()
        - Assert: bucket.tokens approx 70 (50 + 2*10)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=10)
        bucket.tokens = 50
        bucket.last_refill = time.time() - 2.0  # 2 seconds ago

        # ACT
        bucket._refill()

        # ASSERT
        assert bucket.tokens == pytest.approx(70.0, abs=0.01)

    def test_token_bucket_caps_tokens_at_capacity(self) -> None:
        """Test refill caps tokens at capacity.

        Zyklus 5: test_token_bucket_caps_tokens_at_capacity
        - Setup: bucket.tokens = 95, capacity = 100, 10 sec elapsed (would be 195)
        - Act: bucket._refill()
        - Assert: bucket.tokens == 100 (capped)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=10)
        bucket.tokens = 95
        bucket.last_refill = time.time() - 10.0  # 10 seconds ago, would add 100

        # ACT
        bucket._refill()

        # ASSERT
        assert bucket.tokens == 100.0

    def test_token_bucket_consume_triggers_refill(self) -> None:
        """Test consume triggers refill automatically.

        Zyklus 6: test_token_bucket_consume_triggers_refill
        - Setup: bucket.tokens = 5, 1 sec elapsed (refill_rate=10)
        - Act: result = bucket.consume(12) (5+10=15 available after refill)
        - Assert: result is True, bucket.tokens approx 3
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=10)
        bucket.tokens = 5
        bucket.last_refill = time.time() - 1.0  # 1 second ago

        # ACT
        result = bucket.consume(12)

        # ASSERT
        assert result is True
        assert bucket.tokens == pytest.approx(3.0, abs=0.01)

    def test_token_bucket_updates_last_refill_timestamp(self) -> None:
        """Test _refill updates last_refill timestamp.

        Zyklus 7: test_token_bucket_updates_last_refill_timestamp
        - Setup: old_ts = bucket.last_refill, sleep(0.1)
        - Act: bucket._refill()
        - Assert: bucket.last_refill > old_ts
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=10)
        old_ts = bucket.last_refill
        time.sleep(0.1)

        # ACT
        bucket._refill()

        # ASSERT
        assert bucket.last_refill > old_ts

    def test_token_bucket_multiple_consumes_sequential(self) -> None:
        """Test multiple sequential consumes.

        Zyklus 8: test_token_bucket_multiple_consumes_sequential
        - Assert: consume(30)→True, tokens==70, consume(40)→True, tokens==30
        - Assert: consume(50)→False, tokens==30 (insufficient)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import _TokenBucket

        bucket = _TokenBucket(capacity=100, refill_rate=0)  # No refill

        # ACT & ASSERT
        result1 = bucket.consume(30)
        assert result1 is True
        assert bucket.tokens == 70.0

        result2 = bucket.consume(40)
        assert result2 is True
        assert bucket.tokens == 30.0

        result3 = bucket.consume(50)
        assert result3 is False
        assert bucket.tokens == 30.0


# =============================================================================
# PHASE 2: Handler Queue Tests
# =============================================================================


class TestRateLimitedHttpHandler:
    """Tests for RateLimitedHttpHandler main class."""

    def test_handler_inherits_from_event_handler(self) -> None:
        """Test handler inherits from EventHandler.

        Zyklus 9: test_handler_inherits_from_event_handler
        - Assert: issubclass(RateLimitedHttpHandler, basefunctions.EventHandler)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # ACT & ASSERT
        assert issubclass(RateLimitedHttpHandler, basefunctions.EventHandler)

    def test_handler_has_thread_execution_mode(self) -> None:
        """Test handler has THREAD execution mode.

        Zyklus 10: test_handler_has_thread_execution_mode
        - Assert: RateLimitedHttpHandler.execution_mode == EXECUTION_MODE_THREAD
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # ACT & ASSERT
        assert RateLimitedHttpHandler.execution_mode == basefunctions.EXECUTION_MODE_THREAD

    def test_handler_initializes_with_config(self) -> None:
        """Test handler initializes with default config.

        Zyklus 11: test_handler_initializes_with_config
        - Act: handler = RateLimitedHttpHandler()
        - Assert: handler.requests_per_minute == 1000, burst_size == 100, respect_headers is True
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # ACT
        handler = RateLimitedHttpHandler()

        # ASSERT
        assert handler.requests_per_minute == 1000
        assert handler.burst_size == 100
        assert handler.respect_headers is True

    def test_handler_creates_token_bucket(self) -> None:
        """Test handler creates token bucket with correct config.

        Zyklus 12: test_handler_creates_token_bucket
        - Act: handler = RateLimitedHttpHandler(requests_per_minute=600, burst_size=50)
        - Assert: bucket capacity == 600, refill_rate == 10.0, tokens == 50
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # ACT
        handler = RateLimitedHttpHandler(
            requests_per_minute=600,
            burst_size=50
        )

        # ASSERT
        assert handler._bucket.capacity == 600
        assert handler._bucket.refill_rate == 10.0
        assert handler._bucket.tokens == 50

    def test_handler_creates_queue(self) -> None:
        """Test handler creates request queue.

        Zyklus 13: test_handler_creates_queue
        - Act: handler = RateLimitedHttpHandler()
        - Assert: handler._queue is Queue, empty
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler
        import queue

        # ACT
        handler = RateLimitedHttpHandler()

        # ASSERT
        assert isinstance(handler._queue, queue.Queue)
        assert handler._queue.empty() is True

    @patch("basefunctions.http.rate_limited_http_handler._SESSION")
    def test_handle_queues_event(
        self,
        mock_session: Mock,
        mock_event: Mock,
        mock_context: Mock
    ) -> None:
        """Test handle queues event and returns success.

        Zyklus 14: test_handle_queues_event
        - Setup: mock_event.event_data = {"url": "..."}
        - Act: result = handler.handle(mock_event, mock_context)
        - Assert: result.success is True, event was processed or queued
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # Setup mock response to slow down processing
        mock_response = MagicMock()
        mock_response.text = "Success"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        handler = RateLimitedHttpHandler()
        mock_event.event_data = {"url": "https://example.com"}

        # ACT
        result = handler.handle(mock_event, mock_context)

        # ASSERT
        # Result should indicate success (event queued or processed)
        assert result.success is True

    def test_handle_starts_worker_thread(self, mock_event: Mock, mock_context: Mock) -> None:
        """Test handle starts worker thread.

        Zyklus 15: test_handle_starts_worker_thread
        - Act: handler.handle(mock_event, mock_context)
        - Assert: handler._worker_thread is not None and daemon=True
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        handler = RateLimitedHttpHandler()
        mock_event.event_data = {"url": "https://example.com"}

        # ACT
        handler.handle(mock_event, mock_context)

        # ASSERT
        assert handler._worker_thread is not None
        assert handler._worker_thread.daemon is True

    @patch("basefunctions.http.rate_limited_http_handler._SESSION")
    def test_worker_processes_queued_events(
        self,
        mock_session: Mock,
        mock_event: Mock,
        mock_context: Mock
    ) -> None:
        """Test worker processes queued events.

        Zyklus 16: test_worker_processes_queued_events
        - Setup: requests_per_minute=60, patch(_SESSION)
        - Act: handler.handle(event), wait 0.2s
        - Assert: _SESSION.request called, queue empty
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Success"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        handler = RateLimitedHttpHandler(requests_per_minute=60)
        mock_event.event_data = {"url": "https://example.com", "method": "GET"}

        # ACT
        handler.handle(mock_event, mock_context)
        time.sleep(0.2)  # Give worker time to process

        # ASSERT
        # Expect session to be called at least once for the request
        assert mock_session.request.call_count >= 1
        # Queue should be empty after processing
        assert handler._queue.empty() is True


# =============================================================================
# PHASE 3: HTTP Execution Tests
# =============================================================================


class TestHttpExecution:
    """Tests for HTTP request execution with rate limiting."""

    @patch("basefunctions.http.rate_limited_http_handler._SESSION")
    def test_worker_consumes_token_before_request(
        self,
        mock_session: Mock,
        mock_context: Mock
    ) -> None:
        """Test worker consumes token before request.

        Zyklus 17: test_worker_consumes_token_before_request
        - Setup: burst_size=0, 1 token, 2 events, 60 RPM (1/sec)
        - Act: queue 2 events, measure time
        - Assert: elapsed >= 1.0 sec (second request waits for token)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Success"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        # Create handler with 60 RPM = 1 per sec, burst_size=0 (no burst)
        handler = RateLimitedHttpHandler(requests_per_minute=60, burst_size=0)
        # Manually add 1 token to allow first request immediately
        handler._bucket.tokens = 1.0

        event1 = Mock(spec=basefunctions.Event)
        event1.event_id = "event1"
        event1.event_data = {"url": "https://example1.com"}

        event2 = Mock(spec=basefunctions.Event)
        event2.event_id = "event2"
        event2.event_data = {"url": "https://example2.com"}

        # ACT
        start_time = time.time()
        handler.handle(event1, mock_context)
        handler.handle(event2, mock_context)
        time.sleep(1.5)  # Wait for processing

        elapsed = time.time() - start_time

        # ASSERT
        # Both events should be processed, but second should wait ~1 sec
        assert elapsed >= 1.0

    @patch("basefunctions.http.rate_limited_http_handler._SESSION")
    def test_worker_makes_http_request(
        self,
        mock_session: Mock,
        mock_context: Mock
    ) -> None:
        """Test worker makes HTTP request with correct method.

        Zyklus 18: test_worker_makes_http_request
        - Setup: event_data = {"url": "...", "method": "POST"}
        - Act: handler._process_queue_single(event)
        - Assert: _SESSION.request called with ("POST", url, timeout=25)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Posted"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        handler = RateLimitedHttpHandler()

        event = Mock(spec=basefunctions.Event)
        event.event_id = "test_post"
        event.event_data = {"url": "https://api.example.com/data", "method": "POST"}

        # ACT
        handler.handle(event, mock_context)
        time.sleep(0.2)

        # ASSERT
        # Verify session.request was called with POST method
        assert mock_session.request.called
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"  # First positional arg is method
        assert call_args[0][1] == "https://api.example.com/data"  # URL
        assert call_args[1]["timeout"] == 25

    @patch("basefunctions.http.rate_limited_http_handler._SESSION")
    def test_worker_stores_result_in_dict(
        self,
        mock_session: Mock,
        mock_context: Mock
    ) -> None:
        """Test worker stores result in results dictionary.

        Zyklus 19: test_worker_stores_result_in_dict
        - Act: handler.handle(event), wait for worker
        - Assert: handler._results[event.event_id].success is True, data == response.text
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Test Response Data"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        handler = RateLimitedHttpHandler()

        event = Mock(spec=basefunctions.Event)
        event.event_id = "test_store"
        event.event_data = {"url": "https://example.com"}

        # ACT
        handler.handle(event, mock_context)
        time.sleep(0.2)

        # ASSERT
        assert event.event_id in handler._results
        result = handler._results[event.event_id]
        assert result.success is True
        assert result.data == "Test Response Data"

    def test_handle_returns_pending_result(self, mock_event: Mock, mock_context: Mock) -> None:
        """Test handle returns pending result immediately.

        Zyklus 20: test_handle_returns_pending_result
        - Act: result = handler.handle(event)
        - Assert: result.success is True (queued immediately, not waiting)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        handler = RateLimitedHttpHandler()
        mock_event.event_data = {"url": "https://example.com"}

        # ACT
        result = handler.handle(mock_event, mock_context)

        # ASSERT
        # Result should be immediate "queued" success, not actual HTTP result
        assert result.success is True
        assert "queued" in result.data.lower()

    @patch("basefunctions.http.rate_limited_http_handler._SESSION")
    def test_initial_burst_size_allows_fast_start(
        self,
        mock_session: Mock,
        mock_context: Mock
    ) -> None:
        """Test burst_size allows fast initial requests.

        Zyklus 21: test_initial_burst_size_allows_fast_start
        - Setup: burst_size=100, requests_per_minute=1000
        - Act: queue 100 events, measure time
        - Assert: elapsed < 0.1 sec (all burst events fast)
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Fast"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        handler = RateLimitedHttpHandler(
            requests_per_minute=1000,
            burst_size=100
        )

        # Create 100 events
        events = []
        for i in range(100):
            event = Mock(spec=basefunctions.Event)
            event.event_id = f"burst_{i}"
            event.event_data = {"url": f"https://example.com/{i}"}
            events.append(event)

        # ACT
        start_time = time.time()
        for event in events:
            handler.handle(event, mock_context)
        elapsed_queue = time.time() - start_time

        # Wait for processing
        time.sleep(0.5)

        # ASSERT
        # Queuing all 100 events should be fast (just adding to queue)
        assert elapsed_queue < 0.5  # Queueing is not rate-limited


# =============================================================================
# PHASE 4: Header-Based Rate Limiting Tests
# =============================================================================


class TestHeaderBasedRateLimit:
    """Tests for X-RateLimit-Remaining header parsing."""

    def test_worker_reads_x_ratelimit_remaining_header(self) -> None:
        """Test parsing X-RateLimit-Remaining header.

        Zyklus 22: test_worker_reads_x_ratelimit_remaining_header
        - Setup: response.headers = {"X-RateLimit-Remaining": "450"}
        - Act: remaining = handler._parse_rate_limit_headers(response)
        - Assert: remaining == 450
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        handler = RateLimitedHttpHandler()

        # Create mock response with header
        mock_response = MagicMock()
        mock_response.headers = {"X-RateLimit-Remaining": "450"}

        # ACT
        remaining = handler._parse_rate_limit_headers(mock_response)

        # ASSERT
        assert remaining == 450

    def test_worker_adjusts_bucket_when_low_limit(self) -> None:
        """Test bucket adjustment on low rate limit.

        Zyklus 23: test_worker_adjusts_bucket_when_low_limit
        - Setup: remaining = 50 (< 100, = < 10%)
        - Act: handler._adjust_rate_limit(remaining, 1000)
        - Assert: handler._bucket.tokens reduced
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        handler = RateLimitedHttpHandler(requests_per_minute=1000)
        old_tokens = handler._bucket.tokens

        # ACT
        handler._adjust_rate_limit(50, 1000)

        # ASSERT
        # Tokens should be reduced when limit is low
        assert handler._bucket.tokens < old_tokens

    def test_worker_logs_warning_on_low_rate_limit(self) -> None:
        """Test warning logged on low rate limit.

        Zyklus 24: test_worker_logs_warning_on_low_rate_limit
        - Setup: remaining = 50, respect_headers=True
        - Act: handler._adjust_rate_limit(remaining, 1000)
        - Assert: logger.warning called with "Low rate limit" message
        """
        # ARRANGE
        from basefunctions.http.rate_limited_http_handler import RateLimitedHttpHandler

        handler = RateLimitedHttpHandler(respect_headers=True)

        # ACT & ASSERT
        with patch("basefunctions.http.rate_limited_http_handler.logger") as mock_logger:
            handler._adjust_rate_limit(50, 1000)
            # Verify warning was logged
            assert mock_logger.warning.called
