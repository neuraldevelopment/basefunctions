"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Thread pool implementation using event system for task management

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import atexit
import logging
import pickle
import queue
import subprocess
import threading
import os
from typing import Any, Dict, List, Optional, Tuple, Type, Union

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
_DEFAULT_INSTANCE = None

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ThreadPool(basefunctions.EventHandler):
    """
    Thread pool implementation that uses the event system for task distribution.

    This class manages a pool of worker threads and integrates with the
    EventBus to handle task requests and collect results.
    """

    __slots__ = (
        "_num_threads",
        "_thread_list",
        "_input_queue",
        "_output_queue",
        "_event_bus",
        "_handler_registry",
        "_subscriptions",
        "_logger",
        "_active",
        "_worker_threads",
        "_thread_local_data",
    )

    def __init__(self, num_threads: int = 5, event_bus: Optional[basefunctions.EventBus] = None):
        """
        Initialize a new thread pool.

        Parameters
        ----------
        num_threads : int, default=5
            Number of worker threads to create
        event_bus : basefunctions.EventBus, optional
            EventBus instance to use (uses default if not provided)
        """
        # Initialize queues for internal communication
        self._input_queue = queue.Queue()
        self._output_queue = queue.Queue()

        # Get or create event bus
        self._event_bus = event_bus or basefunctions.get_event_bus()

        # Handler registry for task types
        self._handler_registry: Dict[str, Type[basefunctions.ThreadPoolRequestInterface]] = {}

        # Setup worker threads
        self._thread_list: List[threading.Thread] = []
        self._worker_threads: Dict[str, threading.Thread] = {}
        self._thread_local_data = threading.local()

        # Set number of threads (with config override)
        self._num_threads = basefunctions.ConfigHandler().get_config_value(
            "basefunctions/threadpool/num_of_threads", num_threads
        )

        # Tracking subscriptions for cleanup
        self._subscriptions = basefunctions.CompositeSubscription()

        # Logger
        self._logger = logging.getLogger(__name__)

        # Active flag
        self._active = False

        # Register with event bus
        self._subscribe_to_events()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def _subscribe_to_events(self) -> None:
        """
        Subscribe to relevant events in the event bus.
        """
        # Subscribe to task request events
        subscription = self._event_bus.register(basefunctions.ThreadPoolTaskEvent.event_type, self)
        self._subscriptions.add(subscription)

        self._logger.info("Subscribed to thread pool task events")

    def start(self) -> None:
        """
        Start the thread pool and initialize worker threads.
        """
        if self._active:
            return

        self._active = True

        # Create and start worker threads
        for i in range(self._num_threads):
            thread_name = f"WorkerThread-{i}"
            thread = threading.Thread(
                target=self._worker_thread_main, name=thread_name, args=(i,), daemon=True
            )
            thread.start()
            self._thread_list.append(thread)
            self._worker_threads[thread_name] = thread

        self._logger.info(f"Thread pool started with {self._num_threads} worker threads")

    def shutdown(self) -> None:
        """
        Shutdown the thread pool and stop all worker threads.
        """
        if not self._active:
            return

        self._active = False

        # Unsubscribe from event bus
        self._subscriptions.unsubscribe_all()

        # Signal all worker threads to stop
        for _ in range(len(self._thread_list)):
            self._input_queue.put(None)  # Sentinel to stop threads

        # Wait for threads to finish
        for thread in self._thread_list:
            if thread.is_alive():
                thread.join(timeout=2.0)  # Give threads 2 seconds to finish

        self._thread_list.clear()
        self._worker_threads.clear()

        self._logger.info("Thread pool shutdown completed")

    def handle(self, event: basefunctions.Event) -> None:
        """
        Handle incoming task request events.

        This method is called by the EventBus when a ThreadPoolTaskEvent is published.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle (should be a ThreadPoolTaskEvent)
        """
        if not isinstance(event, basefunctions.ThreadPoolTaskEvent):
            return

        if not self._active:
            self.start()

        # Place the task in the input queue for worker threads
        self._input_queue.put(event)
        self._logger.debug(f"Queued task {event.task_id} of type {event.task_type}")

    def get_priority(self) -> int:
        """
        Get the priority of this handler.

        Returns
        -------
        int
            The priority of this handler (higher is executed first)
        """
        return 100  # High priority to ensure thread pool gets tasks first

    def register_handler(
        self, task_type: str, handler_class: Type[basefunctions.ThreadPoolRequestInterface]
    ) -> None:
        """
        Register a handler for a specific task type.

        Parameters
        ----------
        task_type : str
            The type of tasks this handler can process
        handler_class : Type[basefunctions.ThreadPoolRequestInterface]
            The handler class for processing tasks

        Raises
        ------
        TypeError
            If handler_class is not a ThreadPoolRequestInterface subclass
        """
        if not (
            isinstance(handler_class, type)
            and issubclass(handler_class, basefunctions.ThreadPoolRequestInterface)
        ):
            raise TypeError("Handler must be a ThreadPoolRequestInterface subclass")

        self._handler_registry[task_type] = handler_class
        self._logger.info(
            f"Registered handler '{handler_class.__name__}' for task type '{task_type}'"
        )

    def submit_task(
        self,
        task_type: str,
        content: Any = None,
        timeout: int = 5,
        retry_max: int = 3,
        corelet_filename: Optional[str] = None,
    ) -> str:
        """
        Submit a task for execution.

        Parameters
        ----------
        task_type : str
            The type of task to execute
        content : Any, optional
            The content/payload of the task
        timeout : int, default=5
            Timeout in seconds for task execution
        retry_max : int, default=3
            Maximum number of retry attempts
        corelet_filename : str, optional
            Path to corelet file for process-based execution

        Returns
        -------
        str
            The unique ID of the submitted task

        Raises
        ------
        ValueError
            If no handler is registered for the task type
        """
        if task_type not in self._handler_registry and not corelet_filename:
            raise ValueError(f"No handler registered for task type: {task_type}")

        # Create task request event
        task_event = basefunctions.ThreadPoolTaskEvent(
            task_type=task_type,
            content=content,
            source=self,
            timeout=timeout,
            retry_max=retry_max,
            corelet_filename=corelet_filename,
        )

        # Publish to event bus
        self._event_bus.publish(task_event)

        return task_event.task_id

    def _worker_thread_main(self, thread_idx: int) -> None:
        """
        Main function for worker threads.

        Parameters
        ----------
        thread_idx : int
            The index of this worker thread
        """
        thread_name = threading.current_thread().name
        thread_id = threading.get_ident()
        self._logger.debug(f"Worker thread {thread_name} started")

        while self._active:
            try:
                # Get a task from the input queue
                task = self._input_queue.get(block=True, timeout=1.0)

                # Check for sentinel
                if task is None:
                    self._input_queue.task_done()
                    break

                if not isinstance(task, basefunctions.ThreadPoolTaskEvent):
                    self._input_queue.task_done()
                    continue

                # Process the task
                self._process_task(task, thread_id)

                # Mark task as done
                self._input_queue.task_done()

            except queue.Empty:
                # Timeout on queue get, check if still active
                continue

            except Exception as e:
                self._logger.error(f"Error in worker thread {thread_name}: {str(e)}")
                if self._input_queue.unfinished_tasks > 0:
                    self._input_queue.task_done()

        self._logger.debug(f"Worker thread {thread_name} stopped")

    def _process_task(self, task: basefunctions.ThreadPoolTaskEvent, thread_id: int) -> None:
        """
        Process a task using the appropriate handler.

        Parameters
        ----------
        task : basefunctions.ThreadPoolTaskEvent
            The task to process
        thread_id : int
            ID of the current thread
        """
        task_id = task.task_id
        task_type = task.task_type

        self._logger.debug(f"Processing task {task_id} of type {task_type}")

        # Create context for task execution
        context = basefunctions.ThreadPoolContext(
            thread_local_data=self._thread_local_data, input_queue=self._input_queue
        )

        # Initialize result variables
        success = False
        result_data = None
        error = None
        exception_type = None
        exception = None

        # Process with retry
        for attempt in range(task.retry_max):
            # Update retry count
            task.increment_retry()

            try:
                # Use TimerThread as context manager to enforce timeout
                with basefunctions.TimerThread(task.timeout, thread_id):
                    # Determine if this is a corelet task
                    if task.is_corelet_task():
                        # Process as corelet
                        success, result_data = self._process_corelet_task(context, task)
                    else:
                        # Process using registered handler
                        success, result_data = self._process_handler_task(context, task)

                # If successful, break the retry loop
                if success:
                    break

            except TimeoutError as e:
                success = False
                result_data = None
                error = f"Task execution timed out after {task.timeout} seconds"
                exception_type = "TimeoutError"
                exception = e
                self._logger.error(
                    f"Timeout processing task {task_id} (attempt {attempt+1}/{task.retry_max})"
                )

                # Kill subprocess in case of corelet
                if task.is_corelet_task() and hasattr(context, "process_info"):
                    process = getattr(context, "process_info", {}).get("process")
                    if process and hasattr(process, "kill"):
                        process.kill()
                        self._logger.info(f"Killed corelet subprocess due to timeout")

            except Exception as e:
                success = False
                result_data = None
                error = str(e)
                exception_type = type(e).__name__
                exception = e
                self._logger.error(
                    f"Error processing task {task_id} (attempt {attempt+1}/{task.retry_max}): {error}"
                )

            # If we're not retrying or max retries reached, break
            if success or attempt >= task.retry_max - 1:
                break

            self._logger.info(f"Retrying task {task_id} ({attempt+1}/{task.retry_max})")

        # Create result event
        result_event = basefunctions.ThreadPoolResultEvent(
            original_task=task,
            success=success,
            data=result_data,
            error=error,
            exception_type=exception_type,
            exception=exception,
        )

        # Place result in output queue
        self._output_queue.put(result_event)

        # Publish result event to event bus
        self._event_bus.publish(result_event)

    def _process_handler_task(
        self, context: basefunctions.ThreadPoolContext, task: basefunctions.ThreadPoolTaskEvent
    ) -> Tuple[bool, Any]:
        """
        Process a task using a registered handler.

        Parameters
        ----------
        context : basefunctions.ThreadPoolContext
            The context for task execution
        task : basefunctions.ThreadPoolTaskEvent
            The task to process

        Returns
        -------
        Tuple[bool, Any]
            Success status and result data

        Raises
        ------
        ValueError
            If no handler is registered for the task type
        """
        task_type = task.task_type

        if task_type not in self._handler_registry:
            raise ValueError(f"No handler registered for task type: {task_type}")

        # Get handler class
        handler_class = self._handler_registry[task_type]

        # Create handler instance
        handler = handler_class()

        # Create thread pool message for backward compatibility
        message = basefunctions.ThreadPoolMessage(
            id=task.task_id,
            message_type=task.task_type,
            content=task.content,
            retry=task.retry_count,
            retry_max=task.retry_max,
            timeout=task.timeout,
        )

        # Execute handler
        return handler.process_request(context, message)

    def _process_corelet_task(
        self, context: basefunctions.ThreadPoolContext, task: basefunctions.ThreadPoolTaskEvent
    ) -> Tuple[bool, Any]:
        """
        Process a task using a corelet subprocess.

        Parameters
        ----------
        context : basefunctions.ThreadPoolContext
            The context for task execution
        task : basefunctions.ThreadPoolTaskEvent
            The task to process

        Returns
        -------
        Tuple[bool, Any]
            Success status and result data

        Raises
        ------
        FileNotFoundError
            If the corelet file does not exist
        """
        corelet_filename = task.corelet_filename

        if not corelet_filename or not os.path.exists(corelet_filename):
            raise FileNotFoundError(f"Corelet file not found: {corelet_filename}")

        # Create thread pool message for backward compatibility
        message = basefunctions.ThreadPoolMessage(
            id=task.task_id,
            message_type=task.task_type,
            content=task.content,
            retry=task.retry_count,
            retry_max=task.retry_max,
            timeout=task.timeout,
            corelet_filename=corelet_filename,
        )

        # Prepare message data
        message_data = pickle.dumps(message)

        # Create subprocess with pipes for communication
        process = subprocess.Popen(
            ["python", corelet_filename],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Store process in context for timeout handling
        context.process_info = {"process": process, "type": "corelet"}

        try:
            # Send message data to subprocess
            process.stdin.write(message_data)
            process.stdin.flush()
            process.stdin.close()

            # Read result from stdout
            result_data = process.stdout.read()

            # Wait for process to complete
            return_code = process.wait()

            # Check process exit code
            if return_code != 0:
                error_output = process.stderr.read()
                self._logger.error(
                    f"Corelet process exited with code {return_code}: {error_output}"
                )
                return False, f"Corelet process failed with exit code {return_code}"

            # Check if we got a result
            if result_data:
                result = pickle.loads(result_data)
                return result.success, result.data
            else:
                return False, "No result received from corelet process"

        except Exception as e:
            return False, str(e)

        finally:
            # Ensure process is terminated
            if process.poll() is None:
                process.kill()

    def get_results(
        self, block: bool = False, timeout: Optional[float] = None
    ) -> List[basefunctions.ThreadPoolResultEvent]:
        """
        Get all available task results from the output queue.

        Parameters
        ----------
        block : bool, default=False
            Whether to block until at least one result is available
        timeout : float, optional
            Timeout in seconds if blocking

        Returns
        -------
        List[basefunctions.ThreadPoolResultEvent]
            List of task result events
        """
        results = []

        # Get first result (with potential blocking)
        if block and self._output_queue.empty():
            try:
                results.append(self._output_queue.get(block=True, timeout=timeout))
                self._output_queue.task_done()
            except queue.Empty:
                pass

        # Get all remaining results (non-blocking)
        while not self._output_queue.empty():
            results.append(self._output_queue.get(block=False))
            self._output_queue.task_done()

        return results

    def wait_for_all(self) -> None:
        """
        Wait for all queued tasks to complete.
        """
        self._input_queue.join()


def get_thread_pool() -> ThreadPool:
    """
    Get the default ThreadPool instance.

    Returns
    -------
    ThreadPool
        The default thread pool instance
    """
    global _DEFAULT_INSTANCE
    if _DEFAULT_INSTANCE is None:
        _DEFAULT_INSTANCE = ThreadPool()
        _DEFAULT_INSTANCE.start()
    return _DEFAULT_INSTANCE
