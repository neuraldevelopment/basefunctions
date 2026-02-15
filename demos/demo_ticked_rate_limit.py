"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo for TickedRateLimiter - Flood queue with events, watch system
 self-regulate. Simulates TickerHub use-case: bulk updates with API
 rate limiting.
 Log:
 v1.0.0 : Initial implementation
 v1.0.1 : Simplify demo - set burst default to 100, remove detailed analysis
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import argparse
import sys
import time
from typing import Any

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
DEFAULT_URL = "https://heise.de"
DEFAULT_RPM = 1000
DEFAULT_DURATION = 2.0
DEFAULT_BURST = 100
MIN_RPM = 60
MAX_RPM = 10000
MONITOR_INTERVAL = 5.0


# =============================================================================
# FUNCTIONS
# =============================================================================


def parse_arguments() -> dict[str, Any]:
    """
    Parse CLI arguments.

    Returns
    -------
    dict[str, Any]
        Parsed arguments

    Raises
    ------
    ValueError
        If validation fails
    """
    parser = argparse.ArgumentParser(
        description="TickedRateLimiter Demo - HTTP Request Flood & Self-Regulation"
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Target URL (default: {DEFAULT_URL})"
    )
    parser.add_argument(
        "--rpm",
        type=int,
        default=DEFAULT_RPM,
        help=f"Requests per minute (default: {DEFAULT_RPM})"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION,
        help=f"Duration in minutes (default: {DEFAULT_DURATION})"
    )
    parser.add_argument(
        "--burst",
        type=int,
        default=DEFAULT_BURST,
        help=f"Initial burst size (default: {DEFAULT_BURST})"
    )

    args = parser.parse_args()

    # Validation
    if not MIN_RPM <= args.rpm <= MAX_RPM:
        raise ValueError(f"RPM must be {MIN_RPM}-{MAX_RPM}, got {args.rpm}")

    if args.duration <= 0:
        raise ValueError(f"Duration must be positive, got {args.duration}")

    if args.burst < 0:
        raise ValueError(f"Burst must be non-negative, got {args.burst}")

    return {
        "url": args.url,
        "rpm": args.rpm,
        "duration": args.duration,
        "burst": args.burst,
    }


def create_http_events(url: str, count: int) -> list[basefunctions.Event]:
    """
    Create HTTP request events.

    Parameters
    ----------
    url : str
        Target URL
    count : int
        Number of events

    Returns
    -------
    list[basefunctions.Event]
        Created events
    """
    events = []
    for _ in range(count):
        event = basefunctions.Event(
            event_type="http_request",
            event_exec_mode=basefunctions.EXECUTION_MODE_THREAD,
            event_data={
                "url": url,
                "method": "GET",
                "timeout": 10,
            }
        )
        events.append(event)
    return events


def publish_all_events(
    bus: basefunctions.EventBus,
    events: list[basefunctions.Event]
) -> list[str]:
    """
    Publish all events immediately (flood queue).

    Parameters
    ----------
    bus : EventBus
        EventBus instance
    events : list[Event]
        Events to publish

    Returns
    -------
    list[str]
        Event IDs
    """
    event_ids = []
    for event in events:
        event_id = bus.publish(event)
        event_ids.append(event_id)
    return event_ids


def monitor_progress(
    bus: basefunctions.EventBus,
    total_events: int,
    update_interval: float = 5.0
) -> float:
    """
    Monitor rate limiter progress with live updates.

    Parameters
    ----------
    bus : EventBus
        EventBus instance
    total_events : int
        Expected total events
    update_interval : float
        Update interval in seconds

    Returns
    -------
    float
        Total monitoring duration
    """
    start_time = time.time()
    last_update = start_time

    print("\nMonitoring progress (Ctrl+C to stop):")
    print("-" * 70)

    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time

            # Only update at intervals
            if current_time - last_update < update_interval:
                time.sleep(0.5)
                continue

            last_update = current_time

            try:
                metrics = bus.get_rate_limit_metrics("http_request")

                # Format output
                elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
                soll = metrics["limit"]
                ist = metrics["actual_last_second"]
                queued = metrics["queued"]
                processed = metrics["total_processed"]

                # Status indicator
                status = "✓" if queued == 0 and processed == total_events else "⟳"

                print(
                    f"[{elapsed_str}] "
                    f"SOLL: {soll:3d}/s | "
                    f"IST: {ist:3d}/s | "
                    f"Queue: {queued:5d} | "
                    f"Processed: {processed:5d}/{total_events} {status}"
                )

                # Exit condition
                if queued == 0 and processed >= total_events:
                    print("-" * 70)
                    break

            except ValueError:
                # Rate limit not registered yet
                time.sleep(0.5)
                continue

    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")

    return time.time() - start_time


