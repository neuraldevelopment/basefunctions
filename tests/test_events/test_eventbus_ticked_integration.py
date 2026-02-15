"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Integration tests for EventBus with TickedRateLimiter
 Log:
 v1.0.0 : Initial implementation
 v1.0.1 : Update tests for new burst semantics
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import pytest
import time
import basefunctions
from basefunctions import Event, EventBus, EXECUTION_MODE_THREAD, EventFactory, EventHandler, EventResult


# =============================================================================
# TEST HELPER - SIMPLE HANDLER
# =============================================================================
class SimpleTestHandler(EventHandler):
    """Simple test handler that always succeeds."""

    def handle(self, event, context):
        return EventResult.business_result(event.event_id, True, "OK")


# =============================================================================
# TEST CLASS - API METHODS
# =============================================================================
class TestEventBusTickedRateLimitAPI:
    """Test new API methods for rate limiting."""

    def test_register_rate_limit_basic(self):
        """Test basic rate limit registration."""
        # Arrange
        bus = EventBus()

        # Act
        bus.register_rate_limit("test_event", requests_per_second=10)

        # Assert
        soll, ist = bus.get_rate_limit("test_event")
        assert soll == 10
        assert ist == 0  # No events processed yet

    def test_register_rate_limit_with_burst(self):
        """Test rate limit registration with burst."""
        # Arrange
        bus = EventBus()

        # Act
        bus.register_rate_limit("test_event", requests_per_second=10, burst=100)

        # Assert
        metrics = bus.get_rate_limit_metrics("test_event")
        assert metrics["limit"] == 10
        assert metrics["burst_config"] == 100
        assert metrics["current_tokens"] == 100.0  # Tokens start with burst value

    def test_register_rate_limit_invalid_rps(self):
        """Test rate limit registration with invalid requests_per_second."""
        # Arrange
        bus = EventBus()

        # Act & Assert
        with pytest.raises(ValueError, match="requests_per_second must be > 0"):
            bus.register_rate_limit("test_event", requests_per_second=0)

    def test_register_rate_limit_invalid_burst(self):
        """Test rate limit registration with invalid burst."""
        # Arrange
        bus = EventBus()

        # Act & Assert
        with pytest.raises(ValueError, match="burst must be >= 0"):
            bus.register_rate_limit("test_event", requests_per_second=10, burst=-1)

    def test_get_rate_limit_not_registered(self):
        """Test get_rate_limit for unregistered event_type."""
        # Arrange
        bus = EventBus()

        # Act & Assert
        with pytest.raises(ValueError, match="event_type 'unknown' is not registered"):
            bus.get_rate_limit("unknown")

    def test_get_rate_limit_metrics_not_registered(self):
        """Test get_rate_limit_metrics for unregistered event_type."""
        # Arrange
        bus = EventBus()

        # Act & Assert
        with pytest.raises(ValueError, match="event_type 'unknown' is not registered"):
            bus.get_rate_limit_metrics("unknown")

    def test_get_rate_limit_metrics_complete(self):
        """Test get_rate_limit_metrics returns all expected fields."""
        # Arrange
        bus = EventBus()
        bus.register_rate_limit("test_event", requests_per_second=10, burst=50)

        # Act
        metrics = bus.get_rate_limit_metrics("test_event")

        # Assert
        assert "limit" in metrics
        assert "actual_last_second" in metrics
        assert "burst_config" in metrics
        assert "current_tokens" in metrics
        assert "queued" in metrics
        assert "total_processed" in metrics
        assert "start_time" in metrics
        assert "burst_remaining" not in metrics  # No longer tracked


