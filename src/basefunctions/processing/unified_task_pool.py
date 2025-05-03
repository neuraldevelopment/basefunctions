"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unified task pool for handling both thread-based and process-based execution
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import atexit
import pickle
import queue
import subprocess
import threading
import types
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
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
@dataclass
class UnifiedTaskPoolMessage:
    """
    Message object used for communication between threads and processes.

    Attributes
    ----------
    id : str
        Unique identifier for the message.
    message_type : str
        Type of message to determine handler.
    execution_type : str
        Execution type - "thread" or "core".
    corelet_path : Optional[str]
        Optional path to the corelet containing the handler.
    retry_max : int
        Maximum number of retries on failure.
    timeout : int
        Timeout per request in seconds.
    content : Any
        Content payload of the message.
    retry : int
        Current retry count.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: str = ""
    execution_type: str = "thread"  # "thread" or "core"
    corelet_path: Optional[str] = None  # Path for dynamic module
    retry_max: int = 3
    timeout: int = 5
    content: Any = None
    retry: int = 0


@dataclass
class UnifiedTaskPoolResult:
    """
    Result object representing the outcome of task processing.

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
    original_message : Optional[UnifiedTaskPoolMessage]
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
    original_message: Optional[UnifiedTaskPoolMessage] = None
    error: Optional[str] = None
    exception_type: Optional[str] = None
    retry_counter: int = 0
    exception: Optional[Exception] = None


@dataclass
class TaskContext:
    """
    Context object for passing data to tasklets.

    Attributes
    ----------
    thread_local_data : Any
        Thread-local storage.
    input_queue : queue.Queue
        Input queue for messages.
    thread_id : int
        ID of the executing thread.
    process_id : Optional[int]
        Process ID for corelets.
    process_object : Optional[subprocess.Popen]
        Reference to the subprocess for corelets.
    """

    thread_local_data: Any
    input_queue: queue.Queue
    thread_id: int = field(default_factory=threading.get_ident)
    process_id: Optional[int] = None
    process_object: Optional[subprocess.Popen] = None


class TaskletRequestInterface(ABC):
    """
    Interface for processing input messages in the UnifiedTaskPool.

    Implementations must override the process_request method
    to handle specific message types.
    """

    @abstractmethod
    def process_request(
        self, context: TaskContext, message: UnifiedTaskPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Processes an incoming request message.

        Parameters
        ----------
        context : TaskContext
            Context containing thread-local storage and queues.
        message : UnifiedTaskPoolMessage
            Message to process.

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data.
        """
        pass


class DefaultTaskHandler(TaskletRequestInterface):
    """
    Default implementation of TaskletRequestInterface.
    Used when no specific handler is registered for a message type.
    """

    def process_request(
        self, context: TaskContext, message: UnifiedTaskPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Default implementation that returns an error.

        Parameters
        ----------
        context : TaskContext
            Context containing thread-local storage and queues.
        message : UnifiedTaskPoolMessage
            Message to process.

        Returns
        -------
        Tuple[bool, Any]
            Always returns (False, RuntimeError)
        """
        return False, RuntimeError(
            f"No handler implemented for message type: {message.message_type}"
        )


class TimerThread:
    """
    Context manager that enforces a timeout on a thread.

    This class creates a timer that will raise a TimeoutError in
    the specified thread if the context hasn't been exited before
    the timeout expires.
    """

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
            function=self._timeout_thread,
            args=[],
        )

    def __enter__(self):
        """
        Starts the timer when entering the context.

        Returns
        -------
        TimerThread
            Self reference for context manager
        """
        self.timer.start()
        return self

    def __exit__(self, _type, _value, _traceback):
        """
        Cancels the timer when exiting the context.

        Parameters
        ----------
        _type : type
            Exception type if raised
        _value : Exception
            Exception value if raised
        _traceback : traceback
            Traceback if exception raised

        Returns
        -------
        bool
            False to propagate exceptions
        """
        self.timer.cancel()
        return False

    def _timeout_thread(self):
        """
        Raises a TimeoutError in the target thread.
        """
        import ctypes

        basefunctions.get_logger(__name__).error("timeout in thread %d", self.thread_id)
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )


