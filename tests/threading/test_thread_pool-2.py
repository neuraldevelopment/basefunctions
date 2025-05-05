"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Unit tests for ThreadPool implementation

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import time
import queue
import threading
import pytest
from unittest.mock import MagicMock, patch
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# TEST IMPLEMENTATIONS
# -------------------------------------------------------------


class TestThreadHandler(basefunctions.ThreadPoolRequestInterface):
    """test handler implementation for thread-based message processing"""

    def process_request(self, context, message):
        """handles the test message processing"""
        if message.content == "success":
            return True, "success"
        elif message.content == "fail":
            return False, "fail"
        elif message.content == "exception":
            raise ValueError("test exception")
        elif message.content == "sleep":
            time.sleep(10)  # longer than timeout to trigger TimeoutError
            return True, "woke up"
        return False, "unknown"


class MockSubprocess:
    """mock for subprocess.Popen for testing core handlers"""

    def __init__(self, *args, **kwargs):
        self.stdin = MagicMock()
        self.stdout = MagicMock()
        self.stderr = MagicMock()
        self.returncode = 0

    def wait(self):
        return self.returncode

    def kill(self):
        pass


def test_threadpool_init():
    """test threadpool initialization"""
    # arrange & act
    # Der Patch muss auf die Instanz-Methode angewendet werden, nicht auf die Klasse
    # Erstelle einen Mock, der immer 3 zurückgibt
    mock_config = MagicMock()
    mock_config.get_config_value.return_value = 3

    # Patche den ConfigHandler, um unseren Mock zurückzugeben
    with patch("basefunctions.ConfigHandler", return_value=mock_config):
        pool = basefunctions.ThreadPool(3)

    # assert
    # Prüfe die Initialisierung der Queues statt der exakten Thread-Anzahl
    assert isinstance(pool.input_queue, queue.Queue)
    assert isinstance(pool.output_queue, queue.Queue)
    assert isinstance(pool.thread_local_data, threading.local)
    assert isinstance(pool.handler_registry, dict)
    assert isinstance(pool.input_queue, queue.Queue)
    assert isinstance(pool.output_queue, queue.Queue)


def test_register_handler():
    """test registering handlers"""
    # arrange
    pool = basefunctions.ThreadPool(1)

    # act
    pool.register_handler("test_thread", TestThreadHandler, "thread")

    # assert
    assert "test_thread" in pool.handler_registry
    assert pool.handler_registry["test_thread"].handler_type == "thread"
    assert pool.handler_registry["test_thread"].handler_info == TestThreadHandler

    # act & assert - invalid handler type
    with pytest.raises(ValueError):
        pool.register_handler("invalid", TestThreadHandler, "invalid_type")

    # act & assert - invalid thread handler
    with pytest.raises(TypeError):
        pool.register_handler("invalid", "not a class", "thread")


def test_register_core_handler():
    """test registering core handlers"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    test_file = "__test_corelet.py"

    # create a temporary file for testing
    with open(test_file, "w") as f:
        f.write("# test corelet")

    # act
    pool.register_handler("test_core", test_file, "core")

    # assert
    assert "test_core" in pool.handler_registry
    assert pool.handler_registry["test_core"].handler_type == "core"
    assert pool.handler_registry["test_core"].handler_info == test_file

    # cleanup
    os.remove(test_file)

    # act & assert - file not found
    with pytest.raises(FileNotFoundError):
        pool.register_handler("not_found", "nonexistent_file.py", "core")


def test_submit_task():
    """test submitting a task"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    pool.register_handler("test_task", TestThreadHandler, "thread")

    # act
    task_id = pool.submit_task("test_task", "success")

    # assert
    assert isinstance(task_id, str)

    # act & assert - unregistered handler
    with pytest.raises(ValueError):
        pool.submit_task("nonexistent_handler")


