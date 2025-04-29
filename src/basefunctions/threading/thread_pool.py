"""
=============================================================================

 Licensed Materials, Property of Ralph Vogl, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Decorators for simplifying ThreadPool usage

=============================================================================
"""

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
SENTINEL = object()

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


@dataclass
class ThreadPoolMessage:
    """
    Message object used for communication between threads.

    Attributes
    ----------
    id : str
        Unique identifier for the message.
    message_type : str
        Type of message to determine handler.
    retry_max : int
        Maximum number of retries on failure.
    timeout : int
        Timeout per request in seconds.
    content : Any
        Content payload of the message.
    result_handler : Optional[Any]
        Optional handler to process the result.
    retry : int
        Current retry count.
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
    Result object representing the outcome of thread processing.

    Attributes
    ----------
    message_type : str
        Type of message processed.
    id : str
        Identifier of the original message.
    success : bool
        Whether processing was successful.
    data : Any
        Result data from processing.
    metadata : Dict[str, Any]
        Additional metadata.
    original_message : Optional[ThreadPoolMessage]
        Reference to the original message.
    error : Optional[str]
        Error message, if any.
    exception_type : Optional[str]
        Type of exception, if any.
    retry_counter : int
        Number of attempts made.
    exception : Optional[Exception]
        Captured exception object.
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
    Interface for processing input messages in the ThreadPool.
    """

    def process_request(
        self, thread_local_data: Any, input_queue: queue.Queue, message: ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Processes an incoming request message.

        Parameters
        ----------
        thread_local_data : Any
            Thread-local storage.
        input_queue : queue.Queue
            Input queue for messages.
        message : ThreadPoolMessage
            Message to process.

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data.
        """
        return False, RuntimeError("process_request() not implemented")


class ThreadPoolResultInterface:
    """
    Interface for processing results in the ThreadPool.
    """

    def process_result(self, raw_data: Any, original_message: ThreadPoolMessage) -> Any:
        """
        Processes the raw result data.

        Parameters
        ----------
        raw_data : Any
            Data produced by processing the message.
        original_message : ThreadPoolMessage
            Original message that led to the result.

        Returns
        -------
        Any
            Processed result.
        """
        raise NotImplementedError


class ThreadPool:
    """
    ThreadPool implementation for concurrent task processing.
    """

    thread_list: List[threading.Thread] = []
    input_queue: queue.Queue = queue.Queue()
    output_queue: queue.Queue = queue.Queue()
    thread_local_data = threading.local()

    def __init__(self, num_of_threads: int = 5) -> None:
        """
        Initializes the ThreadPool.

        Parameters
        ----------
        num_of_threads : int
            Number of worker threads to start.
        """
        self.thread_pool_user_objects: dict = {}
        self.thread_pool_user_objects["default"] = ThreadPoolRequestInterface()
        self.num_of_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/threadpool/num_of_threads", num_of_threads
        )
        for _ in range(self.num_of_threads):
            self.add_thread(target=self._thread_worker)
        atexit.register(self.stop_threads)

    def add_thread(self, target: types.FunctionType) -> None:
        """
        Adds a new worker thread.

        Parameters
        ----------
        target : types.FunctionType
            Target function for the thread.
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
        Signals all worker threads to stop after current tasks.
        """
        active_threads = len(self.thread_list)
        sentinels_needed = max(active_threads - self.input_queue.qsize(), 0)
        for _ in range(sentinels_needed):
            self.input_queue.put(SENTINEL)

    def wait_for_all(self) -> None:
        """
        Waits for all tasks to complete and stops threads.
        """
        self.input_queue.join()
        self.stop_threads()

    def register_message_handler(
        self, message_type: str, msg_handler: ThreadPoolRequestInterface
    ) -> None:
        """
        Registers a custom handler for a specific message type.

        Parameters
        ----------
        message_type : str
            The type of messages the handler processes.
        msg_handler : ThreadPoolRequestInterface
            The handler to register.
        """
        self.thread_pool_user_objects[message_type] = msg_handler

    def get_message_handler(self, message_type: str) -> ThreadPoolRequestInterface:
        """
        Retrieves a handler for a given message type.

        Parameters
        ----------
        message_type : str
            Message type to retrieve handler for.

        Returns
        -------
        ThreadPoolRequestInterface
            Corresponding message handler.
        """
        return self.thread_pool_user_objects.get(
            message_type, self.thread_pool_user_objects["default"]
        )

    def _thread_worker(
        self, _, thread_local_data, input_queue, output_queue, thread_pool_user_objects
    ) -> None:
        """
        Worker method executed by each thread.
        """
        while True:
            message = input_queue.get()
            if message is SENTINEL:
                input_queue.task_done()
                break
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
                        success, data = handler.process_request(
                            thread_local_data, input_queue, message
                        )
                        if not isinstance((success, data), tuple):
                            raise TypeError("process_request must return a tuple of (bool, data)")
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
        Returns the input queue.

        Returns
        -------
        queue.Queue
            Input queue instance.
        """
        return self.input_queue

    def get_output_queue(self) -> queue.Queue:
        """
        Returns the output queue.

        Returns
        -------
        queue.Queue
            Output queue instance.
        """
        return self.output_queue

    def get_results_from_output_queue(self) -> List[ThreadPoolResult]:
        """
        Retrieves all results currently in the output queue.

        Returns
        -------
        List[ThreadPoolResult]
            List of ThreadPoolResult objects.
        """
        results = []
        while not self.output_queue.empty():
            results.append(self.output_queue.get())
        return results


class TimerThread:
    """
    Context manager that enforces a timeout on a thread.
    """

    timeout: Optional[int] = None
    thread_id: Optional[int] = None
    timer: Optional[threading.Thread] = None

    def __init__(self, timeout: int, thread_id: int) -> None:
        """
        Initializes the TimerThread.

        Parameters
        ----------
        timeout : int
            Timeout duration in seconds.
        thread_id : int
            Identifier of the thread to timeout.
        """
        self.timeout = timeout
        self.thread_id = thread_id
        self.timer = threading.Timer(
            interval=self.timeout,
            function=self.timeout_thread,
            args=[],
        )

    def __enter__(self):
        """
        Starts the timer when entering the context.
        """
        self.timer.start()

    def __exit__(self, _type, _value, _traceback):
        """
        Cancels the timer when exiting the context.
        """
        self.timer.cancel()

    def timeout_thread(self):
        """
        Raises a TimeoutError in the target thread.
        """
        import ctypes

        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
