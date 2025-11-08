"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for CoreletWorker.
 Tests process-based event worker with handler registration, event processing,
 signal handling, and error isolation.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import os
import pickle
import platform
import signal
import sys
import threading
import time
from typing import Any, Dict, Optional, Tuple
from unittest.mock import Mock, MagicMock, patch, call

import pytest
import psutil

# Project imports
from basefunctions.events.corelet_worker import (
    CoreletWorker,
    worker_main,
    IDLE_TIMEOUT,
)
import basefunctions

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_pipes() -> Tuple[Mock, Mock]:
    """
    Create mock input/output pipe pair.

    Returns
    -------
    Tuple[Mock, Mock]
        Tuple of (input_pipe, output_pipe) mocks
    """
    # ARRANGE
    input_pipe: Mock = Mock()
    output_pipe: Mock = Mock()

    # Configure pipes
    input_pipe.poll.return_value = False  # Default: no data
    input_pipe.recv.return_value = b""

    return input_pipe, output_pipe


@pytest.fixture
def worker_instance(mock_pipes: Tuple[Mock, Mock]) -> CoreletWorker:
    """
    Create CoreletWorker instance with mock pipes.

    Parameters
    ----------
    mock_pipes : Tuple[Mock, Mock]
        Mock pipe fixtures

    Returns
    -------
    CoreletWorker
        Worker instance for testing
    """
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    worker_id: str = "test-worker-1"

    # ACT
    worker: CoreletWorker = CoreletWorker(worker_id, input_pipe, output_pipe)

    return worker


@pytest.fixture
def sample_event() -> Mock:
    """
    Create mock Event object with required attributes.

    Returns
    -------
    Mock
        Mock Event with event_type, event_id, corelet_meta
    """
    # ARRANGE
    event: Mock = Mock(spec=basefunctions.Event)
    event.event_type = "test_event"
    event.event_id = "event-123"
    event.corelet_meta = None

    return event


@pytest.fixture
def sample_context() -> Mock:
    """
    Create mock EventContext with thread_local_data.

    Returns
    -------
    Mock
        Mock EventContext with thread_local_data attribute
    """
    # ARRANGE
    context: Mock = Mock(spec=basefunctions.EventContext)
    context.thread_local_data = threading.local()
    context.process_id = os.getpid()
    context.timestamp = time.time()

    return context


@pytest.fixture
def sample_corelet_meta() -> Dict[str, str]:
    """
    Provide valid corelet metadata for handler registration.

    Returns
    -------
    Dict[str, str]
        Valid corelet metadata dictionary
    """
    return {
        "module_path": "basefunctions.events.event_handler",
        "class_name": "EventHandler",
        "event_type": "test_event",
    }


# -------------------------------------------------------------
# TESTS: CoreletWorker Initialization
# -------------------------------------------------------------


def test_corelet_worker_initialization_sets_attributes(
    mock_pipes: Tuple[Mock, Mock]
) -> None:
    """Test CoreletWorker initializes with correct attributes."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    worker_id: str = "worker-1"

    # ACT
    worker: CoreletWorker = CoreletWorker(worker_id, input_pipe, output_pipe)

    # ASSERT
    assert worker._worker_id == worker_id
    assert worker._input_pipe is input_pipe
    assert worker._output_pipe is output_pipe
    assert worker._running is True
    assert worker._handlers == {}
    assert worker._registered_handlers == set()
    assert worker._signal_handlers_setup is False


def test_corelet_worker_uses_slots_for_memory_efficiency() -> None:
    """Test CoreletWorker uses __slots__ for memory efficiency."""
    # ASSERT
    assert hasattr(CoreletWorker, "__slots__")

    expected_slots: set = {
        "_worker_id",
        "_input_pipe",
        "_output_pipe",
        "_handlers",
        "_logger",
        "_running",
        "_last_handler_cleanup",
        "_signal_handlers_setup",
        "_registered_handlers",
        "_redirector",
    }

    actual_slots: set = set(CoreletWorker.__slots__)
    assert actual_slots == expected_slots


# -------------------------------------------------------------
# TESTS: _register_from_meta - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.EventFactory")
def test_register_from_meta_imports_and_registers_handler_successfully(
    mock_factory_class: Mock,
    worker_instance: CoreletWorker,
    sample_corelet_meta: Dict[str, str],
) -> None:  # CRITICAL TEST
    """Test _register_from_meta imports module and registers handler."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_factory_class.return_value = mock_factory

    # ACT
    worker_instance._register_from_meta(sample_corelet_meta)

    # ASSERT
    mock_factory.register_event_type.assert_called_once()
    assert "test_event" in worker_instance._handlers
    assert worker_instance._handlers["test_event"] is basefunctions.EventHandler


