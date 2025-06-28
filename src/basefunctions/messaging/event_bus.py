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
from basefunctions.messaging.event_exceptions import (
    EventBusShutdownError,
    NoHandlerAvailableError,
    InvalidEventError,
    EventBusInitializationError,
)
from basefunctions.messaging.event_handler import DefaultCmdHandler

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_TIMEOUT = 5
DEFAULT_RETRY_COUNT = 3
DEFAULT_PRIORITY = 5
INTERNAL_CORELET_FORWARDING_EVENT = "_corelet_forwarding"
INTERNAL_CMD_EXECUTION_EVENT = "_cmd_execution"

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

        Raises
        ------
        EventBusInitializationError
            If EventBus initialization fails.
        ValueError
            If num_threads is invalid.
        """
        self._logger = logging.getLogger(__name__)

        # autodetect cpus and logical cores
        try:
            logical_cores = psutil.cpu_count(logical=True) or 16
        except Exception:
            logical_cores = 16
            self._logger.warning("Could not detect CPU cores, using default: 16")
        self._num_threads = logical_cores if num_threads is None else num_threads

        if num_threads is not None and num_threads <= 0:
            raise ValueError("num_threads must be positive")

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

        # Create sync event context once
        self._sync_event_context = basefunctions.EventContext(thread_local_data=threading.local())

        # register internal event types
        basefunctions.EventFactory.register_event_type(
            "INTERNAL_CORELET_FORWARDING_EVENT", basefunctions.CoreletForwardingHandler
        )
        basefunctions.EventFactory.register_event_type("INTERNAL_CMD_EXECUTION_EVENT", basefunctions.DefaultCmdHandler)

        # Initialize threading system
        self._setup_thread_system()
        self._logger.info(f"EventBus initialized with {self._num_threads} worker threads")

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

        Raises
        ------
        InvalidEventError
            If event is invalid or missing required attributes.
        EventBusShutdownError
            If EventBus is shutting down.
        NoHandlerAvailableError
            If no handler is available for the event type.
        """
        # Validate event
        if not isinstance(event, basefunctions.Event):
            raise InvalidEventError(f"Invalid event type: {type(event).__name__}")

        if not hasattr(event, "event_id") or not event.event_id:
            raise InvalidEventError("Event must have a valid event_id")

        if not hasattr(event, "event_type") or not event.event_type:
            raise InvalidEventError("Event must have a valid event_type")

        if not hasattr(event, "event_exec_mode"):
            raise InvalidEventError("Event must have a valid event_exec_mode")

        # Thread-safe publish with lock
        with self._publish_lock:
            if self._shutdown_event.is_set():
                raise EventBusShutdownError("EventBus is shutting down, cannot publish events")

            event_type = event.event_type

            if not basefunctions.EventFactory.is_handler_available(event_type):
                raise NoHandlerAvailableError(event_type)

            # Thread-safe event counter and response registration
            self._event_counter += 1
            self._result_list[event.event_id] = None

            # Route event based on execution mode
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
                raise InvalidEventError(f"Unknown execution mode: {execution_mode}")

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
        # Read all results from output queue
        while not self._output_queue.empty():
            try:
                event_result = self._output_queue.get_nowait()
                if event_result.event_id in self._result_list:
                    self._result_list[event_result.event_id] = event_result
            except queue.Empty:
                break

        # Normalize event_ids parameter
        if isinstance(event_ids, str):
            event_ids = [event_ids]
        elif event_ids is None:
            event_ids = list(self._result_list.keys())

        return list(filter(None, [self._result_list.get(eid) for eid in event_ids]))

    def shutdown(self) -> None:
        """
        Shutdown EventBus and all worker threads/processes.
        """
        self._shutdown_event.set()

        # Send shutdown events to all worker threads
        for i in range(len(self._worker_threads)):
            shutdown_event = basefunctions.Event("shutdown")
            shutdown_task = (-1, -i, shutdown_event)  # Negative priority for immediate processing
            self._input_queue.put(shutdown_task)

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

        Raises
        ------
        ValueError
            If event_type is invalid or context is missing thread_local_data
        RuntimeError
            If handler creation fails
        """
        # Validate parameters
        if not event_type:
            raise ValueError("event_type cannot be empty")

        if not context or not context.thread_local_data:
            raise ValueError("context must have valid thread_local_data")

        # Initialize handler cache if not exists
        if not hasattr(context.thread_local_data, "handlers"):
            context.thread_local_data.handlers = {}

        # Check cache first
        if event_type in context.thread_local_data.handlers:
            return context.thread_local_data.handlers[event_type]

        # Create handler via Factory with error handling
        try:
            handler = basefunctions.EventFactory.create_handler(event_type)

            # Validate handler instance
            if not isinstance(handler, basefunctions.EventHandler):
                raise TypeError(f"Factory returned invalid handler type: {type(handler).__name__}")

            # Store in thread-local cache
            context.thread_local_data.handlers[event_type] = handler

            return handler

        except Exception as e:
            raise RuntimeError(f"Failed to create handler for event_type '{event_type}': {str(e)}") from e

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
        # Get handler from cache or create a new one
        handler = self._get_handler(event_type=event.event_type, context=self._sync_event_context)

        # Execute with retry logic
        event_result = self._retry_with_timeout(event, handler, self._sync_event_context)

        # Put result in output queue
        self._output_queue.put(item=event_result)

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

        # Create task tuple: (priority, counter, event)
        with self._publish_lock:
            self._event_counter += 1
            task = (event.priority, self._event_counter, event)  # priority bereits gesetzt

        try:
            self._input_queue.put(item=task)
        except Exception as e:
            self._logger.error("Failed to queue event %s: %s", event.event_type, str(e))
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
        _worker_context.thread_id = thread_id

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

                # Route based on execution mode to specific process functions
                if event.event_exec_mode == basefunctions.EXECUTION_MODE_THREAD:
                    event_result = self._process_event_thread_worker(event, _worker_context)
                elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CORELET:
                    event_result = self._process_event_corelet_worker(event, _worker_context)
                elif event.event_exec_mode == basefunctions.EXECUTION_MODE_CMD:
                    event_result = self._process_event_cmd_worker(event, _worker_context)
                else:
                    raise ValueError(f"Unknown execution mode: {event.event_exec_mode}")

                # Put result in output queue
                self._output_queue.put(item=event_result)

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
    def _retry_with_timeout(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Execute event with timeout and retry logic.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler to execute.
        context : basefunctions.EventContext
            Execution context.

        Returns
        -------
        basefunctions.EventResult
            EventResult from handler execution or retry exhaustion.
        """
        last_exception = None
        last_business_failure = None

        for attempt in range(event.max_retries):
            if self._shutdown_event.is_set():
                break

            try:
                with basefunctions.TimerThread(event.timeout, threading.get_ident()):
                    event_result = handler.handle(event, context)

                if event_result.success:
                    return event_result
                else:
                    last_business_failure = event_result

            except TimeoutError as e:
                last_exception = e
                self._logger.warning("Timeout on attempt %d: %s", attempt + 1, str(e))

            except Exception as e:
                last_business_failure = basefunctions.EventResult.exception_result(event.event_id, e)
                self._logger.warning("Exception on attempt %d: %s", attempt + 1, str(e))

        # All retries exhausted
        if last_exception:
            return basefunctions.EventResult.exception_result(event.event_id, last_exception)
        elif last_business_failure is not None:
            return last_business_failure
        else:
            # Fallback: should not happen but handle gracefully
            return basefunctions.EventResult.business_result(
                event.event_id, False, f"Event failed after {event.max_retries} attempts without result"
            )

    def _process_event_thread_worker(
        self, event: basefunctions.Event, worker_context: basefunctions.EventContext
    ) -> basefunctions.EventResult:
        """
        Process event in thread mode with worker context.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process in thread mode
        worker_context : basefunctions.EventContext
            Worker thread context with thread_local_data for handler cache

        Returns
        -------
        basefunctions.EventResult
            Result from handler execution with retry logic
        """
        # Get handler from cache or create new via Factory
        handler = self._get_handler(event.event_type, worker_context)

        # Execute with retry logic
        return self._retry_with_timeout(event, handler, worker_context)

    def _process_event_cmd_worker(
        self, event: basefunctions.Event, worker_context: basefunctions.EventContext
    ) -> basefunctions.EventResult:
        """
        Process event in cmd mode with DefaultCmdHandler.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process in cmd mode (subprocess execution)
        worker_context : basefunctions.EventContext
            Worker thread context with thread_local_data for handler cache

        Returns
        -------
        basefunctions.EventResult
            Result from subprocess execution with retry logic
        """
        # Get cmd handler from cache or create new
        cmd_handler = self._get_handler("INTERNAL_CMD_EXECUTION_EVENT", worker_context)

        # Execute with retry logic
        return self._retry_with_timeout(event, cmd_handler, worker_context)

    def _process_event_corelet_worker(
        self, event: basefunctions.Event, worker_context: basefunctions.EventContext
    ) -> basefunctions.EventResult:
        """
        Process event in corelet mode with forwarding handler.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process in corelet mode
        worker_context : basefunctions.EventContext
            Worker thread context with thread_local_data for corelet management

        Returns
        -------
        basefunctions.EventResult
            Result from corelet execution with retry logic
        """
        # Get corelet forwarding handler from cache or create new
        forwarding_handler = self._get_handler("INTERNAL_CORELET_FORWARDING_EVENT", worker_context)

        # Execute with retry logic - forwarding handler manages corelet communication
        return self._retry_with_timeout(event, forwarding_handler, worker_context)
