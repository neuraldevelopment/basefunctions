"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Central event distribution system with unified messaging support.

  The EventBus manages handler registrations and event publishing
  across sync, thread, and corelet execution modes.

  Features LRU-based result caching with smart cleanup:
  - Specific event_id requests consume results (remove from cache)
  - Bulk requests preserve results (LRU eviction handles memory)

  Log:
  v1.1 : Added corelet process lifecycle tracking and monitoring API
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import List, Dict, Optional
from collections import OrderedDict
import logging
import threading
import queue
import pickle
import psutil
from basefunctions.utils.logging import setup_logger
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
INTERNAL_CORELET_FORWARDING_EVENT = "_corelet_forwarding"
INTERNAL_CMD_EXECUTION_EVENT = "_cmd_execution"
INTERNAL_SHUTDOWN_EVENT = "_shutdown"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


@basefunctions.singleton
class EventBus:
    """
    Central event distribution system with unified messaging support.

    The EventBus is the core component of the event-driven messaging system,
    managing handler registrations and event publishing across three execution
    modes: SYNC (synchronous), THREAD (thread-based), and CORELET (process-based).

    It implements a producer-consumer pattern with priority-based event queuing,
    thread pool management, automatic retry logic, timeout handling, and LRU-based
    result caching. The EventBus is a singleton to ensure a single point of event
    coordination across the application.

    Attributes
    ----------
    _num_threads : int
        Number of worker threads for async processing
    _input_queue : queue.PriorityQueue
        Priority queue for incoming events
    _output_queue : queue.Queue
        Queue for completed event results
    _worker_threads : List[threading.Thread]
        Pool of worker threads for async event processing
    _result_list : OrderedDict
        LRU cache for event results
    _max_cached_results : int
        Maximum number of cached results before LRU eviction
    _event_factory : EventFactory
        Factory for creating and managing event handlers
    _progress_context : Dict[int, tuple]
        Thread-local progress tracking context

    Notes
    -----
    **Execution Modes:**
    - SYNC: Events processed synchronously in the calling thread
    - THREAD: Events processed asynchronously in worker thread pool
    - CORELET: Events forwarded to isolated worker processes
    - CMD: Special mode for subprocess command execution

    **Internal Events:**
    - `_shutdown`: Graceful shutdown signal
    - `_cmd_execution`: Subprocess command execution
    - `_corelet_forwarding`: Corelet process communication

    **Result Caching Strategy:**
    - Specific event_id requests consume results (remove from cache)
    - Bulk requests preserve results (LRU eviction handles memory)
    - Cache size is auto-configured based on thread pool size

    **Thread Safety:**
    - All public methods are thread-safe
    - Uses RLock for re-entrant locking
    - Worker threads use thread-local storage for handler caching

    Examples
    --------
    Initialize EventBus with auto-detected CPU cores:

    >>> bus = EventBus()

    Initialize with specific thread count:

    >>> bus = EventBus(num_threads=8)

    Publish synchronous event and get results immediately:

    >>> event = Event("data_process", event_exec_mode=EXECUTION_MODE_SYNC)
    >>> event_id = bus.publish(event)
    >>> results = bus.get_results([event_id])

    Publish multiple threaded events and wait for completion:

    >>> events = [Event(f"task_{i}", event_exec_mode=EXECUTION_MODE_THREAD)
    ...           for i in range(10)]
    >>> event_ids = [bus.publish(e) for e in events]
    >>> bus.join()  # Wait for all events to complete
    >>> results = bus.get_results(event_ids)

    Enable progress tracking for current thread:

    >>> tracker = ProgressTracker(total=100)
    >>> bus.set_progress_tracker(tracker, progress_steps=1)
    >>> # All events published from this thread will auto-update progress
    >>> bus.clear_progress_tracker()  # Clean up when done
    """

    __slots__ = (
        "_logger",
        "_input_queue",
        "_output_queue",
        "_worker_threads",
        "_num_threads",
        "_next_thread_id",
        "_event_counter",
        "_result_list",
        "_publish_lock",
        "_sync_event_context",
        "_event_factory",
        "_max_cached_results",
        "_initialized",
        "_progress_context",
        "_active_corelets",
        "_corelet_lock",
    )

    def __init__(self, num_threads: Optional[int] = None) -> None:
        """
        Initialize EventBus singleton.

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
        # Smart init check for singleton pattern
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._logger = logging.getLogger(__name__)

        # Autodetect cpus and logical cores
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

        # Response tracking system
        self._max_cached_results = num_threads * 1000 if num_threads else 10000
        self._result_list = OrderedDict()
        self._publish_lock = threading.RLock()

        # Progress tracking context per thread
        self._progress_context: Dict[int, tuple] = {}

        # Corelet process tracking (thread_id -> process_id)
        self._active_corelets: Dict[int, int] = {}
        self._corelet_lock = threading.Lock()

        # Create sync event context once
        self._sync_event_context = basefunctions.EventContext(thread_local_data=threading.local())

        # Get EventFactory instance
        self._event_factory = basefunctions.EventFactory()

        # Register internal event types
        self._event_factory.register_event_type(
            INTERNAL_CORELET_FORWARDING_EVENT, basefunctions.CoreletForwardingHandler
        )
        self._event_factory.register_event_type(INTERNAL_CMD_EXECUTION_EVENT, basefunctions.DefaultCmdHandler)
        self._event_factory.register_event_type(INTERNAL_SHUTDOWN_EVENT, basefunctions.CoreletForwardingHandler)

        # Initialize threading system
        self._setup_thread_system()
        self._logger.info(f"EventBus initialized with {self._num_threads} worker threads")

        # Mark as initialized
        self._initialized = True

    # =============================================================================
    # PUBLIC API - PROGRESS TRACKING
    # =============================================================================

    def set_progress_tracker(self, progress_tracker: "basefunctions.ProgressTracker", progress_steps: int = 1) -> None:
        """
        Set progress tracker for all events published in current thread.

        Parameters
        ----------
        progress_tracker : basefunctions.ProgressTracker
            Progress tracker instance for automatic progress updates
        progress_steps : int, optional
            Number of steps to advance after each event completion. Default is 1.
        """
        thread_id = threading.get_ident()
        with self._publish_lock:
            self._progress_context[thread_id] = (progress_tracker, progress_steps)

    def clear_progress_tracker(self) -> None:
        """Clear progress tracker for current thread."""
        thread_id = threading.get_ident()
        with self._publish_lock:
            self._progress_context.pop(thread_id, None)

    # =============================================================================
    # PUBLIC API - CORELET MONITORING
    # =============================================================================

    def get_corelet_count(self) -> int:
        """
        Get current count of active corelet processes.

        Returns
        -------
        int
            Number of active corelet worker processes
        """
        with self._corelet_lock:
            return len(self._active_corelets)

    def get_corelet_metrics(self) -> Dict[str, int]:
        """
        Get corelet process metrics.

        Returns
        -------
        Dict[str, int]
            Metrics dictionary with:
            - active_corelets: Number of active corelet processes
            - worker_threads: Number of worker threads
            - max_corelets: Maximum possible corelets (= worker_threads)

        Notes
        -----
        Expected lifecycle:
        - Corelets created on first CORELET event per worker thread
        - Corelets reused for subsequent events in same thread
        - Corelets cleaned up on worker thread shutdown
        - Corelets auto-terminate after 10 minutes idle time
        """
        with self._corelet_lock:
            return {
                "active_corelets": len(self._active_corelets),
                "worker_threads": self._num_threads,
                "max_corelets": self._num_threads,
            }

    # =============================================================================
    # PUBLIC API - EVENT PUBLISHING
    # =============================================================================

    def publish(self, event: "basefunctions.Event") -> str:
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
            raise basefunctions.InvalidEventError(f"Invalid event type: {type(event).__name__}")

        if not hasattr(event, "event_id") or not event.event_id:
            raise basefunctions.InvalidEventError("Event must have a valid event_id")

        if not hasattr(event, "event_type") or not event.event_type:
            raise basefunctions.InvalidEventError("Event must have a valid event_type")

        if not hasattr(event, "event_exec_mode"):
            raise basefunctions.InvalidEventError("Event must have a valid event_exec_mode")

        # Thread-safe publish with lock to prevent race conditions
        with self._publish_lock:

            # Auto-enrich event with progress context if not explicitly set
            # This allows thread-level progress tracking without modifying event creation
            thread_id = threading.get_ident()
            if thread_id in self._progress_context and not event.progress_tracker:
                tracker, steps = self._progress_context[thread_id]
                event.progress_tracker = tracker
                event.progress_steps = steps

            event_type = event.event_type
            execution_mode = event.event_exec_mode

            # Skip handler availability check for CMD mode - uses internal handler
            # CMD mode events are handled by DefaultCmdHandler which is always registered
            if execution_mode != basefunctions.EXECUTION_MODE_CMD:
                if not self._event_factory.is_handler_available(event_type):
                    raise basefunctions.NoHandlerAvailableError(event_type)

            # Thread-safe event counter and response registration
            self._event_counter += 1
            self._result_list[event.event_id] = None

            # Route event based on execution mode
            if execution_mode == basefunctions.EXECUTION_MODE_SYNC:
                self._handle_sync_event(event=event)
            elif execution_mode == basefunctions.EXECUTION_MODE_THREAD:
                self._handle_thread_and_corelet_event(event=event)
            elif execution_mode == basefunctions.EXECUTION_MODE_CORELET:
                self._handle_thread_and_corelet_event(event=event)
            elif execution_mode == basefunctions.EXECUTION_MODE_CMD:
                self._handle_thread_and_corelet_event(event=event)
            else:
                raise basefunctions.InvalidEventError(f"Unknown execution mode: {execution_mode}")

            return event.event_id

    def join(self) -> None:
        """
        Wait for all async tasks to complete and collect results.
        """
        self._input_queue.join()

    def get_results(
        self,
        event_ids: List[str] | None = None,
        join_before: bool = True,
    ) -> Dict[str, "basefunctions.EventResult"]:
        """
        Get response(s) from processed events with smart cleanup strategy.

        This method implements a dual-mode result retrieval system:
        - Specific event_ids: Consumer pattern (results removed from cache)
        - No event_ids: Observer pattern (results preserved in cache)

        Parameters
        ----------
        event_ids : List[str], optional
            List of event_ids to retrieve. If None, returns all cached events.
            Specific IDs will be consumed (removed from cache) and returned as Dict.
            Can also be a single string event_id (will be normalized to list).
        join_before : bool, optional
            If True, waits for input queue to be empty before retrieving results.
            Set to False for non-blocking result retrieval (default: True).

        Returns
        -------
        Dict[str, EventResult]
            Dictionary mapping event_ids to EventResult objects.
            When specific event_ids are given, they are consumed (removed from cache).
            When None, returns all cached results (preserved in cache).

        Notes
        -----
        **Result Cleanup Strategy:**
        - Specific IDs: Results are removed from cache (consumer pattern)
        - Bulk request (None): Results preserved, LRU handles eviction
        - This prevents unbounded memory growth while supporting both patterns

        **Thread Safety:**
        - Output queue draining uses try/except to avoid race conditions
        - Result list operations are protected by _publish_lock

        Examples
        --------
        Get specific event results (consumer pattern):

        >>> event_id = bus.publish(event)
        >>> results = bus.get_results([event_id])  # Result removed from cache
        >>> results[event_id].success
        True

        Get all results without consuming (observer pattern):

        >>> results = bus.get_results()  # All results, preserved in cache
        >>> len(results)
        42

        Non-blocking result check:

        >>> results = bus.get_results([event_id], join_before=False)
        >>> if event_id in results:
        ...     print("Event completed")
        """
        # Wait for all queued events to finish if requested
        # This ensures all results are available before retrieval
        if join_before:
            self._input_queue.join()

        # Drain output queue and populate result cache with LRU eviction
        # Use try/except pattern to avoid race condition between empty() and get_nowait()
        while True:
            try:
                event_result = self._output_queue.get_nowait()
                # Store result in LRU cache (oldest results auto-evicted when limit reached)
                self._add_result_with_lru(event_result.event_id, event_result)
            except queue.Empty:
                break

        # Normalize event_ids parameter to list
        if isinstance(event_ids, str):
            event_ids = [event_ids]
        elif event_ids is None:
            # CASE 2: Bulk request - return all but keep in cache (LRU handles cleanup)
            # Observer pattern: Multiple consumers can read the same results
            with self._publish_lock:
                event_ids = list(self._result_list.keys())
                return {eid: self._result_list.get(eid) for eid in event_ids if self._result_list.get(eid)}

        # CASE 1: Specific IDs requested - Consumer pattern (remove from cache)
        # One-time consumption: Results are removed after retrieval
        results = {}
        with self._publish_lock:
            for eid in event_ids:
                result = self._result_list.pop(eid, None)  # pop() removes from cache!
                if result:
                    results[eid] = result
        return results

    def shutdown(self, immediately: bool = False) -> None:
        """
        Shutdown EventBus and all worker threads/processes.

        Parameters
        ----------
        immediately : bool, optional
            If True, shutdown immediately with high priority.
            If False, shutdown gracefully after queue processing. Default is False.
        """
        # Create shutdown event with corelet execution mode
        shutdown_event = basefunctions.Event(
            basefunctions.INTERNAL_SHUTDOWN_EVENT,
            event_exec_mode=basefunctions.EXECUTION_MODE_CORELET,
            priority=-1 if immediately else DEFAULT_PRIORITY,
        )

        # Send shutdown events to all worker threads using publish
        for i in range(len(self._worker_threads)):
            self.publish(shutdown_event)

        # Wait for worker threads to finish
        self.join()

        self._logger.info("EventBus shutdown complete")

    # =============================================================================
    # EVENT ROUTING & PROCESSING
    # =============================================================================

    def _handle_sync_event(self, event: "basefunctions.Event") -> None:
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

        # Update progress tracker if attached
        if event.progress_tracker and event.progress_steps > 0:
            event.progress_tracker.progress(event.progress_steps)

    def _handle_thread_and_corelet_event(self, event: "basefunctions.Event") -> None:
        """
        Handle a threading or corelet event by queuing for async processing.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle
        """

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
        _running_flag = True

        while _running_flag:
            task = None
            try:
                # Get new task from input queue with timeout
                task = self._input_queue.get(timeout=5.0)

                # Extract task components: (priority, counter, event)
                if not task or len(task) != 3:
                    self._logger.warning("Invalid task format in worker thread %d", thread_id)
                    continue

                _, _, event = task

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

                # Update progress tracker if attached
                if event.progress_tracker and event.progress_steps > 0:
                    event.progress_tracker.progress(event.progress_steps)

                # Check for shutdown event after processing
                if event.event_type == INTERNAL_SHUTDOWN_EVENT:
                    # Cleanup corelet BEFORE exiting worker thread
                    self._cleanup_corelet(_worker_context)
                    _running_flag = False
                    break

            except queue.Empty:
                continue

            except Exception as e:
                self._logger.error("Critical error in worker thread %d: %s", thread_id, str(e))
                if task is not None:
                    _, _, event = task
                    error_result = basefunctions.EventResult.exception_result(event.event_id, e)
                    self._output_queue.put(item=error_result)
            finally:
                if task is not None:
                    self._input_queue.task_done()

    # =============================================================================
    # EVENT PROCESSING ENGINE
    # =============================================================================
    def _process_event_thread_worker(
        self,
        event: "basefunctions.Event",
        worker_context: "basefunctions.EventContext",
    ) -> "basefunctions.EventResult":
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
        self,
        event: "basefunctions.Event",
        worker_context: "basefunctions.EventContext",
    ) -> "basefunctions.EventResult":
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
        cmd_handler = self._get_handler(INTERNAL_CMD_EXECUTION_EVENT, worker_context)

        # Execute with retry logic
        return self._retry_with_timeout(event, cmd_handler, worker_context)

    def _process_event_corelet_worker(
        self,
        event: "basefunctions.Event",
        worker_context: "basefunctions.EventContext",
    ) -> "basefunctions.EventResult":
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
        forwarding_handler = self._get_handler(INTERNAL_CORELET_FORWARDING_EVENT, worker_context)

        # Execute with retry logic - forwarding handler manages corelet communication
        return self._retry_with_timeout(event, forwarding_handler, worker_context)

    def _retry_with_timeout(
        self,
        event: "basefunctions.Event",
        handler: "basefunctions.EventHandler",
        context: "basefunctions.EventContext",
    ) -> "basefunctions.EventResult":
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
            try:
                # For corelet mode: Add 1 second safety buffer to TimerThread
                timer_timeout = (
                    event.timeout + 1
                    if event.event_exec_mode == basefunctions.EXECUTION_MODE_CORELET
                    else event.timeout
                )

                with basefunctions.TimerThread(timer_timeout, threading.get_ident()):
                    event_result = handler.handle(event, context)

                if event_result.success:
                    return event_result
                else:
                    last_business_failure = event_result

            except TimeoutError as e:
                last_exception = e
                self._logger.warning("Timeout on attempt %d: %s", attempt + 1, str(e))

                # Terminate handler process if timeout occurs
                if hasattr(handler, "terminate"):
                    try:
                        handler.terminate(context=context)
                    except Exception as terminate_error:
                        self._logger.error("Failed to terminate handler process: %s", str(terminate_error))

            except Exception as e:
                last_exception = e
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

    def _cleanup_corelet(self, context: "basefunctions.EventContext") -> None:
        """
        Clean up corelet process and pipes when worker thread shuts down.

        Parameters
        ----------
        context : basefunctions.EventContext
            Worker context containing corelet_handle in thread_local_data
        """
        if not hasattr(context.thread_local_data, "corelet_handle"):
            return

        handle = context.thread_local_data.corelet_handle
        thread_id = threading.get_ident()

        try:
            # Send shutdown event to corelet
            shutdown_event = basefunctions.Event(
                INTERNAL_SHUTDOWN_EVENT, event_exec_mode=basefunctions.EXECUTION_MODE_CORELET
            )
            pickled_event = pickle.dumps(shutdown_event)
            handle.input_pipe.send(pickled_event)

            # Wait for acknowledgment with timeout
            if handle.output_pipe.poll(timeout=5):
                handle.output_pipe.recv()

            # Terminate process
            handle.process.terminate()
            handle.process.join(timeout=2)

            # Close pipes
            handle.input_pipe.close()
            handle.output_pipe.close()

            # Remove from tracking
            with self._corelet_lock:
                self._active_corelets.pop(thread_id, None)

            self._logger.debug(
                "Corelet cleanup successful for thread %d (PID: %d, remaining: %d)",
                thread_id,
                handle.process.pid,
                len(self._active_corelets),
            )

        except Exception as e:
            self._logger.error(f"Corelet cleanup failed: {e}")
            # Force kill on cleanup failure
            try:
                handle.process.kill()
            except Exception:
                pass
            finally:
                # Remove from tracking even on failure
                with self._corelet_lock:
                    self._active_corelets.pop(thread_id, None)
        finally:
            delattr(context.thread_local_data, "corelet_handle")

    def _register_corelet(self, thread_id: int, process_id: int) -> None:
        """
        Register new corelet process for tracking.

        Parameters
        ----------
        thread_id : int
            Worker thread ID that owns the corelet
        process_id : int
            Corelet process ID
        """
        with self._corelet_lock:
            self._active_corelets[thread_id] = process_id

    # =============================================================================
    # HANDLER MANAGEMENT
    # =============================================================================

    def _get_handler(self, event_type: str, context: "basefunctions.EventContext") -> "basefunctions.EventHandler":
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
            handler = self._event_factory.create_handler(event_type)

            # Validate handler instance
            if not isinstance(handler, basefunctions.EventHandler):
                raise TypeError(f"Factory returned invalid handler type: {type(handler).__name__}")

            # Store in thread-local cache
            context.thread_local_data.handlers[event_type] = handler

            return handler

        except Exception as e:
            raise RuntimeError(f"Failed to create handler for event_type '{event_type}': {str(e)}") from e

    def _add_result_with_lru(self, event_id: str, result: "basefunctions.EventResult") -> None:
        """
        Add result with LRU eviction policy.

        Parameters
        ----------
        event_id : str
            Event ID for result storage
        result : basefunctions.EventResult
            Result to store
        """
        with self._publish_lock:  # Thread-safe
            # Entfernen falls bereits vorhanden (für move-to-end)
            if event_id in self._result_list:
                del self._result_list[event_id]

            # Hinzufügen (ans Ende)
            self._result_list[event_id] = result

            # LRU eviction: älteste entfernen wenn Limit überschritten
            while len(self._result_list) > self._max_cached_results:
                oldest_id = next(iter(self._result_list))  # erstes Element
                del self._result_list[oldest_id]