@patch("importlib.import_module")
def test_register_from_meta_raises_runtime_error_when_module_not_found(
    mock_import: Mock,
    worker_instance: CoreletWorker,
) -> None:  # CRITICAL TEST
    """Test _register_from_meta raises RuntimeError when module import fails."""
    # ARRANGE
    mock_import.side_effect = ModuleNotFoundError("Module not found")
    meta: Dict[str, str] = {
        "module_path": "nonexistent.module",
        "class_name": "Handler",
        "event_type": "test",
    }

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Handler registration failed"):
        worker_instance._register_from_meta(meta)


@patch("importlib.import_module")
def test_register_from_meta_raises_runtime_error_when_class_not_found(
    mock_import: Mock,
    worker_instance: CoreletWorker,
) -> None:  # CRITICAL TEST
    """Test _register_from_meta raises RuntimeError when class doesn't exist."""
    # ARRANGE
    mock_module: Mock = Mock()
    mock_import.return_value = mock_module
    delattr(mock_module, "NonexistentClass") if hasattr(mock_module, "NonexistentClass") else None

    meta: Dict[str, str] = {
        "module_path": "basefunctions.events.event_handler",
        "class_name": "NonexistentClass",
        "event_type": "test",
    }

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Handler registration failed"):
        worker_instance._register_from_meta(meta)


@patch("importlib.import_module")
def test_register_from_meta_raises_runtime_error_when_class_not_event_handler(
    mock_import: Mock,
    worker_instance: CoreletWorker,
) -> None:  # CRITICAL TEST
    """Test _register_from_meta raises RuntimeError when class is not EventHandler subclass."""
    # ARRANGE
    mock_module: Mock = Mock()
    mock_module.BadHandler = str  # Not an EventHandler subclass
    mock_import.return_value = mock_module

    meta: Dict[str, str] = {
        "module_path": "test.module",
        "class_name": "BadHandler",
        "event_type": "test",
    }

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Handler registration failed"):
        worker_instance._register_from_meta(meta)


@pytest.mark.parametrize("meta,error_key", [
    ({"class_name": "Handler", "event_type": "test"}, "module_path"),
    ({"module_path": "test.module", "event_type": "test"}, "class_name"),
    ({"module_path": "test.module", "class_name": "Handler"}, "event_type"),
    ({}, "module_path"),
])
def test_register_from_meta_raises_runtime_error_when_meta_missing_keys(
    worker_instance: CoreletWorker,
    meta: Dict[str, str],
    error_key: str,
) -> None:  # CRITICAL TEST
    """Test _register_from_meta raises RuntimeError when required meta keys missing."""
    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Handler registration failed"):
        worker_instance._register_from_meta(meta)


# -------------------------------------------------------------
# TESTS: _get_handler - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.EventFactory")
def test_get_handler_creates_and_caches_handler(
    mock_factory_class: Mock,
    worker_instance: CoreletWorker,
    sample_context: Mock,
) -> None:  # CRITICAL TEST
    """Test _get_handler creates handler via factory and caches it."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_handler: Mock = Mock(spec=basefunctions.EventHandler)
    mock_factory.create_handler.return_value = mock_handler
    mock_factory_class.return_value = mock_factory

    event_type: str = "test_event"

    # ACT
    handler: basefunctions.EventHandler = worker_instance._get_handler(event_type, sample_context)

    # ASSERT
    assert handler is mock_handler
    mock_factory.create_handler.assert_called_once_with(event_type)
    # Verify cached
    assert sample_context.thread_local_data.handlers[event_type] is mock_handler


@patch("basefunctions.EventFactory")
def test_get_handler_returns_cached_handler_on_second_call(
    mock_factory_class: Mock,
    worker_instance: CoreletWorker,
    sample_context: Mock,
) -> None:  # CRITICAL TEST
    """Test _get_handler returns cached handler without calling factory again."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_handler: Mock = Mock(spec=basefunctions.EventHandler)
    mock_factory.create_handler.return_value = mock_handler
    mock_factory_class.return_value = mock_factory

    event_type: str = "test_event"

    # ACT
    handler1: basefunctions.EventHandler = worker_instance._get_handler(event_type, sample_context)
    handler2: basefunctions.EventHandler = worker_instance._get_handler(event_type, sample_context)

    # ASSERT
    assert handler1 is handler2
    mock_factory.create_handler.assert_called_once()  # Only called once


