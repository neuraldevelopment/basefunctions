"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo script for RateLimitedHttpHandler with performance analysis
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import argparse
import statistics
import sys
import time
from typing import Any
from urllib.parse import urlparse

# Project imports
import basefunctions
from basefunctions.utils.logging import setup_logger, get_logger

# =============================================================================
# LOGGING
# =============================================================================
setup_logger(__name__)
logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================
MIN_RPM = 1
MAX_RPM = 10000
DEFAULT_RPM = 600
DEFAULT_DURATION = 60
DEFAULT_BURST = 50
MAX_EVENTS_PER_BATCH = 100
BATCH_DELAY = 0.01
REQUEST_TIMEOUT = 30


# =============================================================================
# FUNCTIONS
# =============================================================================


def validate_url(url: str) -> str:
    """
    Validate URL format.

    Parameters
    ----------
    url : str
        URL to validate

    Returns
    -------
    str
        Validated URL

    Raises
    ------
    ValueError
        If URL format invalid
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        if result.scheme not in ("http", "https"):
            raise ValueError("Only HTTP/HTTPS supported")
        return url
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid URL: {e}") from e


def validate_rpm(rpm: int) -> int:
    """
    Validate RPM is in valid range.

    Parameters
    ----------
    rpm : int
        Requests per minute

    Returns
    -------
    int
        Validated RPM

    Raises
    ------
    ValueError
        If RPM out of range
    """
    if not MIN_RPM <= rpm <= MAX_RPM:
        raise ValueError(f"RPM must be {MIN_RPM}-{MAX_RPM}, got {rpm}")
    return rpm


def parse_arguments() -> dict[str, Any]:
    """
    Parse CLI arguments.

    Returns
    -------
    dict
        Parsed arguments dict
    """
    parser = argparse.ArgumentParser(
        description="RateLimitedHttpHandler demo with performance analysis"
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Target URL for HTTP requests"
    )
    parser.add_argument(
        "--rpm",
        type=int,
        default=DEFAULT_RPM,
        help=f"Requests per minute (default: {DEFAULT_RPM})"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Duration in seconds (default: {DEFAULT_DURATION})"
    )
    parser.add_argument(
        "--burst",
        type=int,
        default=DEFAULT_BURST,
        help=f"Initial burst size (default: {DEFAULT_BURST})"
    )

    parsed_args = parser.parse_args()

    # Validate arguments
    parsed_args.url = validate_url(parsed_args.url)
    parsed_args.rpm = validate_rpm(parsed_args.rpm)

    if parsed_args.duration <= 0:
        raise ValueError("Duration must be positive")
    if parsed_args.burst < 0:
        raise ValueError("Burst size must be non-negative")

    return {
        "url": parsed_args.url,
        "rpm": parsed_args.rpm,
        "duration": parsed_args.duration,
        "burst": parsed_args.burst,
    }


def create_events(url: str, count: int) -> list[basefunctions.Event]:
    """
    Create HTTP request events.

    Parameters
    ----------
    url : str
        Target URL
    count : int
        Number of events to create

    Returns
    -------
    list[basefunctions.Event]
        List of event objects
    """
    events = []
    for i in range(count):
        event = basefunctions.Event(
            event_type="http_request",
            event_data={"url": url}
        )
        event.event_id = f"event_{i}"
        events.append(event)
    return events


def _send_events(
    handler: basefunctions.http.RateLimitedHttpHandler,
    events: list[basefunctions.Event],
    batch_size: int = 100,
    batch_delay: float = 0.01
) -> tuple[int, list[float]]:
    """
    Send events in batches.

    Parameters
    ----------
    handler : RateLimitedHttpHandler
        Handler to use
    events : list[Event]
        Events to send
    batch_size : int
        Batch size
    batch_delay : float
        Delay between batches

    Returns
    -------
    tuple[int, list[float]]
        (sent_count, sent_timestamps)
    """
    sent_count = 0
    sent_timestamps: list[float] = []

    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]

        for event in batch:
            try:
                context = basefunctions.EventContext()
                handler.handle(event, context)
                sent_count += 1
                sent_timestamps.append(time.time())
            except (AttributeError, ValueError, OSError) as e:
                logger.error("Error sending event %s: %s", event.event_id, e)

        if i + batch_size < len(events):
            time.sleep(batch_delay)

    return sent_count, sent_timestamps


def _wait_for_results(
    handler: basefunctions.http.RateLimitedHttpHandler,
    expected_count: int,
    timeout: float = 30.0
) -> float:
    """
    Wait for results from handler.

    Parameters
    ----------
    handler : RateLimitedHttpHandler
        Handler to wait for
    expected_count : int
        Expected number of results
    timeout : float
        Timeout in seconds

    Returns
    -------
    float
        Actual wait time
    """
    wait_start = time.time()

    while time.time() - wait_start < timeout:
        try:
            results = handler.get_results()
            if len(results) >= expected_count:
                break
        except (AttributeError, TypeError):
            pass

        time.sleep(0.1)

    return time.time() - wait_start


def _collect_results(
    handler: basefunctions.http.RateLimitedHttpHandler,
    events: list[basefunctions.Event],
    sent_timestamps: list[float]
) -> dict[str, Any]:
    """
    Collect and analyze results.

    Parameters
    ----------
    handler : RateLimitedHttpHandler
        Handler to collect from
    events : list[Event]
        Original events
    sent_timestamps : list[float]
        Timestamps when events were sent

    Returns
    -------
    dict
        Analysis results
    """
    success_count = 0
    failure_count = 0
    response_times: list[float] = []

    results_dict = handler.get_results()

    for idx, event in enumerate(events):
        if event.event_id in results_dict:
            result = results_dict[event.event_id]
            if result.success:
                success_count += 1
                if idx < len(sent_timestamps):
                    elapsed = time.time() - sent_timestamps[idx]
                    response_times.append(max(0.01, elapsed))
            else:
                failure_count += 1

    return {
        "success": success_count,
        "failure": failure_count,
        "response_times": response_times,
    }


def _calculate_metrics(
    results: dict[str, Any],
    sent_count: int,
    total_duration: float
) -> dict[str, Any]:
    """
    Calculate performance metrics.

    Parameters
    ----------
    results : dict
        Results from _collect_results
    sent_count : int
        Number of events sent
    total_duration : float
        Total duration

    Returns
    -------
    dict
        Metrics
    """
    success_count = results["success"]
    response_times = results["response_times"]

    actual_rpm = (sent_count / total_duration) * 60 if total_duration > 0 else 0
    success_rate = (success_count / sent_count * 100) if sent_count > 0 else 0

    return {
        "actual_rpm": actual_rpm,
        "success_rate": success_rate,
        "failure_rate": 100 - success_rate,
        "min_time": min(response_times) if response_times else 0,
        "max_time": max(response_times) if response_times else 0,
        "avg_time": statistics.mean(response_times) if response_times else 0,
    }


def print_results(results: dict[str, Any]) -> None:
    """
    Print formatted results.

    Parameters
    ----------
    results : dict
        Results to print
    """
    sep = "=" * 53

    print(f"\n{sep}")
    print("RateLimitedHttpHandler Demo - Performance Analysis")
    print(sep)
    print("\nResults:")
    print(f"  Total Duration: {results['total_duration']:.1f}s")
    print(f"  Actual Throughput: {results['actual_rpm']:.2f} req/sec")
    print(f"  Success: {results['success']}/{results['sent']}")
    print(f"  Failed: {results['failure']}/{results['sent']}")
    print(f"  Success Rate: {results['success_rate']:.1f}%")

    print("\nTiming Analysis:")
    print(f"  Min Response Time: {results['min_time']:.2f}s")
    print(f"  Max Response Time: {results['max_time']:.2f}s")
    print(f"  Avg Response Time: {results['avg_time']:.2f}s")

    print("\nRate Limit Compliance:")
    target_rps = results["actual_rpm"] / 60
    if target_rps <= 16.67:  # 1000 RPM = 16.67 RPS
        print("  Status: OK ✓")
    else:
        print("  Status: WARNING - exceeding rate limit")

    print(sep)


def execute_demo(url: str, rpm: int, duration: int, burst: int) -> None:
    """
    Execute the rate-limited HTTP demo.

    Parameters
    ----------
    url : str
        Target URL
    rpm : int
        Requests per minute
    duration : int
        Duration in seconds
    burst : int
        Burst size
    """
    # Calculate request count
    requests_count = int((rpm / 60) * duration)

    print(f"\n{'=' * 53}")
    print("RateLimitedHttpHandler Demo")
    print("=" * 53)
    print("Configuration:")
    print(f"  URL: {url}")
    print(f"  RPM: {rpm} ({rpm/60:.2f} req/sec)")
    print(f"  Duration: {duration} seconds")
    print(f"  Burst Size: {burst}")
    print(f"  Expected Requests: {requests_count}")
    print()

    # Setup handler
    handler = basefunctions.http.RateLimitedHttpHandler(
        requests_per_minute=rpm,
        burst_size=burst,
        respect_headers=True
    )

    # Create events
    events = create_events(url, requests_count)

    print("Execution Progress:")
    print(f"  Sending {requests_count} requests...")

    start_time = time.time()

    # Send events
    sent_count, sent_timestamps = _send_events(
        handler, events, MAX_EVENTS_PER_BATCH, BATCH_DELAY
    )

    # Wait for results
    print(f"  Waiting for responses (timeout: {REQUEST_TIMEOUT}s)...")
    _wait_for_results(handler, sent_count, REQUEST_TIMEOUT)

    total_duration = time.time() - start_time

    # Collect results
    results = _collect_results(handler, events, sent_timestamps)
    metrics = _calculate_metrics(results, sent_count, total_duration)

    # Print results
    print_results({
        "sent": sent_count,
        "success": results["success"],
        "failure": results["failure"],
        "total_duration": total_duration,
        "actual_rpm": metrics["actual_rpm"],
        "success_rate": metrics["success_rate"],
        "failure_rate": metrics["failure_rate"],
        "min_time": metrics["min_time"],
        "max_time": metrics["max_time"],
        "avg_time": metrics["avg_time"],
    })


# =============================================================================
# MAIN
# =============================================================================


if __name__ == "__main__":
    try:
        parsed = parse_arguments()
        execute_demo(
            url=parsed["url"],
            rpm=parsed["rpm"],
            duration=parsed["duration"],
            burst=parsed["burst"]
        )
    except (ValueError, KeyboardInterrupt) as e:
        logger.exception("Demo failed: %s", e)
        sys.exit(1)
