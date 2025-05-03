"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unit tests for UnifiedTaskPool module
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import queue
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock
import basefunctions
from basefunctions import UnifiedTaskPool, UnifiedTaskPoolMessage, TaskletRequestInterface

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class TestTaskHandler(TaskletRequestInterface):
    """Test implementation of TaskletRequestInterface for testing."""

    def process_request(self, context, message):
        """Simple implementation that returns success and the message content."""
        return True, message.content


class SlowTaskHandler(TaskletRequestInterface):
    """Task handler that sleeps to test timeout functionality."""

    def process_request(self, context, message):
        """Sleep longer than the timeout and return success."""
        time.sleep(message.timeout + 1)
        return True, "completed"


class FailingTaskHandler(TaskletRequestInterface):
    """Task handler that always fails."""

    def process_request(self, context, message):
        """Always return failure."""
        return False, "failed"


class ExceptionTaskHandler(TaskletRequestInterface):
    """Task handler that raises an exception."""

    def process_request(self, context, message):
        """Raise an exception."""
        raise ValueError("Test exception")


@pytest.fixture
def task_pool():
    # Setup: Create the unified task pool with exactly 2 threads
    # This matches the assertion in test_initialization
    pool = basefunctions.UnifiedTaskPool(num_of_threads=2)

    # Provide the pool to the test
    yield pool

    # Teardown: Explicit shutdown after each test
    pool.shutdown(timeout=2)

    # Additional check to ensure all threads are terminated
    for thread in pool.thread_list:
        if thread.is_alive():
            basefunctions.get_logger(__name__).warning(
                "thread %s did not terminate properly", thread.name
            )


