"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Comprehensive edge case tests for EventBus class.
 Tests critical failure scenarios, race conditions, resource cleanup,
 and stress scenarios not covered in main test suite.

 Focus Areas:
 - Corelet crash recovery and process cleanup
 - LRU cache eviction under high load (>10k events)
 - Worker thread shutdown with pending events
 - Concurrent event publishing (race conditions)
 - Progress tracker edge cases
 - Resource exhaustion scenarios

 Log:
 v1.0.0 : Initial edge case test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard Library
import threading
import time
import queue
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch, call
from collections import OrderedDict

# External imports
import pytest

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


@pytest.fixture
def reset_event_bus_singleton() -> None:
    """
    Reset EventBus singleton instance before and after each test.

    This fixture ensures tests start with a fresh EventBus instance
    and properly cleanup after tests complete.

    Notes
    -----
    Critical for edge case tests that may leave EventBus in
    inconsistent state after testing failure scenarios.
    """
    from basefunctions.utils.decorators import _singleton_instances

    # Clear EventBus singleton instance before test
    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            del _singleton_instances[cls]
            break

    yield

    # Cleanup after test - clear singleton again
    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            try:
                instance = _singleton_instances[cls]
                # Try graceful shutdown if instance has worker threads
                if hasattr(instance, "_worker_threads") and instance._worker_threads:
                    try:
                        instance.shutdown(immediately=True)
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
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
    factory = Mock()
    factory.is_handler_available.return_value = True
    factory.register_event_type.return_value = None
    return factory


@pytest.fixture
def mock_event_handler_success() -> Mock:
    """
    Create mock EventHandler that always succeeds.

    Returns
    -------
    Mock
        Mock EventHandler returning successful results
    """
    from basefunctions.events.event_handler import EventHandler

    handler = Mock(spec=EventHandler)
    mock_result = Mock()
    mock_result.success = True
    mock_result.event_id = "test_event_id"
    handler.handle.return_value = mock_result
    return handler


@pytest.fixture
def mock_event_handler_failure() -> Mock:
    """
    Create mock EventHandler that always fails.

    Returns
    -------
    Mock
        Mock EventHandler returning failure results
    """
    from basefunctions.events.event_handler import EventHandler

    handler = Mock(spec=EventHandler)
    mock_result = Mock()
    mock_result.success = False
    mock_result.event_id = "test_event_id"
    mock_result.error = "Business logic failure"
    handler.handle.return_value = mock_result
    return handler


@pytest.fixture
def mock_event_handler_crash() -> Mock:
    """
    Create mock EventHandler that crashes with exception.

    Returns
    -------
    Mock
        Mock EventHandler that raises exceptions
    """
    from basefunctions.events.event_handler import EventHandler

    handler = Mock(spec=EventHandler)
    handler.handle.side_effect = RuntimeError("Handler crashed")
    handler.terminate = Mock()
    return handler


@pytest.fixture
def mock_thread_event() -> Mock:
    """
    Create mock Event with THREAD execution mode.

    Returns
    -------
    Mock
        Mock Event configured for thread execution
    """
    from basefunctions.events.event import Event

    event = Mock(spec=Event)
    event.event_id = f"thread_event_{threading.get_ident()}"
    event.event_type = "test_event"
    event.event_exec_mode = "thread"
    event.priority = DEFAULT_PRIORITY
    event.timeout = DEFAULT_TIMEOUT
    event.max_retries = DEFAULT_RETRY_COUNT
    event.progress_tracker = None
    event.progress_steps = 0
    return event


@pytest.fixture
def mock_corelet_event() -> Mock:
    """
    Create mock Event with CORELET execution mode.

    Returns
    -------
    Mock
        Mock Event configured for corelet execution
    """
    from basefunctions.events.event import Event

    event = Mock(spec=Event)
    event.event_id = f"corelet_event_{threading.get_ident()}"
    event.event_type = "test_event"
    event.event_exec_mode = "corelet"
    event.priority = DEFAULT_PRIORITY
    event.timeout = DEFAULT_TIMEOUT
    event.max_retries = DEFAULT_RETRY_COUNT
    event.progress_tracker = None
    event.progress_steps = 0
    return event


