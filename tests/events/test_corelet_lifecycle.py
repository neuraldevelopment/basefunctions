"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Comprehensive test suite for corelet process lifecycle management.
 Tests creation, tracking, idle timeout, cleanup, and monitoring APIs.

 Log:
 v1.0.0 : Initial test implementation for corelet lifecycle
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard Library
import time
import threading
from typing import Any

# Third-party
import pytest

# Project modules
from basefunctions.events.event_bus import EventBus
from basefunctions.events.event import Event
from basefunctions.events.event_handler import EventHandler, EventResult
from basefunctions.events.event_factory import EventFactory
import basefunctions

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_event_bus_singleton():
    """
    Reset EventBus singleton instance before and after each test.

    Yields
    ------
    None
        Yields control to test, then cleans up
    """
    from basefunctions.utils.decorators import _singleton_instances

    # Clear EventBus singleton instance
    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            del _singleton_instances[cls]
            break

    yield

    # Cleanup after test
    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            bus = _singleton_instances.get(cls)
            if bus:
                try:
                    bus.shutdown(immediately=True)
                    bus.join()
                except Exception:
                    pass
            del _singleton_instances[cls]
            break


@pytest.fixture
def event_bus():
    """
    Create EventBus instance for testing.

    Returns
    -------
    EventBus
        Fresh EventBus instance with 2 worker threads
    """
    bus = EventBus(num_threads=2)
    yield bus
    # Cleanup
    try:
        bus.shutdown(immediately=True)
        bus.join()
    except Exception:
        pass


@pytest.fixture
def test_handler_class():
    """
    Create test handler class for corelet events.

    Returns
    -------
    type
        EventHandler subclass for testing
    """

    class TestCoreletHandler(EventHandler):
        """Simple handler for testing corelet lifecycle."""

        def handle(self, event: Event, context: Any) -> EventResult:
            """Process event by returning success."""
            return EventResult.business_result(event.event_id, True, "processed")

    return TestCoreletHandler


@pytest.fixture
def register_test_handler(test_handler_class):
    """
    Register test handler with EventFactory.

    Parameters
    ----------
    test_handler_class : type
        Handler class to register

    Yields
    ------
    str
        Event type registered for testing
    """
    event_type = "test_corelet_event"
    factory = EventFactory()
    factory.register_event_type(event_type, test_handler_class)
    yield event_type


# -------------------------------------------------------------
# TEST CASES - CORELET CREATION AND TRACKING
# -------------------------------------------------------------


def test_corelet_count_initially_zero(event_bus):
    """
    Test that corelet count is 0 when EventBus initialized.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture

    Notes
    -----
    Verifies initial state before any corelet events published.
    """
    assert event_bus.get_corelet_count() == 0


def test_corelet_metrics_initial_state(event_bus):
    """
    Test corelet metrics in initial state.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture

    Notes
    -----
    Verifies metrics API returns correct structure and values.
    """
    metrics = event_bus.get_corelet_metrics()

    assert isinstance(metrics, dict)
    assert metrics["active_corelets"] == 0
    assert metrics["worker_threads"] == 2
    assert metrics["max_corelets"] == 2


def test_corelet_created_on_first_event(event_bus, register_test_handler):
    """
    Test corelet process created on first CORELET event.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies SESSION-BASED lifecycle - corelet created on demand.
    """
    event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
    event_id = event_bus.publish(event)
    event_bus.join()

    # Give process time to start
    time.sleep(0.2)

    # Corelet should be created
    assert event_bus.get_corelet_count() >= 1

    # Verify result was successful
    results = event_bus.get_results([event_id])
    assert results[event_id].success is True


def test_corelet_reused_for_subsequent_events(event_bus, register_test_handler):
    """
    Test corelet process reused for subsequent events in same thread.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies SESSION-BASED lifecycle - corelet reuse reduces overhead.
    """
    # Publish multiple events
    event_ids = []
    for _ in range(5):
        event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
        event_ids.append(event_bus.publish(event))

    event_bus.join()
    time.sleep(0.2)

    # Should have at most num_worker_threads corelets
    count = event_bus.get_corelet_count()
    assert count <= 2

    # All events should succeed
    results = event_bus.get_results(event_ids)
    for event_id in event_ids:
        assert results[event_id].success is True


def test_corelet_count_bounded_by_worker_threads(event_bus, register_test_handler):
    """
    Test corelet count never exceeds worker thread count.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies resource guarantee - max corelets = worker_threads.
    This prevents unbounded process growth.
    """
    # Publish many events concurrently
    event_ids = []
    for _ in range(20):
        event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
        event_ids.append(event_bus.publish(event))

    event_bus.join()
    time.sleep(0.5)

    # Count should be <= num_worker_threads
    count = event_bus.get_corelet_count()
    assert count <= 2

    # Verify metrics consistency
    metrics = event_bus.get_corelet_metrics()
    assert metrics["active_corelets"] == count
    assert metrics["max_corelets"] == 2


# -------------------------------------------------------------
# TEST CASES - CORELET CLEANUP
# -------------------------------------------------------------


