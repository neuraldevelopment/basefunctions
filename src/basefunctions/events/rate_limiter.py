"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Rate limiting for EventBus with sliding window algorithm
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
import threading
import time
from collections import deque

# =============================================================================
# CONSTANTS
# =============================================================================
WINDOW_SECONDS = 60

# =============================================================================
# CLASS DEFINITIONS
# =============================================================================


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm.

    Tracks requests per event_type within a 60-second rolling window.
    Uses a global lock for thread-safety and deque for efficient FIFO operations.

    Attributes
    ----------
    _limits : dict[str, int]
        Maps event_type to requests_per_minute limit
    _windows : dict[str, deque[float]]
        Maps event_type to timestamp queue (sliding window)
    _lock : threading.Lock
        Global lock for thread-safe operations

    Notes
    -----
    - has_limit() is lock-free for zero-overhead on unlimited events
    - Window automatically resets after 60 seconds
    - Thread-safe for concurrent access

    Examples
    --------
    Register rate limit and check requests:

    >>> limiter = RateLimiter()
    >>> limiter.register("api_call", requests_per_minute=10)
    >>> limiter.try_acquire("api_call")
    True
    """

    __slots__ = ("_limits", "_windows", "_lock")

    def __init__(self) -> None:
        """Initialize RateLimiter with empty state."""
        self._limits: dict[str, int] = {}
        self._windows: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def register(self, event_type: str, requests_per_minute: int) -> None:
        """
        Register rate limit for an event type.

        Parameters
        ----------
        event_type : str
            Event type to rate limit
        requests_per_minute : int
            Maximum requests per 60-second window

        Raises
        ------
        ValueError
            If requests_per_minute is not positive
        """
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")

        with self._lock:
            self._limits[event_type] = requests_per_minute
            self._windows[event_type] = deque()

    def has_limit(self, event_type: str) -> bool:
        """
        Check if event type has rate limit (lock-free).

        Parameters
        ----------
        event_type : str
            Event type to check

        Returns
        -------
        bool
            True if rate limit is registered
        """
        return event_type in self._limits

    def try_acquire(self, event_type: str) -> bool:
        """
        Try to acquire permission for request (non-blocking).

        Parameters
        ----------
        event_type : str
            Event type requesting permission

        Returns
        -------
        bool
            True if request allowed, False if rate limit exceeded
        """
        # Fast path: No limit registered
        if not self.has_limit(event_type):
            return True

        current_time = time.time()
        window_start = current_time - WINDOW_SECONDS

        with self._lock:
            window = self._windows[event_type]
            limit = self._limits[event_type]

            # Remove timestamps outside window
            while window and window[0] < window_start:
                window.popleft()

            # Check if limit exceeded
            if len(window) >= limit:
                return False

            # Grant permission
            window.append(current_time)
            return True
