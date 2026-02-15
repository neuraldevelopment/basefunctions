"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for TickedRateLimiter - TDD implementation
 Log:
 v1.0.0 : Initial implementation
 v1.0.1 : Update tests for new burst semantics
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import queue
import time
import pytest
from basefunctions.events.event import Event
from basefunctions.events.ticked_rate_limiter import (
    RateLimitConfig,
    RateLimitMetrics,
    TickedRateLimiter,
)


# =============================================================================
# TEST CLASS DEFINITIONS
# =============================================================================
class TestTickedRateLimiterBasics:
    """Test basic registration and validation."""

    def test_rate_limit_config_creation_success(self):
        """Test RateLimitConfig dataclass creation with valid parameters."""
        # Arrange & Act
        config = RateLimitConfig(
            event_type="test_event",
            requests_per_second=10,
            burst=5,
            max_tokens=600
        )

        # Assert
        assert config.event_type == "test_event"
        assert config.requests_per_second == 10
        assert config.burst == 5
        assert config.max_tokens == 600

    def test_rate_limit_metrics_creation_success(self):
        """Test RateLimitMetrics dataclass creation with valid parameters."""
        # Arrange & Act
        metrics = RateLimitMetrics(
            limit=10,
            actual_last_second=8,
            burst_config=5,
            current_tokens=15.5,
            queued=2,
            total_processed=100,
            start_time=1234567890.0
        )

        # Assert
        assert metrics.limit == 10
        assert metrics.actual_last_second == 8
        assert metrics.burst_config == 5
        assert metrics.current_tokens == 15.5
        assert metrics.queued == 2
        assert metrics.total_processed == 100
        assert metrics.start_time == 1234567890.0

    def test_ticked_rate_limiter_init_success(self):
        """Test TickedRateLimiter initialization with valid queue."""
        # Arrange
        target_queue = queue.PriorityQueue()

        # Act
        limiter = TickedRateLimiter(target_input_queue=target_queue)

        # Assert
        assert limiter is not None
        assert limiter.has_limit("any_event") is False

    def test_register_valid_parameters_success(self):
        """Test register with valid parameters."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)

        # Act
        limiter.register(event_type="test_event", requests_per_second=10, burst=5)

        # Assert
        assert limiter.has_limit("test_event") is True

    def test_register_invalid_requests_per_second_fails(self):
        """Test register with requests_per_second <= 0 raises ValueError."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)

        # Act & Assert
        with pytest.raises(ValueError, match="requests_per_second must be > 0"):
            limiter.register(event_type="test_event", requests_per_second=0, burst=5)

    def test_register_invalid_burst_fails(self):
        """Test register with burst < 0 raises ValueError."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)

        # Act & Assert
        with pytest.raises(ValueError, match="burst must be >= 0"):
            limiter.register(event_type="test_event", requests_per_second=10, burst=-1)

    def test_submit_registered_event_type_success(self):
        """Test submit with registered event_type."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=10, burst=5)
        event = Event(event_type="test_event")

        # Act
        limiter.submit(event_type="test_event", priority=5, counter=1, event=event)

        # Assert - no exception raised

    def test_submit_unregistered_event_type_fails(self):
        """Test submit with unregistered event_type raises ValueError."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        event = Event(event_type="test_event")

        # Act & Assert
        with pytest.raises(ValueError, match="event_type 'test_event' is not registered"):
            limiter.submit(event_type="test_event", priority=5, counter=1, event=event)

    def test_get_limit_registered_event_type_success(self):
        """Test get_limit with registered event_type."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=10, burst=5)

        # Act
        soll, ist = limiter.get_limit(event_type="test_event")

        # Assert
        assert soll == 10
        assert ist == 0

    def test_get_limit_unregistered_event_type_fails(self):
        """Test get_limit with unregistered event_type raises ValueError."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)

        # Act & Assert
        with pytest.raises(ValueError, match="event_type 'test_event' is not registered"):
            limiter.get_limit(event_type="test_event")


class TestTickedRateLimiterMetrics:
    """Test metrics tracking."""

    def test_get_metrics_registered_event_type_success(self):
        """Test get_metrics with registered event_type."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=10, burst=5)

        # Act
        metrics = limiter.get_metrics(event_type="test_event")

        # Assert
        assert metrics["limit"] == 10
        assert metrics["actual_last_second"] == 0
        assert metrics["burst_config"] == 5
        assert metrics["current_tokens"] == 5.0  # Tokens start with burst value
        assert metrics["queued"] == 0
        assert metrics["total_processed"] == 0
        assert "start_time" in metrics
        assert "burst_remaining" not in metrics  # No longer tracked

    def test_get_metrics_unregistered_event_type_fails(self):
        """Test get_metrics with unregistered event_type raises ValueError."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)

        # Act & Assert
        with pytest.raises(ValueError, match="event_type 'test_event' is not registered"):
            limiter.get_metrics(event_type="test_event")


class TestTickedRateLimiterShutdown:
    """Test shutdown behavior."""

    def test_shutdown_with_flush_success(self):
        """Test shutdown with flush=True."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=10, burst=5)

        # Act
        limiter.shutdown(flush=True)

        # Assert - no exception raised

    def test_shutdown_with_drop_success(self):
        """Test shutdown with flush=False."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=10, burst=5)

        # Act
        limiter.shutdown(flush=False)

        # Assert - no exception raised


class TestTickedRateLimiterBurstPhase:
    """Test burst phase behavior."""

    def test_burst_phase_bypasses_rate_limiting(self):
        """Test that burst events are forwarded immediately from initial token budget."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=2, burst=3)

        # Act - Submit 3 burst events
        for i in range(3):
            event = Event(event_type="test_event")
            limiter.submit(event_type="test_event", priority=5, counter=i, event=event)

        # Wait briefly for worker to process
        time.sleep(0.5)

        # Assert - All 3 should be in target queue (consumed from initial tokens)
        assert target_queue.qsize() == 3

        # Verify burst_remaining is no longer tracked in metrics
        metrics = limiter.get_metrics(event_type="test_event")
        assert "burst_remaining" not in metrics

    def test_post_burst_enforces_rate_limiting(self):
        """Test that events after burst are rate limited correctly."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=1, burst=2)

        # Act - Submit 4 events (burst gives us 2 initial tokens)
        for i in range(4):
            event = Event(event_type="test_event")
            limiter.submit(event_type="test_event", priority=5, counter=i, event=event)

        # Wait for initial tokens to process
        time.sleep(0.5)

        # Assert - Initial 2 tokens consumed immediately
        assert target_queue.qsize() == 2

        # Wait 2 more seconds for rate-limited refill (1 per second = 2 more)
        time.sleep(2.5)

        # Now should have all 4 processed
        assert target_queue.qsize() == 4


class TestTickedRateLimiterTokenPhase:
    """Test token bucket enforcement."""

    def test_token_bucket_limits_rate(self):
        """Test that token bucket enforces rate limit."""
        # Arrange
        target_queue = queue.PriorityQueue()
        limiter = TickedRateLimiter(target_input_queue=target_queue)
        limiter.register(event_type="test_event", requests_per_second=2, burst=0)

        # Act - Submit 5 events
        for i in range(5):
            event = Event(event_type="test_event")
            limiter.submit(event_type="test_event", priority=5, counter=i, event=event)

        # Wait 2 seconds (should process ~4 events at 2/sec)
        time.sleep(2.5)

        # Assert - Should have processed approximately 4-5 events
        processed = target_queue.qsize()
        assert 4 <= processed <= 5

        # Cleanup
        limiter.shutdown(flush=True)