class TestUnifiedTaskPool:

    def test_initialization(self, task_pool):
        """Test that the task pool initializes correctly."""
        assert len(task_pool.thread_list) == 2
        assert isinstance(task_pool.input_queue, queue.Queue)
        assert isinstance(task_pool.output_queue, queue.Queue)
        assert "default" in task_pool.task_handlers

    def test_register_message_handler(self, task_pool):
        """Test registering a custom message handler."""
        handler = TestTaskHandler()
        task_pool.register_message_handler("test_type", handler)
        assert task_pool.get_message_handler("test_type") == handler

    def test_get_message_handler_default(self, task_pool):
        """Test that default handler is returned for unknown message types."""
        handler = task_pool.get_message_handler("unknown_type")
        assert handler == task_pool.task_handlers["default"]

    def test_register_handler_invalid_type(self, task_pool):
        """Test that registering a non-TaskletRequestInterface handler raises TypeError."""
        with pytest.raises(TypeError):
            task_pool.register_message_handler("test_type", object())

    def test_submit_task_success(self, task_pool):
        """Test successful task submission and processing."""
        # Register our test handler
        handler = TestTaskHandler()
        task_pool.register_message_handler("test_type", handler)

        # Create and submit a message
        message = UnifiedTaskPoolMessage(message_type="test_type", content="test_content")
        msg_id = task_pool.submit_task(message)

        # Wait for processing to complete
        time.sleep(0.5)

        # Get results from output queue
        results = task_pool.get_results_from_output_queue()

        # Verify results
        assert len(results) == 1
        assert results[0].id == msg_id
        assert results[0].success is True
        assert results[0].data == "test_content"

    def test_submit_invalid_task(self, task_pool):
        """Test that submitting a non-UnifiedTaskPoolMessage raises TypeError."""
        with pytest.raises(TypeError):
            task_pool.submit_task("not_a_message")

    def test_timeout_handling(self, task_pool):
        """Test that task timeouts are properly handled."""
        # Register a slow handler
        handler = SlowTaskHandler()
        task_pool.register_message_handler("slow_type", handler)

        # Create message with short timeout
        message = UnifiedTaskPoolMessage(
            message_type="slow_type",
            timeout=1,
            retry_max=1,  # Nur einen Versuch, um den Test zu beschleunigen
        )
        msg_id = task_pool.submit_task(message)

        # Wait for processing to complete (with timeout)
        # Warten wir länger, um sicherzustellen, dass der Timeout und die Verarbeitung
        # der Ergebnisse abgeschlossen sind
        time.sleep(3)

        # Get results
        results = task_pool.get_results_from_output_queue()

        # Verify results
        assert len(results) == 1
        assert results[0].id == msg_id
        assert results[0].success is False
        assert "Timeout" in results[0].error

    def test_retry_mechanism(self, task_pool):
        """Test that tasks are retried the correct number of times."""
        # Register a failing handler
        handler = FailingTaskHandler()
        task_pool.register_message_handler("failing_type", handler)

        # Create message with retry settings
        message = UnifiedTaskPoolMessage(message_type="failing_type", retry_max=3)
        msg_id = task_pool.submit_task(message)

        # Wait for processing (including retries)
        time.sleep(1)

        # Get results
        results = task_pool.get_results_from_output_queue()

        # Verify retries
        assert len(results) == 1
        assert results[0].id == msg_id
        assert results[0].success is False
        assert results[0].retry_counter == 3  # Should have tried 3 times

    def test_exception_handling(self, task_pool):
        """Test handling of exceptions in task handlers."""
        # Register a handler that raises exceptions
        handler = ExceptionTaskHandler()
        task_pool.register_message_handler("exception_type", handler)

        # Create and submit message
        message = UnifiedTaskPoolMessage(message_type="exception_type")
        msg_id = task_pool.submit_task(message)

        # Wait for processing
        time.sleep(0.5)

        # Get results
        results = task_pool.get_results_from_output_queue()

        # Verify exception handling
        assert len(results) == 1
        assert results[0].id == msg_id
        assert results[0].success is False
        assert results[0].exception_type == "ValueError"
        assert "Test exception" in results[0].error

    @patch("basefunctions.Subject.notify_observers")
    def test_observer_notifications(self, mock_notify, task_pool):
        """Test that observers are notified for task start and completion."""
        # Register our test handler
        handler = TestTaskHandler()
        task_pool.register_message_handler("test_type", handler)

        # Create and submit a message
        message = UnifiedTaskPoolMessage(message_type="test_type", content="test_content")
        task_pool.submit_task(message)

        # Wait for processing
        time.sleep(0.5)

        # Verify notifications
        assert mock_notify.call_count >= 2
        # First call should be for start notification
        start_call_args = mock_notify.call_args_list[0][0]
        assert start_call_args[0] == "start-test_type"
        # Last call should be for stop notification
        stop_call_args = mock_notify.call_args_list[-1][0]
        assert stop_call_args[0] == "stop-test_type"

    def test_wait_for_all(self, task_pool):
        """Test that wait_for_all blocks until all tasks are processed."""
        # Register our test handler
        handler = TestTaskHandler()
        task_pool.register_message_handler("test_type", handler)

        # Submit multiple tasks
        for i in range(5):
            message = UnifiedTaskPoolMessage(message_type="test_type", content=f"content_{i}")
            task_pool.submit_task(message)

        # Wait for all tasks to complete
        task_pool.wait_for_all()

        # Verify all tasks processed
        results = task_pool.get_results_from_output_queue()
        assert len(results) == 5
        assert all(result.success for result in results)

    @patch("basefunctions.CoreletManager.start_corelet")
    @patch("basefunctions.CoreletManager.terminate_corelet")
    def test_corelet_execution(self, mock_terminate, mock_start, task_pool):
        """Test corelet execution path with mocks."""
        # Mock process object
        import pickle  # Separate import for pickle

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            # Mock pickled result data
            pickle.dumps({"success": True, "data": "corelet_result"}),
            None,
        )
        mock_start.return_value = mock_process

        # Submit corelet task
        message = UnifiedTaskPoolMessage(
            message_type="corelet_type", execution_type="core", corelet_path="/mock/path"
        )
        msg_id = task_pool.submit_task(message)

        # Wait for processing
        time.sleep(0.5)

        # Verify corelet was started
        mock_start.assert_called_once()

        # Get results
        results = task_pool.get_results_from_output_queue()

        # Verify results
        assert len(results) == 1
        assert results[0].id == msg_id
        assert results[0].success is True
        assert results[0].data == "corelet_result"

        # Verify terminate not called (successful execution)
        mock_terminate.assert_not_called()