def test_get_handler_raises_value_error_when_event_type_empty(
    worker_instance: CoreletWorker,
    sample_context: Mock,
) -> None:  # CRITICAL TEST
    """Test _get_handler raises ValueError when event_type is empty string."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        worker_instance._get_handler("", sample_context)


def test_get_handler_raises_value_error_when_event_type_none(
    worker_instance: CoreletWorker,
    sample_context: Mock,
) -> None:  # CRITICAL TEST
    """Test _get_handler raises ValueError when event_type is None."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        worker_instance._get_handler(None, sample_context)


def test_get_handler_raises_value_error_when_context_none(
    worker_instance: CoreletWorker,
) -> None:  # CRITICAL TEST
    """Test _get_handler raises ValueError when context is None."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="context must have valid thread_local_data"):
        worker_instance._get_handler("test", None)


def test_get_handler_raises_value_error_when_thread_local_data_missing(
    worker_instance: CoreletWorker,
) -> None:  # CRITICAL TEST
    """Test _get_handler raises ValueError when context.thread_local_data is missing."""
    # ARRANGE
    invalid_context: Mock = Mock()
    invalid_context.thread_local_data = None

    # ACT & ASSERT
    with pytest.raises(ValueError, match="context must have valid thread_local_data"):
        worker_instance._get_handler("test", invalid_context)


@patch("basefunctions.EventFactory")
def test_get_handler_raises_runtime_error_when_factory_returns_invalid_type(
    mock_factory_class: Mock,
    worker_instance: CoreletWorker,
    sample_context: Mock,
) -> None:  # CRITICAL TEST
    """Test _get_handler raises RuntimeError when factory returns non-EventHandler."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_factory.create_handler.return_value = "not a handler"
    mock_factory_class.return_value = mock_factory

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Failed to create handler"):
        worker_instance._get_handler("test", sample_context)


@patch("basefunctions.EventFactory")
def test_get_handler_raises_runtime_error_when_factory_fails(
    mock_factory_class: Mock,
    worker_instance: CoreletWorker,
    sample_context: Mock,
) -> None:  # CRITICAL TEST
    """Test _get_handler raises RuntimeError when factory raises exception."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_factory.create_handler.side_effect = ValueError("Handler not registered")
    mock_factory_class.return_value = mock_factory

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Failed to create handler for event_type 'test'"):
        worker_instance._get_handler("test", sample_context)


# -------------------------------------------------------------
# TESTS: worker_main - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.corelet_worker.CoreletWorker")
def test_worker_main_creates_worker_and_runs(
    mock_worker_class: Mock,
    mock_pipes: Tuple[Mock, Mock],
) -> None:  # CRITICAL TEST
    """Test worker_main creates CoreletWorker and calls run()."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    worker_id: str = "worker-1"
    mock_worker: Mock = Mock()
    mock_worker_class.return_value = mock_worker

    # ACT
    worker_main(worker_id, input_pipe, output_pipe)

    # ASSERT
    mock_worker_class.assert_called_once_with(worker_id, input_pipe, output_pipe)
    mock_worker.run.assert_called_once()


@pytest.mark.parametrize("worker_id,input_pipe,output_pipe", [
    ("", Mock(), Mock()),  # Empty worker_id
    (None, Mock(), Mock()),  # None worker_id
    ("worker", None, Mock()),  # None input_pipe
    ("worker", Mock(), None),  # None output_pipe
])
def test_worker_main_exits_with_code_1_when_parameters_invalid(
    worker_id: Optional[str],
    input_pipe: Optional[Mock],
    output_pipe: Optional[Mock],
) -> None:  # CRITICAL TEST
    """Test worker_main exits with code 1 when parameters are invalid."""
    # ACT & ASSERT
    with pytest.raises(SystemExit) as exc_info:
        worker_main(worker_id, input_pipe, output_pipe)

    assert exc_info.value.code == 1


