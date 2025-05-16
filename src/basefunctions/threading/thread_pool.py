"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Improved ThreadPool implementation with symmetric handler handling

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import atexit
import os
import pickle
import queue
import subprocess
import threading
import types
import uuid
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict, Tuple, Union, Type
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
    message object used for communication between threads.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: str = ""
    retry_max: int = field(default=3)
    timeout: int = 5
    content: Any = None
    retry: int = 0
    corelet_filename: Optional[str] = None


@dataclass
class ThreadPoolResult:
    """
    result object representing the outcome of thread processing.
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


@dataclass
class ThreadPoolContext:
    """
    context object passed to process_request with context-specific data.
    """

    thread_local_data: Any = None
    input_queue: Optional[queue.Queue] = None
    process_info: Optional[Dict[str, Any]] = None


class ThreadPoolRequestInterface:
    """
    interface for processing input messages in the threadpool.
    """

    def process_request(
        self, context: ThreadPoolContext, message: ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        processes an incoming request message.
        """
        return False, RuntimeError("process_request() not implemented")


@dataclass
class HandlerRegistration:
    """
    registration info for a message handler.
    """

    handler_type: str  # "thread" or "core"
    handler_info: Union[Type[ThreadPoolRequestInterface], str]  # Class or path to file


class ThreadPool(basefunctions.Subject):
    """
    improved threadpool implementation for concurrent task processing.
    """

    def __init__(self, num_of_threads: int = 5) -> None:
        """
        initializes the threadpool.
        """
        basefunctions.Subject.__init__(self)
        # Instanzvariablen statt Klassenvariablen
        self.thread_list: List[threading.Thread] = []
        self.input_queue: queue.Queue = queue.Queue()
        self.output_queue: queue.Queue = queue.Queue()
        self.thread_local_data = threading.local()
        self.handler_registry: Dict[str, HandlerRegistration] = {}

        self.num_of_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/threadpool/num_of_threads", num_of_threads
        )
        for _ in range(self.num_of_threads):
            self.add_thread(target=self._thread_worker)
        atexit.register(self.stop_threads)
        basefunctions.get_logger(__name__).info(
            "threadpool initialized with %d threads", self.num_of_threads
        )

    def add_thread(self, target: types.FunctionType) -> None:
        """
        adds a new worker thread.
        """
        thread = threading.Thread(
            target=target,
            name=f"WorkerThread-{len(self.thread_list)}",
            args=(
                len(self.thread_list),
                self.thread_local_data,
                self.input_queue,
                self.output_queue,
                self.handler_registry,
            ),
            daemon=True,
        )
        thread.start()
        self.thread_list.append(thread)
        basefunctions.get_logger(__name__).info("started new thread: %s", thread.name)

    def stop_threads(self) -> None:
        """
        signals all worker threads to stop after current tasks.
        """
        active_threads = len(self.thread_list)
        sentinels_needed = max(active_threads - self.input_queue.qsize(), 0)
        for _ in range(sentinels_needed):
            self.input_queue.put(SENTINEL)
        basefunctions.get_logger(__name__).info("stop signal sent to %d threads", sentinels_needed)

    def wait_for_all(self) -> None:
        """
        waits for all tasks to complete and stops threads.
        """
        self.input_queue.join()
        self.stop_threads()

    def register_handler(
        self,
        message_type: str,
        handler: Union[Type[ThreadPoolRequestInterface], str],
        handler_type: str,
    ) -> None:
        """
        registers a handler for a specific message type.

        parameters
        ----------
        message_type : str
            the type of messages the handler processes
        handler : Union[Type[ThreadPoolRequestInterface], str]
            either a handler class for thread execution or a path to a corelet file
        handler_type : str
            either "thread" or "core"
        """
        if handler_type not in ["thread", "core"]:
            raise ValueError(f"invalid handler_type: {handler_type}, must be 'thread' or 'core'")

        if handler_type == "thread" and not (
            isinstance(handler, type) and issubclass(handler, ThreadPoolRequestInterface)
        ):
            raise TypeError("thread handler must be a ThreadPoolRequestInterface subclass")

        if handler_type == "core" and not isinstance(handler, str):
            raise TypeError("core handler must be a string path to the corelet file")

        if handler_type == "core" and not os.path.exists(handler):
            raise FileNotFoundError(f"corelet file not found: {handler}")

        self.handler_registry[message_type] = HandlerRegistration(
            handler_type=handler_type, handler_info=handler
        )

    def _create_thread_handler(
        self, message_type: str, thread_local_data: threading.local
    ) -> ThreadPoolRequestInterface:
        """
        creates or retrieves a thread-local handler instance for a given message type.

        parameters
        ----------
        message_type : str
            message type to create handler for
        thread_local_data : threading.local
            thread-local storage to cache handler instances

        returns
        -------
        ThreadPoolRequestInterface
            thread-local handler instance
        """
        if message_type not in self.handler_registry:
            raise ValueError(f"no handler registered for message type: {message_type}")

        registration = self.handler_registry[message_type]
        if registration.handler_type != "thread":
            raise ValueError(f"handler for {message_type} is not a thread handler")

        # Initialize handler cache in thread_local_data if it doesn't exist
        if not hasattr(thread_local_data, "handler_cache"):
            thread_local_data.handler_cache = {}

        # Create handler instance only if it doesn't exist in the cache
        if message_type not in thread_local_data.handler_cache:
            handler_class = registration.handler_info
            thread_local_data.handler_cache[message_type] = handler_class()

        # Return cached instance
        return thread_local_data.handler_cache[message_type]

    def _get_corelet_path(self, message_type: str) -> str:
        """
        gets the corelet path for a given message type.

        parameters
        ----------
        message_type : str
            message type to get corelet path for

        returns
        -------
        str
            path to the corelet file
        """
        if message_type not in self.handler_registry:
            raise ValueError(f"no handler registered for message type: {message_type}")

        registration = self.handler_registry[message_type]
        if registration.handler_type != "core":
            raise ValueError(f"handler for {message_type} is not a core handler")

        return registration.handler_info

    def _process_request_core(
        self, context: ThreadPoolContext, message: ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        processes a request in a separate process as a corelet.
        """
        # get corelet path from registration
        corelet_path = self._get_corelet_path(message.message_type)

        # create subprocess with pipes for communication
        process = None
        try:
            # prepare message data
            message_data = pickle.dumps(message)

            # start subprocess
            process = subprocess.Popen(
                ["python", corelet_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # store process in context for timeout handling
            if context:
                context.process_info = {"process": process, "type": "corelet"}

            # send message data to subprocess
            process.stdin.write(message_data)
            process.stdin.flush()
            process.stdin.close()

            # read result from stdout
            result_data = process.stdout.read()

            # check process exit code
            return_code = process.wait()
            if return_code != 0:
                error_output = process.stderr.read()
                basefunctions.get_logger(__name__).error(
                    "corelet process exited with code %d: %s", return_code, error_output
                )
                return False, f"corelet process failed with exit code {return_code}"

            # check if we got a result
            if result_data:
                result = pickle.loads(result_data)
                return result.success, result.data
            else:
                return False, "no result received from corelet process"

        except Exception as e:
            return False, str(e)

    def _process_request_thread(
        self, context: ThreadPoolContext, message: ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        processes a request in the current thread.
        """
        # Create a new handler instance for this request
        handler = self._create_thread_handler(message.message_type, context.thread_local_data)
        return handler.process_request(context, message)

    def _thread_worker(
        self, _, thread_local_data, input_queue, output_queue, handler_registry
    ) -> None:
        """
        worker method executed by each thread.
        """
        while True:
            message = input_queue.get()
            if message is SENTINEL:
                input_queue.task_done()
                break
            if not isinstance(message, ThreadPoolMessage):
                raise ValueError("message is not a ThreadPoolMessage")

            result = ThreadPoolResult(
                message_type=message.message_type,
                id=message.id,
                original_message=message,
            )

            # Notify observers of start
            self.notify_observers(f"start_{message.message_type}", message)

            attempt = 0
            for attempt in range(message.retry_max):
                message.retry = attempt
                # Prepare context for consistent interface
                context = ThreadPoolContext(
                    thread_local_data=thread_local_data, input_queue=input_queue
                )

                # Get handler type from registration
                if message.message_type not in handler_registry:
                    raise ValueError(
                        f"no handler registered for message type: {message.message_type}"
                    )

                handler_type = handler_registry[message.message_type].handler_type

                with TimerThread(message.timeout, threading.get_ident()):
                    try:
                        # Process based on handler type
                        if handler_type == "thread":
                            success, data = self._process_request_thread(context, message)
                        elif handler_type == "core":
                            success, data = self._process_request_core(context, message)
                        else:
                            raise ValueError(f"unknown handler_type: {handler_type}")

                        if not isinstance(success, bool):
                            raise TypeError("process_request success must be a boolean")

                        result.success = success
                        result.data = data
                        if success:
                            break
                    except TimeoutError as e:
                        result.success = False
                        result.error = str(e)
                        result.exception_type = type(e).__name__
                        result.exception = e

                        # Kill subprocess in case of corelet
                        if (
                            handler_type == "core"
                            and context.process_info
                            and context.process_info.get("process")
                        ):
                            process = context.process_info.get("process")
                            process.kill()
                            basefunctions.get_logger(__name__).info(
                                "killed corelet subprocess due to timeout"
                            )

                    except Exception as e:
                        result.success = False
                        result.error = str(e)
                        result.exception_type = type(e).__name__
                        result.exception = e
                        basefunctions.get_logger(__name__).error(
                            "exception in thread worker: %s", str(e)
                        )

            result.retry_counter = attempt + 1
            result.metadata = result.metadata or {}
            output_queue.put(result)

            # Notify observers of stop with both the message and the result
            self.notify_observers(f"stop_{message.message_type}", message, result)

            input_queue.task_done()

    def get_input_queue(self) -> queue.Queue:
        """
        returns the input queue.
        """
        return self.input_queue

    def get_output_queue(self) -> queue.Queue:
        """
        returns the output queue.
        """
        return self.output_queue

    def get_results_from_output_queue(self) -> List[ThreadPoolResult]:
        """
        retrieves all results currently in the output queue.
        """
        results = []
        while not self.output_queue.empty():
            results.append(self.output_queue.get())
        return results

    def submit_task(
        self, message_type: str, content: Any = None, timeout: int = 5, retry_max: int = 3
    ) -> str:
        """
        convenience method to submit a task to the threadpool.

        returns the message id.
        """
        # Check if handler is registered
        if message_type not in self.handler_registry:
            raise ValueError(f"no handler registered for message type: {message_type}")

        # Create message
        message = ThreadPoolMessage(
            message_type=message_type, content=content, timeout=timeout, retry_max=retry_max
        )

        # Submit to queue
        self.input_queue.put(message)
        return message.id


class TimerThread:
    """
    context manager that enforces a timeout on a thread.
    """

    timeout: Optional[int] = None
    thread_id: Optional[int] = None
    timer: Optional[threading.Thread] = None

    def __init__(self, timeout: int, thread_id: int) -> None:
        """
        initializes the timerthread.
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
        starts the timer when entering the context.
        """
        self.timer.start()

    def __exit__(self, _type, _value, _traceback):
        """
        cancels the timer when exiting the context.
        """
        self.timer.cancel()

    def timeout_thread(self):
        """
        raises a timeouterror in the target thread.
        """
        import ctypes

        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
        basefunctions.get_logger(__name__).error("timeout in thread %d", self.thread_id)
