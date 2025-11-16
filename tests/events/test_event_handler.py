"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for EventHandler, EventResult, and handler implementations.
 Tests handler interface, result handling, subprocess execution, and corelet forwarding.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
import threading
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock, MagicMock, patch, call

# Project imports
from basefunctions.events.event_handler import (
    EventResult,
    EventHandler,
    DefaultCmdHandler,
    CoreletForwardingHandler,
    CoreletHandle,
)
from basefunctions.events.event import Event, EXECUTION_MODE_CMD, EXECUTION_MODE_CORELET
from basefunctions.events.event_context import EventContext

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_event_id() -> str:
    """
    Provide sample event ID.

    Returns
    -------
    str
        Sample event identifier
    """
    return "test-event-123"


@pytest.fixture
def sample_event_context() -> EventContext:
    """
    Create sample event context.

    Returns
    -------
    EventContext
        Event context with thread_local_data
    """
    return EventContext(thread_local_data=threading.local())


@pytest.fixture
def sample_event() -> Event:
    """
    Create sample event.

    Returns
    -------
    Event
        Sample event instance
    """
    return Event(event_type="test_event", event_exec_mode=EXECUTION_MODE_CMD)


# -------------------------------------------------------------
# TESTS: EventResult - Business Results
# -------------------------------------------------------------


def test_event_result_business_success(sample_event_id: str) -> None:
    """Test EventResult.business_result() creates successful result."""
    # ARRANGE
    result_data: dict = {"processed": 100, "errors": 0}

    # ACT
    result: EventResult = EventResult.business_result(event_id=sample_event_id, success=True, data=result_data)

    # ASSERT
    assert result.event_id == sample_event_id
    assert result.success is True
    assert result.data == result_data
    assert result.exception is None


def test_event_result_business_failure(sample_event_id: str) -> None:
    """Test EventResult.business_result() creates failure result."""
    # ARRANGE
    error_message: str = "Validation failed: missing required field"

    # ACT
    result: EventResult = EventResult.business_result(event_id=sample_event_id, success=False, data=error_message)

    # ASSERT
    assert result.event_id == sample_event_id
    assert result.success is False
    assert result.data == error_message
    assert result.exception is None


def test_event_result_business_result_with_none_data(sample_event_id: str) -> None:
    """Test EventResult.business_result() handles None data."""
    # ACT
    result: EventResult = EventResult.business_result(event_id=sample_event_id, success=True, data=None)

    # ASSERT
    assert result.data is None


# -------------------------------------------------------------
# TESTS: EventResult - Exception Results
# -------------------------------------------------------------


def test_event_result_exception_result(sample_event_id: str) -> None:
    """Test EventResult.exception_result() creates exception result."""
    # ARRANGE
    exception: Exception = ValueError("Test error")

    # ACT
    result: EventResult = EventResult.exception_result(sample_event_id, exception)

    # ASSERT
    assert result.event_id == sample_event_id
    assert result.success is False
    assert result.exception is exception
    assert result.data is None


def test_event_result_exception_result_with_timeout_error(sample_event_id: str) -> None:
    """Test EventResult.exception_result() handles TimeoutError."""
    # ARRANGE
    exception: TimeoutError = TimeoutError("Operation timed out")

    # ACT
    result: EventResult = EventResult.exception_result(sample_event_id, exception)

    # ASSERT
    assert result.exception is exception
    assert isinstance(result.exception, TimeoutError)


# -------------------------------------------------------------
# TESTS: EventResult - String Representation
# -------------------------------------------------------------


def test_event_result_str_success() -> None:
    """Test EventResult __str__ for successful result."""
    # ACT
    result: EventResult = EventResult.business_result("evt-123", True, {"key": "value"})

    # ARRANGE
    result_str: str = str(result)

    # ASSERT
    assert "evt-123" in result_str
    assert "SUCCESS" in result_str


def test_event_result_str_failure() -> None:
    """Test EventResult __str__ for failed result."""
    # ACT
    result: EventResult = EventResult.business_result("evt-456", False, "Error message")

    # ARRANGE
    result_str: str = str(result)

    # ASSERT
    assert "evt-456" in result_str
    assert "FAILED" in result_str


# -------------------------------------------------------------
# TESTS: EventHandler Abstract Interface
# -------------------------------------------------------------


def test_event_handler_is_abstract_base_class() -> None:
    """Test EventHandler cannot be instantiated directly."""
    # ACT & ASSERT
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        EventHandler()


def test_event_handler_subclass_must_implement_handle() -> None:
    """Test EventHandler subclass must implement handle() method."""

    # ARRANGE
    class IncompleteHandler(EventHandler):
        pass

    # ACT & ASSERT
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteHandler()


