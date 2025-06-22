"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

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
from typing import Dict, List, Optional, Any, Tuple, Union
from multiprocessing import Process, Pipe, connection
import logging
import threading
import queue
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
        "_thread_local",
        "_logger",
        "_input_queue",
        "_output_queue",
        "_worker_threads",
        "_shutdown_event",
        "_num_threads",
        "_next_thread_id",
        "_event_counter",
        "_result_list",
        "_publish_lock",
        "_context",
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
        self._thread_local = threading.local()
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

        # Response tracking system
        self._result_list = {}
        self._publish_lock = threading.RLock()  # Thread-safe publish

        # EventBus context
        self._context = basefunctions.EventContext(
            execution_mode=basefunctions.EXECUTION_MODE_SYNC,
            process_id=None,
            timestamp=None,
        )

        # initialize threading system
        self._setup_thread_system()

    # =============================================================================
    # PUBLIC API - EVENT PUBLISHING
    # =============================================================================

    def publish(self, event: basefunctions.Event) -> str:
        """
        Publish an event to all registered handlers.

        Parameters
        ----------
        event : Event
            The event to publish.

        Returns
        -------
        str
            Event ID for result tracking.
        """
        # Thread-safe publish with lock
        with self._publish_lock:
            if self._shutdown_event.is_set():
                self._logger.warning("Ignoring event during shutdown: %s", event.event_type)
                return event.event_id

            event_type = event.event_type

            if not basefunctions.EventFactory.is_handler_available(event_type):
                self._logger.debug("No handlers registered for event type: %s", event_type)
                return event.event_id

            # Thread-safe event counter and response registration
            self._event_counter += 1
            self._result_list[event.event_id] = None

            # Use event.event_exec_mode for routing
            execution_mode = event.event_exec_mode

            if execution_mode == basefunctions.EXECUTION_MODE_SYNC:
                self._handle_sync_event(event=event)
            elif execution_mode == basefunctions.EXECUTION_MODE_THREAD:
                self._handle_thread_and_corelet_event(event=event)
            elif execution_mode == basefunctions.EXECUTION_MODE_CORELET:
                self._handle_thread_and_corelet_event(event=event)
            elif execution_mode == basefunctions.EXECUTION_MODE_CMD:
                self._handle_thread_and_corelet_event(event=event)
            else:
                self._logger.warning("Unknown execution mode: %s for event %s", execution_mode, event.event_type)

        return event.event_id

    def join(self) -> None:
        """
        Wait for all async tasks to complete and collect results.
        """
        self._input_queue.join()

    def get_results(
        self, event_id: Union[str, List[str], None] = None
    ) -> Union[basefunctions.Event, List[basefunctions.Event], Dict[str, basefunctions.Event], None]:
        """
        Get response(s) from processed events.

        Parameters
        ----------
        event_id : str, List[str], or None
            - str: Return single response for this event_id
            - List[str]: Return list of responses for these event_ids
            - None: Return complete responses dict

        Returns
        -------
        Event, List[Event], or Dict[str, Event]
            Depending on input parameter type
        """
        self._get_results_from_output_queue()
        if event_id is None:
            # Complete dict
            return self._result_list.copy()
        elif isinstance(event_id, list):
            # List of IDs -> List of Results
            return [self._result_list.get(eid) for eid in event_id]
        else:
            # Single ID -> Single Result
            return self._result_list.get(event_id)

    def clear_handlers(self) -> None:
        """
        Clear all registered handlers.
        Removes all handler registrations but keeps EventBus instance
        and worker threads alive for reuse.
        """
        if hasattr(self._thread_local, "handlers"):
            self._thread_local.handlers.clear()

        for _ in range(len(self._worker_threads)):
            cleanup_event = basefunctions.Event.cleanup()
            self.publish(cleanup_event)

        self._logger.info("Cleared all registered handlers")

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

    # =============================================================================
    # HANDLER MANAGEMENT
    # =============================================================================

    def _get_handler(self, event_type: str, thread_local) -> basefunctions.EventHandler:
        """
        Get handler from cache or create new via Factory.

        Parameters
        ----------
        event_type : str
            Event type for handler lookup
        thread_local : threading.local
            Thread-local storage for handler cache

        Returns
        -------
        basefunctions.EventHandler
            Handler instance for the event type
        """
        # Initialize handler cache if not exists
        if not hasattr(thread_local, "handlers"):
            thread_local.handlers = {}

        # Check cache first
        if event_type in thread_local.handlers:
            return thread_local.handlers[event_type]

        # Create handler via Factory
        handler = basefunctions.EventFactory.create_handler(event_type)

        # Store in thread-local cache
        thread_local.handlers[event_type] = handler

        return handler

    # =============================================================================
    # EVENT ROUTING & PROCESSING
    # =============================================================================

    def _handle_sync_event(self, event: basefunctions.Event) -> None:
        """
        Handle a synchronous event with timeout and retry logic.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle
        """
        event.max_retries = event.max_retries if event.max_retries else DEFAULT_RETRY_COUNT
        event.timeout = event.timeout if event.timeout else DEFAULT_TIMEOUT
        last_exception = None

        # get handler from cache or create a new one
        handler = self._get_handler(event_type=event.event_type, thread_local=self._thread_local)

        for attempt in range(event.max_retries):
            if self._shutdown_event.is_set():
                return

            try:
                # Create context for sync execution
                context = basefunctions.EventContext(execution_mode=basefunctions.EXECUTION_MODE_SYNC)

                # Apply timeout if specified
                with basefunctions.TimerThread(event.timeout, threading.get_ident()):
                    success, result = self._safe_handle_event(handler, event, context)

                if success:
                    # Success - send result event
                    result_event = basefunctions.Event.result(event.event_id, success, result)
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
                    event.event_type,
                    attempt + 2,
                    event.max_retries,
                )

        # All retries exhausted - put error in output queue
        error_message = f"Sync event failed after {event.max_retries} attempts"
        if last_exception:
            error_message += f": {str(last_exception)}"

        error_event = basefunctions.Event.error(event.event_id, error_message, exception=last_exception)
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
        with self._publish_lock:
            self._event_counter += 1
            task = (priority, self._event_counter, event)

        try:
            self._input_queue.put(item=task)
            self._logger.debug("Queued %s event for async processing", event.event_type)
        except Exception as e:
            self._logger.error("Failed to queue event %s: %s", event.event_type, str(e))
            # Put error directly in output queue
            error_event = basefunctions.Event.error(event.event_id, f"Failed to queue event: {str(e)}", exception=e)
            self._output_queue.put(item=error_event)

    # =============================================================================
    # EVENT PROCESSING ENGINE
    # =============================================================================

    def _process_event_thread(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        thread_id: int,
        thread_local,
        context: basefunctions.EventContext,
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
        context : basefunctions.EventContext
            Pre-created execution context.

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data from handler execution.
        """
        return self._safe_handle_event(handler, event, context)

    def _process_event_cmd(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        thread_id: int,
        context: basefunctions.EventContext,
    ) -> Tuple[bool, Any]:
        """
        Process event in cmd mode via handler.handle().

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler to process the event (DefaultCmdHandler).
        thread_id : int
            Thread identifier.
        context : basefunctions.EventContext
            Pre-created execution context.

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data from handler execution.
        """
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
            if not self._is_handler_registered_in_corelet(event.event_type, thread_local):
                self._register_handler_in_corelet(event.event_type, handler, corelet_handle, thread_local)
            # Send event to corelet via pipe
            pickled_event = pickle.dumps(event)
            corelet_handle.input_pipe.send(pickled_event)

            # Receive result from corelet (blocking - TimerThread handles timeout)
            pickled_result = corelet_handle.output_pipe.recv()
            result_event = pickle.loads(pickled_result)

            # Parse result based on event type
            if result_event.event_type == "result":
                return result_event.event_data["result_success"], result_event.event_data["result_data"]
            elif result_event.event_type == "error":
                return False, result_event.event_data["error"]
            else:
                return False, f"Unknown result event type: {result_event.event_type}"

        except Exception as e:
            return False, f"Corelet communication error: {str(e)}"

    def _safe_handle_event(self, handler, event, context) -> Tuple[bool, Any]:
        """
        Safely handle event with automatic exception to tuple conversion.

        Parameters
        ----------
        handler : basefunctions.EventHandler
            Handler to execute
        event : basefunctions.Event
            Event to process
        context : basefunctions.EventContext
            Execution context

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result data
        """
        try:
            # Pass context as required parameter
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

    # =============================================================================
    # THREAD POOL MANAGEMENT
    # =============================================================================

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

    def _worker_loop(self, thread_id: int) -> None:
        """
        Main worker thread loop for processing async events.

        Parameters
        ----------
        thread_id : int
            Unique identifier for this worker thread.
        """
        self._logger.debug("Worker thread %d started with handler cache", thread_id)

        # Initialize thread-local storage
        _thread_local = threading.local()
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
                if event.event_type == "shutdown":
                    self._logger.debug("Worker thread %d received shutdown event", thread_id)
                    break  # Exit worker loop

                # Check for cleanup signal
                elif event.event_type == "cleanup":
                    if hasattr(_thread_local, "handlers"):
                        _thread_local.handlers.clear()
                    self._logger.debug("Worker thread %d cleared handler cache", thread_id)
                    continue

                # Set default values if not specified
                event.max_retries = event.max_retries if event.max_retries else DEFAULT_RETRY_COUNT
                event.timeout = event.timeout if event.timeout else DEFAULT_TIMEOUT

                # Get or create handler for this event type
                handler = self._get_handler(event.event_type, _thread_local)

                # Create context once per event processing
                if event.event_exec_mode == basefunctions.EXECUTION_MODE_THREAD:
                    context = basefunctions.EventContext(
                        execution_mode=basefunctions.EXECUTION_MODE_THREAD,
                        thread_id=thread_id,
                        thread_local_data=_thread_local,
                    )
                elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CMD:
                    context = basefunctions.EventContext(
                        execution_mode=basefunctions.EXECUTION_MODE_CMD,
                        thread_id=thread_id,
                    )
                else:
                    context = None  # Corelet doesn't use context in process methods

                # Process event with timeout and retry logic
                last_exception = None

                for attempt in range(event.max_retries):
                    if self._shutdown_event.is_set():
                        break

                    try:
                        with basefunctions.TimerThread(event.timeout, threading.get_ident()):
                            # Use event.event_exec_mode instead of handler.execution_mode
                            if event.event_exec_mode == basefunctions.EXECUTION_MODE_THREAD:
                                success, result = self._process_event_thread(
                                    event, handler, thread_id, _thread_local, context
                                )
                            elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CORELET:
                                success, result = self._process_event_corelet(event, handler, thread_id)
                            elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CMD:
                                success, result = self._process_event_cmd(event, handler, thread_id, context)
                            else:
                                raise ValueError(f"Unknown execution mode: {event.event_exec_mode}")

                        # Validate return type
                        if not isinstance(success, bool):
                            raise TypeError(
                                f"Handler must return (bool, Any), got success type: {type(success).__name__}"
                            )

                        if success:
                            # Success - put result in output queue
                            result_event = basefunctions.Event.result(event.event_id, success, result)
                            self._output_queue.put(item=result_event)
                            break  # Exit retry loop
                        else:
                            # Handler returned failure - retry
                            last_exception = Exception(f"Handler returned failure on attempt {attempt + 1}")

                    except TimeoutError as e:
                        # Cleanup dead corelet after timeout
                        if event.event_exec_mode == basefunctions.EXECUTION_MODE_CORELET:
                            self._shutdown_corelet(_thread_local, thread_id)

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
                            event.event_type,
                            thread_id,
                            attempt + 2,
                            event.max_retries,
                        )
                else:
                    # All retries exhausted - put error in output queue
                    error_message = f"Event failed in worker thread {thread_id} after {event.max_retries} attempts"
                    if last_exception:
                        error_message += f": {str(last_exception)}"

                    error_event = basefunctions.Event.error(event.event_id, error_message, exception=last_exception)
                    self._output_queue.put(item=error_event)

            except queue.Empty:
                # Timeout on queue.get() - continue loop
                continue

            except Exception as e:
                self._logger.error("Critical error in worker thread %d: %s", thread_id, str(e))
                if task is not None:
                    # Put error for this task
                    _, _, event = task
                    error_event = basefunctions.Event.error(
                        event.event_id, f"Critical worker error: {str(e)}", exception=e
                    )
                    self._output_queue.put(item=error_event)

            finally:
                if task is not None:
                    self._input_queue.task_done()

        self._logger.debug("Worker thread %d stopped", thread_id)

    # =============================================================================
    # CORELET MANAGEMENT
    # =============================================================================

    def _get_corelet_worker(self, thread_local, thread_id: int) -> CoreletHandle:
        """
        Get or create a corelet worker for the current thread.

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

    def _is_handler_registered_in_corelet(self, event_type: str, thread_local) -> bool:
        """
        Check if handler is already registered in the corelet process.

        Parameters
        ----------
        event_type : str
            Event type to check registration for.
        thread_local : threading.local
            Thread-local storage for tracking registrations.

        Returns
        -------
        bool
            True if handler is registered, False otherwise.
        """
        if not hasattr(thread_local, "registered_handlers"):
            thread_local.registered_handlers = set()

        return event_type in thread_local.registered_handlers

    def _register_handler_in_corelet(self, event_type: str, handler, corelet_handle, thread_local) -> None:
        """
        Register event handler in corelet process.

        Parameters
        ----------
        event_type : str
            Event type to register.
        handler : basefunctions.EventHandler
            Handler instance for getting class information.
        corelet_handle : CoreletHandle
            Corelet process handle.
        thread_local : threading.local
            Thread-local storage for tracking registrations.
        """
        try:
            # Get handler class information
            handler_class = handler.__class__
            module_path = handler_class.__module__
            class_name = handler_class.__name__

            # Create registration event
            register_event = basefunctions.Event.register_handler(event_type, module_path, class_name)

            # Send registration to corelet
            pickled_event = pickle.dumps(register_event)
            corelet_handle.input_pipe.send(pickled_event)

            # Receive confirmation
            pickled_result = corelet_handle.output_pipe.recv()
            result_event = pickle.loads(pickled_result)

            # Track registration
            if not hasattr(thread_local, "registered_handlers"):
                thread_local.registered_handlers = set()
            thread_local.registered_handlers.add(event_type)

            self._logger.debug("Registered handler %s for event type %s in corelet", class_name, event_type)

        except Exception as e:
            self._logger.error("Failed to register handler in corelet: %s", str(e))
            raise

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
                thread_local.corelet_worker.input_pipe.close()
                thread_local.corelet_worker.output_pipe.close()
                thread_local.corelet_worker.process.kill()
                delattr(thread_local, "corelet_worker")
                self._logger.debug("Killed corelet for thread %d", thread_id)
            except:
                pass  # Already dead

    # =============================================================================
    # RESULT MANAGEMENT
    # =============================================================================

    def _get_results_from_output_queue(self) -> None:
        """
        Read all results from output queue and fill pending responses dict.
        """
        while not self._output_queue.empty():
            try:
                result_event = self._output_queue.get_nowait()
                if result_event.event_id in self._result_list:
                    self._result_list[result_event.event_id] = result_event
            except queue.Empty:
                break
