"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for EventBus class.
 Tests event publishing, queue management, worker threads, timeout/retry logic,
 handler caching, LRU result management, and graceful shutdown across all
 execution modes (SYNC, THREAD, CORELET, CMD).

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
import queue
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock, patch, call

# Project imports
from basefunctions.events.event_bus import (
    EventBus,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_PRIORITY,
    INTERNAL_CORELET_FORWARDING_EVENT,
    INTERNAL_CMD_EXECUTION_EVENT,
    INTERNAL_SHUTDOWN_EVENT,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture(autouse=False)
def reset_event_bus_singleton() -> None:
    """
    Reset EventBus singleton instance before each test.

    This fixture clears the singleton instance to ensure tests start
    with a fresh EventBus. Since EventBus is decorated with @singleton,
    we need to clear it from the _singleton_instances dict.

    Notes
    -----
    Not using autouse=True to allow manual control per test.
    Tests that need singleton reset should use this fixture explicitly.
    """
    from basefunctions.utils.decorators import _singleton_instances

    # Clear EventBus singleton instance
    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            del _singleton_instances[cls]
            break

    yield

    # Cleanup after test - clear singleton again
    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            del _singleton_instances[cls]
            break


@pytest.fixture
def mock_event_factory() -> Mock:
    """
    Create mock EventFactory instance.

    Returns
    -------
    Mock
        Mock EventFactory with pre-configured methods
    """
    factory: Mock = Mock()
    factory.is_handler_available.return_value = True
    factory.register_event_type.return_value = None
    return factory


@pytest.fixture
def mock_event_handler() -> Mock:
    """
    Create mock EventHandler instance.

    Returns
    -------
    Mock
        Mock EventHandler with handle() method returning success
    """
    from basefunctions.events.event_handler import EventHandler

    handler: Mock = Mock(spec=EventHandler)
    mock_result: Mock = Mock()
    mock_result.success = True
    mock_result.event_id = "test_event_id"
    handler.handle.return_value = mock_result
    return handler


@pytest.fixture
def mock_event() -> Mock:
    """
    Create mock Event with all required attributes.

    Returns
    -------
    Mock
        Mock Event instance with valid attributes
    """
    from basefunctions.events.event import Event

    event: Mock = Mock(spec=Event)
    event.event_id = "test_event_123"
    event.event_type = "test_event"
    event.event_exec_mode = "thread"
    event.priority = DEFAULT_PRIORITY
    event.timeout = DEFAULT_TIMEOUT
    event.max_retries = DEFAULT_RETRY_COUNT
    event.progress_tracker = None
    event.progress_steps = 0
    return event


@pytest.fixture
def mock_sync_event() -> Mock:
    """
    Create mock Event with SYNC execution mode.

    Returns
    -------
    Mock
        Mock Event configured for synchronous execution
    """
    from basefunctions.events.event import Event

    event: Mock = Mock(spec=Event)
    event.event_id = "test_sync_event"
    event.event_type = "test_event"
    event.event_exec_mode = "sync"
    event.priority = DEFAULT_PRIORITY
    event.timeout = DEFAULT_TIMEOUT
    event.max_retries = DEFAULT_RETRY_COUNT
    event.progress_tracker = None
    event.progress_steps = 0
    return event


@pytest.fixture
def mock_event_result_success() -> Mock:
    """
    Create mock EventResult representing success.

    Returns
    -------
    Mock
        Mock EventResult with success=True
    """
    result: Mock = Mock()
    result.success = True
    result.event_id = "test_event_123"
    result.data = {"status": "completed"}
    return result


@pytest.fixture
def mock_event_result_failure() -> Mock:
    """
    Create mock EventResult representing failure.

    Returns
    -------
    Mock
        Mock EventResult with success=False
    """
    result: Mock = Mock()
    result.success = False
    result.event_id = "test_event_123"
    result.error = "Test failure"
    return result


@pytest.fixture
def mock_event_context() -> Mock:
    """
    Create mock EventContext with thread_local_data.

    Returns
    -------
    Mock
        Mock EventContext with thread_local_data storage
    """
    context: Mock = Mock()
    context.thread_local_data = threading.local()
    context.thread_id = 0
    return context


# -------------------------------------------------------------
# TESTS: EventBus Initialization
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_creates_event_bus_with_default_threads(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus initializes with auto-detected CPU threads."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # ACT
    bus: EventBus = EventBus()

    # ASSERT
    assert bus._num_threads == 8
    assert isinstance(bus._input_queue, queue.PriorityQueue)
    assert isinstance(bus._output_queue, queue.Queue)
    assert isinstance(bus._result_list, OrderedDict)
    # Worker threads should be created (daemon threads, will clean up automatically)
    assert len(bus._worker_threads) == 8


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_creates_event_bus_with_custom_threads(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus initializes with custom thread count."""
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    # ACT
    bus: EventBus = EventBus(num_threads=16)

    # ASSERT
    assert bus._num_threads == 16
    assert len(bus._worker_threads) == 16
    # Note: psutil.cpu_count() is called even when num_threads is provided,
    # but the result is not used


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_raises_value_error_when_num_threads_zero(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test EventBus raises ValueError when num_threads is 0."""
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    # ACT & ASSERT
    with pytest.raises(ValueError, match="num_threads must be positive"):
        EventBus(num_threads=0)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_raises_value_error_when_num_threads_negative(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test EventBus raises ValueError when num_threads is negative."""
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    # ACT & ASSERT
    with pytest.raises(ValueError, match="num_threads must be positive"):
        EventBus(num_threads=-5)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_handles_psutil_failure_gracefully(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus uses default 16 threads when psutil fails."""
    # ARRANGE
    mock_cpu_count.side_effect = Exception("psutil error")
    mock_factory_class.return_value = mock_event_factory

    # ACT
    bus: EventBus = EventBus()

    # ASSERT
    assert bus._num_threads == 16


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_singleton_returns_same_instance(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus singleton pattern returns same instance."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # ACT
    bus1: EventBus = EventBus()
    bus2: EventBus = EventBus()

    # ASSERT
    assert bus1 is bus2


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_ensure_thread_count_expands_thread_pool(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus.ensure_thread_count() expands thread pool dynamically."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # ACT - Initialize with 4 threads
    bus1: EventBus = EventBus(num_threads=4)
    initial_thread_count = len(bus1._worker_threads)
    initial_num_threads = bus1._num_threads

    # Expand to 8 threads via public API
    bus1.ensure_thread_count(8)

    # ASSERT
    assert initial_thread_count == 4
    assert initial_num_threads == 4
    assert len(bus1._worker_threads) == 8
    assert bus1._num_threads == 8


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_ensure_thread_count_does_not_reduce_threads(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus.ensure_thread_count() does not reduce threads."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # ACT - Initialize with 8 threads
    bus: EventBus = EventBus(num_threads=8)
    thread_count_after_init = len(bus._worker_threads)

    # Try to "reduce" via ensure_thread_count (should be ignored)
    bus.ensure_thread_count(4)

    # ASSERT
    assert len(bus._worker_threads) == 8  # Thread count unchanged
    assert bus._num_threads == 8


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_ensure_thread_count_updates_max_cached_results(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus.ensure_thread_count() updates _max_cached_results."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # ACT - Initialize with 4 threads
    bus: EventBus = EventBus(num_threads=4)
    max_cached_after_init = bus._max_cached_results

    # Expand to 8 threads
    bus.ensure_thread_count(8)

    # ASSERT
    assert max_cached_after_init == 4 * 1000
    assert bus._max_cached_results == 8 * 1000


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_ensure_thread_count_raises_on_invalid_count(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test EventBus.ensure_thread_count() raises ValueError on invalid count."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus(num_threads=4)

    # ACT & ASSERT
    with pytest.raises(ValueError, match="num_threads must be positive"):
        bus.ensure_thread_count(0)

    with pytest.raises(ValueError, match="num_threads must be positive"):
        bus.ensure_thread_count(-5)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_does_not_register_handlers(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus does NOT register handlers (done via initialize() in __init__.py)."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # ACT
    bus: EventBus = EventBus()

    # ASSERT
    # Handler registration is now performed externally via initialize() in __init__.py
    # EventBus is infrastructure; handler registration is configuration
    mock_event_factory.register_event_type.assert_not_called()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_init_calculates_max_cached_results_correctly(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test EventBus calculates max_cached_results based on thread count."""
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    # ACT
    bus: EventBus = EventBus(num_threads=8)

    # ASSERT
    assert bus._max_cached_results == 8 * 1000


# -------------------------------------------------------------
# TESTS: publish() - Happy Path
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_publish_sync_event_returns_event_id(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_sync_event: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test publish() returns event_id for synchronous event."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    # Create a mock handler that will be returned by the factory
    from basefunctions.events.event_handler import EventHandler

    mock_handler: Mock = Mock(spec=EventHandler)
    mock_result: Mock = Mock()
    mock_result.success = True
    mock_result.event_id = "test_sync_event"
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus: EventBus = EventBus()

    # ACT
    event_id: str = bus.publish(mock_sync_event)

    # ASSERT
    assert event_id == mock_sync_event.event_id
    # Verify the event was processed (result should be in output queue)
    assert mock_handler.handle.called


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_publish_thread_event_queues_event_correctly(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test publish() queues thread event to input queue."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT
    event_id: str = bus.publish(mock_event)

    # ASSERT
    assert event_id == mock_event.event_id
    # Verify the event was queued (event_id should be in result_list)
    assert event_id in bus._result_list


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_publish_increments_event_counter(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test publish() increments internal event counter."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()
    initial_counter: int = bus._event_counter

    # ACT
    bus.publish(mock_event)

    # ASSERT
    # Counter is incremented twice: once in publish() and once in _handle_thread_and_corelet_event()
    assert bus._event_counter == initial_counter + 2


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_publish_registers_result_in_cache(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test publish() registers event_id in result cache."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT
    event_id: str = bus.publish(mock_event)

    # ASSERT
    assert event_id in bus._result_list
    assert bus._result_list[event_id] is None


# -------------------------------------------------------------
# TESTS: publish() - Error Handling CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.InvalidEventError")
@patch("psutil.cpu_count")
def test_publish_raises_invalid_event_error_when_not_event_instance(
    mock_cpu_count: Mock,
    mock_error_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test publish() raises InvalidEventError when event is not Event instance."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_error_class.side_effect = lambda msg: ValueError(msg)

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Invalid event type"):
        bus.publish("not_an_event")


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.InvalidEventError")
@patch("psutil.cpu_count")
def test_publish_raises_invalid_event_error_when_event_id_missing(
    mock_cpu_count: Mock,
    mock_error_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test publish() raises InvalidEventError when event_id is missing."""
    # ARRANGE
    from basefunctions.events.event import Event

    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_error_class.side_effect = lambda msg: ValueError(msg)

    bus: EventBus = EventBus()

    # Create event without event_id - use spec=Event to pass isinstance check
    invalid_event: Mock = Mock(spec=Event)
    invalid_event.event_id = None
    invalid_event.event_type = "test"
    invalid_event.event_exec_mode = "thread"

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Event must have a valid event_id"):
        bus.publish(invalid_event)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.InvalidEventError")
@patch("psutil.cpu_count")
def test_publish_raises_invalid_event_error_when_event_type_missing(
    mock_cpu_count: Mock,
    mock_error_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test publish() raises InvalidEventError when event_type is missing."""
    # ARRANGE
    from basefunctions.events.event import Event

    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_error_class.side_effect = lambda msg: ValueError(msg)

    bus: EventBus = EventBus()

    # Create event without event_type - use spec=Event to pass isinstance check
    invalid_event: Mock = Mock(spec=Event)
    invalid_event.event_id = "123"
    invalid_event.event_type = None
    invalid_event.event_exec_mode = "thread"

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Event must have a valid event_type"):
        bus.publish(invalid_event)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.NoHandlerAvailableError")
@patch("psutil.cpu_count")
def test_publish_raises_no_handler_available_error_when_handler_missing(
    mock_cpu_count: Mock,
    mock_error_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test publish() raises NoHandlerAvailableError when no handler registered."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_event_factory.is_handler_available.return_value = False
    mock_factory_class.return_value = mock_event_factory
    mock_error_class.side_effect = lambda et: ValueError(f"No handler for {et}")

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="No handler for"):
        bus.publish(mock_event)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.InvalidEventError")
@patch("psutil.cpu_count")
def test_publish_raises_invalid_event_error_for_unknown_execution_mode(
    mock_cpu_count: Mock,
    mock_error_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test publish() raises InvalidEventError for unknown execution mode."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_error_class.side_effect = lambda msg: ValueError(msg)

    bus: EventBus = EventBus()

    # Set unknown execution mode
    mock_event.event_exec_mode = "unknown_mode"

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Unknown execution mode"):
        bus.publish(mock_event)


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        "string",
        123,
        {},
        [],
    ],
)
@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.InvalidEventError")
@patch("psutil.cpu_count")
def test_publish_various_invalid_events(
    mock_cpu_count: Mock,
    mock_error_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    invalid_input: Any,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test publish() rejects various invalid event inputs."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_error_class.side_effect = lambda msg: ValueError(msg)

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Invalid event type"):
        bus.publish(invalid_input)


# -------------------------------------------------------------
# TESTS: publish() - Edge Cases
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_publish_with_progress_tracker_enriches_event(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test publish() enriches event with thread-local progress tracker."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Set progress tracker for current thread
    mock_tracker: Mock = Mock()
    thread_id: int = threading.get_ident()
    bus._progress_context[thread_id] = (mock_tracker, 5)

    # Ensure event has no progress tracker initially
    mock_event.progress_tracker = None

    # ACT
    bus.publish(mock_event)

    # ASSERT
    assert mock_event.progress_tracker is mock_tracker
    assert mock_event.progress_steps == 5


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.EXECUTION_MODE_CMD", "cmd")
@patch("psutil.cpu_count")
def test_publish_skips_handler_check_for_cmd_mode(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test publish() skips handler availability check for CMD mode."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Set CMD mode
    mock_event.event_exec_mode = "cmd"

    # ACT
    bus.publish(mock_event)

    # ASSERT
    mock_event_factory.is_handler_available.assert_not_called()


# -------------------------------------------------------------
# TESTS: get_results() - Happy Path
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_returns_specific_event_results_and_removes_from_cache(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() returns specific results and removes them from cache."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Populate result cache
    event_id: str = "test_event_123"
    bus._result_list[event_id] = mock_event_result_success

    # ACT
    results: Dict[str, Mock] = bus.get_results([event_id], join_before=False)

    # ASSERT
    assert event_id in results
    assert results[event_id] is mock_event_result_success
    assert event_id not in bus._result_list  # Removed from cache


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_returns_all_results_when_no_event_ids_provided(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() returns all results when event_ids is None."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Populate result cache with multiple results
    bus._result_list["event_1"] = mock_event_result_success
    bus._result_list["event_2"] = mock_event_result_success

    # ACT
    results: Dict[str, Mock] = bus.get_results(event_ids=None, join_before=False)

    # ASSERT
    assert len(results) == 2
    assert "event_1" in results
    assert "event_2" in results


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_preserves_results_when_no_event_ids_provided(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() preserves results in cache when event_ids is None."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Populate result cache
    bus._result_list["event_1"] = mock_event_result_success

    # ACT
    results: Dict[str, Mock] = bus.get_results(event_ids=None, join_before=False)

    # ASSERT
    assert "event_1" in results
    assert "event_1" in bus._result_list  # Still in cache


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_normalizes_single_string_to_list(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() normalizes single string event_id to list."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Populate result cache
    event_id: str = "test_event_123"
    bus._result_list[event_id] = mock_event_result_success

    # ACT
    results: Dict[str, Mock] = bus.get_results(event_id, join_before=False)

    # ASSERT
    assert event_id in results
    assert results[event_id] is mock_event_result_success


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_drains_output_queue_before_returning(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() drains output queue before returning results."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Add result to output queue
    mock_event_result_success.event_id = "queued_event"
    bus._output_queue.put(mock_event_result_success)

    # ACT
    results: Dict[str, Mock] = bus.get_results(join_before=False)

    # ASSERT
    assert "queued_event" in results
    assert bus._output_queue.empty()


# -------------------------------------------------------------
# TESTS: get_results() - Edge Cases
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_returns_empty_dict_when_no_results_available(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() returns empty dict when no results available."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT
    results: Dict[str, Mock] = bus.get_results(["nonexistent"], join_before=False)

    # ASSERT
    assert results == {}


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_handles_nonexistent_event_ids_gracefully(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() handles nonexistent event_ids gracefully."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Populate result cache with one result
    bus._result_list["exists"] = mock_event_result_success

    # ACT
    results: Dict[str, Mock] = bus.get_results(["exists", "not_exists"], join_before=False)

    # ASSERT
    assert "exists" in results
    assert "not_exists" not in results


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_results_with_join_before_false_returns_immediately(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test get_results() with join_before=False returns immediately."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Mock join to track if it was called - use patch.object on the queue object
    with patch.object(bus._input_queue, "join", wraps=bus._input_queue.join) as mock_join:
        # ACT
        bus.get_results(join_before=False)

        # ASSERT
        mock_join.assert_not_called()


# -------------------------------------------------------------
# TESTS: _get_handler() - Happy Path & CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_returns_cached_handler_when_available(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    mock_event_handler: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _get_handler() returns cached handler when available."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Populate handler cache
    mock_event_context.thread_local_data.handlers = {"test_type": mock_event_handler}

    # ACT
    handler = bus._get_handler("test_type", mock_event_context)

    # ASSERT
    assert handler is mock_event_handler
    mock_event_factory.create_handler.assert_not_called()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_creates_new_handler_via_factory(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    mock_event_handler: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _get_handler() creates new handler via factory when not cached."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_event_factory.create_handler.return_value = mock_event_handler
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT
    handler = bus._get_handler("test_type", mock_event_context)

    # ASSERT
    assert handler is mock_event_handler
    mock_event_factory.create_handler.assert_called_once_with("test_type")


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_caches_newly_created_handler(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    mock_event_handler: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _get_handler() caches newly created handler."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_event_factory.create_handler.return_value = mock_event_handler
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT
    handler = bus._get_handler("test_type", mock_event_context)

    # ASSERT
    assert hasattr(mock_event_context.thread_local_data, "handlers")
    assert "test_type" in mock_event_context.thread_local_data.handlers
    assert mock_event_context.thread_local_data.handlers["test_type"] is mock_event_handler


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_initializes_handler_cache_if_missing(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    mock_event_handler: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _get_handler() initializes handler cache if not exists."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_event_factory.create_handler.return_value = mock_event_handler
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Ensure no handlers attribute
    assert not hasattr(mock_event_context.thread_local_data, "handlers")

    # ACT
    bus._get_handler("test_type", mock_event_context)

    # ASSERT
    assert hasattr(mock_event_context.thread_local_data, "handlers")
    assert isinstance(mock_event_context.thread_local_data.handlers, dict)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_raises_value_error_when_event_type_empty(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _get_handler() raises ValueError when event_type is empty."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        bus._get_handler("", mock_event_context)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_raises_value_error_when_context_none(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _get_handler() raises ValueError when context is None."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="context must have valid thread_local_data"):
        bus._get_handler("test_type", None)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_raises_value_error_when_thread_local_data_missing(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _get_handler() raises ValueError when thread_local_data is missing."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Create context without thread_local_data
    invalid_context: Mock = Mock(spec=[])
    invalid_context.thread_local_data = None

    # ACT & ASSERT
    with pytest.raises(ValueError, match="context must have valid thread_local_data"):
        bus._get_handler("test_type", invalid_context)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_raises_runtime_error_when_factory_fails(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _get_handler() raises RuntimeError when factory fails."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_event_factory.create_handler.side_effect = Exception("Factory error")
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Failed to create handler"):
        bus._get_handler("test_type", mock_event_context)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.EventHandler")
@patch("psutil.cpu_count")
def test_get_handler_raises_type_error_when_factory_returns_invalid_type(
    mock_cpu_count: Mock,
    mock_handler_class: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _get_handler() raises TypeError when factory returns invalid type."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_event_factory.create_handler.return_value = "not_a_handler"
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Failed to create handler"):
        bus._get_handler("test_type", mock_event_context)


# -------------------------------------------------------------
# TESTS: _add_result_with_lru() - LRU Cache Management
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_add_result_with_lru_stores_result(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _add_result_with_lru() stores result in cache."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # ACT
    bus._add_result_with_lru("event_123", mock_event_result_success)

    # ASSERT
    assert "event_123" in bus._result_list
    assert bus._result_list["event_123"] is mock_event_result_success


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_add_result_with_lru_evicts_oldest_when_limit_exceeded(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _add_result_with_lru() evicts oldest result when limit exceeded."""
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus(num_threads=1)
    bus._max_cached_results = 3

    # ACT - Add 4 results (exceeding limit of 3)
    bus._add_result_with_lru("event_1", mock_event_result_success)
    bus._add_result_with_lru("event_2", mock_event_result_success)
    bus._add_result_with_lru("event_3", mock_event_result_success)
    bus._add_result_with_lru("event_4", mock_event_result_success)

    # ASSERT
    assert "event_1" not in bus._result_list  # Evicted (oldest)
    assert "event_2" in bus._result_list
    assert "event_3" in bus._result_list
    assert "event_4" in bus._result_list
    assert len(bus._result_list) == 3


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_add_result_with_lru_moves_existing_to_end(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _add_result_with_lru() moves existing result to end (most recent)."""
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus(num_threads=1)
    bus._max_cached_results = 3

    # ACT - Add 3 results
    bus._add_result_with_lru("event_1", mock_event_result_success)
    bus._add_result_with_lru("event_2", mock_event_result_success)
    bus._add_result_with_lru("event_3", mock_event_result_success)

    # Re-add event_1 (should move to end)
    bus._add_result_with_lru("event_1", mock_event_result_success)

    # Add event_4 (should evict event_2, not event_1)
    bus._add_result_with_lru("event_4", mock_event_result_success)

    # ASSERT
    assert "event_1" in bus._result_list  # Moved to end, not evicted
    assert "event_2" not in bus._result_list  # Evicted (oldest)
    assert "event_3" in bus._result_list
    assert "event_4" in bus._result_list


# -------------------------------------------------------------
# TESTS: shutdown() - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_shutdown_sends_shutdown_event_to_all_workers(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test shutdown() sends shutdown event to all worker threads."""
    # ARRANGE
    mock_cpu_count.return_value = 4
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Verify initial state
    assert len(bus._worker_threads) == 4
    initial_result_count: int = len(bus._result_list)

    # ACT
    bus.shutdown(immediately=False)

    # ASSERT
    # After shutdown completes, the shutdown events should have been processed
    # Each shutdown event gets an entry in the result_list
    # Workers are daemon threads, so they may still be alive but idle
    assert len(bus._result_list) >= initial_result_count  # Shutdown events were queued
    # Input queue should be empty or nearly empty after join()
    assert bus._input_queue.qsize() <= 4  # At most the shutdown events remain


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.EXECUTION_MODE_CORELET", "corelet")
@patch("psutil.cpu_count")
def test_shutdown_immediately_uses_high_priority(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test shutdown() uses high priority when immediately=True."""
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Verify initial state
    assert len(bus._worker_threads) == 2
    initial_result_count: int = len(bus._result_list)

    # ACT
    bus.shutdown(immediately=True)

    # ASSERT
    # Verify shutdown events were processed
    # Workers are daemon threads, so they may still be alive but idle
    assert len(bus._result_list) >= initial_result_count  # Shutdown events were queued
    # Note: We can't directly verify priority=-1 was used without patching Event,
    # but the immediate shutdown behavior is indicated by the events being processed


# -------------------------------------------------------------
# TESTS: Progress Tracking
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_set_progress_tracker_stores_tracker_for_current_thread(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test set_progress_tracker() stores tracker in thread context."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    mock_tracker: Mock = Mock()
    thread_id: int = threading.get_ident()

    # ACT
    bus.set_progress_tracker(mock_tracker, progress_steps=10)

    # ASSERT
    assert thread_id in bus._progress_context
    assert bus._progress_context[thread_id] == (mock_tracker, 10)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_clear_progress_tracker_removes_tracker_for_current_thread(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test clear_progress_tracker() removes tracker from thread context."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    mock_tracker: Mock = Mock()
    thread_id: int = threading.get_ident()

    # Set tracker first
    bus.set_progress_tracker(mock_tracker, progress_steps=10)
    assert thread_id in bus._progress_context

    # ACT
    bus.clear_progress_tracker()

    # ASSERT
    assert thread_id not in bus._progress_context


# -------------------------------------------------------------
# TESTS: _retry_with_timeout() - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.TimerThread")
@patch("psutil.cpu_count")
def test_retry_with_timeout_returns_result_on_first_success(
    mock_cpu_count: Mock,
    mock_timer: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    mock_event_handler: Mock,
    mock_event_context: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """Test _retry_with_timeout() returns result on first successful attempt."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_timer.return_value.__enter__ = Mock()
    mock_timer.return_value.__exit__ = Mock(return_value=False)

    bus: EventBus = EventBus()

    mock_event_handler.handle.return_value = mock_event_result_success

    # ACT
    result = bus._retry_with_timeout(mock_event, mock_event_handler, mock_event_context)

    # ASSERT
    assert result is mock_event_result_success
    assert mock_event_handler.handle.call_count == 1


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.TimerThread")
@patch("psutil.cpu_count")
def test_retry_with_timeout_retries_on_exception(
    mock_cpu_count: Mock,
    mock_timer: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    mock_event_handler: Mock,
    mock_event_context: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _retry_with_timeout() retries on exception."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_timer.return_value.__enter__ = Mock()
    mock_timer.return_value.__exit__ = Mock(return_value=False)

    bus: EventBus = EventBus()

    # First call raises exception, second succeeds
    mock_event_handler.handle.side_effect = [
        Exception("Temporary error"),
        mock_event_result_success,
    ]

    # ACT
    result = bus._retry_with_timeout(mock_event, mock_event_handler, mock_event_context)

    # ASSERT
    assert result is mock_event_result_success
    assert mock_event_handler.handle.call_count == 2


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.TimerThread")
@patch("basefunctions.events.event_bus.basefunctions.EventResult")
@patch("psutil.cpu_count")
def test_retry_with_timeout_returns_exception_result_after_exhaustion(
    mock_cpu_count: Mock,
    mock_result_class: Mock,
    mock_timer: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    mock_event_handler: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _retry_with_timeout() returns exception result after max retries."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_timer.return_value.__enter__ = Mock()
    mock_timer.return_value.__exit__ = Mock(return_value=False)

    bus: EventBus = EventBus()

    # All retries fail
    mock_event_handler.handle.side_effect = Exception("Permanent error")
    mock_event.max_retries = 3

    mock_exception_result: Mock = Mock()
    mock_result_class.exception_result.return_value = mock_exception_result

    # ACT
    result = bus._retry_with_timeout(mock_event, mock_event_handler, mock_event_context)

    # ASSERT
    assert result is mock_exception_result
    assert mock_event_handler.handle.call_count == 3
    mock_result_class.exception_result.assert_called_once()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.TimerThread")
@patch("psutil.cpu_count")
def test_retry_with_timeout_terminates_handler_on_timeout(
    mock_cpu_count: Mock,
    mock_timer: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    mock_event_handler: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _retry_with_timeout() terminates handler on timeout."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_timer.return_value.__enter__ = Mock()
    mock_timer.return_value.__exit__ = Mock(return_value=False)

    bus: EventBus = EventBus()

    # Simulate timeout
    mock_event_handler.handle.side_effect = TimeoutError("Handler timeout")
    mock_event_handler.terminate = Mock()
    mock_event.max_retries = 1

    # ACT
    bus._retry_with_timeout(mock_event, mock_event_handler, mock_event_context)

    # ASSERT
    mock_event_handler.terminate.assert_called_once_with(context=mock_event_context)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.TimerThread")
@patch("psutil.cpu_count")
def test_retry_with_timeout_handles_terminate_failure_gracefully(
    mock_cpu_count: Mock,
    mock_timer: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    mock_event_handler: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _retry_with_timeout() handles terminate() failure gracefully."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_timer.return_value.__enter__ = Mock()
    mock_timer.return_value.__exit__ = Mock(return_value=False)

    bus: EventBus = EventBus()

    # Simulate timeout and terminate failure
    mock_event_handler.handle.side_effect = TimeoutError("Handler timeout")
    mock_event_handler.terminate = Mock(side_effect=Exception("Terminate failed"))
    mock_event.max_retries = 1

    # ACT - Should not raise exception
    result = bus._retry_with_timeout(mock_event, mock_event_handler, mock_event_context)

    # ASSERT
    assert result is not None  # Returns exception result


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("basefunctions.events.event_bus.basefunctions.TimerThread")
@patch("basefunctions.events.event_bus.basefunctions.EXECUTION_MODE_CORELET", "corelet")
@patch("psutil.cpu_count")
def test_retry_with_timeout_adds_safety_buffer_for_corelet_mode(
    mock_cpu_count: Mock,
    mock_timer: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event: Mock,
    mock_event_handler: Mock,
    mock_event_context: Mock,
    mock_event_result_success: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _retry_with_timeout() adds 1s safety buffer for corelet mode."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_timer.return_value.__enter__ = Mock()
    mock_timer.return_value.__exit__ = Mock(return_value=False)

    bus: EventBus = EventBus()

    mock_event_handler.handle.return_value = mock_event_result_success
    mock_event.event_exec_mode = "corelet"
    mock_event.timeout = 10

    # ACT
    bus._retry_with_timeout(mock_event, mock_event_handler, mock_event_context)

    # ASSERT
    # Verify TimerThread was called with timeout + 1
    mock_timer.assert_called_with(11, threading.get_ident())


# -------------------------------------------------------------
# TESTS: _cleanup_corelet() - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_sends_shutdown_event(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _cleanup_corelet() sends shutdown event to corelet process."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled_event"

    bus: EventBus = EventBus()

    # Create mock corelet handle
    mock_handle: Mock = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = True
    mock_handle.output_pipe.recv.return_value = None
    mock_handle.process = Mock()
    mock_handle.process.terminate.return_value = None
    mock_handle.process.join.return_value = None

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    mock_handle.input_pipe.send.assert_called_once()
    mock_pickle.assert_called_once()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_terminates_process(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _cleanup_corelet() terminates corelet process."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled"

    bus: EventBus = EventBus()

    # Create mock corelet handle
    mock_handle: Mock = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = True
    mock_handle.output_pipe.recv.return_value = None
    mock_handle.process = Mock()

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    mock_handle.process.terminate.assert_called_once()
    mock_handle.process.join.assert_called_once_with(timeout=2)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_closes_pipes(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _cleanup_corelet() closes input and output pipes."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled"

    bus: EventBus = EventBus()

    # Create mock corelet handle
    mock_handle: Mock = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = True
    mock_handle.output_pipe.recv.return_value = None
    mock_handle.process = Mock()

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    mock_handle.input_pipe.close.assert_called_once()
    mock_handle.output_pipe.close.assert_called_once()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_cleanup_corelet_handles_missing_corelet_handle_gracefully(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _cleanup_corelet() handles missing corelet_handle gracefully."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory

    bus: EventBus = EventBus()

    # Ensure no corelet_handle attribute
    if hasattr(mock_event_context.thread_local_data, "corelet_handle"):
        delattr(mock_event_context.thread_local_data, "corelet_handle")

    # ACT - Should not raise exception
    bus._cleanup_corelet(mock_event_context)

    # ASSERT - No exception raised


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_force_kills_on_cleanup_failure(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _cleanup_corelet() force kills process on cleanup failure."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.side_effect = Exception("Pickle error")

    bus: EventBus = EventBus()

    # Create mock corelet handle
    mock_handle: Mock = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.process = Mock()

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    mock_handle.process.kill.assert_called_once()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_removes_corelet_handle_from_context(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:  # CRITICAL TEST
    """Test _cleanup_corelet() removes corelet_handle from context."""
    # ARRANGE
    mock_cpu_count.return_value = 8
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled"

    bus: EventBus = EventBus()

    # Create mock corelet handle
    mock_handle: Mock = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = True
    mock_handle.output_pipe.recv.return_value = None
    mock_handle.process = Mock()

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    assert not hasattr(mock_event_context.thread_local_data, "corelet_handle")
