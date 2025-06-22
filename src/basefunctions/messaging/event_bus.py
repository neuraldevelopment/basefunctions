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
DEFAULT_PRIORITY = 5

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
        "_sync_event_context",
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
        self._logger = logging.getLogger(__name__)

        # autodetect cpus and logical cores
        logical_cores = psutil.cpu_count(logical=True) or 16
        self._num_threads = logical_cores if num_threads is None else num_threads

        # Queue system
        self._input_queue = queue.PriorityQueue()
        self._output_queue = queue.PriorityQueue()

        # Threading system
        self._worker_threads: List[threading.Thread] = []
        self._next_thread_id = 0
        self._event_counter = 0

        # State management
        self._shutdown_event = threading.Event()

        # Response tracking system
        self._result_list = {}
        self._publish_lock = threading.RLock()  # Thread-safe publish

        # Create sync event context once
        self._sync_event_context = basefunctions.EventContext(thread_local_data=threading.local())

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

        # check for correct event type
        if not isinstance(event, basefunctions.Event):
            self._logger.error("Invalid event type: %s", type(event).__name__)
            return

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

    def get_results(self, event_ids: List[str] = None) -> List[basefunctions.EventResult]:
        """
        Get response(s) from processed events.
        Parameters
        ----------
        event_ids : List[str], optional
            List of event_ids to retrieve. If None, returns all events.
        Returns
        -------
        List[EventResult]
            List of EventResults for requested event_ids
        """
        # Read all results from output queue and fill pending responses dict
        while not self._output_queue.empty():
            try:
                event_result = self._output_queue.get_nowait()
                if event_result.event_id in self._result_list:
                    self._result_list[event_result.event_id] = event_result
            except queue.Empty:
                break

        if isinstance(event_ids, str):
            event_ids = [event_ids]
        if event_ids is None:
            # None means all events
            event_ids = list(self._result_list.keys())
        # Return list of results
        return [self._result_list.get(eid) for eid in event_ids]

    def shutdown(self) -> None:
        """
        Shutdown EventBus and all worker threads/processes.
        """
        self._shutdown_event.set()
        # Send shutdown events to all worker threads
        for i in range(len(self._worker_threads)):
            try:
                shutdown_event = basefunctions.Event("shutdown")
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

    def _get_handler(self, event_type: str, context: basefunctions.EventContext) -> basefunctions.EventHandler:
        """
        Get handler from cache or create new via Factory.

        Parameters
        ----------
        event_type : str
            Event type for handler lookup
        context : basefunctions.EventContext
            Event context containing thread_local_data for handler cache

        Returns
        -------
        basefunctions.EventHandler
            Handler instance for the event type
        """
        # Initialize handler cache if not exists
        if not hasattr(context.thread_local_data, "handlers"):
            context.thread_local_data.handlers = {}

        # Check cache first
        if event_type in context.thread_local_data.handlers:
            return context.thread_local_data.handlers[event_type]

        # Create handler via Factory
        handler = basefunctions.EventFactory.create_handler(event_type)

        # Store in thread-local cache
        context.thread_local_data.handlers[event_type] = handler

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
        last_business_failure = None

        # Get handler from cache or create a new one - use context instead of thread_local
        handler = self._get_handler(event_type=event.event_type, context=self._sync_event_context)

        for attempt in range(event.max_retries):
            if self._shutdown_event.is_set():
                return

            try:
                # Use existing sync context instead of creating new one
                context = self._sync_event_context

                # Apply timeout if specified
                with basefunctions.TimerThread(event.timeout, threading.get_ident()):
                    event_result = self._safe_handle_event(handler, event, context)

                # Check if business success or failure
                if event_result.success:
                    # Success - put EventResult directly in output queue
                    self._output_queue.put(item=event_result)
                    return
                else:
                    # Business failure (success=False) - store for potential final return and retry
                    last_business_failure = event_result

            except TimeoutError as e:
                last_exception = e
                self._logger.warning("Timeout in sync handler on attempt %d: %s", attempt + 1, str(e))

            except Exception as e:
                last_exception = e
                self._logger.warning("Exception in sync handler on attempt %d: %s", attempt + 1, str(e))

        # All retries exhausted - return appropriate result
        if last_exception:
            # Exception occurred - return exception result
            error_result = basefunctions.EventResult.exception_result(event.event_id, last_exception)
            self._output_queue.put(item=error_result)
        else:
            # No exceptions - return last business failure
            self._output_queue.put(item=last_business_failure)

    def _handle_thread_and_corelet_event(self, event: basefunctions.Event) -> None:
        """
        Handle a threading or corelet event by queuing for async processing.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle
        """
        if self._shutdown_event.is_set():
            return

        # Set default values if not specified
        event.timeout = event.timeout or DEFAULT_TIMEOUT
        event.max_retries = event.max_retries or DEFAULT_RETRY_COUNT
        event.priority = event.priority or DEFAULT_PRIORITY

        # Create task tuple: (priority, counter, event)
        # Counter ensures unique ordering for PriorityQueue
        with self._publish_lock:
            self._event_counter += 1
            task = (event.priority, self._event_counter, event)

        try:
            self._input_queue.put(item=task)
        except Exception as e:
            self._logger.error("Failed to queue event %s: %s", event.event_type, str(e))
            # Put error directly in output queue
            error_result = basefunctions.EventResult.exception_result(event.event_id, e)
            self._output_queue.put(item=error_result)

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
        # Create worker context once
        _worker_context = basefunctions.EventContext(thread_local_data=threading.local())

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
                    break  # Exit worker loop

                # Set default values if not specified
                event.max_retries = event.max_retries if event.max_retries else DEFAULT_RETRY_COUNT
                event.timeout = event.timeout if event.timeout else DEFAULT_TIMEOUT

                # Get or create handler for this event type
                handler = self._get_handler(event.event_type, _worker_context)

                # Create context once per event processing
                if event.event_exec_mode == basefunctions.EXECUTION_MODE_THREAD:
                    context = basefunctions.EventContext(
                        thread_id=thread_id,
                        thread_local_data=_worker_context.thread_local_data,
                    )
                elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CMD:
                    context = basefunctions.EventContext(
                        thread_id=thread_id,
                    )
                else:
                    context = None  # Corelet doesn't use context in process methods

                # Process event with timeout and retry logic
                last_exception = None
                last_business_failure = None

                for attempt in range(event.max_retries):
                    if self._shutdown_event.is_set():
                        break

                    try:
                        with basefunctions.TimerThread(event.timeout, threading.get_ident()):
                            # Use event.event_exec_mode instead of handler.execution_mode
                            if event.event_exec_mode == basefunctions.EXECUTION_MODE_THREAD:
                                event_result = self._process_event_thread(event, handler, thread_id, context)
                            elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CORELET:
                                event_result = self._process_event_corelet(event, handler, thread_id, context)
                            elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CMD:
                                event_result = self._process_event_cmd(event, handler, thread_id, context)
                            else:
                                raise ValueError(f"Unknown execution mode: {event.event_exec_mode}")

                        # Validate EventResult
                        if not isinstance(event_result, basefunctions.EventResult):
                            raise TypeError(f"Handler must return EventResult, got: {type(event_result).__name__}")

                        if event_result.success:
                            # Success - put EventResult directly in output queue
                            self._output_queue.put(item=event_result)
                            break  # Exit retry loop
                        else:
                            # Handler returned failure - retry
                            last_business_failure = event_result

                    except TimeoutError as e:
                        # Cleanup dead corelet after timeout
                        if event.event_exec_mode == basefunctions.EXECUTION_MODE_CORELET:
                            self._shutdown_corelet(_worker_context.thread_local_data, thread_id)

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

                else:
                    # All retries exhausted - return appropriate result
                    if last_exception:
                        # Exception occurred - return exception result
                        error_result = basefunctions.EventResult.exception_result(event.event_id, last_exception)
                    elif last_business_failure:
                        # No exceptions but business failure - return last business failure
                        error_result = last_business_failure
                    else:
                        # Should not happen
                        error_message = f"Event failed in worker thread {thread_id} after {event.max_retries} attempts"
                        error_result = basefunctions.EventResult.business_result(event.event_id, False, error_message)

                    self._output_queue.put(item=error_result)

            except queue.Empty:
                # Timeout on queue.get() - continue loop
                continue

            except Exception as e:
                self._logger.error("Critical error in worker thread %d: %s", thread_id, str(e))
                if task is not None:
                    # Put error for this task
                    _, _, event = task
                    error_result = basefunctions.EventResult.exception_result(event.event_id, e)
                    self._output_queue.put(item=error_result)

            finally:
                if task is not None:
                    self._input_queue.task_done()

    # =============================================================================
    # EVENT PROCESSING ENGINE
    # =============================================================================

    def _process_event_thread(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Process event in thread mode with context.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler to process the event.
        context : basefunctions.EventContext
            Pre-created execution context.

        Returns
        -------
        basefunctions.EventResult
            EventResult from handler execution.
        """
        return self._safe_handle_event(handler, event, context)

    def _process_event_cmd(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Process event in cmd mode via handler.handle().

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler to process the event (DefaultCmdHandler).
        context : basefunctions.EventContext
            Pre-created execution context.

        Returns
        -------
        basefunctions.EventResult
            EventResult from handler execution.
        """
        return self._safe_handle_event(handler, event, context)

    def _process_event_corelet(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Process event in corelet mode via pipe communication.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler for validation (execution mode check).
        context : basefunctions.EventContext
            Execution context containing thread_local_data and thread_id.

        Returns
        -------
        basefunctions.EventResult
            EventResult from corelet execution.
        """
        # Get thread-local corelet handle from context
        if not hasattr(context.thread_local_data, "corelet_worker"):
            corelet_handle = self._get_corelet_worker(context)
        else:
            corelet_handle = context.thread_local_data.corelet_worker

        try:
            # Check if handler is registered in corelet
            if not self._is_handler_registered_in_corelet(event.event_type, context.thread_local_data):
                self._register_handler_in_corelet(event.event_type, handler, corelet_handle, context.thread_local_data)

            # Send event to corelet via pipe
            pickled_event = pickle.dumps(event)
            corelet_handle.input_pipe.send(pickled_event)

            # Receive result from corelet (blocking - TimerThread handles timeout)
            pickled_result = corelet_handle.output_pipe.recv()
            event_result = pickle.loads(pickled_result)

            # Corelet sends EventResult directly
            return event_result

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)

    def _safe_handle_event(self, handler, event, context) -> basefunctions.EventResult:
        """
        Safely handle event with automatic exception to EventResult conversion.

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
        basefunctions.EventResult
            EventResult from handler or exception result on error
        """
        try:
            # Handler returns EventResult directly - pass through
            return handler.handle(event, context)

        except Exception as e:
            # Convert exception to EventResult
            return basefunctions.EventResult.exception_result(event.event_id, e)

    # =============================================================================
    # CORELET MANAGEMENT
    # =============================================================================

    def _get_corelet_worker(self, context: basefunctions.EventContext) -> CoreletHandle:
        """
        Get or create a corelet worker for the current thread.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing thread_local_data.

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
            args=(f"corelet_{threading.current_thread().ident}", input_pipe_b, output_pipe_b),
            daemon=True,
        )
        process.start()

        # Create wrapper handle
        corelet_handle = CoreletHandle(process, input_pipe_a, output_pipe_a)
        context.thread_local_data.corelet_worker = corelet_handle

        return corelet_handle

    def _is_handler_registered_in_corelet(self, event_type: str, context: basefunctions.EventContext) -> bool:
        """
        Check if handler is already registered in the corelet process.

        Parameters
        ----------
        event_type : str
            Event type to check registration for.
        context : basefunctions.EventContext
            Event context containing thread_local_data for tracking registrations.

        Returns
        -------
        bool
            True if handler is registered, False otherwise.
        """
        if not hasattr(context.thread_local_data, "registered_handlers"):
            context.thread_local_data.registered_handlers = set()

        return event_type in context.thread_local_data.registered_handlers

    def _register_handler_in_corelet(
        self,
        event_type: str,
        handler: basefunctions.EventHandler,
        corelet_handle: CoreletHandle,
        context: basefunctions.EventContext,
    ) -> None:
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
        context : basefunctions.EventContext
            Event context containing thread_local_data for tracking registrations.
        """
        # Get handler class information
        handler_class = handler.__class__
        module_path = handler_class.__module__
        class_name = handler_class.__name__

        # Create registration event
        register_event = basefunctions.Event(
            "_register_handler",
            event_data={"event_type": event_type, "module_path": module_path, "class_name": class_name},
        )

        # Send registration to corelet
        pickled_event = pickle.dumps(register_event)
        corelet_handle.input_pipe.send(pickled_event)

        # Receive confirmation with timeout
        if corelet_handle.output_pipe.poll(DEFAULT_TIMEOUT):
            pickled_result = corelet_handle.output_pipe.recv()
            event_result = pickle.loads(pickled_result)
        else:
            raise TimeoutError(f"Corelet registration timeout for {event_type}")

        # Track registration
        if not hasattr(context.thread_local_data, "registered_handlers"):
            context.thread_local_data.registered_handlers = set()
        context.thread_local_data.registered_handlers.add(event_type)

    def _shutdown_corelet(self, context: basefunctions.EventContext) -> None:
        """
        Kill corelet process.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing thread_local_data with corelet worker.
        """
        if hasattr(context.thread_local_data, "corelet_worker"):
            try:
                context.thread_local_data.corelet_worker.input_pipe.close()
                context.thread_local_data.corelet_worker.output_pipe.close()
                context.thread_local_data.corelet_worker.process.kill()
                delattr(context.thread_local_data, "corelet_worker")
            except:
                pass  # Already dead
