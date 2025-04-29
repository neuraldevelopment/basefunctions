"""
# =============================================================================
#
#  Licensed Materials, Property of neuraldevelopment, Munich
#
#  Project : basefunctions
#
#  Copyright (c) by neuraldevelopment
#
#  All rights reserved.
#
#  Description:
#
#  A simple thread pool library to execute commands in a multithreaded
#  environment using Message and Result objects.
# =============================================================================
"""

# pylint: disable=W0718

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import atexit
import queue
import threading
import types
import uuid
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict, Tuple
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
# CLASS DEFINITIONS
# -------------------------------------------------------------


@dataclass
class ThreadPoolMessage:
    """
    A message container for communication with the thread pool.

    Attributes
    ----------
    id : str
        Unique identifier for the message.
    message_type : str
        The type used to route to the appropriate handler.
    retry_max : int
        Maximum number of allowed retry attempts.
    timeout : int
        Timeout in seconds for processing the message.
    content : Any
        Payload of the message.
    result_handler : Optional[Any]
        Optional result handler to post-process result.
    retry : int
        Current retry count, managed internally.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: str = ""
    retry_max: int = 3
    timeout: int = 5
    content: Any = None
    result_handler: Optional[Any] = None
    retry: int = 0


@dataclass
class ThreadPoolResult:
    """
    Result of a thread pool task.

    Attributes
    ----------
    message_type : str
        Message type that was processed.
    id : str
        Corresponding message ID.
    success : bool
        True if the task was successful.
    data : Any
        Result data or error information.
    metadata : Dict[str, Any]
        Optional metadata.
    original_message : Optional[ThreadPoolMessage]
        The original message object.
    error : Optional[str]
        Error string if failed.
    exception_type : Optional[str]
        Type of exception raised.
    retry_counter : int
        Number of attempts performed.
    exception : Optional[Exception]
        Captured exception object (optional).
    """

    message_type: str
    id: str
    success: bool = False
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    original_message: Optional[ThreadPoolMessage] = None
    error: Optional[str] = None
    exception_type: Optional[str] = None
    retry_counter: int = 0
    exception: Optional[Exception] = None


class ThreadPoolRequestInterface:
    """
    Interface for message handlers used in the thread pool.
    """

    def process_request(
        self,
        thread_local_data: Any,
        input_queue: queue.Queue,
        message: ThreadPoolMessage,
    ) -> Tuple[bool, Any]:
        """
        Handle a message and return success flag and result data.

        Parameters
        ----------
        thread_local_data : Any
            Thread-local context.
        input_queue : queue.Queue
            Reference to the input queue.
        message : ThreadPoolMessage
            The message to process.

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data.
        """
        return False, RuntimeError("process_request() not implemented")


class ThreadPoolResultInterface:
    """
    Interface for post-processing results before they enter the output queue.
    """

    def process_result(self, raw_data: Any, original_message: ThreadPoolMessage) -> Any:
        """
        Transform or filter result data.

        Parameters
        ----------
        raw_data : Any
            Raw result data from processing.
        original_message : ThreadPoolMessage
            The original message.

        Returns
        -------
        Any
            Final result data.
        """
        raise NotImplementedError


class ThreadPool:
    """
    ThreadPool to handle parallel task execution based on message types.
    """

    thread_list: List[threading.Thread] = []
    input_queue: queue.Queue = queue.Queue()
    output_queue: queue.Queue = queue.Queue()
    thread_local_data = threading.local()

    def __init__(self, num_of_threads: int = 5) -> None:
        """
        Initialize thread pool with configurable number of workers.

        Parameters
        ----------
        num_of_threads : int
            Default thread count if not overridden by config.
        """
        self.thread_pool_user_objects: dict = {}
        self.thread_pool_user_objects["default"] = ThreadPoolRequestInterface()
        self.num_of_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/threadpool/num_of_threads", num_of_threads
        )
        for i in range(self.num_of_threads):
            self.add_thread(target=self._thread_worker)
        atexit.register(self.stop_threads)

    def add_thread(self, target: types.FunctionType) -> None:
        """
        Add and start a worker thread.

        Parameters
        ----------
        target : FunctionType
            The worker function to execute.
        """
        thread = threading.Thread(
            target=target,
            name=f"WorkerThread-{len(self.thread_list)}",
            args=(
                len(self.thread_list),
                self.thread_local_data,
                self.input_queue,
                self.output_queue,
                self.thread_pool_user_objects,
            ),
            daemon=True,
        )
        thread.start()
        self.thread_list.append(thread)

    def stop_threads(self) -> None:
        """
        Stop all threads by sending sentinel messages.
        """
        for _ in range(len(self.thread_list)):
            self.input_queue.put("##STOP##")

    def wait_for_all(self) -> None:
        """
        Wait until all tasks are finished and shut down all threads.
        """
        self.input_queue.join()
        self.stop_threads()

    def register_message_handler(
        self, message_type: str, msg_handler: ThreadPoolRequestInterface
    ) -> None:
        """
        Register a handler for a specific message type.

        Parameters
        ----------
        message_type : str
            The type identifier.
        msg_handler : ThreadPoolRequestInterface
            The handler to register.
        """
        self.thread_pool_user_objects[message_type] = msg_handler

    def get_message_handler(self, message_type: str) -> ThreadPoolRequestInterface:
        """
        Retrieve handler for given message type.

        Parameters
        ----------
        message_type : str
            Type identifier.

        Returns
        -------
        ThreadPoolRequestInterface
            The handler.
        """
        return self.thread_pool_user_objects.get(
            message_type, self.thread_pool_user_objects["default"]
        )

    def _thread_worker(
        self,
        _,
        thread_local_data,
        input_queue,
        output_queue,
        thread_pool_user_objects,
    ) -> None:
        """
        Main worker loop that processes incoming messages.
        """
        for message in iter(input_queue.get, "##STOP##"):
            if not isinstance(message, ThreadPoolMessage):
                raise ValueError("Message is not a ThreadPoolMessage")

            result = ThreadPoolResult(
                message_type=message.message_type,
                id=message.id,
                original_message=message,
            )

            for attempt in range(message.retry_max):
                message.retry = attempt
                with TimerThread(message.timeout, threading.get_ident()):
                    try:
                        handler = thread_pool_user_objects.get(
                            message.message_type, thread_pool_user_objects["default"]
                        )
                        result_tuple = handler.process_request(
                            thread_local_data,
                            input_queue,
                            message,
                        )
                        if not isinstance(result_tuple, tuple) or len(result_tuple) != 2:
                            raise TypeError("process_request must return a tuple of (bool, data)")
                        success, data = result_tuple
                        result.success = success
                        result.data = data
                        if success:
                            break
                    except TimeoutError as e:
                        result.success = False
                        result.error = str(e)
                        result.exception_type = type(e).__name__
                        result.exception = e
                    except Exception as e:
                        result.success = False
                        result.error = str(e)
                        result.exception_type = type(e).__name__
                        result.exception = e

            result.retry_counter = attempt + 1

            if result.success and message.result_handler is not None:
                try:
                    result.data = message.result_handler.process_result(result.data, message)
                except Exception as e:
                    result.success = False
                    result.error = str(e)
                    result.exception_type = type(e).__name__
                    result.exception = e

            result.metadata = result.metadata or {}
            output_queue.put(result)
            input_queue.task_done()

    def get_input_queue(self) -> queue.Queue:
        """
        Return the input queue for sending messages.

        Returns
        -------
        queue.Queue
        """
        return self.input_queue

    def get_output_queue(self) -> queue.Queue:
        """
        Return the output queue for collecting results.

        Returns
        -------
        queue.Queue
        """
        return self.output_queue

    def get_results_from_output_queue(self) -> List[ThreadPoolResult]:
        """
        Drain and return all available results from the output queue.

        Returns
        -------
        List[ThreadPoolResult]
        """
        results = []
        while not self.output_queue.empty():
            results.append(self.output_queue.get())
        return results


class TimerThread:
    """
    Timeout context manager that forcefully terminates thread execution.

    Attributes
    ----------
    timeout : Optional[int]
        Timeout in seconds.
    thread_id : Optional[int]
        Target thread ID.
    timer : Optional[threading.Thread]
        Timer thread.
    """

    timeout: Optional[int] = None
    thread_id: Optional[int] = None
    timer: Optional[threading.Thread] = None

    def __init__(self, timeout: int, thread_id: int) -> None:
        self.timeout = timeout
        self.thread_id = thread_id
        self.timer = threading.Timer(
            interval=self.timeout,
            function=self.timeout_thread,
            args=[],
        )

    def __enter__(self):
        self.timer.start()

    def __exit__(self, _type, _value, _traceback):
        self.timer.cancel()

    def timeout_thread(self):
        import ctypes

        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