def test_event_handler_subclass_can_be_instantiated_with_handle() -> None:
    """Test EventHandler subclass can be instantiated when handle() is implemented."""

    # ARRANGE
    class CompleteHandler(EventHandler):
        def handle(self, event: Event, context: EventContext) -> EventResult:
            return EventResult.business_result(event.event_id, True, None)

    # ACT
    handler: EventHandler = CompleteHandler()

    # ASSERT
    assert isinstance(handler, EventHandler)


def test_event_handler_terminate_default_implementation() -> None:
    """Test EventHandler.terminate() default implementation does nothing."""

    # ARRANGE
    class TestHandler(EventHandler):
        def handle(self, event: Event, context: EventContext) -> EventResult:
            return EventResult.business_result(event.event_id, True, None)

    handler: EventHandler = TestHandler()
    context: EventContext = EventContext()

    # ACT & ASSERT (should not raise)
    handler.terminate(context)


# -------------------------------------------------------------
# TESTS: DefaultCmdHandler - Successful Execution - CRITICAL
# -------------------------------------------------------------


def test_default_cmd_handler_executes_simple_command(sample_event_context: EventContext) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler executes simple command successfully."""
    # ARRANGE
    handler: DefaultCmdHandler = DefaultCmdHandler()
    event: Event = Event(
        event_type="test_cmd",
        event_exec_mode=EXECUTION_MODE_CMD,
        event_data={
            "executable": "echo",
            "args": ["Hello, World!"],
        },
    )

    # ACT
    result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    assert result.success is True
    assert result.data["returncode"] == 0
    assert "Hello, World!" in result.data["stdout"]


def test_default_cmd_handler_with_working_directory(
    sample_event_context: EventContext, tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler executes command with custom working directory."""
    # ARRANGE
    handler: DefaultCmdHandler = DefaultCmdHandler()
    event: Event = Event(
        event_type="test_cmd",
        event_exec_mode=EXECUTION_MODE_CMD,
        event_data={"executable": "pwd", "args": [], "cwd": str(tmp_path)},
    )

    # ACT
    result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    assert result.success is True
    assert str(tmp_path) in result.data["stdout"]


def test_default_cmd_handler_with_stdout_file(
    sample_event_context: EventContext, tmp_path: Path
) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler redirects stdout to file."""
    # ARRANGE
    stdout_file: Path = tmp_path / "stdout.txt"
    handler: DefaultCmdHandler = DefaultCmdHandler()
    event: Event = Event(
        event_type="test_cmd",
        event_exec_mode=EXECUTION_MODE_CMD,
        event_data={"executable": "echo", "args": ["File output test"], "stdout_file": str(stdout_file)},
    )

    # ACT
    result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    assert result.success is True
    assert stdout_file.exists()
    assert "File output test" in stdout_file.read_text()
    assert result.data["stdout"] == str(stdout_file)


# -------------------------------------------------------------
# TESTS: DefaultCmdHandler - Error Handling - CRITICAL
# -------------------------------------------------------------


def test_default_cmd_handler_missing_executable(sample_event_context: EventContext) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler handles missing executable in event data."""
    # ARRANGE
    handler: DefaultCmdHandler = DefaultCmdHandler()
    event: Event = Event(
        event_type="test_cmd",
        event_exec_mode=EXECUTION_MODE_CMD,
        event_data={"args": ["arg1"]},  # Missing 'executable'
    )

    # ACT
    result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    assert result.success is False
    assert "Missing executable" in result.data


def test_default_cmd_handler_nonexistent_executable(sample_event_context: EventContext) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler handles non-existent executable."""
    # ARRANGE
    handler: DefaultCmdHandler = DefaultCmdHandler()
    event: Event = Event(
        event_type="test_cmd",
        event_exec_mode=EXECUTION_MODE_CMD,
        event_data={"executable": "nonexistent_command_12345", "args": []},
    )

    # ACT
    result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    assert result.success is False
    assert result.exception is not None
    assert isinstance(result.exception, FileNotFoundError)


def test_default_cmd_handler_command_fails_with_nonzero_exit(
    sample_event_context: EventContext,
) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler handles command with non-zero exit code."""
    # ARRANGE
    handler: DefaultCmdHandler = DefaultCmdHandler()
    event: Event = Event(
        event_type="test_cmd",
        event_exec_mode=EXECUTION_MODE_CMD,
        event_data={"executable": "sh", "args": ["-c", "exit 42"]},
    )

    # ACT
    result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    assert result.success is False
    assert result.data["returncode"] == 42