class UnifiedTaskPool(basefunctions.Subject):
    """
    UnifiedTaskPool implementation for concurrent task processing with both threads and processes.

    This class manages worker threads and processes for executing tasks concurrently,
    with support for both in-process execution via threads and out-of-process
    execution via subprocesses (corelets).
    """

    # Class-level sentinel object for signaling thread termination
    _SENTINEL = object()

    def __init__(self, num_of_threads: int = 5) -> None:
        """
        Initializes the UnifiedTaskPool.

        Parameters
        ----------
        num_of_threads : int, optional
            Number of worker threads to start, by default 5
        """
        # Initialize parent class
        super().__init__()

        # Initialize instance variables
        self.thread_list: List[threading.Thread] = []
        self.input_queue: queue.Queue = queue.Queue()
        self.output_queue: queue.Queue = queue.Queue()
        self.thread_local_data = threading.local()
        self.task_handlers: Dict[str, TaskletRequestInterface] = {}
        self.task_handlers["default"] = DefaultTaskHandler()

        # Get thread count from config
        self.num_of_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/taskpool/num_of_threads", num_of_threads
        )

        # Initialize corelet manager
        self.corelet_manager = basefunctions.CoreletManager()

        # Start worker threads
        self._start_worker_threads()

        # Register shutdown handler
        atexit.register(self.shutdown)

        basefunctions.get_logger(__name__).info(
            "taskpool initialized with %d threads", self.num_of_threads
        )

    def _start_worker_threads(self) -> None:
        """
        Starts the worker threads for the task pool.
        """
        for _ in range(self.num_of_threads):
            self.add_thread(target=self._thread_worker)

    def add_thread(self, target: types.FunctionType) -> None:
        """
        Adds a new worker thread to the pool.

        Parameters
        ----------
        target : types.FunctionType
            Target function for the thread to execute.
        """
        thread = threading.Thread(
            target=target,
            name=f"WorkerThread-{len(self.thread_list)}",
            args=(
                len(self.thread_list),
                self.thread_local_data,
                self.input_queue,
                self.output_queue,
                self.task_handlers,
            ),
            daemon=True,
        )
        thread.start()
        self.thread_list.append(thread)
        basefunctions.get_logger(__name__).info("started new thread: %s", thread.name)

    def stop_threads(self) -> None:
        """
        Signals all worker threads to stop after completing current tasks.

        This method sends a sentinel value to each worker thread, which
        will cause them to exit their processing loop when received.
        """
        active_threads = len(self.thread_list)
        sentinels_needed = max(active_threads - self.input_queue.qsize(), 0)
        for _ in range(sentinels_needed):
            self.input_queue.put(self._SENTINEL)
        basefunctions.get_logger(__name__).info("stop signal sent to %d threads", sentinels_needed)

    def shutdown(self) -> None:
        """
        Performs a graceful shutdown of the task pool.

        This method first waits for the input queue to be processed,
        then signals threads to stop, and finally waits for all threads
        to complete their work.
        """
        # Wait for queued tasks to complete
        try:
            # Use a timeout to avoid blocking indefinitely
            self.input_queue.join()
        except Exception as e:
            basefunctions.get_logger(__name__).error("error during queue join: %s", str(e))

        # Stop threads
        self.stop_threads()

        # Wait for threads to terminate (with timeout)
        for thread in self.thread_list:
            thread.join(timeout=2.0)

        # Check for any running corelets and terminate them
        if hasattr(self, "corelet_manager") and self.corelet_manager:
            for process_id in list(self.corelet_manager.active_processes.keys()):
                self.corelet_manager.terminate_corelet(process_id)

        basefunctions.get_logger(__name__).info("taskpool shutdown complete")

    def wait_for_all(self) -> None:
        """
        Waits for all tasks to complete and stops threads.

        This method blocks until all tasks in the input queue
        have been processed, then stops all worker threads.
        """
        self.input_queue.join()
        self.stop_threads()

    def register_message_handler(
        self, message_type: str, message_handler: TaskletRequestInterface
    ) -> None:
        """
        Registers a custom handler for a specific message type.

        The handler must implement the TaskletRequestInterface.

        Parameters
        ----------
        message_type : str
            The type of messages the handler processes.
        message_handler : TaskletRequestInterface
            The handler to register.

        Raises
        ------
        TypeError
            If message_handler does not implement TaskletRequestInterface
        """
        # Validate that the handler implements the required interface
        if not isinstance(message_handler, TaskletRequestInterface):
            raise TypeError(f"Handler for {message_type} must implement TaskletRequestInterface")

        self.task_handlers[message_type] = message_handler

    def get_message_handler(self, message_type: str) -> TaskletRequestInterface:
        """
        Retrieves a handler for a given message type.

        If no handler is registered for the specified message type,
        returns the default handler.

        Parameters
        ----------
        message_type : str
            Message type to retrieve handler for.

        Returns
        -------
        TaskletRequestInterface
            Corresponding message handler.
        """
        return self.task_handlers.get(message_type, self.task_handlers["default"])

    def register_observer_for_message_type(
        self, message_type: str, is_start: bool, observer: basefunctions.Observer
    ) -> None:
        """
        Registers an observer for a specific message type (start or stop event).

        This allows components to be notified when processing of a specific
        message type begins or ends.

        Parameters
        ----------
        message_type : str
            The type of message to observe.
        is_start : bool
            True for start message, False for stop message.
        observer : Observer
            The observer to register.
        """
        prefix = "start-" if is_start else "stop-"
        event_type = f"{prefix}{message_type}"
        self.attach_observer_for_event(event_type, observer)

    def _should_terminate_corelet(self, message_id: str) -> bool:
        """
        Checks if a corelet process should be terminated.

        Parameters
        ----------
        message_id : str
            ID of the message associated with the corelet

        Returns
        -------
        bool
            True if the corelet process should be terminated
        """
        return (
            hasattr(self, "corelet_manager")
            and self.corelet_manager
            and message_id in self.corelet_manager.active_processes
        )

    def _handle_thread_execution(
        self,
        context: TaskContext,
        message: UnifiedTaskPoolMessage,
        handler: TaskletRequestInterface,
    ) -> Tuple[bool, Any]:
        """
        Handles thread-based execution of a task.

        Parameters
        ----------
        context : TaskContext
            Execution context
        message : UnifiedTaskPoolMessage
            Message to process
        handler : TaskletRequestInterface
            Handler for the message type

        Returns
        -------
        Tuple[bool, Any]
            Success status and result data

        Raises
        ------
        TypeError
            If handler returns invalid result format
        """
        success, data = handler.process_request(context, message)

        # Validate handler return value
        if not isinstance(success, bool) or not isinstance((success, data), tuple):
            raise TypeError(
                f"Handler for {message.message_type} returned invalid result: "
                f"expected (bool, Any), got {type((success, data))}"
            )

        return success, data

    def _handle_corelet_execution(self, process: subprocess.Popen) -> Tuple[bool, Any]:
        """
        Handles corelet-based (subprocess) execution of a task.

        Parameters
        ----------
        process : subprocess.Popen
            Subprocess handle

        Returns
        -------
        Tuple[bool, Any]
            Success status and result data

        Raises
        ------
        RuntimeError
            If the subprocess exits with non-zero status
        """
        try:
            stdout, stderr = process.communicate()

            # Check process exit code
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise RuntimeError(f"Corelet failed with code {process.returncode}: {error_msg}")

            # Deserialize result
            if not stdout:
                raise RuntimeError("Corelet returned empty result")

            result_data = pickle.loads(stdout)
            success = result_data.get("success", False)
            data = result_data.get("data")

            return success, data

        except (subprocess.SubprocessError, EOFError, pickle.PickleError) as e:
            # Handle specific subprocess and deserialization errors
            basefunctions.get_logger(__name__).error("error in corelet communication: %s", str(e))
            raise RuntimeError(f"Corelet communication error: {str(e)}") from e

    def _thread_worker(
        self, thread_id, thread_local_data, input_queue, output_queue, task_handlers
    ) -> None:
        """
        Worker method executed by each thread.

        This method continuously takes messages from the input queue,
        processes them, and puts results in the output queue.

        Parameters
        ----------
        thread_id : int
            ID of the worker thread.
        thread_local_data : threading.local
            Thread-local storage.
        input_queue : queue.Queue
            Input queue for messages.
        output_queue : queue.Queue
            Output queue for results.
        task_handlers : dict
            Dictionary of task handlers.
        """
        logger = basefunctions.get_logger(__name__)

        try:
            while True:
                # Get message from queue
                message = input_queue.get()

                # Check for sentinel (stop signal)
                if message is self._SENTINEL:
                    input_queue.task_done()
                    logger.debug("thread %d received stop signal", thread_id)
                    break

                # Process the message
                self._process_message(
                    message, thread_local_data, input_queue, output_queue, task_handlers
                )

                # Mark task as done in queue
                input_queue.task_done()

        except Exception as e:
            logger.error("unhandled exception in worker thread %d: %s", thread_id, str(e))
            # Re-raise to let Python's default exception handler deal with it
            raise

    def _process_message(
        self, message, thread_local_data, input_queue, output_queue, task_handlers
    ) -> None:
        """
        Processes a single message from the input queue.

        Parameters
        ----------
        message : Any
            Message to process
        thread_local_data : threading.local
            Thread-local storage
        input_queue : queue.Queue
            Input queue
        output_queue : queue.Queue
            Output queue
        task_handlers : dict
            Dictionary of task handlers
        """
        logger = basefunctions.get_logger(__name__)

        # Validate message type
        if not isinstance(message, UnifiedTaskPoolMessage):
            logger.error("invalid message type: %s", type(message))
            raise ValueError("Message is not a UnifiedTaskPoolMessage")

        # Create context and result objects
        context = TaskContext(
            thread_local_data=thread_local_data,
            input_queue=input_queue,
            thread_id=threading.get_ident(),
        )

        result = UnifiedTaskPoolResult(
            message_type=message.message_type,
            id=message.id,
            original_message=message,
        )

        # Notify start observers
        start_message_type = f"start-{message.message_type}"
        self.notify_observers(start_message_type, result)

        # Initialize variables
        process = None
        attempt = 0

        # Retry loop
        for attempt in range(message.retry_max):
            message.retry = attempt

            try:
                # Start corelet if needed
                if message.execution_type == "core":
                    process = self.corelet_manager.start_corelet(message)
                    if not process:
                        raise RuntimeError(f"Failed to start corelet for message {message.id}")

                    # Update context with process info
                    context.process_id = process.pid
                    context.process_object = process

                # Execute with timeout
                with TimerThread(message.timeout, threading.get_ident()):
                    if message.execution_type == "thread":
                        # Thread execution
                        handler = task_handlers.get(message.message_type, task_handlers["default"])
                        success, data = self._handle_thread_execution(context, message, handler)
                    else:
                        # Corelet execution
                        success, data = self._handle_corelet_execution(process)

                    # Store result
                    result.success = success
                    result.data = data

                    # Break retry loop if successful
                    if success:
                        break

            except TimeoutError as e:
                # Handle timeout
                if self._should_terminate_corelet(message.id):
                    self.corelet_manager.terminate_corelet(message.id)

                result.success = False
                result.error = f"Timeout after {message.timeout} seconds"
                result.exception_type = type(e).__name__
                result.exception = e
                logger.error(
                    "timeout processing message %s (attempt %d/%d)",
                    message.id,
                    attempt + 1,
                    message.retry_max,
                )

            except Exception as e:
                # Handle other exceptions
                if self._should_terminate_corelet(message.id):
                    self.corelet_manager.terminate_corelet(message.id)

                result.success = False
                result.error = str(e)
                result.exception_type = type(e).__name__
                result.exception = e
                logger.error(
                    "exception in %s execution: %s (attempt %d/%d)",
                    message.execution_type,
                    str(e),
                    attempt + 1,
                    message.retry_max,
                    exc_info=True,
                )

        # Update retry counter
        result.retry_counter = attempt + 1

        # Ensure metadata dictionary exists
        result.metadata = result.metadata or {}

        # Put result in output queue
        output_queue.put(result)

        # Notify stop observers
        stop_message_type = f"stop-{message.message_type}"
        self.notify_observers(stop_message_type, result)

    def get_input_queue(self) -> queue.Queue:
        """
        Returns the input queue for task submission.

        This queue is used to submit new tasks to the task pool.

        Returns
        -------
        queue.Queue
            Input queue instance for submitting tasks.
        """
        return self.input_queue

    def get_output_queue(self) -> queue.Queue:
        """
        Returns the output queue for retrieving task results.

        This queue contains results of completed tasks.

        Returns
        -------
        queue.Queue
            Output queue instance containing task results.
        """
        return self.output_queue

    def get_results_from_output_queue(self) -> List[UnifiedTaskPoolResult]:
        """
        Retrieves all results currently in the output queue.

        This method is non-blocking and returns all available results
        at the time of calling.

        Returns
        -------
        List[UnifiedTaskPoolResult]
            List of UnifiedTaskPoolResult objects.
        """
        results = []
        try:
            while True:
                results.append(self.output_queue.get_nowait())
                self.output_queue.task_done()
        except queue.Empty:
            pass

        return results

    def submit_task(self, message: UnifiedTaskPoolMessage) -> str:
        """
        Submits a task to the task pool for processing.

        Parameters
        ----------
        message : UnifiedTaskPoolMessage
            The message to process

        Returns
        -------
        str
            The message ID

        Raises
        ------
        TypeError
            If message is not a UnifiedTaskPoolMessage
        """
        if not isinstance(message, UnifiedTaskPoolMessage):
            raise TypeError("Message must be a UnifiedTaskPoolMessage")

        self.input_queue.put(message)
        return message.id
