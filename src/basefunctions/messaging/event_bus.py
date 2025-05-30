"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  EventBus implementation with unified messaging system and asynchronous corelet pool
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Tuple
from multiprocessing import Process, Pipe, connection
import logging
import threading
import queue
import ctypes
import pickle
import psutil

import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_TIMEOUT = 5
DEFAULT_RETRY_COUNT = 3

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
SENTINEL = object()
CLEANUP = object()

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CoreletHandle:
    """
    Wrapper for corelet process communication.

    This class provides a simple interface for EventBus to communicate
    with corelet worker processes via pipes.
    """

    __slots__ = ("process", "input_pipe", "output_pipe")

    def __init__(
        self,
        process: Process,
        input_pipe: connection.Connection,
        output_pipe: connection.Connection,
    ):
        """
        Initialize corelet handle.

        Parameters
        ----------
        process : multiprocessing.Process
            Corelet worker process.
        input_pipe : multiprocessing.Connection
            Pipe for sending events to corelet.
        output_pipe : multiprocessing.Connection
            Pipe for receiving results from corelet.
        """
        self.process = process
        self.input_pipe = input_pipe
        self.output_pipe = output_pipe


@basefunctions.singleton
class EventBus:
    """
    Central event distribution system with unified messaging support.

    The EventBus manages handler registrations and event publishing
    across sync, thread, and corelet execution modes.
    """

    __slots__ = (
        "_handlers",
        "_logger",
        "_input_queue",
        "_output_queue",
        "_worker_threads",
        "_shutdown_event",
        "_num_threads",
        "_next_thread_id",
        "_event_counter",
    )

    def __init__(self, num_threads: Optional[int] = None):
        """
        Initialize a new EventBus.

        Parameters
        ----------
        num_threads : int, optional
            Number of worker threads for async processing.
            If None, auto-detects logical CPU core count.
        """
        self._handlers: Dict[str, List[basefunctions.EventHandler]] = {}
        self._logger = logging.getLogger(__name__)

        # autodetect cpus and logical cores
        logical_cores = psutil.cpu_count(logical=True) or 16
        self._num_threads = logical_cores if num_threads is None else num_threads

        # Queue system
        self._input_queue = queue.PriorityQueue()
        self._output_queue = queue.Queue()

        # Threading system
        self._worker_threads: List[threading.Thread] = []
        self._next_thread_id = 0
        self._event_counter = 0

        # State management
        self._shutdown_event = threading.Event()

        # initialize threading system
        self._setup_thread_system()

    def register(self, event_type: str, handler: basefunctions.EventHandler) -> bool:
        """
        Register a handler for a specific event type.

        Parameters
        ----------
        event_type : str
            The type of events to handle.
        handler : EventHandler
            The handler to register.

        Returns
        -------
        bool
            True if registration was successful, False otherwise.

        Raises
        ------
        TypeError
            If handler is not an EventHandler instance
        ValueError
            If corelet handlers are defined in __main__ module
        """
        if not isinstance(handler, basefunctions.EventHandler):
            raise TypeError("Handler must be an instance of EventHandler")

        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler.execution_mode == basefunctions.EXECUTION_MODE_CORELET:
            module_name = handler.__class__.__module__
            if module_name == "__main__":
                raise ValueError(
                    f"Corelet handlers cannot be defined in __main__. "
                    f"Move {handler.__class__.__name__} to a separate module."
                )

        self._handlers[event_type].append(handler)
        return True

    def publish(self, event: basefunctions.Event) -> None:
        """
        Publish an event to all registered handlers.

        Parameters
        ----------
        event : Event
            The event to publish.
        """
        if self._shutdown_event.is_set():
            self._logger.warning("Ignoring event during shutdown: %s", event.type)
            return

        event_type = event.type

        if event_type not in self._handlers:
            self._logger.debug("No handlers registered for event type: %s", event_type)
            return

        for handler in self._handlers[event_type]:
            if self._shutdown_event.is_set():
                return

            if handler.execution_mode == basefunctions.EXECUTION_MODE_SYNC:
                self._handle_sync_event(handler=handler, event=event)
            elif handler.execution_mode == basefunctions.EXECUTION_MODE_THREAD:
                self._handle_thread_and_corelet_event(event=event)
            elif handler.execution_mode == basefunctions.EXECUTION_MODE_CORELET:
                self._handle_thread_and_corelet_event(event=event)
            else:
                self._logger.warning(
                    "Unknown execution mode: %s for handler %s",
                    handler.execution_mode,
                    handler.__class__.__name__,
                )

    def get_results(self) -> Tuple[List[Any], List[str]]:
        """Get collected results and errors from last operation."""
        results = []
        errors = []

        while not self._output_queue.empty():
            try:
                event = self._output_queue.get_nowait()
                if event.type == "result":
                    results.append(event.data["result_data"])
                elif event.type == "error":
                    errors.append(event.data["error"])
            except queue.Empty:
                break

        return results, errors

    def join(self) -> None:
        """
        Wait for all async tasks to complete and collect results.
        """
        self._input_queue.join()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive EventBus statistics.

        Returns
        -------
        Dict[str, Any]
            Statistics from all subsystems.
        """
        stats = {
            "handlers_registered": sum(len(handlers) for handlers in self._handlers.values()),
            "event_types": list(self._handlers.keys()),
            "thread_system_active": self._input_queue is not None,
            "shutdown": self._shutdown_event.is_set(),
        }

        if self._input_queue is not None:
            alive_threads = sum(1 for t in self._worker_threads if t.is_alive())
            stats.update(
                {
                    "worker_threads": len(self._worker_threads),
                    "alive_threads": alive_threads,
                    "pending_thread_tasks": self._input_queue.qsize(),
                    "output_queue_size": self._output_queue.qsize(),
                }
            )

        return stats

    def shutdown(self) -> None:
        """
        Shutdown EventBus and all worker threads/processes.
        """
        self._shutdown_event.set()

        # Send shutdown events to all worker threads
        for i in range(len(self._worker_threads)):
            try:
                shutdown_event = basefunctions.Event.shutdown()
                # Use tuple format: (priority, counter, event)
                shutdown_task = (-1, -i, shutdown_event)  # Negative priority for immediate processing
                self._input_queue.put(shutdown_task)
            except:
                pass

        # Wait for worker threads to finish
        self.join()
        self._logger.info("EventBus shutdown complete")

    # -------------------------------------------------------------
    # _INTERNAL_ STUFF
    # -------------------------------------------------------------

    def _safe_handle_event(self, handler, event, context) -> Tuple[bool, Any]:
        """
        Safely handle event with automatic exception to tuple conversion.
        """
        try:
            result = handler.handle(event, context)

            # Handler returned tuple - validate and return
            if isinstance(result, tuple) and len(result) == 2:
                success, data = result
                if isinstance(success, bool):
                    return (success, data)
                else:
                    return (False, f"Handler returned invalid success type: {type(success).__name__}")
            else:
                return (False, f"Handler returned invalid format: {type(result).__name__}")

        except Exception as e:
            # Convert any exception to error tuple
            return (False, str(e))

    def _handle_sync_event(self, handler: basefunctions.EventHandler, event: basefunctions.Event) -> None:
        """
        Handle a synchronous event with timeout and retry logic.

        Parameters
        ----------
        handler : basefunctions.EventHandler
            The handler that processes the event
        event : basefunctions.Event
            The event to handle
        """
        if not isinstance(event, basefunctions.Event):
            self._logger.error("Invalid event type: %s", type(event).__name__)
            return

        event.max_retries = event.max_retries if event.max_retries else DEFAULT_RETRY_COUNT
        event.timeout = event.timeout if event.timeout else DEFAULT_TIMEOUT
        last_exception = None

        for attempt in range(event.max_retries):
            if self._shutdown_event.is_set():
                return

            try:
                # Create context for sync execution
                context = basefunctions.EventContext(execution_mode=basefunctions.EXECUTION_MODE_SYNC)

                # Apply timeout if specified
                with TimerThread(event.timeout, threading.get_ident()):
                    success, result = self._safe_handle_event(handler, event, context)

                if success:
                    # Success - put result in output queue
                    result_event = basefunctions.Event.result(success, result)
                    self._output_queue.put(item=result_event)
                    return
                else:
                    # Handler returned failure - retry
                    last_exception = Exception(f"Handler returned failure on attempt {attempt + 1}: {result}")

            except TimeoutError as e:
                last_exception = e
                self._logger.warning("Timeout in sync handler on attempt %d: %s", attempt + 1, str(e))

            except Exception as e:
                last_exception = e
                self._logger.warning("Exception in sync handler on attempt %d: %s", attempt + 1, str(e))

            # Log retry attempt
            if attempt < event.max_retries - 1:
                self._logger.debug(
                    "Retrying sync event %s, attempt %d/%d",
                    event.type,
                    attempt + 2,
                    event.max_retries,
                )

        # All retries exhausted - put error in output queue
        error_message = f"Sync event failed after {event.max_retries} attempts"
        if last_exception:
            error_message += f": {str(last_exception)}"

        error_event = basefunctions.Event.error(error_message, exception=last_exception)
        self._output_queue.put(item=error_event)

    def _handle_thread_and_corelet_event(self, event: basefunctions.Event) -> None:
        """
        Handle a threading or corelet event by queuing for async processing.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle
        """
        if not isinstance(event, basefunctions.Event):
            self._logger.error("Invalid event type: %s", type(event).__name__)
            return

        if self._shutdown_event.is_set():
            return

        # Set default values if not specified
        if event.timeout is None:
            event.timeout = DEFAULT_TIMEOUT
        if event.max_retries is None:
            event.max_retries = DEFAULT_RETRY_COUNT

        # Create task tuple: (priority, counter, event)
        # Counter ensures unique ordering for PriorityQueue
        priority = getattr(event, "priority", 5)  # Default priority 5
        self._event_counter += 1
        task = (priority, self._event_counter, event)

        try:
            self._input_queue.put(item=task)
            self._logger.debug("Queued %s event for async processing", event.type)
        except Exception as e:
            self._logger.error("Failed to queue event %s: %s", event.type, str(e))
            # Put error directly in output queue
            error_event = basefunctions.Event.error(f"Failed to queue event: {str(e)}", exception=e)
            self._output_queue.put(item=error_event)

    def _setup_thread_system(self) -> None:
        """
        Initialize thread processing system on first thread handler registration.
        """
        if self._worker_threads:
            return

        for _ in range(self._num_threads):
            self._add_worker_thread()

        self._logger.info("Thread system initialized with %d worker threads", self._num_threads)

    def _add_worker_thread(self) -> None:
        """
        Add a new worker thread to the pool.
        """
        thread_id = self._next_thread_id
        self._next_thread_id += 1

        thread = threading.Thread(
            target=self._worker_loop,
            name=f"EventWorker-{thread_id}",
            args=(thread_id,),
            daemon=True,
        )
        thread.start()
        self._worker_threads.append(thread)
        self._logger.debug("Started new worker thread: %s", thread.name)

    def _get_handler(self, event_type: str, thread_local) -> basefunctions.EventHandler:
        # 1. Cache prüfen
        if event_type in thread_local.handlers:
            return thread_local.handlers[event_type]

        # 2. Handler erstellen (Factory)
        handler = basefunctions.EventFactory.create_handler(event_type)

        # 3. In Cache speichern ← DAS MACHT _get_handler()
        thread_local.handlers[event_type] = handler

        return handler

    def _worker_loop(self, thread_id: int) -> None:
        """
        Main worker thread loop for processing async events.

        Parameters
        ----------
        thread_id : int
            Unique identifier for this worker thread.
        """
        # Initialize thread-local storage
        thread_local = threading.local()
        if not hasattr(thread_local, "handlers"):
            thread_local.handlers = {}

        self._logger.debug("Worker thread %d started with handler cache", thread_id)

        while not self._shutdown_event.is_set():
            task = None
            try:
                # Get new task from input queue with timeout
                task = self._input_queue.get(timeout=5.0)

                # Extract task components: (priority, counter, event_or_special)
                if not task or len(task) != 3:
                    self._logger.warning("Invalid task format in worker thread %d", thread_id)
                    continue

                _, _, event = task

                # Check for shutdown event
                if event.type == "shutdown":
                    self._logger.debug("Worker thread %d received shutdown event", thread_id)
                    break  # Exit worker loop

                # Check for cleanup signal
                elif event is CLEANUP:
                    # Reset thread-local handler cache
                    thread_local.handlers.clear()
                    self._logger.debug("Worker thread %d cleared handler cache", thread_id)
                    continue  # Don't call task_done() for cleanup signals

                # Set default values if not specified
                event.max_retries = event.max_retries if event.max_retries else DEFAULT_RETRY_COUNT
                event.timeout = event.timeout if event.timeout else DEFAULT_TIMEOUT

                # Get or create handler for this event type
                handler = self._get_handler(event.type, thread_local)

                # Process event with timeout and retry logic
                last_exception = None

                for attempt in range(event.max_retries):
                    if self._shutdown_event.is_set():
                        break

                    try:
                        with TimerThread(event.timeout, threading.get_ident()):
                            if handler.execution_mode == basefunctions.EXECUTION_MODE_THREAD:
                                success, result = self._process_event_thread(event, handler, thread_id, thread_local)
                            elif handler.execution_mode == basefunctions.EXECUTION_MODE_CORELET:
                                success, result = self._process_event_corelet(event, handler, thread_id)
                            else:
                                raise ValueError(f"Unknown execution mode: {handler.execution_mode}")

                        # Validate return type
                        if not isinstance(success, bool):
                            raise TypeError(
                                f"Handler must return (bool, Any), got success type: {type(success).__name__}"
                            )

                        if success:
                            # Success - put result in output queue
                            result_event = basefunctions.Event.result(success, result)
                            self._output_queue.put(item=result_event)
                            break  # Exit retry loop
                        else:
                            # Handler returned failure - retry
                            last_exception = Exception(f"Handler returned failure on attempt {attempt + 1}")

                    except TimeoutError as e:
                        # Cleanup dead corelet after timeout
                        if handler.execution_mode == basefunctions.EXECUTION_MODE_CORELET:
                            self._shutdown_corelet(thread_local, thread_id)

                        last_exception = e
                        self._logger.warning(
                            "Timeout in worker thread %d on attempt %d: %s",
                            thread_id,
                            attempt + 1,
                            str(e),
                        )

                    except Exception as e:
                        last_exception = e
                        self._logger.warning(
                            "Exception in worker thread %d on attempt %d: %s",
                            thread_id,
                            attempt + 1,
                            str(e),
                        )

                    # Log retry attempt
                    if attempt < event.max_retries - 1:
                        self._logger.debug(
                            "Retrying event %s in thread %d, attempt %d/%d",
                            event.type,
                            thread_id,
                            attempt + 2,
                            event.max_retries,
                        )
                else:
                    # All retries exhausted - put error in output queue
                    error_message = f"Event failed in worker thread {thread_id} after {event.max_retries} attempts"
                    if last_exception:
                        error_message += f": {str(last_exception)}"

                    error_event = basefunctions.Event.error(error_message, exception=last_exception)
                    self._output_queue.put(item=error_event)

            except queue.Empty:
                # Timeout on queue.get() - continue loop
                continue

            except Exception as e:
                self._logger.error("Critical error in worker thread %d: %s", thread_id, str(e))
                if task is not None:
                    # Put error for this task
                    error_event = basefunctions.Event.error(f"Critical worker error: {str(e)}", exception=e)
                    self._output_queue.put(item=error_event)

            finally:
                if task is not None and not (len(task) == 3 and task[2] is CLEANUP):
                    self._input_queue.task_done()

        self._logger.debug("Worker thread %d stopped", thread_id)

    def _process_event_thread(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        thread_id: int,
        thread_local,
    ) -> Tuple[bool, Any]:
        """
        Process event in thread mode with context.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler to process the event.
        thread_id : int
            Thread identifier.
        thread_local : threading.local
            Thread-local data storage.

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data from handler execution.
        """
        context = basefunctions.EventContext(
            execution_mode=basefunctions.EXECUTION_MODE_THREAD,
            thread_id=thread_id,
            thread_local_data=thread_local,
        )

        return self._safe_handle_event(handler, event, context)

    def _process_event_corelet(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        thread_id: int,
    ) -> Tuple[bool, Any]:
        """
        Process event in corelet mode via pipe communication.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler for validation (execution mode check).
        thread_id : int
            Thread identifier.

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data from corelet execution.
        """
        # Get thread-local corelet handle
        thread_local = threading.local()
        if not hasattr(thread_local, "corelet_worker"):
            corelet_handle = self._get_corelet_worker(thread_local, thread_id)
        else:
            corelet_handle = thread_local.corelet_worker

        try:
            # Check if handler is registered in corelet
            if not self._is_handler_registered_in_corelet(event.type, thread_local):
                self._register_handler_in_corelet(event.type, handler, corelet_handle, thread_local)
            # Send event to corelet via pipe
            pickled_event = pickle.dumps(event)
            corelet_handle.input_pipe.send(pickled_event)

            # Receive result from corelet (blocking - TimerThread handles timeout)
            pickled_result = corelet_handle.output_pipe.recv()
            result_event = pickle.loads(pickled_result)

            # Parse result based on event type
            if result_event.type == "result":
                return result_event.data["result_success"], result_event.data["result_data"]
            elif result_event.type == "error":
                return False, result_event.data["error"]
            else:
                return False, f"Unknown result event type: {result_event.type}"

        except Exception as e:
            return False, f"Corelet communication error: {str(e)}"

    def _is_handler_registered_in_corelet(self, event_type: str, thread_local) -> bool:
        """
        Check if handler is already registered in the corelet process.

        Parameters
        ----------
        event_type : str
            Event type to check registration for.
        thread_local : threading.local
            Thread-local storage containing corelet state.

        Returns
        -------
        bool
            True if handler is registered in corelet, False otherwise.
        """
        if not hasattr(thread_local, "registered_handlers"):
            thread_local.registered_handlers = set()
            return False

        return event_type in thread_local.registered_handlers

    def _register_handler_in_corelet(
        self, event_type: str, handler: basefunctions.EventHandler, corelet_handle: CoreletHandle, thread_local
    ) -> None:
        """
        Register handler class in corelet process via register event.

        Parameters
        ----------
        event_type : str
            Event Type for registration.
        handler : basefunctions.EventHandler
            Handler instance containing class information for registration.
        corelet_handle : CoreletHandle
            Corelet handle for pipe communication.
        thread_local : threading.local
            Thread-local storage for tracking registered handlers.
        """
        try:
            # Create register event with handler class information
            handler_module = handler.__class__.__module__
            handler_class_name = handler.__class__.__name__

            register_event = basefunctions.Event(
                type="__register_handler",
                data={
                    "event_type": event_type,
                    "module_path": handler_module,
                    "class_name": handler_class_name,
                },
            )

            # Send register event to corelet
            pickled_event = pickle.dumps(register_event)
            corelet_handle.input_pipe.send(pickled_event)

            # Wait for registration confirmation
            pickled_result = corelet_handle.output_pipe.recv()
            result_event = pickle.loads(pickled_result)

            if result_event.type == "result" and result_event.data.get("result_success"):
                # Mark handler as registered in thread-local cache
                if not hasattr(thread_local, "registered_handlers"):
                    thread_local.registered_handlers = set()
                thread_local.registered_handlers.add(event_type)

                self._logger.debug("Handler %s registered in corelet", handler_class_name)
            else:
                raise RuntimeError(f"Handler registration failed: {result_event.data}")

        except Exception as e:
            self._logger.error("Failed to register handler in corelet: %s", str(e))
            raise

    def _get_corelet_worker(self, thread_local, thread_id: int):
        """
        Create new corelet worker process for thread.

        Parameters
        ----------
        thread_local : threading.local
            Thread-local storage for corelet worker.
        thread_id : int
            Thread identifier.

        Returns
        -------
        CoreletHandle
            New corelet handle for process communication.
        """
        # Create pipes
        input_pipe_a, input_pipe_b = Pipe()
        output_pipe_a, output_pipe_b = Pipe()

        # Start corelet process
        process = Process(
            target=basefunctions.worker_main,
            args=(f"thread_{thread_id}", input_pipe_b, output_pipe_b),
            daemon=True,
        )
        process.start()

        # Create wrapper handle
        corelet_handle = CoreletHandle(process, input_pipe_a, output_pipe_a)
        thread_local.corelet_worker = corelet_handle

        return corelet_handle

    def _shutdown_corelet(self, thread_local, thread_id: int) -> None:
        """
        Kill corelet process brutally.

        Parameters
        ----------
        thread_local : threading.local
            Thread-local storage containing corelet worker.
        thread_id : int
            Thread identifier.
        """
        if hasattr(thread_local, "corelet_worker"):
            try:
                thread_local.corelet_worker.input_queue.close()
                thread_local.corelet_worker.output_queue.close()
                thread_local.corelet_worker.process.kill()
                delattr(thread_local, "corelet_worker")
                self._logger.debug("Killed corelet for thread %d", thread_id)
            except:
                pass  # Already dead

    def clear_handlers(self) -> None:
        """
        Clear all registered handlers.

        Removes all handler registrations but keeps EventBus instance
        and worker threads alive for reuse.
        """
        self._handlers.clear()
        self._logger.info("Cleared all registered handlers")


class TimerThread:
    """
    context manager that enforces a timeout on a thread.
    """

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

        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
        basefunctions.get_logger(__name__).error("timeout in thread %d", self.thread_id)
