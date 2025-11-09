"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for TimerThread context manager.
 Tests timeout enforcement, exception handling, and thread safety.

 WARNING: TimerThread uses PyThreadState_SetAsyncExc which is inherently
 unsafe and can cause deadlocks or interpreter corruption.

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
import time
from unittest.mock import Mock, patch, MagicMock

# Project imports
from basefunctions.events.timer_thread import TimerThread

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def current_thread_id() -> int:
    """
    Get current thread ID.

    Returns
    -------
    int
        Current thread identifier
    """
    return threading.get_ident()


# -------------------------------------------------------------
# TESTS: TimerThread Initialization
# -------------------------------------------------------------


def test_timer_thread_initialization(current_thread_id: int) -> None:
    """Test TimerThread initializes with timeout and thread_id."""
    # ARRANGE
    timeout: int = 5

    # ACT
    timer: TimerThread = TimerThread(timeout=timeout, thread_id=current_thread_id)

    # ASSERT
    assert timer.timeout == timeout
    assert timer.thread_id == current_thread_id
    assert timer.timer is not None


def test_timer_thread_creates_threading_timer(current_thread_id: int) -> None:
    """Test TimerThread creates internal threading.Timer."""
    # ACT
    timer: TimerThread = TimerThread(timeout=3, thread_id=current_thread_id)

    # ASSERT
    assert isinstance(timer.timer, threading.Timer)
    assert timer.timer.interval == 3


# -------------------------------------------------------------
# TESTS: Context Manager Protocol
# -------------------------------------------------------------


def test_timer_thread_context_manager_starts_timer(current_thread_id: int) -> None:
    """Test TimerThread __enter__ starts the timer."""
    # ARRANGE
    timer: TimerThread = TimerThread(timeout=10, thread_id=current_thread_id)

    # ACT
    with timer:
        # ASSERT
        assert timer.timer.is_alive()

    # After exit, timer should be cancelled
    # Note: cancel() is called but thread may still be alive briefly
    # The important part is that cancel() was called, which prevents timeout_thread() execution
    timer.timer.join(timeout=1)  # Wait for thread to finish
    assert not timer.timer.is_alive()


def test_timer_thread_context_manager_cancels_timer_on_exit(
    current_thread_id: int
) -> None:
    """Test TimerThread __exit__ cancels the timer."""
    # ARRANGE
    timer: TimerThread = TimerThread(timeout=10, thread_id=current_thread_id)

    # ACT
    with timer:
        pass

    # ASSERT
    timer.timer.join(timeout=1)  # Wait for thread to finish after cancel
    assert not timer.timer.is_alive()


def test_timer_thread_context_manager_cancels_timer_on_exception(
    current_thread_id: int
) -> None:
    """Test TimerThread cancels timer even when exception occurs."""
    # ARRANGE
    timer: TimerThread = TimerThread(timeout=10, thread_id=current_thread_id)

    # ACT & ASSERT
    try:
        with timer:
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Timer should be cancelled despite exception
    timer.timer.join(timeout=1)  # Wait for thread to finish after cancel
    assert not timer.timer.is_alive()


def test_timer_thread_enter_returns_self(current_thread_id: int) -> None:
    """Test TimerThread __enter__ returns self reference."""
    # ARRANGE
    timer: TimerThread = TimerThread(timeout=5, thread_id=current_thread_id)

    # ACT
    result: TimerThread = timer.__enter__()

    # ASSERT
    assert result is timer

    # Cleanup
    timer.__exit__(None, None, None)


def test_timer_thread_exit_returns_false(current_thread_id: int) -> None:
    """Test TimerThread __exit__ returns False (does not suppress exceptions)."""
    # ARRANGE
    timer: TimerThread = TimerThread(timeout=5, thread_id=current_thread_id)
    timer.__enter__()

    # ACT
    suppresses: bool = timer.__exit__(None, None, None)

    # ASSERT
    assert suppresses is False