# -------------------------------------------------------------
# TESTS: DefaultCmdHandler - Terminate - CRITICAL
# -------------------------------------------------------------


@patch("subprocess.Popen")
def test_default_cmd_handler_terminate_kills_subprocess(
    mock_popen: Mock, sample_event_context: EventContext
) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler.terminate() kills running subprocess."""
    # ARRANGE
    mock_process: Mock = Mock()
    mock_process.poll.return_value = None  # Process still running
    mock_popen.return_value = mock_process

    handler: DefaultCmdHandler = DefaultCmdHandler()

    # Store subprocess reference in context
    sample_event_context.thread_local_data.current_subprocess = mock_process

    # ACT
    handler.terminate(sample_event_context)

    # ASSERT
    mock_process.terminate.assert_called_once()


@patch("subprocess.Popen")
def test_default_cmd_handler_terminate_force_kills_if_terminate_fails(
    mock_popen: Mock, sample_event_context: EventContext
) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler.terminate() force kills if terminate fails."""
    # ARRANGE
    mock_process: Mock = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 2)
    mock_popen.return_value = mock_process

    handler: DefaultCmdHandler = DefaultCmdHandler()
    sample_event_context.thread_local_data.current_subprocess = mock_process

    # ACT
    handler.terminate(sample_event_context)

    # ASSERT
    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_called_once()


def test_default_cmd_handler_terminate_handles_missing_subprocess(
    sample_event_context: EventContext,
) -> None:  # CRITICAL TEST
    """Test DefaultCmdHandler.terminate() handles missing subprocess gracefully."""
    # ARRANGE
    handler: DefaultCmdHandler = DefaultCmdHandler()
    # No subprocess stored in context

    # ACT & ASSERT (should not raise)
    handler.terminate(sample_event_context)


# -------------------------------------------------------------
# TESTS: CoreletHandle
# -------------------------------------------------------------


def test_corelet_handle_initialization() -> None:
    """Test CoreletHandle stores process and pipe references."""
    # ARRANGE
    mock_process: Mock = Mock()
    mock_input_pipe: Mock = Mock()
    mock_output_pipe: Mock = Mock()

    # ACT
    handle: CoreletHandle = CoreletHandle(mock_process, mock_input_pipe, mock_output_pipe)

    # ASSERT
    assert handle.process is mock_process
    assert handle.input_pipe is mock_input_pipe
    assert handle.output_pipe is mock_output_pipe


def test_corelet_handle_uses_slots() -> None:
    """Test CoreletHandle uses __slots__ for memory efficiency."""
    # ASSERT
    assert hasattr(CoreletHandle, "__slots__")
    assert set(CoreletHandle.__slots__) == {"process", "input_pipe", "output_pipe"}


# -------------------------------------------------------------
# TESTS: CoreletForwardingHandler - Successful Forwarding
# -------------------------------------------------------------


@patch("basefunctions.events.event_handler.multiprocessing.Pipe")
@patch("basefunctions.events.event_handler.Process")
def test_corelet_forwarding_handler_creates_corelet(
    mock_process_class: Mock, mock_pipe: Mock, sample_event_context: EventContext
) -> None:  # CRITICAL TEST
    """Test CoreletForwardingHandler creates corelet worker process."""
    # ARRANGE
    mock_input_pipe_a: Mock = Mock()
    mock_input_pipe_b: Mock = Mock()
    mock_output_pipe_a: Mock = Mock()
    mock_output_pipe_b: Mock = Mock()
    mock_pipe.side_effect = [(mock_input_pipe_a, mock_input_pipe_b), (mock_output_pipe_a, mock_output_pipe_b)]

    mock_process: Mock = Mock()
    mock_process_class.return_value = mock_process

    handler: CoreletForwardingHandler = CoreletForwardingHandler()
    event: Event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_CORELET)

    # Mock output pipe to return result
    mock_output_pipe_a.poll.return_value = True
    mock_result: EventResult = EventResult.business_result(event.event_id, True, None)
    mock_output_pipe_a.recv.return_value = Mock(__class__=bytes)

    with patch("pickle.dumps") as mock_dumps, patch("pickle.loads") as mock_loads:
        mock_dumps.return_value = b"pickled_event"
        mock_loads.return_value = mock_result

        # ACT
        result: EventResult = handler.handle(event, sample_event_context)

    # ASSERT
    mock_process_class.assert_called_once()
    mock_process.start.assert_called_once()
    assert result.success is True