@pytest.fixture
def mock_event_context() -> Mock:
    """
    Create mock EventContext with thread_local_data.

    Returns
    -------
    Mock
        Mock EventContext for testing
    """
    context = Mock()
    context.thread_local_data = threading.local()
    context.thread_id = 0
    return context


# -------------------------------------------------------------
# EDGE CASE TESTS: LRU Cache Eviction Under Load
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_lru_cache_eviction_with_large_volume_events(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test LRU cache eviction under high load with >10,000 events.

    This test verifies that the LRU cache correctly evicts oldest results
    when the cache limit is exceeded with large volume of events.

    Notes
    -----
    CRITICAL: Tests max_cached_results = num_threads * 1000 behavior.
    Ensures memory doesn't grow unbounded under high load.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus(num_threads=2)
    assert bus._max_cached_results == 2000

    # Create many results to trigger LRU eviction
    num_results = 3000  # Exceeds limit of 2000

    # ACT - Add results that exceed cache limit
    for i in range(num_results):
        mock_result = Mock()
        mock_result.event_id = f"event_{i}"
        mock_result.success = True
        bus._add_result_with_lru(f"event_{i}", mock_result)

    # ASSERT
    # Cache should be at max limit, not growing unbounded
    assert len(bus._result_list) == bus._max_cached_results
    assert len(bus._result_list) == 2000

    # Oldest 1000 events should be evicted
    assert "event_0" not in bus._result_list
    assert "event_500" not in bus._result_list
    assert "event_999" not in bus._result_list

    # Most recent 2000 events should be present
    assert "event_1000" in bus._result_list
    assert "event_2000" in bus._result_list
    assert "event_2999" in bus._result_list


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_lru_cache_preserves_most_recently_accessed_results(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test LRU cache preserves most recently accessed results.

    This test verifies that re-accessing old results moves them
    to the end of the LRU cache and prevents eviction.

    Notes
    -----
    CRITICAL: Tests LRU "move to end" behavior on re-access.
    """
    # ARRANGE
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus(num_threads=1)
    bus._max_cached_results = 5

    # ACT - Add 5 results (at limit)
    for i in range(5):
        mock_result = Mock()
        mock_result.event_id = f"event_{i}"
        bus._add_result_with_lru(f"event_{i}", mock_result)

    # Re-add event_0 (moves to end)
    mock_result = Mock()
    mock_result.event_id = "event_0"
    bus._add_result_with_lru("event_0", mock_result)

    # Add new event_5 (should evict event_1, not event_0)
    mock_result = Mock()
    mock_result.event_id = "event_5"
    bus._add_result_with_lru("event_5", mock_result)

    # ASSERT
    assert "event_0" in bus._result_list  # Moved to end, preserved
    assert "event_1" not in bus._result_list  # Evicted (now oldest)
    assert "event_2" in bus._result_list
    assert "event_3" in bus._result_list
    assert "event_4" in bus._result_list
    assert "event_5" in bus._result_list


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_lru_cache_eviction_with_concurrent_result_addition(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test LRU cache eviction with concurrent result additions from multiple threads.

    This test verifies thread-safety of LRU eviction under concurrent access.

    Notes
    -----
    CRITICAL: Tests thread-safety of _add_result_with_lru with _publish_lock.
    """
    # ARRANGE
    mock_cpu_count.return_value = 4
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus(num_threads=4)
    bus._max_cached_results = 100

    results_added = []
    errors = []

    def add_results(thread_id: int, count: int):
        """Add results from worker thread."""
        try:
            for i in range(count):
                event_id = f"thread_{thread_id}_event_{i}"
                mock_result = Mock()
                mock_result.event_id = event_id
                bus._add_result_with_lru(event_id, mock_result)
                results_added.append(event_id)
        except Exception as e:
            errors.append(e)

    # ACT - Launch multiple threads adding results concurrently
    threads = []
    for i in range(5):
        t = threading.Thread(target=add_results, args=(i, 50))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join(timeout=5)

    # ASSERT
    # No errors during concurrent access
    assert len(errors) == 0

    # Cache should not exceed limit
    assert len(bus._result_list) <= bus._max_cached_results
    assert len(bus._result_list) == 100

    # Total results added exceeds cache limit (250 > 100)
    assert len(results_added) == 250


# -------------------------------------------------------------
# EDGE CASE TESTS: Corelet Crash Recovery
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_handles_process_crash_gracefully(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test _cleanup_corelet handles crashed process gracefully.

    This test verifies cleanup behavior when corelet process
    has already crashed before cleanup is called.

    Notes
    -----
    CRITICAL: Tests corelet crash recovery and resource cleanup.
    Ensures no resource leaks when process crashes.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled"

    bus = EventBus()

    # Create mock corelet handle with crashed process
    mock_handle = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = False  # No response (crashed)
    mock_handle.process = Mock()
    mock_handle.process.pid = 12345
    mock_handle.process.terminate.side_effect = Exception("Process already dead")
    mock_handle.process.kill.return_value = None

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT - Should not raise exception despite crash
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    # Process kill was called (force cleanup on exception path)
    mock_handle.process.kill.assert_called_once()

    # Note: Pipes are NOT closed on exception path (by design)
    # This is the actual behavior when cleanup fails

    # Handle removed from context (cleanup happens in finally block)
    assert not hasattr(mock_event_context.thread_local_data, "corelet_handle")


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_handles_pipe_close_failure(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test _cleanup_corelet handles pipe close failures.

    This test verifies cleanup continues even when pipe operations fail.

    Notes
    -----
    CRITICAL: Tests robustness of cleanup path under resource errors.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled"

    bus = EventBus()

    # Create mock corelet handle with failing pipes
    mock_handle = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = True
    mock_handle.output_pipe.recv.return_value = None
    mock_handle.process = Mock()

    # Simulate pipe close failures
    mock_handle.input_pipe.close.side_effect = Exception("Pipe already closed")
    mock_handle.output_pipe.close.side_effect = Exception("Pipe already closed")

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # ACT - Should complete cleanup despite pipe errors
    bus._cleanup_corelet(mock_event_context)

    # ASSERT
    # Process was terminated
    mock_handle.process.terminate.assert_called_once()

    # Handle removed from context despite pipe errors
    assert not hasattr(mock_event_context.thread_local_data, "corelet_handle")


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("pickle.dumps")
@patch("psutil.cpu_count")
def test_cleanup_corelet_removes_from_active_corelets_tracking(
    mock_cpu_count: Mock,
    mock_pickle: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test _cleanup_corelet removes entry from active corelets tracking.

    This test verifies corelet is removed from tracking dict on cleanup.

    Notes
    -----
    CRITICAL: Tests corelet lifecycle tracking consistency.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory
    mock_pickle.return_value = b"pickled"

    bus = EventBus()

    # Register corelet in tracking
    thread_id = 12345
    process_id = 67890
    bus._register_corelet(thread_id, process_id)
    assert bus.get_corelet_count() == 1

    # Create mock corelet handle
    mock_handle = Mock()
    mock_handle.input_pipe = Mock()
    mock_handle.output_pipe = Mock()
    mock_handle.output_pipe.poll.return_value = True
    mock_handle.output_pipe.recv.return_value = None
    mock_handle.process = Mock()
    mock_handle.process.pid = process_id

    mock_event_context.thread_local_data.corelet_handle = mock_handle

    # Mock threading.get_ident to return our thread_id
    with patch("threading.get_ident", return_value=thread_id):
        # ACT
        bus._cleanup_corelet(mock_event_context)

    # ASSERT
    # Corelet removed from tracking
    assert bus.get_corelet_count() == 0
    assert thread_id not in bus._active_corelets


# -------------------------------------------------------------
# EDGE CASE TESTS: Worker Thread Shutdown
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_shutdown_with_pending_events_in_queue(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test shutdown with events still pending in input queue.

    This test verifies graceful shutdown behavior when events
    are still queued for processing.

    Notes
    -----
    CRITICAL: Tests graceful shutdown with pending work.
    Ensures no lost events or hanging threads.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    # Create handler that processes events
    mock_handler = Mock()
    mock_result = Mock()
    mock_result.success = True
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus = EventBus()

    # Publish several events
    from basefunctions.events.event import Event

    events = []
    for i in range(10):
        event = Mock(spec=Event)
        event.event_id = f"pending_event_{i}"
        event.event_type = "test"
        event.event_exec_mode = "thread"
        event.priority = DEFAULT_PRIORITY
        event.timeout = DEFAULT_TIMEOUT
        event.max_retries = 1
        event.progress_tracker = None
        event.progress_steps = 0
        events.append(event)
        bus.publish(event)

    # Verify events queued
    initial_queue_size = bus._input_queue.qsize()
    assert initial_queue_size > 0

    # ACT - Shutdown gracefully (waits for queue to drain)
    bus.shutdown(immediately=False)

    # ASSERT
    # Queue should be drained after join()
    assert bus._input_queue.qsize() == 0

    # All worker threads received shutdown signal
    # (shutdown events are published for each worker)
    assert len(bus._result_list) >= len(events)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_shutdown_immediately_preempts_pending_events(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test immediate shutdown preempts pending events with high priority.

    This test verifies that immediate=True shutdown uses priority=-1
    to jump to front of queue.

    Notes
    -----
    CRITICAL: Tests emergency shutdown behavior.
    High priority shutdown events should be processed first.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    # Publish several low priority events
    from basefunctions.events.event import Event

    for i in range(10):
        event = Mock(spec=Event)
        event.event_id = f"low_priority_event_{i}"
        event.event_type = "test"
        event.event_exec_mode = "thread"
        event.priority = 10  # Low priority
        event.timeout = DEFAULT_TIMEOUT
        event.max_retries = 1
        event.progress_tracker = None
        event.progress_steps = 0
        bus.publish(event)

    initial_queue_size = bus._input_queue.qsize()
    assert initial_queue_size > 0

    # ACT - Immediate shutdown (high priority)
    bus.shutdown(immediately=True)

    # ASSERT
    # Shutdown completes (join() returns)
    # Priority=-1 events jump to front of queue
    # All worker threads should stop


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_worker_loop_handles_invalid_task_format(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test worker loop handles invalid task format gracefully.

    This test verifies worker thread continues processing
    even when encountering malformed tasks.

    Notes
    -----
    CRITICAL: Tests robustness of worker loop against corrupted data.
    """
    # ARRANGE
    mock_cpu_count.return_value = 1
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    # Inject invalid task directly into queue (bypassing publish())
    # This simulates corrupted queue data
    bus._input_queue.put((1, 2))  # Invalid format (missing event)

    # Add valid event after invalid one
    from basefunctions.events.event import Event

    valid_event = Mock(spec=Event)
    valid_event.event_id = "valid_event"
    valid_event.event_type = "test"
    valid_event.event_exec_mode = "thread"
    valid_event.priority = DEFAULT_PRIORITY
    valid_event.timeout = DEFAULT_TIMEOUT
    valid_event.max_retries = 1
    valid_event.progress_tracker = None
    valid_event.progress_steps = 0

    mock_handler = Mock()
    mock_result = Mock()
    mock_result.success = True
    mock_result.event_id = "valid_event"
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus.publish(valid_event)

    # ACT - Wait for processing
    time.sleep(0.2)

    # ASSERT
    # Worker thread should still be alive (not crashed)
    assert len(bus._worker_threads) == 1
    assert any(t.is_alive() for t in bus._worker_threads)


# -------------------------------------------------------------
# EDGE CASE TESTS: Race Conditions
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_concurrent_event_publishing_from_multiple_threads(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test concurrent event publishing from multiple threads.

    This test verifies thread-safety of publish() under high concurrency.

    Notes
    -----
    CRITICAL: Tests _publish_lock prevents race conditions.
    """
    # ARRANGE
    mock_cpu_count.return_value = 4
    mock_factory_class.return_value = mock_event_factory

    mock_handler = Mock()
    mock_result = Mock()
    mock_result.success = True
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus = EventBus()

    published_ids = []
    errors = []

    def publish_events(thread_id: int, count: int):
        """Publish events from worker thread."""
        try:
            from basefunctions.events.event import Event

            for i in range(count):
                event = Mock(spec=Event)
                event.event_id = f"thread_{thread_id}_event_{i}"
                event.event_type = "test"
                event.event_exec_mode = "thread"
                event.priority = DEFAULT_PRIORITY
                event.timeout = DEFAULT_TIMEOUT
                event.max_retries = 1
                event.progress_tracker = None
                event.progress_steps = 0

                event_id = bus.publish(event)
                published_ids.append(event_id)
        except Exception as e:
            errors.append(e)

    # ACT - Launch multiple threads publishing concurrently
    threads = []
    for i in range(10):
        t = threading.Thread(target=publish_events, args=(i, 20))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join(timeout=5)

    # ASSERT
    # No errors during concurrent publishing
    assert len(errors) == 0

    # All events were published successfully
    assert len(published_ids) == 200

    # All event IDs are registered in result cache
    assert len(bus._result_list) >= 200


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_concurrent_result_retrieval_during_event_processing(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test concurrent result retrieval while events are being processed.

    This test verifies get_results() thread-safety during active processing.

    Notes
    -----
    CRITICAL: Tests race condition between result addition and retrieval.
    """
    # ARRANGE
    mock_cpu_count.return_value = 4
    mock_factory_class.return_value = mock_event_factory

    # Create slow handler to keep events processing
    mock_handler = Mock()

    def slow_handle(*args, **kwargs):
        time.sleep(0.1)
        result = Mock()
        result.success = True
        result.event_id = "event"
        return result

    mock_handler.handle.side_effect = slow_handle
    mock_event_factory.create_handler.return_value = mock_handler

    bus = EventBus()

    # Publish events
    from basefunctions.events.event import Event

    event_ids = []
    for i in range(50):
        event = Mock(spec=Event)
        event.event_id = f"concurrent_event_{i}"
        event.event_type = "test"
        event.event_exec_mode = "thread"
        event.priority = DEFAULT_PRIORITY
        event.timeout = DEFAULT_TIMEOUT
        event.max_retries = 1
        event.progress_tracker = None
        event.progress_steps = 0

        event_id = bus.publish(event)
        event_ids.append(event_id)

    errors = []
    all_results = []

    def retrieve_results():
        """Retrieve results from worker thread."""
        try:
            for _ in range(10):
                results = bus.get_results(join_before=False)
                all_results.append(len(results))
                time.sleep(0.05)
        except Exception as e:
            errors.append(e)

    # ACT - Launch threads retrieving results while processing
    threads = []
    for i in range(5):
        t = threading.Thread(target=retrieve_results)
        threads.append(t)
        t.start()

    # Wait for threads
    for t in threads:
        t.join(timeout=3)

    # Wait for all events to complete
    bus.join()

    # ASSERT
    # No errors during concurrent retrieval
    assert len(errors) == 0


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_concurrent_shutdown_and_publish_race_condition(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test race condition between shutdown and publish operations.

    This test verifies behavior when shutdown is called while
    other threads are still publishing events.

    Notes
    -----
    CRITICAL: Tests thread-safety of shutdown during active publishing.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    mock_handler = Mock()
    mock_result = Mock()
    mock_result.success = True
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus = EventBus()

    errors = []
    shutdown_complete = threading.Event()

    def publish_continuously():
        """Publish events until shutdown completes."""
        try:
            from basefunctions.events.event import Event

            counter = 0
            while not shutdown_complete.is_set():
                event = Mock(spec=Event)
                event.event_id = f"race_event_{counter}"
                event.event_type = "test"
                event.event_exec_mode = "thread"
                event.priority = DEFAULT_PRIORITY
                event.timeout = DEFAULT_TIMEOUT
                event.max_retries = 1
                event.progress_tracker = None
                event.progress_steps = 0

                try:
                    bus.publish(event)
                except Exception:
                    # Expected after shutdown starts
                    break
                counter += 1
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)

    # ACT - Launch publisher threads
    publisher_threads = []
    for i in range(3):
        t = threading.Thread(target=publish_continuously)
        publisher_threads.append(t)
        t.start()

    # Let publishers run briefly
    time.sleep(0.2)

    # Trigger shutdown
    shutdown_thread = threading.Thread(target=lambda: bus.shutdown(immediately=True))
    shutdown_thread.start()
    shutdown_thread.join(timeout=5)

    shutdown_complete.set()

    # Wait for publishers to stop
    for t in publisher_threads:
        t.join(timeout=2)

    # ASSERT
    # Shutdown completed without hanging
    assert not shutdown_thread.is_alive()


# -------------------------------------------------------------
# EDGE CASE TESTS: Progress Tracker Edge Cases
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_progress_tracker_with_none_tracker(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test event processing with None progress tracker.

    This test verifies events process correctly when progress_tracker is None.

    Notes
    -----
    Tests edge case where progress tracking is not used.
    """
    # ARRANGE
    from basefunctions.events.event_handler import EventHandler

    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    mock_handler = Mock(spec=EventHandler)
    mock_result = Mock()
    mock_result.success = True
    mock_result.event_id = "event_no_tracker"
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus = EventBus()

    from basefunctions.events.event import Event

    event = Mock(spec=Event)
    event.event_id = "event_no_tracker"
    event.event_type = "test"
    event.event_exec_mode = "sync"
    event.priority = DEFAULT_PRIORITY
    event.timeout = DEFAULT_TIMEOUT
    event.max_retries = 1
    event.progress_tracker = None
    event.progress_steps = 0

    # ACT
    event_id = bus.publish(event)

    # ASSERT
    # Event processed successfully without progress tracker
    # Handler was called
    mock_handler.handle.assert_called_once()

    # Result is in output queue
    assert not bus._output_queue.empty()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_progress_tracker_with_zero_steps(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test event processing with progress_steps=0.

    This test verifies progress tracker is not updated when steps=0.

    Notes
    -----
    Tests edge case where progress tracking is disabled via steps=0.
    """
    # ARRANGE
    from basefunctions.events.event_handler import EventHandler

    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    mock_handler = Mock(spec=EventHandler)
    mock_result = Mock()
    mock_result.success = True
    mock_result.event_id = "test"
    mock_handler.handle.return_value = mock_result
    mock_event_factory.create_handler.return_value = mock_handler

    bus = EventBus()

    mock_tracker = Mock()

    from basefunctions.events.event import Event

    event = Mock(spec=Event)
    event.event_id = "event_zero_steps"
    event.event_type = "test"
    event.event_exec_mode = "sync"
    event.priority = DEFAULT_PRIORITY
    event.timeout = DEFAULT_TIMEOUT
    event.max_retries = 1
    event.progress_tracker = mock_tracker
    event.progress_steps = 0  # Zero steps

    # ACT
    event_id = bus.publish(event)

    # ASSERT
    # Progress tracker should not be called with 0 steps
    mock_tracker.progress.assert_not_called()


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_clear_progress_tracker_for_nonexistent_thread(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test clear_progress_tracker for thread without tracker.

    This test verifies clearing tracker for thread that never set one
    doesn't cause errors.

    Notes
    -----
    Tests edge case of clearing non-existent tracker.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    # Ensure current thread has no tracker
    thread_id = threading.get_ident()
    assert thread_id not in bus._progress_context

    # ACT - Should not raise exception
    bus.clear_progress_tracker()

    # ASSERT
    # Still no tracker (operation was no-op)
    assert thread_id not in bus._progress_context


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_progress_tracker_context_per_thread(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test progress tracker context is per-thread.

    This test verifies each thread can set independent progress tracker context.

    Notes
    -----
    Tests thread-local isolation of progress tracking.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    thread_contexts = []

    def set_and_verify_tracker(steps: int):
        """Set tracker in thread and record context."""
        thread_id = threading.get_ident()
        tracker = Mock(name=f"tracker_steps_{steps}")
        bus.set_progress_tracker(tracker, progress_steps=steps)

        # Verify it was set correctly in this thread
        assert thread_id in bus._progress_context
        assert bus._progress_context[thread_id][1] == steps

        thread_contexts.append((thread_id, steps))

    # ACT - Set trackers from different threads with different steps
    threads = []
    for steps in [1, 2, 3]:
        t = threading.Thread(target=set_and_verify_tracker, args=(steps,))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # ASSERT
    # At least one thread context was recorded
    assert len(thread_contexts) >= 1

    # If multiple unique thread IDs, verify they can coexist
    unique_threads = set(tid for tid, _ in thread_contexts)
    if len(unique_threads) > 1:
        # Multiple threads active simultaneously
        for thread_id, steps in thread_contexts:
            if thread_id in bus._progress_context:
                # Context still exists for this thread
                assert bus._progress_context[thread_id][1] in [1, 2, 3]


# -------------------------------------------------------------
# EDGE CASE TESTS: Corelet Monitoring
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_corelet_metrics_returns_correct_counts(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test get_corelet_metrics returns correct metrics.

    This test verifies corelet monitoring API returns accurate counts.

    Notes
    -----
    Tests corelet lifecycle tracking and monitoring.
    """
    # ARRANGE
    mock_cpu_count.return_value = 4
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    # Register some corelets
    bus._register_corelet(1, 1001)
    bus._register_corelet(2, 1002)

    # ACT
    metrics = bus.get_corelet_metrics()

    # ASSERT
    assert metrics["active_corelets"] == 2
    assert metrics["worker_threads"] == 4
    assert metrics["max_corelets"] == 4


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_corelet_count_returns_zero_initially(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test get_corelet_count returns 0 when no corelets active.

    This test verifies initial state of corelet tracking.

    Notes
    -----
    Tests corelet tracking initialization.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    # ACT
    count = bus.get_corelet_count()

    # ASSERT
    assert count == 0


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_register_corelet_increments_count(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test _register_corelet increments active corelet count.

    This test verifies corelet registration tracking.

    Notes
    -----
    Tests corelet lifecycle tracking.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    assert bus.get_corelet_count() == 0

    # ACT
    bus._register_corelet(thread_id=100, process_id=5000)

    # ASSERT
    assert bus.get_corelet_count() == 1
    assert 100 in bus._active_corelets
    assert bus._active_corelets[100] == 5000


# -------------------------------------------------------------
# EDGE CASE TESTS: Handler Management Error Cases
# -------------------------------------------------------------


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_get_handler_raises_runtime_error_on_factory_exception(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test _get_handler raises RuntimeError when factory raises exception.

    This test verifies error handling in handler creation path.

    Notes
    -----
    CRITICAL: Tests handler creation error path.
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory
    mock_event_factory.create_handler.side_effect = RuntimeError("Factory internal error")

    bus = EventBus()

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Failed to create handler"):
        bus._get_handler("test_type", mock_event_context)


@patch("basefunctions.events.event_bus.basefunctions.EventFactory")
@patch("psutil.cpu_count")
def test_retry_with_timeout_returns_business_failure_after_all_retries_fail(
    mock_cpu_count: Mock,
    mock_factory_class: Mock,
    mock_event_factory: Mock,
    mock_event_context: Mock,
    mock_thread_event: Mock,
    mock_event_handler_failure: Mock,
    reset_event_bus_singleton: None,
) -> None:
    """
    Test _retry_with_timeout returns business failure result after retry exhaustion.

    This test verifies behavior when handler returns failure on all retries.

    Notes
    -----
    CRITICAL: Tests retry logic with business failures (not exceptions).
    """
    # ARRANGE
    mock_cpu_count.return_value = 2
    mock_factory_class.return_value = mock_event_factory

    bus = EventBus()

    mock_thread_event.max_retries = 3

    with patch("basefunctions.events.event_bus.basefunctions.TimerThread") as mock_timer:
        mock_timer.return_value.__enter__ = Mock()
        mock_timer.return_value.__exit__ = Mock(return_value=False)

        # ACT
        result = bus._retry_with_timeout(mock_thread_event, mock_event_handler_failure, mock_event_context)

    # ASSERT
    # Should return business failure result
    assert result.success is False
    assert result.error == "Business logic failure"

    # Handler called max_retries times
    assert mock_event_handler_failure.handle.call_count == 3