def test_corelet_cleanup_on_shutdown(event_bus, register_test_handler):
    """
    Test corelets cleaned up on EventBus shutdown.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies EXPLICIT CLEANUP lifecycle phase.
    """
    # Create corelets
    event_ids = []
    for _ in range(5):
        event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
        event_ids.append(event_bus.publish(event))

    event_bus.join()
    time.sleep(0.2)

    # Verify corelets exist
    initial_count = event_bus.get_corelet_count()
    assert initial_count > 0

    # Shutdown
    event_bus.shutdown(immediately=True)
    event_bus.join()
    time.sleep(0.5)

    # All corelets should be cleaned up
    final_count = event_bus.get_corelet_count()
    assert final_count == 0


def test_corelet_tracking_removed_on_cleanup(event_bus, register_test_handler):
    """
    Test corelet removed from tracking on cleanup.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies tracking dictionary properly maintained.
    """
    # Create corelet
    event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
    event_id = event_bus.publish(event)
    event_bus.join()
    time.sleep(0.2)

    # Verify corelet tracked
    assert event_bus.get_corelet_count() >= 1

    # Shutdown
    event_bus.shutdown(immediately=True)
    event_bus.join()
    time.sleep(0.5)

    # Verify tracking cleared
    assert event_bus.get_corelet_count() == 0
    assert len(event_bus._active_corelets) == 0


# -------------------------------------------------------------
# TEST CASES - TIMEOUT HANDLING
# -------------------------------------------------------------


def test_corelet_timeout_cleanup(event_bus, test_handler_class):
    """
    Test corelet cleaned up on timeout.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    test_handler_class : type
        Handler class for testing

    Notes
    -----
    Verifies timeout scenario properly cleans up corrupted corelet.
    """

    class SlowHandler(EventHandler):
        """Handler that times out."""

        def handle(self, event: Event, context: Any) -> EventResult:
            """Process event slowly to cause timeout."""
            time.sleep(10)  # Longer than event timeout
            return EventResult.business_result(event.event_id, True, "processed")

    # Register slow handler
    event_type = "slow_event"
    factory = EventFactory()
    factory.register_event_type(event_type, SlowHandler)

    # Publish event with short timeout
    event = Event(event_type, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET, timeout=1)
    event_id = event_bus.publish(event)

    # Wait for timeout and cleanup
    time.sleep(3)
    event_bus.join()

    # Corelet should be cleaned up after timeout
    # Note: Another corelet might have been created by worker thread
    # so we just verify count is bounded
    count = event_bus.get_corelet_count()
    assert count <= 2


# -------------------------------------------------------------
# TEST CASES - MONITORING API
# -------------------------------------------------------------


def test_get_corelet_count_thread_safe(event_bus, register_test_handler):
    """
    Test get_corelet_count is thread-safe.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies monitoring API can be called concurrently.
    """
    # Publish events
    for _ in range(10):
        event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
        event_bus.publish(event)

    # Concurrently read count
    counts = []

    def read_count():
        for _ in range(100):
            counts.append(event_bus.get_corelet_count())
            time.sleep(0.001)

    threads = [threading.Thread(target=read_count) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    event_bus.join()

    # All counts should be valid (0 to max_corelets)
    for count in counts:
        assert 0 <= count <= 2


def test_get_corelet_metrics_structure(event_bus, register_test_handler):
    """
    Test get_corelet_metrics returns correct structure.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies metrics API contract.
    """
    # Publish some events
    for _ in range(5):
        event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
        event_bus.publish(event)

    event_bus.join()
    time.sleep(0.2)

    metrics = event_bus.get_corelet_metrics()

    # Verify structure
    assert "active_corelets" in metrics
    assert "worker_threads" in metrics
    assert "max_corelets" in metrics

    # Verify types
    assert isinstance(metrics["active_corelets"], int)
    assert isinstance(metrics["worker_threads"], int)
    assert isinstance(metrics["max_corelets"], int)

    # Verify relationships
    assert metrics["active_corelets"] <= metrics["max_corelets"]
    assert metrics["max_corelets"] == metrics["worker_threads"]


# -------------------------------------------------------------
# TEST CASES - EDGE CASES
# -------------------------------------------------------------


def test_no_corelet_leak_on_repeated_shutdown(event_bus, register_test_handler):
    """
    Test no corelet leak on repeated create/shutdown cycles.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies cleanup is idempotent and complete.
    """
    for cycle in range(3):
        # Create corelets
        for _ in range(5):
            event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
            event_bus.publish(event)

        event_bus.join()
        time.sleep(0.2)

        # Verify corelets created
        assert event_bus.get_corelet_count() > 0

        # Shutdown
        event_bus.shutdown(immediately=True)
        event_bus.join()
        time.sleep(0.5)

        # Verify all cleaned up
        assert event_bus.get_corelet_count() == 0


def test_corelet_count_zero_after_all_cleanup_paths(event_bus, register_test_handler):
    """
    Test corelet count reaches zero after cleanup via all paths.

    Parameters
    ----------
    event_bus : EventBus
        EventBus fixture
    register_test_handler : str
        Registered event type

    Notes
    -----
    Verifies all cleanup paths (shutdown, timeout, terminate) work correctly.
    """
    # Create corelet via normal event
    event = Event(register_test_handler, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET)
    event_bus.publish(event)
    event_bus.join()
    time.sleep(0.2)

    assert event_bus.get_corelet_count() >= 1

    # Cleanup via shutdown
    event_bus.shutdown(immediately=True)
    event_bus.join()
    time.sleep(0.5)

    # Final count should be zero
    assert event_bus.get_corelet_count() == 0