@patch("basefunctions.events.event_handler.multiprocessing.Pipe")
@patch("basefunctions.events.event_handler.Process")
def test_corelet_forwarding_handler_reuses_existing_corelet(
    mock_process_class: Mock, mock_pipe: Mock, sample_event_context: EventContext
) -> None:
    """Test CoreletForwardingHandler reuses existing corelet for same thread."""
    # ARRANGE
    mock_input_pipe_a: Mock = Mock()
    mock_input_pipe_b: Mock = Mock()
    mock_output_pipe_a: Mock = Mock()
    mock_output_pipe_b: Mock = Mock()
    mock_pipe.side_effect = [(mock_input_pipe_a, mock_input_pipe_b), (mock_output_pipe_a, mock_output_pipe_b)]

    mock_process: Mock = Mock()
    mock_process_class.return_value = mock_process

    handler: CoreletForwardingHandler = CoreletForwardingHandler()
    event1: Event = Event(event_type="test1", event_exec_mode=EXECUTION_MODE_CORELET)
    event2: Event = Event(event_type="test2", event_exec_mode=EXECUTION_MODE_CORELET)

    # Mock output pipe
    mock_output_pipe_a.poll.return_value = True
    mock_result1: EventResult = EventResult.business_result(event1.event_id, True, None)
    mock_result2: EventResult = EventResult.business_result(event2.event_id, True, None)

    with patch("pickle.dumps"), patch("pickle.loads") as mock_loads:
        mock_loads.side_effect = [mock_result1, mock_result2]

        # ACT
        handler.handle(event1, sample_event_context)
        handler.handle(event2, sample_event_context)

    # ASSERT - Process created only once
    assert mock_process_class.call_count == 1


# -------------------------------------------------------------
# TESTS: CoreletForwardingHandler - Timeout Handling - CRITICAL
# -------------------------------------------------------------


@patch("basefunctions.events.event_handler.multiprocessing.Pipe")
@patch("basefunctions.events.event_handler.Process")
def test_corelet_forwarding_handler_handles_timeout(
    mock_process_class: Mock, mock_pipe: Mock, sample_event_context: EventContext
) -> None:  # CRITICAL TEST
    """Test CoreletForwardingHandler raises TimeoutError when corelet doesn't respond."""
    # ARRANGE
    mock_input_pipe_a: Mock = Mock()
    mock_input_pipe_b: Mock = Mock()
    mock_output_pipe_a: Mock = Mock()
    mock_output_pipe_b: Mock = Mock()
    mock_pipe.side_effect = [(mock_input_pipe_a, mock_input_pipe_b), (mock_output_pipe_a, mock_output_pipe_b)]

    mock_process: Mock = Mock()
    mock_process_class.return_value = mock_process

    # Simulate timeout - poll returns False
    mock_output_pipe_a.poll.return_value = False

    handler: CoreletForwardingHandler = CoreletForwardingHandler()
    event: Event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_CORELET, timeout=1)

    with patch("pickle.dumps"):
        # ACT & ASSERT
        with pytest.raises(TimeoutError, match="No response from corelet"):
            handler.handle(event, sample_event_context)

    # ASSERT - Process should be terminated
    mock_process.terminate.assert_called_once()


# -------------------------------------------------------------
# TESTS: CoreletForwardingHandler - Terminate - CRITICAL
# -------------------------------------------------------------


def test_corelet_forwarding_handler_terminate_kills_corelet(
    sample_event_context: EventContext,
) -> None:  # CRITICAL TEST
    """Test CoreletForwardingHandler.terminate() kills corelet process."""
    # ARRANGE
    mock_process: Mock = Mock()
    mock_input_pipe: Mock = Mock()
    mock_output_pipe: Mock = Mock()

    corelet_handle: CoreletHandle = CoreletHandle(mock_process, mock_input_pipe, mock_output_pipe)
    sample_event_context.thread_local_data.corelet_handle = corelet_handle

    handler: CoreletForwardingHandler = CoreletForwardingHandler()

    # ACT
    handler.terminate(sample_event_context)

    # ASSERT
    mock_process.terminate.assert_called_once()
    mock_input_pipe.close.assert_called_once()
    mock_output_pipe.close.assert_called_once()


def test_corelet_forwarding_handler_terminate_handles_missing_corelet(
    sample_event_context: EventContext,
) -> None:  # CRITICAL TEST
    """Test CoreletForwardingHandler.terminate() handles missing corelet gracefully."""
    # ARRANGE
    handler: CoreletForwardingHandler = CoreletForwardingHandler()
    # No corelet stored in context

    # ACT & ASSERT (should not raise)
    handler.terminate(sample_event_context)