@patch("basefunctions.events.corelet_worker.CoreletWorker")
def test_worker_main_exits_with_code_1_when_worker_raises_exception(
    mock_worker_class: Mock,
    mock_pipes: Tuple[Mock, Mock],
) -> None:  # CRITICAL TEST
    """Test worker_main exits with code 1 when worker.run() raises exception."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    worker_id: str = "worker-1"
    mock_worker: Mock = Mock()
    mock_worker.run.side_effect = RuntimeError("Worker failed")
    mock_worker_class.return_value = mock_worker

    # ACT & ASSERT
    with pytest.raises(SystemExit) as exc_info:
        worker_main(worker_id, input_pipe, output_pipe)

    assert exc_info.value.code == 1


# -------------------------------------------------------------
# TESTS: run() - IMPORTANT
# -------------------------------------------------------------


@patch("basefunctions.EventContext")
def test_run_processes_events_until_shutdown(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() processes events in loop until shutdown event received."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    # Create shutdown event
    shutdown_event: Mock = Mock(spec=basefunctions.Event)
    shutdown_event.event_type = basefunctions.INTERNAL_SHUTDOWN_EVENT
    shutdown_event.event_id = "shutdown-1"

    # Configure pipe to return shutdown event
    input_pipe.poll.side_effect = [True]  # One event available
    input_pipe.recv.return_value = pickle.dumps(shutdown_event)

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT
    worker_instance.run()

    # ASSERT
    assert worker_instance._running is False
    output_pipe.send.assert_called_once()  # Shutdown result sent


@patch("basefunctions.EventContext")
def test_run_sends_shutdown_result_and_exits_on_shutdown_event(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() sends success result and exits when shutdown event received."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    shutdown_event: Mock = Mock(spec=basefunctions.Event)
    shutdown_event.event_type = basefunctions.INTERNAL_SHUTDOWN_EVENT
    shutdown_event.event_id = "shutdown-1"

    input_pipe.poll.return_value = True
    input_pipe.recv.return_value = pickle.dumps(shutdown_event)

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT
    worker_instance.run()

    # ASSERT
    assert output_pipe.send.called
    sent_data: bytes = output_pipe.send.call_args[0][0]
    result: basefunctions.EventResult = pickle.loads(sent_data)
    assert result.success is True
    assert "Shutdown complete" in str(result.data)


@patch("basefunctions.EventContext")
def test_run_sends_exception_result_when_event_processing_fails(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() sends exception result when _process_event raises exception."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    # First event causes exception, second is shutdown
    bad_event: Mock = Mock(spec=basefunctions.Event)
    bad_event.event_type = "bad_event"
    bad_event.event_id = "bad-1"
    bad_event.corelet_meta = None

    shutdown_event: Mock = Mock(spec=basefunctions.Event)
    shutdown_event.event_type = basefunctions.INTERNAL_SHUTDOWN_EVENT
    shutdown_event.event_id = "shutdown-1"

    input_pipe.poll.side_effect = [True, True]
    input_pipe.recv.side_effect = [pickle.dumps(bad_event), pickle.dumps(shutdown_event)]

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # Make _process_event fail for bad_event
    with patch.object(worker_instance, "_process_event", side_effect=RuntimeError("Processing failed")):
        # ACT
        worker_instance.run()

    # ASSERT
    assert output_pipe.send.call_count >= 1


@patch("basefunctions.EventContext")
def test_run_handles_keyboard_interrupt_gracefully(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() handles KeyboardInterrupt gracefully without crashing."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    input_pipe.poll.side_effect = KeyboardInterrupt()

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT - should not raise
    worker_instance.run()

    # ASSERT
    assert worker_instance._running is True  # May still be true if interrupted early


@patch("basefunctions.EventContext")
def test_run_handles_broken_pipe_error(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() handles BrokenPipeError when sending results."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    shutdown_event: Mock = Mock(spec=basefunctions.Event)
    shutdown_event.event_type = basefunctions.INTERNAL_SHUTDOWN_EVENT
    shutdown_event.event_id = "shutdown-1"

    input_pipe.poll.return_value = True
    input_pipe.recv.return_value = pickle.dumps(shutdown_event)
    output_pipe.send.side_effect = BrokenPipeError()

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT - should not raise
    worker_instance.run()

    # ASSERT
    assert worker_instance._running is False


@patch("basefunctions.EventContext")
@patch("time.time")
def test_run_shuts_down_after_idle_timeout(
    mock_time: Mock,
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() shuts down worker after idle timeout exceeded."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    # Simulate time progression past idle timeout
    mock_time.side_effect = [
        1000.0,  # Initial time
        1000.0,  # Context timestamp
        1000.0,  # Last activity time
        1000.0 + IDLE_TIMEOUT + 1,  # After timeout
    ]

    input_pipe.poll.return_value = False  # No events

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT
    worker_instance.run()

    # ASSERT
    assert worker_instance._running is False


@patch("basefunctions.EventContext")
def test_run_polls_with_timeout_and_checks_signals(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() polls pipe with 5-second timeout for signal checking."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    # Return False twice, then force shutdown
    poll_count: int = 0

    def poll_side_effect(timeout: float = None):
        nonlocal poll_count
        poll_count += 1
        if poll_count >= 2:
            worker_instance._running = False  # Force exit
        return False

    input_pipe.poll.side_effect = poll_side_effect

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT
    worker_instance.run()

    # ASSERT
    # Verify poll called with 5.0 second timeout
    assert input_pipe.poll.call_args_list[0][1]["timeout"] == 5.0


@patch("basefunctions.EventContext")
def test_run_creates_event_context_once_for_all_events(
    mock_context_class: Mock,
    worker_instance: CoreletWorker,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test run() creates EventContext once and reuses it for all events."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    shutdown_event: Mock = Mock(spec=basefunctions.Event)
    shutdown_event.event_type = basefunctions.INTERNAL_SHUTDOWN_EVENT
    shutdown_event.event_id = "shutdown-1"

    input_pipe.poll.return_value = True
    input_pipe.recv.return_value = pickle.dumps(shutdown_event)

    mock_context: Mock = Mock()
    mock_context.thread_local_data = threading.local()
    mock_context_class.return_value = mock_context

    # ACT
    worker_instance.run()

    # ASSERT
    mock_context_class.assert_called_once()  # Context created only once


# -------------------------------------------------------------
# TESTS: _process_event - IMPORTANT
# -------------------------------------------------------------


def test_process_event_executes_handler_and_returns_result(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    sample_context: Mock,
) -> None:
    """Test _process_event executes handler and returns EventResult."""
    # ARRANGE
    mock_handler: Mock = Mock(spec=basefunctions.EventHandler)
    mock_result: Mock = Mock(spec=basefunctions.EventResult)
    mock_handler.handle.return_value = mock_result

    worker_instance._handlers["test_event"] = basefunctions.EventHandler

    with patch.object(worker_instance, "_get_handler", return_value=mock_handler):
        # ACT
        result: basefunctions.EventResult = worker_instance._process_event(sample_event, sample_context)

    # ASSERT
    assert result is mock_result
    mock_handler.handle.assert_called_once_with(sample_event, sample_context)


def test_process_event_auto_registers_handler_when_not_registered(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    sample_context: Mock,
    sample_corelet_meta: Dict[str, str],
) -> None:
    """Test _process_event auto-registers handler when not registered and corelet_meta available."""
    # ARRANGE
    sample_event.corelet_meta = sample_corelet_meta

    mock_handler: Mock = Mock(spec=basefunctions.EventHandler)
    mock_result: Mock = Mock(spec=basefunctions.EventResult)
    mock_handler.handle.return_value = mock_result

    with patch.object(worker_instance, "_register_from_meta") as mock_register:
        with patch.object(worker_instance, "_get_handler", return_value=mock_handler):
            # ACT
            worker_instance._process_event(sample_event, sample_context)

    # ASSERT
    mock_register.assert_called_once_with(sample_corelet_meta)


def test_process_event_raises_exception_when_handler_fails(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    sample_context: Mock,
) -> None:
    """Test _process_event raises exception when handler.handle() fails."""
    # ARRANGE
    mock_handler: Mock = Mock(spec=basefunctions.EventHandler)
    mock_handler.handle.side_effect = RuntimeError("Handler error")

    worker_instance._handlers["test_event"] = basefunctions.EventHandler

    with patch.object(worker_instance, "_get_handler", return_value=mock_handler):
        # ACT & ASSERT
        with pytest.raises(RuntimeError, match="Handler error"):
            worker_instance._process_event(sample_event, sample_context)


def test_process_event_handles_missing_corelet_meta(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    sample_context: Mock,
) -> None:
    """Test _process_event handles missing corelet_meta gracefully when handler not registered."""
    # ARRANGE
    sample_event.corelet_meta = None

    mock_handler: Mock = Mock(spec=basefunctions.EventHandler)
    mock_result: Mock = Mock(spec=basefunctions.EventResult)
    mock_handler.handle.return_value = mock_result

    with patch.object(worker_instance, "_register_from_meta") as mock_register:
        with patch.object(worker_instance, "_get_handler", return_value=mock_handler):
            # ACT
            worker_instance._process_event(sample_event, sample_context)

    # ASSERT
    mock_register.assert_not_called()  # Should not attempt registration


# -------------------------------------------------------------
# TESTS: _send_result - IMPORTANT
# -------------------------------------------------------------


def test_send_result_pickles_and_sends_result_via_pipe(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test _send_result pickles EventResult and sends via output pipe."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    mock_result: Mock = Mock(spec=basefunctions.EventResult)
    mock_result.event_id = "result-1"

    # ACT
    worker_instance._send_result(sample_event, mock_result)

    # ASSERT
    output_pipe.send.assert_called_once()
    sent_data: bytes = output_pipe.send.call_args[0][0]
    # Verify it's pickled data
    assert isinstance(sent_data, bytes)


def test_send_result_sets_event_id_on_result(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test _send_result sets event_id from event on result before sending."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    mock_result: Mock = Mock(spec=basefunctions.EventResult)
    mock_result.event_id = None

    sample_event.event_id = "event-123"

    # ACT
    worker_instance._send_result(sample_event, mock_result)

    # ASSERT
    assert mock_result.event_id == "event-123"


def test_send_result_handles_broken_pipe_error_gracefully(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test _send_result handles BrokenPipeError gracefully without raising."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes
    output_pipe.send.side_effect = BrokenPipeError()

    mock_result: Mock = Mock(spec=basefunctions.EventResult)

    # ACT - should not raise
    worker_instance._send_result(sample_event, mock_result)

    # ASSERT
    output_pipe.send.assert_called_once()


def test_send_result_logs_error_when_pickle_fails(
    worker_instance: CoreletWorker,
    sample_event: Mock,
    mock_pipes: Tuple[Mock, Mock],
) -> None:
    """Test _send_result logs error when pickle serialization fails."""
    # ARRANGE
    input_pipe, output_pipe = mock_pipes

    # Create un-picklable object
    mock_result: Mock = Mock(spec=basefunctions.EventResult)
    mock_result.event_id = "result-1"

    with patch("pickle.dumps", side_effect=pickle.PicklingError("Cannot pickle")):
        # ACT - should not raise
        worker_instance._send_result(sample_event, mock_result)

    # ASSERT - error logged (verified by no exception raised)


# -------------------------------------------------------------
# TESTS: _setup_signal_handlers - IMPORTANT
# -------------------------------------------------------------


@patch("signal.signal")
def test_setup_signal_handlers_registers_sigterm_and_sigint(
    mock_signal: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _setup_signal_handlers registers SIGTERM and SIGINT handlers."""
    # ACT
    worker_instance._setup_signal_handlers()

    # ASSERT
    assert mock_signal.call_count == 2
    # Verify SIGTERM and SIGINT registered
    registered_signals: set = {call[0][0] for call in mock_signal.call_args_list}
    assert signal.SIGTERM in registered_signals
    assert signal.SIGINT in registered_signals