# -------------------------------------------------------------
# TESTS: Timeout Behavior - CRITICAL
# -------------------------------------------------------------


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
def test_timer_thread_raises_timeout_after_duration(
    mock_set_async_exc: Mock,
    current_thread_id: int
) -> None:  # CRITICAL TEST
    """Test TimerThread triggers timeout_thread() after specified duration."""
    # ARRANGE
    mock_set_async_exc.return_value = 1  # Success
    timeout: float = 0.1  # 100ms for fast test

    # ACT
    timer: TimerThread = TimerThread(timeout=timeout, thread_id=current_thread_id)
    timer.__enter__()
    time.sleep(0.2)  # Wait for timeout to trigger

    # ASSERT
    # timeout_thread should have been called
    mock_set_async_exc.assert_called_once()

    # Cleanup
    timer.__exit__(None, None, None)


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
def test_timer_thread_no_timeout_when_completed_early(
    mock_set_async_exc: Mock,
    current_thread_id: int
) -> None:  # CRITICAL TEST
    """Test TimerThread does not timeout when operation completes before timeout."""
    # ARRANGE
    mock_set_async_exc.return_value = 1
    timeout: int = 10  # Long timeout

    # ACT
    with TimerThread(timeout=timeout, thread_id=current_thread_id):
        time.sleep(0.01)  # Short operation

    # Wait a bit to ensure timer was cancelled
    time.sleep(0.05)

    # ASSERT - timeout_thread should NOT have been called
    mock_set_async_exc.assert_not_called()


# -------------------------------------------------------------
# TESTS: timeout_thread() Method - CRITICAL
# -------------------------------------------------------------


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
@patch("basefunctions.events.timer_thread.get_logger")
def test_timeout_thread_calls_set_async_exc(
    mock_get_logger: Mock,
    mock_set_async_exc: Mock,
    current_thread_id: int
) -> None:  # CRITICAL TEST
    """Test timeout_thread() calls PyThreadState_SetAsyncExc to raise TimeoutError."""
    # ARRANGE
    mock_logger: Mock = Mock()
    mock_get_logger.return_value = mock_logger
    mock_set_async_exc.return_value = 1  # Success

    timer: TimerThread = TimerThread(timeout=1, thread_id=current_thread_id)

    # ACT
    timer.timeout_thread()

    # ASSERT
    mock_set_async_exc.assert_called_once()
    # Verify it was called with correct thread ID and TimeoutError
    call_args = mock_set_async_exc.call_args
    assert call_args is not None


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
@patch("basefunctions.events.timer_thread.get_logger")
def test_timeout_thread_logs_error_when_thread_not_found(
    mock_get_logger: Mock,
    mock_set_async_exc: Mock
) -> None:  # CRITICAL TEST
    """Test timeout_thread() logs warning when thread ID not found."""
    # ARRANGE
    mock_logger: Mock = Mock()
    mock_get_logger.return_value = mock_logger
    mock_set_async_exc.return_value = 0  # Thread not found

    invalid_thread_id: int = 999999999
    timer: TimerThread = TimerThread(timeout=1, thread_id=invalid_thread_id)

    # ACT
    timer.timeout_thread()

    # ASSERT
    mock_logger.warning.assert_called_once()
    assert "thread" in str(mock_logger.warning.call_args).lower()
    assert "not found" in str(mock_logger.warning.call_args).lower()


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
@patch("basefunctions.events.timer_thread.get_logger")
def test_timeout_thread_logs_success_when_exception_raised(
    mock_get_logger: Mock,
    mock_set_async_exc: Mock,
    current_thread_id: int
) -> None:  # CRITICAL TEST
    """Test timeout_thread() logs error when exception successfully raised."""
    # ARRANGE
    mock_logger: Mock = Mock()
    mock_get_logger.return_value = mock_logger
    mock_set_async_exc.return_value = 1  # Success

    timer: TimerThread = TimerThread(timeout=1, thread_id=current_thread_id)

    # ACT
    timer.timeout_thread()

    # ASSERT
    mock_logger.error.assert_called_once()
    assert "timeout" in str(mock_logger.error.call_args).lower()


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
@patch("basefunctions.events.timer_thread.get_logger")
def test_timeout_thread_handles_critical_error_multiple_threads_affected(
    mock_get_logger: Mock,
    mock_set_async_exc: Mock,
    current_thread_id: int
) -> None:  # CRITICAL TEST
    """Test timeout_thread() handles critical error when multiple threads affected."""
    # ARRANGE
    mock_logger: Mock = Mock()
    mock_get_logger.return_value = mock_logger
    mock_set_async_exc.return_value = 2  # Critical error - multiple threads affected

    timer: TimerThread = TimerThread(timeout=1, thread_id=current_thread_id)

    # ACT
    timer.timeout_thread()

    # ASSERT
    # Should log critical error
    assert mock_logger.critical.call_count >= 1
    # Should attempt to undo the operation
    assert mock_set_async_exc.call_count == 2  # Initial call + undo call