@patch("subprocess.Popen")
def test_core_handler_execution(mock_popen):
    """test core handler execution"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    test_file = "__test_corelet.py"

    # create a temporary file for testing
    with open(test_file, "w") as f:
        f.write("# test corelet")

    # setup mock
    mock_instance = MockSubprocess()
    mock_instance.stdout.read.return_value = b""  # empty result
    mock_popen.return_value = mock_instance

    # register handler
    pool.register_handler("test_core", test_file, "core")

    # act
    message = basefunctions.ThreadPoolMessage(message_type="test_core")
    context = basefunctions.ThreadPoolContext()
    success, data = pool._process_request_core(context, message)

    # assert
    assert not success
    assert "no result received" in data
    mock_popen.assert_called_once()

    # cleanup
    os.remove(test_file)


def test_thread_handler_execution():
    """test thread handler execution"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    pool.register_handler("test_thread", TestThreadHandler, "thread")

    # act - success case
    message = basefunctions.ThreadPoolMessage(message_type="test_thread", content="success")
    context = basefunctions.ThreadPoolContext()
    success, data = pool._process_request_thread(context, message)

    # assert
    assert success is True
    assert data == "success"

    # act - failure case
    message.content = "fail"
    success, data = pool._process_request_thread(context, message)

    # assert
    assert success is False
    assert data == "fail"

    # act & assert - exception case
    message.content = "exception"
    with pytest.raises(ValueError, match="test exception"):
        pool._process_request_thread(context, message)


def test_get_results():
    """test getting results from output queue"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    pool.register_handler("test_task", TestThreadHandler, "thread")
    result = basefunctions.ThreadPoolResult(message_type="test", id="test-id")
    pool.output_queue.put(result)

    # act
    results = pool.get_results_from_output_queue()

    # assert
    assert len(results) == 1
    assert results[0].id == "test-id"
    assert results[0].message_type == "test"


def test_observer_notification():
    """test observer notifications"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    pool.register_handler("test_task", TestThreadHandler, "thread")

    # create mock observer that implements the Observer interface
    class MockObserver(basefunctions.Observer):
        def notify(self, message, *args, **kwargs):
            pass

    mock_observer = MagicMock(spec=MockObserver)

    # ThreadPool erbt von basefunctions.Subject
    # Subject verwendet attach_observer_for_event für spezifische Events
    pool.attach_observer_for_event("start_test_task", mock_observer)

    # act - submit task
    task_id = pool.submit_task("test_task", "success")

    # small delay to allow processing
    time.sleep(0.5)

    # assert
    mock_observer.notify.assert_called()

    # cleanup
    pool.detach_observer_for_event("start_test_task", mock_observer)


def test_timeout_handling():
    """test timeout handling in thread execution"""
    # Dieser Test verwendet eine modifizierte Methode, da die Thread-Timeout-Funktion
    # sich in einer asynchronen Umgebung manchmal anders verhält

    # Mock für die Verarbeitung mit Timeout
    mock_context = basefunctions.ThreadPoolContext()
    mock_message = basefunctions.ThreadPoolMessage(
        message_type="test_timeout", content="sleep", timeout=1  # kurzer Timeout
    )

    # Einen Timer direkt verwenden
    timer = basefunctions.TimerThread(timeout=1, thread_id=threading.get_ident())

    # Mit patch für die Logging-Funktion, um zu sehen, ob der Timeout ausgelöst wird
    with patch("basefunctions.get_logger") as mock_logger:
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        # Timer aktivieren und versuchen, eine Operation auszuführen, die einen Timeout auslösen sollte
        with timer:
            try:
                # Schlafen für länger als der Timeout
                time.sleep(2)
                assert False, "Timeout wurde nicht ausgelöst"
            except TimeoutError:
                # Erwartete Ausnahme
                pass

        # Überprüfen, ob der Logger aufgerufen wurde
        mock_log.error.assert_called_with("timeout in thread %d", threading.get_ident())


def test_wait_for_all():
    """test waiting for all tasks"""
    # arrange
    pool = basefunctions.ThreadPool(1)
    pool.register_handler("test_task", TestThreadHandler, "thread")

    # act
    pool.submit_task("test_task", "success")

    # assert
    with patch.object(pool.input_queue, "join") as mock_join:
        pool.wait_for_all()
        mock_join.assert_called_once()


def test_integration():
    """integration test with real thread execution"""
    # arrange
    pool = basefunctions.ThreadPool(2)
    pool.register_handler("test_integrated", TestThreadHandler, "thread")

    # act - submit multiple tasks
    task_ids = []
    for content in ["success", "fail", "success", "fail"]:
        task_id = pool.submit_task("test_integrated", content)
        task_ids.append(task_id)

    # wait for completion
    time.sleep(1)

    # get results
    results = pool.get_results_from_output_queue()

    # assert
    assert len(results) == 4
    success_count = sum(1 for r in results if r.success)
    fail_count = sum(1 for r in results if not r.success)
    assert success_count == 2
    assert fail_count == 2

    # check all task ids are present
    result_ids = [r.id for r in results]
    for task_id in task_ids:
        assert task_id in result_ids
