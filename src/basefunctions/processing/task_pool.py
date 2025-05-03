"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Main implementation of the unified task pool system
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
import time
import types
from typing import Any, Dict, List, Tuple

import basefunctions
from .handlers import DefaultTaskHandler
from .interfaces import TaskContext, TaskletRequestInterface
from .message_types import UnifiedTaskPoolMessage, UnifiedTaskPoolResult
from .timer import TimerThread


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

        # Initialize state tracking variables
        self.accepting_tasks = True
        self.is_shutdown = False
        self.shutdown_event = threading.Event()

        # Get thread count from config
        self.num_of_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/taskpool/num_of_threads", num_of_threads
        )

        # Initialize corelet manager
        self.corelet_manager = basefunctions.CoreletManager()

        # Start worker threads
        self._start_worker_threads()

        # Register shutdown handler
        self._atexit_registered = True
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
                self.shutdown_event,  # Pass the shutdown event to the thread
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
        if self.is_shutdown:
            return

        active_threads = len(self.thread_list)
        sentinels_needed = active_threads  # Always send enough sentinels for all threads

        try:
            for _ in range(sentinels_needed):
                self.input_queue.put(self._SENTINEL)
            basefunctions.get_logger(__name__).info(
                "stop signal sent to %d threads", sentinels_needed
            )
        except Exception as e:
            basefunctions.get_logger(__name__).warning("error sending stop signals: %s", str(e))

    def shutdown(self, timeout=5):
        """
        Complete shutdown of the ThreadPool.

        Parameters
        ----------
        timeout : float
            Maximum wait time per thread in seconds.
        """
        logger = basefunctions.get_logger(__name__)

        # Prevent multiple shutdown calls
        if self.is_shutdown:
            logger.debug("shutdown already in progress, ignoring duplicate call")
            return

        self.is_shutdown = True
        logger.info("starting taskpool shutdown sequence")

        # 1. Stop accepting new tasks
        self.accepting_tasks = False

        # 2. Signal shutdown to all threads
        self.shutdown_event.set()

        # 3. Terminate all active corelets
        try:
            if hasattr(self, "corelet_manager") and self.corelet_manager:
                active_processes = list(self.corelet_manager.active_processes.keys())
                for process_id in active_processes:
                    try:
                        self.corelet_manager.terminate_corelet(process_id)
                    except Exception as e:
                        logger.warning("error terminating corelet %s: %s", process_id, str(e))
        except Exception as e:
            logger.warning("error during corelet cleanup: %s", str(e))

        # 4. Send sentinels to all threads to ensure they exit
        try:
            # Always send enough sentinels for all threads
            for _ in range(len(self.thread_list)):
                try:
                    self.input_queue.put(self._SENTINEL)
                except Exception as e:
                    logger.warning("error sending sentinel: %s", str(e))
        except Exception as e:
            logger.warning("error during sentinel distribution: %s", str(e))

        # 5. Wait for threads to terminate with timeout
        try:
            active_threads = list(self.thread_list)
            for thread in active_threads:
                try:
                    if thread.is_alive():
                        thread.join(timeout=timeout)
                except Exception as e:
                    logger.warning("error joining thread %s: %s", thread.name, str(e))
        except Exception as e:
            logger.warning("error during thread termination: %s", str(e))

        # 6. Clear thread list
        self.thread_list.clear()

        # 7. Unregister from atexit
        if hasattr(self, "_atexit_registered") and self._atexit_registered:
            try:
                atexit.unregister(self.shutdown)
                self._atexit_registered = False
            except Exception as e:
                logger.warning("error unregistering atexit handler: %s", str(e))

        logger.info("taskpool shutdown complete")

    def wait_for_all(self) -> None:
        """
        Waits for all tasks to complete and stops threads.

        This method blocks until all tasks in the input queue
        have been processed, then stops all worker threads.
        """
        logger = basefunctions.get_logger(__name__)

        try:
            # Check if queue is empty to avoid potential deadlocks
            if not self.input_queue.empty():
                logger.info("waiting for all tasks to complete")
                try:
                    # Use a timeout-based approach to avoid possible deadlocks
                    start_time = time.time()
                    max_wait = 60  # Maximum wait time in seconds

                    while not self.input_queue.empty() and time.time() - start_time < max_wait:
                        time.sleep(0.1)

                    # If there are still items in the queue after timeout, log warning
                    if not self.input_queue.empty():
                        logger.warning("some tasks still in queue after %d seconds", max_wait)
                except Exception as e:
                    logger.warning("error waiting for tasks: %s", str(e))
        except Exception as e:
            logger.warning("error waiting for tasks: %s", str(e))

        # Stop the threads
        self.stop_threads()

        # Additional wait for threads to exit
        start_time = time.time()
        max_thread_wait = 10  # seconds

        while time.time() - start_time < max_thread_wait and any(
            t.is_alive() for t in self.thread_list
        ):
            time.sleep(0.1)

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
        self,
        thread_id,
        thread_local_data,
        input_queue,
        output_queue,
        task_handlers,
        shutdown_event,
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
        shutdown_event : threading.Event
            Event signaling that shutdown is in progress.
        """
        logger = basefunctions.get_logger(__name__)
        logger.debug("worker thread %d started", thread_id)

        try:
            while not shutdown_event.is_set():
                try:
                    # Use a shorter timeout to be more responsive to shutdown
                    message = input_queue.get(block=True, timeout=0.2)
                except queue.Empty:
                    continue

                # Check for sentinel (stop signal)
                if message is self._SENTINEL:
                    input_queue.task_done()
                    logger.debug("thread %d received stop signal", thread_id)
                    break

                # Process the message
                try:
                    self._process_message(
                        message, thread_local_data, input_queue, output_queue, task_handlers
                    )
                except Exception as e:
                    logger.error("error processing message: %s", str(e), exc_info=True)
                    # Mark as done even if processing failed
                    input_queue.task_done()
                    continue

                # Mark task as done in queue
                input_queue.task_done()

                # Check again for shutdown after processing a message
                if shutdown_event.is_set():
                    logger.debug("thread %d detected shutdown event", thread_id)
                    break

        except Exception as e:
            logger.error(
                "unhandled exception in worker thread %d: %s", thread_id, str(e), exc_info=True
            )

        logger.debug("worker thread %d exiting", thread_id)

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
        RuntimeError
            If the task pool is shutting down
        """
        if not isinstance(message, UnifiedTaskPoolMessage):
            raise TypeError("Message must be a UnifiedTaskPoolMessage")

        if not self.accepting_tasks:
            raise RuntimeError("Task pool is shutting down, not accepting new tasks")

        self.input_queue.put(message)
        return message.id
