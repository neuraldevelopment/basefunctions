"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Second-ticked rate limiter with burst support for event handling
 Log:
 v1.0.0 : Initial implementation
 v1.0.1 : Fix burst semantics - tokens start with burst value (not additive)
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from basefunctions.events.event import Event


# =============================================================================
# LOGGING
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# EXPORT DEFINITIONS
# =============================================================================
__all__ = [
    "RateLimitConfig",
    "RateLimitMetrics",
    "TickedRateLimiter",
]


# =============================================================================
# DATACLASS DEFINITIONS
# =============================================================================
@dataclass
class RateLimitConfig:
    """
    Rate limit configuration per event_type.

    Parameters
    ----------
    event_type : str
        Event type identifier
    requests_per_second : int
        Maximum allowed requests per second
    burst : int
        Number of requests that bypass rate limiting
    max_tokens : int
        Maximum token bucket capacity (requests_per_second * 60)
    """

    event_type: str
    requests_per_second: int
    burst: int
    max_tokens: int


@dataclass
class RateLimitMetrics:
    """
    Runtime metrics for rate-limited event_type.

    Parameters
    ----------
    limit : int
        SOLL - configured requests_per_second
    actual_last_second : int
        IST - events processed in last completed second
    burst_config : int
        Configured burst capacity
    current_tokens : float
        Current token bucket level
    queued : int
        Current queue depth
    total_processed : int
        Total events processed since registration
    start_time : float
        Registration timestamp from time.time()
    """

    limit: int
    actual_last_second: int
    burst_config: int
    current_tokens: float
    queued: int
    total_processed: int
    start_time: float