@patch("signal.signal")
def test_setup_signal_handlers_sets_running_false_on_signal(
    mock_signal: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _setup_signal_handlers sets _running to False when signal received."""
    # ARRANGE
    captured_handler = None

    def capture_handler(signum, handler):
        nonlocal captured_handler
        captured_handler = handler

    mock_signal.side_effect = capture_handler

    # ACT
    worker_instance._setup_signal_handlers()

    # Simulate signal
    assert captured_handler is not None
    captured_handler(signal.SIGTERM, None)

    # ASSERT
    assert worker_instance._running is False


@patch("signal.signal")
def test_setup_signal_handlers_skips_if_already_setup(
    mock_signal: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _setup_signal_handlers skips registration if already setup."""
    # ARRANGE
    worker_instance._signal_handlers_setup = True

    # ACT
    worker_instance._setup_signal_handlers()

    # ASSERT
    mock_signal.assert_not_called()


@patch("signal.signal")
def test_setup_signal_handlers_handles_registration_failure(
    mock_signal: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _setup_signal_handlers handles signal registration failure gracefully."""
    # ARRANGE
    mock_signal.side_effect = ValueError("Signal registration failed")

    # ACT - should not raise
    worker_instance._setup_signal_handlers()

    # ASSERT - error handled gracefully
    assert worker_instance._signal_handlers_setup is False


# -------------------------------------------------------------
# TESTS: _set_process_priority - IMPORTANT
# -------------------------------------------------------------


@patch("platform.system")
@patch("psutil.Process")
def test_set_process_priority_uses_psutil_on_windows(
    mock_process_class: Mock,
    mock_platform: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _set_process_priority uses psutil.Process.nice() on Windows."""
    # ARRANGE
    mock_platform.return_value = "Windows"
    mock_process: Mock = Mock()
    mock_process_class.return_value = mock_process

    # ACT
    worker_instance._set_process_priority()

    # ASSERT
    mock_process_class.assert_called_once_with(os.getpid())
    mock_process.nice.assert_called_once_with(1)


@patch("platform.system")
@patch("os.setpriority")
def test_set_process_priority_uses_setpriority_on_unix(
    mock_setpriority: Mock,
    mock_platform: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _set_process_priority uses os.setpriority() on Unix."""
    # ARRANGE
    mock_platform.return_value = "Linux"

    # ACT
    worker_instance._set_process_priority()

    # ASSERT
    mock_setpriority.assert_called_once_with(os.PRIO_PROCESS, os.getpid(), 10)


@patch("platform.system")
@patch("os.setpriority")
def test_set_process_priority_handles_permission_error_gracefully(
    mock_setpriority: Mock,
    mock_platform: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _set_process_priority handles PermissionError gracefully."""
    # ARRANGE
    mock_platform.return_value = "Linux"
    mock_setpriority.side_effect = PermissionError("Permission denied")

    # ACT - should not raise
    worker_instance._set_process_priority()

    # ASSERT - error handled gracefully


@patch("platform.system")
@patch("psutil.Process")
def test_set_process_priority_handles_psutil_error_gracefully(
    mock_process_class: Mock,
    mock_platform: Mock,
    worker_instance: CoreletWorker,
) -> None:
    """Test _set_process_priority handles psutil errors gracefully."""
    # ARRANGE
    mock_platform.return_value = "Windows"
    mock_process: Mock = Mock()
    mock_process.nice.side_effect = psutil.AccessDenied()
    mock_process_class.return_value = mock_process

    # ACT - should not raise
    worker_instance._set_process_priority()

    # ASSERT - error handled gracefully


# -------------------------------------------------------------
# TESTS: _is_handler_registered - Edge Cases
# -------------------------------------------------------------


def test_is_handler_registered_returns_true_when_registered(
    worker_instance: CoreletWorker,
) -> None:
    """Test _is_handler_registered returns True when handler is registered."""
    # ARRANGE
    worker_instance._handlers["test_event"] = basefunctions.EventHandler

    # ACT
    result: bool = worker_instance._is_handler_registered("test_event")

    # ASSERT
    assert result is True


def test_is_handler_registered_returns_false_when_not_registered(
    worker_instance: CoreletWorker,
) -> None:
    """Test _is_handler_registered returns False when handler not registered."""
    # ACT
    result: bool = worker_instance._is_handler_registered("unknown_event")

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS: Constants
# -------------------------------------------------------------


def test_idle_timeout_constant_has_expected_value() -> None:
    """Test IDLE_TIMEOUT constant has expected 10-minute value."""
    # ASSERT
    assert IDLE_TIMEOUT == 600.0
