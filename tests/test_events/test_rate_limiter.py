"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Test suite for RateLimiter with sliding window algorithm
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import time
import threading
import pytest
from basefunctions.events.rate_limiter import RateLimiter

# =============================================================================
# TEST CLASS - BASICS
# =============================================================================


class TestRateLimiterBasics:
    """Test basic RateLimiter functionality."""

    def test_register_rate_limit_stores_limit(self):
        """Test that register() stores the rate limit correctly."""
        # Arrange
        limiter = RateLimiter()
        event_type = "test_event"
        requests_per_minute = 10

        # Act
        limiter.register(event_type, requests_per_minute)

        # Assert
        assert limiter.has_limit(event_type) is True

    def test_has_limit_returns_false_for_unregistered_event(self):
        """Test that has_limit() returns False for unregistered event types."""
        # Arrange
        limiter = RateLimiter()

        # Act & Assert
        assert limiter.has_limit("unknown_event") is False

    def test_try_acquire_allows_request_within_limit(self):
        """Test that try_acquire() allows requests within the rate limit."""
        # Arrange
        limiter = RateLimiter()
        event_type = "test_event"
        limiter.register(event_type, requests_per_minute=10)

        # Act
        result = limiter.try_acquire(event_type)

        # Assert
        assert result is True

    def test_try_acquire_rejects_request_exceeding_limit(self):
        """Test that try_acquire() rejects requests exceeding the rate limit."""
        # Arrange
        limiter = RateLimiter()
        event_type = "test_event"
        limiter.register(event_type, requests_per_minute=2)

        # Act - Fill up the limit
        limiter.try_acquire(event_type)
        limiter.try_acquire(event_type)
        result = limiter.try_acquire(event_type)

        # Assert
        assert result is False

    def test_try_acquire_allows_request_after_window_reset(self):
        """Test that try_acquire() allows requests after window resets."""
        # Arrange
        limiter = RateLimiter()
        event_type = "test_event"
        limiter.register(event_type, requests_per_minute=2)

        # Act - Fill up the limit
        limiter.try_acquire(event_type)
        limiter.try_acquire(event_type)
        assert limiter.try_acquire(event_type) is False

        # Wait for window to reset (60+ seconds)
        time.sleep(61)

        # Act - Try again after window reset
        result = limiter.try_acquire(event_type)

        # Assert
        assert result is True

    def test_try_acquire_returns_true_for_unregistered_event(self):
        """Test that try_acquire() returns True for events without rate limit."""
        # Arrange
        limiter = RateLimiter()

        # Act
        result = limiter.try_acquire("no_limit_event")

        # Assert
        assert result is True


# =============================================================================
# TEST CLASS - THREAD SAFETY
# =============================================================================


class TestRateLimiterThreadSafety:
    """Test thread safety of RateLimiter."""

    def test_concurrent_try_acquire_respects_limit(self):
        """Test that concurrent try_acquire() calls respect the rate limit."""
        # Arrange
        limiter = RateLimiter()
        event_type = "concurrent_event"
        requests_per_minute = 10
        limiter.register(event_type, requests_per_minute)

        results = []
        lock = threading.Lock()

        def worker():
            result = limiter.try_acquire(event_type)
            with lock:
                results.append(result)

        # Act - Launch 20 concurrent requests
        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert - Exactly 10 should succeed
        assert sum(results) == requests_per_minute