# =============================================================================
# TEST CLASS - RATE LIMIT ENFORCEMENT
# =============================================================================
class TestEventBusTickedRateLimitEnforcement:
    """Test rate limiting is actually enforced end-to-end."""

    def test_rate_limit_enforcement_basic(self):
        """Test that rate limiting actually slows down events."""
        # Arrange
        event_type = "test_event_enforcement_basic"
        factory = EventFactory()
        factory.register_event_type(event_type, SimpleTestHandler)

        bus = EventBus()
        bus.register_rate_limit(event_type, requests_per_second=5, burst=0)

        # Act - publish 15 events (3 seconds worth at 5/sec)
        start_time = time.time()
        event_ids = []
        for i in range(15):
            event = Event(event_type, event_exec_mode=EXECUTION_MODE_THREAD)
            event_id = bus.publish(event)
            event_ids.append(event_id)

        # Wait for all events to be processed (poll until all results available)
        timeout = 10
        results = {}
        while time.time() - start_time < timeout:
            # Don't consume results during polling
            temp_results = bus.get_results(None, join_before=False)
            matching = {eid: temp_results[eid] for eid in event_ids if eid in temp_results}
            if len(matching) == 15:
                results = matching
                break
            time.sleep(0.1)

        elapsed = time.time() - start_time

        # Assert - should take at least 2 seconds (15 events / 5 per second = 3s, allow tolerance)
        assert elapsed >= 2.0

        # Verify all events processed
        assert len(results) == 15

    def test_rate_limit_with_burst(self):
        """Test burst allows initial events to bypass rate limit."""
        # Arrange
        event_type = "test_event_with_burst"
        factory = EventFactory()
        factory.register_event_type(event_type, SimpleTestHandler)

        bus = EventBus()
        bus.register_rate_limit(event_type, requests_per_second=5, burst=50)

        # Act - publish 50 events (all should use initial burst tokens)
        start_time = time.time()
        event_ids = []
        for i in range(50):
            event = Event(event_type, event_exec_mode=EXECUTION_MODE_THREAD)
            event_id = bus.publish(event)
            event_ids.append(event_id)

        # Wait for all events to be processed
        timeout = 10
        results = {}
        while time.time() - start_time < timeout:
            temp_results = bus.get_results(None, join_before=False)
            matching = {eid: temp_results[eid] for eid in event_ids if eid in temp_results}
            if len(matching) == 50:
                results = matching
                break
            time.sleep(0.1)

        elapsed = time.time() - start_time

        # Assert - burst should be fast (< 2 seconds for 50 events)
        assert elapsed < 2.0
        assert len(results) == 50

        # Verify tokens were consumed (should be near 0 after 50 events from 50 initial tokens)
        metrics = bus.get_rate_limit_metrics(event_type)
        assert metrics["current_tokens"] < 5.0  # Allow some refill during processing

    def test_rate_limit_metrics_update(self):
        """Test that metrics are updated during event processing."""
        # Arrange
        event_type = "test_event_metrics"
        factory = EventFactory()
        factory.register_event_type(event_type, SimpleTestHandler)

        bus = EventBus()
        bus.register_rate_limit(event_type, requests_per_second=10, burst=0)

        # Act - publish 5 events
        event_ids = []
        for i in range(5):
            event = Event(event_type, event_exec_mode=EXECUTION_MODE_THREAD)
            event_id = bus.publish(event)
            event_ids.append(event_id)

        # Wait for all events to be processed
        timeout = 5
        start_time = time.time()
        results = {}
        while time.time() - start_time < timeout:
            temp_results = bus.get_results(None, join_before=False)
            matching = {eid: temp_results[eid] for eid in event_ids if eid in temp_results}
            if len(matching) == 5:
                results = matching
                break
            time.sleep(0.1)

        # Assert
        assert len(results) == 5
        metrics = bus.get_rate_limit_metrics(event_type)
        assert metrics["total_processed"] == 5


# =============================================================================
# TEST CLASS - SHUTDOWN BEHAVIOR
# =============================================================================
# NOTE: Shutdown tests are skipped due to EventBus singleton behavior in tests.
# The shutdown() integration is verified through code inspection:
# - shutdown() calls _ticked_rate_limiter.shutdown(flush=not immediately)
# - This delegates flush/drop behavior to TickedRateLimiter
# - TickedRateLimiter shutdown tests cover the actual behavior