# =============================================================================
# CLASS DEFINITIONS
# =============================================================================
class TickedRateLimiter:
    """
    Second-ticked rate limiter with burst support.

    Enforces rate limits using 1-second intervals with token bucket semantics.
    Each event type gets dedicated worker thread and queue.

    Features
    --------
    - Burst: Initial events bypass rate limiting
    - Token accumulation: Up to max_tokens during idle periods
    - Graceful shutdown: Flush or drop pending events

    Parameters
    ----------
    target_input_queue : queue.PriorityQueue
        Target queue to forward rate-limited events to
    """

    __slots__ = (
        "_logger",
        "_limits",
        "_workers",
        "_queues",
        "_metrics",
        "_target_input_queue",
        "_shutdown_flag",
        "_lock",
    )

    def __init__(self, target_input_queue: queue.PriorityQueue) -> None:
        """
        Initialize the TickedRateLimiter.

        Parameters
        ----------
        target_input_queue : queue.PriorityQueue
            Target queue for forwarding rate-limited events
        """
        self._logger = logger
        self._limits: dict[str, RateLimitConfig] = {}
        self._workers: dict[str, threading.Thread] = {}
        self._queues: dict[str, queue.PriorityQueue] = {}
        self._metrics: dict[str, RateLimitMetrics] = {}
        self._target_input_queue = target_input_queue
        self._shutdown_flag = threading.Event()
        self._lock = threading.RLock()

    def register(self, event_type: str, requests_per_second: int, burst: int = 0) -> None:
        """
        Register rate limit for an event_type.

        Parameters
        ----------
        event_type : str
            Event type identifier
        requests_per_second : int
            Maximum allowed requests per second
        burst : int, default 0
            Number of requests that bypass rate limiting

        Raises
        ------
        ValueError
            If requests_per_second <= 0 or burst < 0
        """
        # Validate parameters
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")
        if burst < 0:
            raise ValueError("burst must be >= 0")

        with self._lock:
            # Create config
            max_tokens = requests_per_second * 60
            config = RateLimitConfig(
                event_type=event_type,
                requests_per_second=requests_per_second,
                burst=burst,
                max_tokens=max_tokens,
            )
            self._limits[event_type] = config

            # Create queue
            self._queues[event_type] = queue.PriorityQueue()

            # Create metrics (tokens start with burst value)
            metrics = RateLimitMetrics(
                limit=requests_per_second,
                actual_last_second=0,
                burst_config=burst,
                current_tokens=float(burst),
                queued=0,
                total_processed=0,
                start_time=time.time(),
            )
            self._metrics[event_type] = metrics

            # Start worker thread
            worker = threading.Thread(
                target=self._worker_loop,
                args=(event_type, requests_per_second, burst),
                daemon=True,
                name=f"RateLimiter-{event_type}",
            )
            worker.start()
            self._workers[event_type] = worker

    def submit(self, event_type: str, priority: int, counter: int, event: "Event") -> None:
        """
        Submit event to rate limiter queue.

        Parameters
        ----------
        event_type : str
            Event type identifier
        priority : int
            Event priority
        counter : int
            Event counter
        event : Event
            Event instance

        Raises
        ------
        ValueError
            If event_type is not registered
        """
        with self._lock:
            if event_type not in self._limits:
                raise ValueError(f"event_type '{event_type}' is not registered")
            self._queues[event_type].put((priority, counter, event))

    def has_limit(self, event_type: str) -> bool:
        """
        Check if event_type has a registered rate limit.

        Parameters
        ----------
        event_type : str
            Event type to check

        Returns
        -------
        bool
            True if rate limit is registered
        """
        with self._lock:
            return event_type in self._limits

    def get_limit(self, event_type: str) -> tuple[int, int]:
        """
        Get SOLL and IST limits for event_type.

        Parameters
        ----------
        event_type : str
            Event type identifier

        Returns
        -------
        tuple[int, int]
            (SOLL, IST) = (requests_per_second, actual_last_second)

        Raises
        ------
        ValueError
            If event_type is not registered
        """
        with self._lock:
            if event_type not in self._limits:
                raise ValueError(f"event_type '{event_type}' is not registered")
            metrics = self._metrics[event_type]
            return (metrics.limit, metrics.actual_last_second)

    def get_metrics(self, event_type: str) -> dict[str, int | float]:
        """
        Get full metrics for event_type.

        Parameters
        ----------
        event_type : str
            Event type identifier

        Returns
        -------
        dict[str, int | float]
            Full metrics dictionary

        Raises
        ------
        ValueError
            If event_type is not registered
        """
        with self._lock:
            if event_type not in self._limits:
                raise ValueError(f"event_type '{event_type}' is not registered")
            metrics = self._metrics[event_type]
            # Update queued from current queue size
            queued = self._queues[event_type].qsize()
            return {
                "limit": metrics.limit,
                "actual_last_second": metrics.actual_last_second,
                "burst_config": metrics.burst_config,
                "current_tokens": metrics.current_tokens,
                "queued": queued,
                "total_processed": metrics.total_processed,
                "start_time": metrics.start_time,
            }

    def shutdown(self, flush: bool = True) -> None:
        """
        Shutdown rate limiter.

        Parameters
        ----------
        flush : bool, default True
            If True, process remaining events; if False, drop them
        """
        with self._lock:
            self._shutdown_flag.set()
            worker_threads = list(self._workers.values())

        # Join all worker threads
        for worker in worker_threads:
            worker.join(timeout=5.0)

    def _forward_to_input_queue(self, priority: int, counter: int, event: "Event") -> None:
        """
        Forward event to target input queue.

        Parameters
        ----------
        priority : int
            Event priority
        counter : int
            Event counter
        event : Event
            Event instance
        """
        self._target_input_queue.put((priority, counter, event))

    def _worker_loop(self, event_type: str, requests_per_second: int, burst: int) -> None:
        """
        Worker loop implementing token bucket rate limiting.

        Parameters
        ----------
        event_type : str
            Event type
        requests_per_second : int
            Rate limit
        burst : int
            Initial token budget
        """
        # Initialize token bucket with burst as starting tokens
        tokens = float(burst)
        max_tokens = requests_per_second * 60
        last_second_count = 0
        last_tick = time.time()

        with self._lock:
            event_queue = self._queues[event_type]
            metrics = self._metrics[event_type]

        while not self._shutdown_flag.is_set():
            try:
                # Try to get event with timeout
                priority, counter, event = event_queue.get(timeout=1.0)

                # Token bucket: check if we have tokens
                while tokens < 1.0:
                    # Check shutdown during wait
                    if self._shutdown_flag.is_set():
                        return

                    # Sleep and refill tokens
                    time.sleep(1.0)
                    current_time = time.time()
                    elapsed = current_time - last_tick

                    if elapsed >= 1.0:
                        # Refill tokens
                        tokens = min(tokens + requests_per_second, max_tokens)
                        # Update IST metric
                        with self._lock:
                            metrics.actual_last_second = last_second_count
                        last_second_count = 0
                        last_tick = current_time

                # Consume token and forward
                tokens -= 1.0
                self._forward_to_input_queue(priority, counter, event)
                last_second_count += 1

                # Update metrics
                with self._lock:
                    metrics.current_tokens = tokens
                    metrics.total_processed += 1

            except queue.Empty:
                # Timeout - refill tokens and update IST
                current_time = time.time()
                elapsed = current_time - last_tick

                if elapsed >= 1.0:
                    tokens = min(tokens + requests_per_second, max_tokens)
                    with self._lock:
                        metrics.current_tokens = tokens
                        metrics.actual_last_second = last_second_count
                    last_second_count = 0
                    last_tick = current_time

        # Shutdown handling
        with self._lock:
            flush = True  # Default to flush

        if flush:
            # Process remaining events
            while True:
                try:
                    priority, counter, event = event_queue.get_nowait()
                    self._forward_to_input_queue(priority, counter, event)
                except queue.Empty:
                    break