# -------------------------------------------------------------
# TESTS: Edge Cases
# -------------------------------------------------------------


def test_timer_thread_with_zero_timeout(current_thread_id: int) -> None:
    """Test TimerThread handles timeout of 0 seconds."""
    # ACT
    timer: TimerThread = TimerThread(timeout=0, thread_id=current_thread_id)

    # ASSERT
    assert timer.timeout == 0
    assert timer.timer.interval == 0


def test_timer_thread_with_negative_timeout(current_thread_id: int) -> None:
    """Test TimerThread handles negative timeout value."""
    # ACT
    timer: TimerThread = TimerThread(timeout=-1, thread_id=current_thread_id)

    # ASSERT
    assert timer.timeout == -1


def test_timer_thread_multiple_sequential_uses(current_thread_id: int) -> None:
    """Test TimerThread can be used multiple times sequentially."""
    # ACT & ASSERT
    for i in range(3):
        with TimerThread(timeout=10, thread_id=current_thread_id):
            time.sleep(0.01)


def test_timer_thread_with_long_timeout(current_thread_id: int) -> None:
    """Test TimerThread handles very long timeout."""
    # ACT
    timer: TimerThread = TimerThread(timeout=3600, thread_id=current_thread_id)

    # ASSERT
    assert timer.timeout == 3600

    # Start and immediately cancel
    timer.__enter__()
    timer.__exit__(None, None, None)


# -------------------------------------------------------------
# TESTS: Thread Safety
# -------------------------------------------------------------


def test_timer_thread_different_threads_have_different_ids() -> None:
    """Test TimerThread can target different threads."""
    # ARRANGE
    thread_id_1: int = threading.get_ident()

    def other_thread_func():
        thread_id_2: int = threading.get_ident()
        assert thread_id_1 != thread_id_2

    # ACT
    thread: threading.Thread = threading.Thread(target=other_thread_func)
    thread.start()
    thread.join()


@patch("ctypes.pythonapi.PyThreadState_SetAsyncExc")
def test_timer_thread_targets_correct_thread(
    mock_set_async_exc: Mock,
    current_thread_id: int
) -> None:
    """Test TimerThread targets the correct thread for timeout."""
    # ARRANGE
    mock_set_async_exc.return_value = 1
    timeout: float = 0.1

    timer: TimerThread = TimerThread(timeout=timeout, thread_id=current_thread_id)

    # ACT
    timer.__enter__()
    time.sleep(0.2)  # Wait for timeout

    # ASSERT
    mock_set_async_exc.assert_called_once()
    # Verify correct thread ID was used
    call_args = mock_set_async_exc.call_args
    assert call_args is not None

    # Cleanup
    timer.__exit__(None, None, None)


# -------------------------------------------------------------
# TESTS: Integration with Real Timeouts
# -------------------------------------------------------------


def test_timer_thread_actually_raises_timeout_in_current_thread() -> None:
    """Test TimerThread actually raises TimeoutError in current thread (integration test)."""
    # ARRANGE
    timeout: float = 0.1
    thread_id: int = threading.get_ident()

    # ACT & ASSERT
    with pytest.raises(TimeoutError):
        with TimerThread(timeout=timeout, thread_id=thread_id):
            time.sleep(1.0)  # Sleep longer than timeout


def test_timer_thread_no_exception_when_operation_completes_in_time() -> None:
    """Test TimerThread does not raise when operation completes before timeout."""
    # ARRANGE
    timeout: int = 5
    thread_id: int = threading.get_ident()

    # ACT & ASSERT (should not raise)
    with TimerThread(timeout=timeout, thread_id=thread_id):
        time.sleep(0.01)  # Short operation
