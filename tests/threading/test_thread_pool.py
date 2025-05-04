"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions_tests

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Pytest-based test suite for ThreadPool and TimerThread classes

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from unittest import mock
import queue
import threading
import pytest
from basefunctions.threading.thread_pool import TimerThread
import basefunctions

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


class TestThreadPoolMessageAndResult:

    def test_thread_pool_message_creation(self):
        msg = basefunctions.ThreadPoolMessage(message_type="test", content="data")
        assert isinstance(msg.id, str)
        assert msg.message_type == "test"
        assert msg.content == "data"
        assert msg.retry_max == 3

    def test_thread_pool_result_creation(self):
        result = basefunctions.ThreadPoolResult(message_type="test", id="1234")
        assert result.success is False
        assert result.data is None
        assert result.retry_counter == 0


class TestInterfaces:

    def test_thread_pool_request_interface_default(self):
        interface = basefunctions.ThreadPoolRequestInterface()
        success, data = interface.process_request(None, None, None)
        assert success is False
        assert isinstance(data, RuntimeError)


class TestThreadPoolInitialization:

    def test_thread_pool_initialization(self, monkeypatch):
        monkeypatch.setattr(
            basefunctions,
            "ConfigHandler",
            lambda: mock.Mock(get_config_value=lambda *args, **kwargs: 2),
        )
        pool = basefunctions.ThreadPool(num_of_threads=1)
        assert len(pool.thread_list) == 2

    def test_add_thread(self, monkeypatch):
        monkeypatch.setattr(
            basefunctions,
            "ConfigHandler",
            lambda: mock.Mock(get_config_value=lambda *args, **kwargs: 0),
        )
        pool = basefunctions.ThreadPool(num_of_threads=0)
        initial_count = len(pool.thread_list)
        pool.add_thread(target=pool._thread_worker)
        assert len(pool.thread_list) == initial_count + 1


class TestThreadPoolHandlerManagement:

    def test_register_and_get_message_handler(self, monkeypatch):
        monkeypatch.setattr(
            basefunctions,
            "ConfigHandler",
            lambda: mock.Mock(get_config_value=lambda *args, **kwargs: 0),
        )
        pool = basefunctions.ThreadPool(num_of_threads=0)
        handler = mock.Mock(spec=basefunctions.ThreadPoolRequestInterface)
        pool.register_message_handler("custom", handler)
        assert pool.get_message_handler("custom") is handler


class TestThreadPoolQueues:

    def test_stop_threads_puts_sentinel(self, monkeypatch):
        monkeypatch.setattr(
            basefunctions,
            "ConfigHandler",
            lambda: mock.Mock(get_config_value=lambda *args, **kwargs: 1),
        )
        pool = basefunctions.ThreadPool(num_of_threads=1)
        pool.stop_threads()
        assert not pool.input_queue.empty()

    def test_get_input_and_output_queue(self, monkeypatch):
        monkeypatch.setattr(
            basefunctions,
            "ConfigHandler",
            lambda: mock.Mock(get_config_value=lambda *args, **kwargs: 0),
        )
        pool = basefunctions.ThreadPool(num_of_threads=0)
        assert isinstance(pool.get_input_queue(), queue.Queue)
        assert isinstance(pool.get_output_queue(), queue.Queue)

    def test_get_results_from_output_queue(self, monkeypatch):
        monkeypatch.setattr(
            basefunctions,
            "ConfigHandler",
            lambda: mock.Mock(get_config_value=lambda *args, **kwargs: 0),
        )
        pool = basefunctions.ThreadPool(num_of_threads=0)
        dummy_result = basefunctions.ThreadPoolResult(message_type="test", id="1")
        pool.output_queue.put(dummy_result)
        results = pool.get_results_from_output_queue()
        assert len(results) == 1
        assert results[0].id == "1"


class TestTimerThread:

    def test_timer_thread_enters_and_exits(self):
        timer = TimerThread(timeout=1, thread_id=threading.get_ident())
        with mock.patch.object(timer, "timeout_thread") as mocked_timeout:
            with timer:
                pass
            mocked_timeout.assert_not_called()

    def test_timer_thread_timeout_thread(self):
        timer = TimerThread(timeout=1, thread_id=threading.get_ident())
        with mock.patch(
            "ctypes.pythonapi.PyThreadState_SetAsyncExc", return_value=1
        ) as mocked_ctypes:
            timer.timeout_thread()
            mocked_ctypes.assert_called()
