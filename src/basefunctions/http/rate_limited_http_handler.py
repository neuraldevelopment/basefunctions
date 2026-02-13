"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Rate-limited HTTP event handler with token bucket queue system
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from __future__ import annotations
import time
import queue
import threading
from typing import Any

# Third-party
import requests

# Project modules
import basefunctions
from basefunctions.utils.logging import setup_logger, get_logger

# =============================================================================
# LOGGING
# =============================================================================
setup_logger(__name__)
logger = get_logger(__name__)

# =============================================================================
# MODULE-LEVEL SESSION (for HTTP requests)
# =============================================================================
try:
    # Import _SESSION from http_client_handler if available
    from basefunctions.http.http_client_handler import _SESSION
except ImportError:
    # Fallback: create own session
    _SESSION = requests.Session()

# =============================================================================
# INTERNAL CLASSES
# =============================================================================


class _TokenBucket:
    """
    Token bucket for rate limiting with continuous refill.

    Parameters
    ----------
    capacity : int
        Maximum tokens available
    refill_rate : float
        Tokens added per second

    Attributes
    ----------
    capacity : int
        Maximum token capacity
    tokens : float
        Current available tokens
    refill_rate : float
        Tokens per second
    last_refill : float
        Timestamp of last refill
    """

    def __init__(self, capacity: int, refill_rate: float) -> None:
        """
        Initialize token bucket with full capacity.

        Parameters
        ----------
        capacity : int
            Maximum tokens available
        refill_rate : float
            Tokens added per second
        """
        self.capacity: int = capacity
        self.tokens: float = float(capacity)
        self.refill_rate: float = refill_rate
        self.last_refill: float = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens from bucket.

        Parameters
        ----------
        tokens : int, default 1
            Number of tokens to consume

        Returns
        -------
        bool
            True if tokens available and consumed, False otherwise
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """Refill bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now


# =============================================================================
# PUBLIC CLASSES
# =============================================================================


class RateLimitedHttpHandler(basefunctions.EventHandler):
    """
    HTTP request handler with rate limiting via token bucket.

    Queues requests and processes them with controlled rate to respect API limits.
    Uses token bucket algorithm with configurable requests per minute and burst size.

    Parameters
    ----------
    requests_per_minute : int, default 1000
        Target request rate (converted to refill_rate = rpm/60)
    burst_size : int, default 100
        Initial burst capacity (fast requests before rate limiting)
    respect_headers : bool, default True
        Adjust rate limit based on X-RateLimit-Remaining header
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def __init__(
        self,
        requests_per_minute: int = 1000,
        burst_size: int = 100,
        respect_headers: bool = True,
    ) -> None:
        """
        Initialize rate-limited HTTP handler.

        Parameters
        ----------
        requests_per_minute : int, default 1000
            Maximum requests per minute
        burst_size : int, default 100
            Initial token capacity for burst requests
        respect_headers : bool, default True
            Respect X-RateLimit-Remaining header
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.respect_headers = respect_headers

        # Create token bucket: capacity=rpm, refill_rate=rpm/60, tokens=burst_size
        refill_rate = requests_per_minute / 60.0
        self._bucket = _TokenBucket(
            capacity=requests_per_minute,
            refill_rate=refill_rate
        )
        self._bucket.tokens = float(burst_size)

        # Create request queue
        self._queue: queue.Queue[basefunctions.Event] = queue.Queue()

        # Worker thread management
        self._worker_thread: threading.Thread | None = None

        # Results storage (event_id -> EventResult)
        self._results: dict[str, basefunctions.EventResult] = {}

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Queue event for rate-limited processing.

        Parameters
        ----------
        event : basefunctions.Event
            HTTP request event
        context : basefunctions.EventContext
            Event context

        Returns
        -------
        basefunctions.EventResult
            Success result indicating event was queued
        """
        # Queue the event
        self._queue.put(event)

        # Start worker thread if needed
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(
                target=self._process_queue,
                daemon=True
            )
            self._worker_thread.start()

        # Return success immediately (event queued for processing)
        return basefunctions.EventResult.business_result(
            event.event_id,
            True,
            "Event queued for rate-limited processing"
        )

    def _process_queue(self) -> None:
        """Process queued events with rate limiting via token bucket."""
        while True:
            try:
                # Try to get event from queue (non-blocking)
                event = self._queue.get(timeout=0.1)
            except queue.Empty:
                # Queue is empty, exit worker
                break

            try:
                # Wait for token (blocking until available)
                while not self._bucket.consume(1):
                    time.sleep(0.01)  # Small sleep to avoid busy-waiting

                # Make HTTP request
                url = event.event_data.get("url")
                method = event.event_data.get("method", "GET").upper()

                response = _SESSION.request(method, url, timeout=25)
                response.raise_for_status()

                # Check rate limit headers if enabled
                if self.respect_headers:
                    remaining = self._parse_rate_limit_headers(response)
                    if remaining is not None:
                        self._adjust_rate_limit(remaining, self.requests_per_minute)

                # Store success result
                result = basefunctions.EventResult.business_result(
                    event.event_id,
                    True,
                    response.text
                )
                self._results[event.event_id] = result

            except Exception as e:
                # Store error result
                result = basefunctions.EventResult.exception_result(
                    event.event_id,
                    e
                )
                self._results[event.event_id] = result

    def _parse_rate_limit_headers(self, response: Any) -> int | None:
        """
        Parse X-RateLimit-Remaining header from response.

        Parameters
        ----------
        response : Any
            HTTP response object with headers attribute

        Returns
        -------
        int | None
            Remaining requests or None if header not present
        """
        try:
            remaining_str = response.headers.get("X-RateLimit-Remaining")
            if remaining_str is not None:
                return int(remaining_str)
        except (ValueError, AttributeError):
            pass
        return None

    def _adjust_rate_limit(self, remaining: int, limit: int) -> None:
        """
        Adjust rate limit if remaining requests is low.

        Parameters
        ----------
        remaining : int
            Remaining requests from header
        limit : int
            Total limit from header
        """
        # If remaining < 10% of limit, reduce tokens
        threshold = limit // 10
        if remaining < threshold:
            logger.warning(
                f"Low rate limit remaining: {remaining}/{limit} "
                f"({100*remaining//limit}%). Reducing request tokens."
            )
            # Reduce current tokens to be conservative
            self._bucket.tokens = min(self._bucket.tokens, remaining // 2)