def collect_results(
    bus: basefunctions.EventBus,
    event_ids: list[str]
) -> dict[str, Any]:
    """
    Collect results (lightweight - only count success/failure).

    Parameters
    ----------
    bus : EventBus
        EventBus instance
    event_ids : list[str]
        Event IDs to collect

    Returns
    -------
    dict[str, Any]
        Simple results: total, success, failure
    """
    # Don't join - just check what's available
    results_dict = bus.get_results(event_ids, join_before=False)

    success_count = 0
    failure_count = 0

    for event_id in event_ids:
        if event_id in results_dict:
            result = results_dict[event_id]
            # Only check success flag, discard data
            if result.success:
                success_count += 1
            else:
                failure_count += 1
        else:
            # Not processed yet
            pass

    return {
        "total": len(event_ids),
        "success": success_count,
        "failure": failure_count,
    }


def print_summary(
    results: dict[str, Any],
    duration: float,
    rpm: int,
    rps: int
) -> None:
    """
    Print formatted summary.

    Parameters
    ----------
    results : dict
        Results from collect_results
    duration : float
        Total duration in seconds
    rpm : int
        Target requests per minute
    rps : int
        Target requests per second
    """
    total = results["total"]
    success = results["success"]
    failure = results["failure"]

    success_rate = (success / total * 100) if total > 0 else 0
    actual_rpm = (total / duration) * 60 if duration > 0 else 0
    actual_rps = total / duration if duration > 0 else 0

    # Compliance check
    compliance = "✓ WITHIN LIMIT" if actual_rps <= rps * 1.1 else "✗ EXCEEDED LIMIT"

    sep = "=" * 70

    print(f"\n{sep}")
    print("Results Summary")
    print(sep)
    print(f"\nExecution:")
    print(f"  Total Duration: {duration:.1f}s ({duration / 60:.2f} minutes)")
    print(f"  Events Published: {total}")
    print(f"  Events Processed: {success + failure}")
    print(f"  Success: {success} ({success_rate:.1f}%)")
    print(f"  Failed: {failure}")

    print(f"\nRate Limit Compliance:")
    print(f"  Target: {rpm} req/min ({rps:.2f} req/sec)")
    print(f"  Actual: {actual_rpm:.0f} req/min ({actual_rps:.2f} req/sec)")
    print(f"  Status: {compliance}")

    print(f"\n{sep}\n")


def main() -> None:
    """Execute demo."""
    # Parse arguments
    args = parse_arguments()
    url = args["url"]
    rpm = args["rpm"]
    duration = args["duration"]
    burst = args["burst"]

    # Calculate parameters
    total_events = int(rpm * duration)
    rps = max(1, int(rpm / 60))

    # Print configuration
    sep = "=" * 70
    print(f"\n{sep}")
    print("TickedRateLimiter Demo - HTTP Request Flood")
    print(sep)
    print("\nConfiguration:")
    print(f"  URL: {url}")
    print(f"  SOLL: {rpm} req/min ({rps:.2f} req/sec)")
    print(f"  Duration: {duration} minutes")
    print(f"  Total Events: {total_events}")
    print(f"  Burst: {burst}")
    print(sep)

    # Setup EventBus
    bus = basefunctions.EventBus(num_threads=10)
    bus.register_rate_limit("http_request", requests_per_second=rps, burst=burst)

    # Register HTTP handler
    factory = basefunctions.EventFactory()
    factory.register_event_type("http_request", basefunctions.HttpClientHandler)

    # Create events
    print(f"\nCreating {total_events} events...")
    events = create_http_events(url, total_events)
    print(f"✓ Created {len(events)} events")

    # Publish all events immediately (flood queue)
    print(f"\nPublishing {total_events} events to queue...")
    publish_start = time.time()
    event_ids = publish_all_events(bus, events)
    publish_duration = time.time() - publish_start
    print(f"✓ Published {len(event_ids)} events in {publish_duration:.2f}s")

    # Monitor progress
    monitoring_duration = monitor_progress(
        bus,
        total_events,
        update_interval=MONITOR_INTERVAL
    )

    # Collect results
    print("\nCollecting results...")
    results = collect_results(bus, event_ids)

    # Print summary
    print_summary(results, monitoring_duration, rpm, rps)

    # Cleanup
    bus.shutdown()


# =============================================================================
# MAIN
# =============================================================================


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyboardInterrupt) as e:
        logger.error("Demo failed: %s", e)
        sys.exit(1)
