"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 EventBus implementation with unified messaging system and corelet pool
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import threading
import queue
import time
import os
import psutil
from typing import Dict, List, Optional, Tuple, Any, Union

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
SENTINEL = object()

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ControlHandler(basefunctions.EventHandler):
    """
    Control handler for system management events.
    """

    execution_mode = 0  # sync

    def __init__(self, event_bus):
        """
        Initialize control handler.

        Parameters
        ----------
        event_bus : EventBus
            Reference to the event bus for system management.
        """
        self.event_bus = event_bus
        self._logger = logging.getLogger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle control events.

        Parameters
        ----------
        event : Event
            Control event to process.
        context : EventContext, optional
            Event context (unused for control events).

        Returns
        -------
        Any
            Result data on success, raise Exception on error.
        """
        try:
            if event.type == "control.thread_create":
                return self._handle_thread_create(event)
            elif event.type == "control.ping_request":
                return self._handle_ping_request(event)
            elif event.type == "control.ping_response":
                return self._handle_ping_response(event)
            elif event.type == "control.shutdown":
                return self._handle_shutdown(event)
            else:
                self._logger.warning("Unknown control event type: %s", event.type)
                raise ValueError(f"Unknown control event: {event.type}")
        except Exception as e:
            self._logger.error("Error in control handler: %s", str(e))
            raise

    def _handle_thread_create(self, event: basefunctions.Event) -> Any:
        """Handle thread creation request."""
        try:
            self.event_bus._add_worker_thread()
            return "Thread created"
        except Exception as e:
            raise Exception(f"Thread creation failed: {str(e)}")

    def _handle_ping_request(self, event: basefunctions.Event) -> Any:
        """Handle ping request - this is sent BY control thread, not handled by it."""
        return "Ping request processed"

    def _handle_ping_response(self, event: basefunctions.Event) -> Any:
        """Handle ping response from workers."""
        return "Ping response received"

    def _handle_shutdown(self, event: basefunctions.Event) -> Any:
        """Handle shutdown request."""
        try:
            self.event_bus.shutdown()
            return "Shutdown initiated"
        except Exception as e:
            raise Exception(f"Shutdown failed: {str(e)}")


class EventBus:
    """
    Central event distribution system with unified messaging support.

    The EventBus manages handler registrations and event publishing
    across sync, thread, and corelet execution modes.
    """

    __slots__ = (
        "_handlers",
        "_logger",
        "_results",
        "_task_queue",
        "_output_queue",
        "_worker_threads",
        "_control_thread",
        "_corelet_pool",
        "_running",
        "_num_threads",
        "_corelet_pool_size",
        "_control_handler",
    )

    def __init__(self, num_threads: Optional[int] = None, corelet_pool_size: Optional[int] = None):
        """
        Initialize a new EventBus.

        Parameters
        ----------
        num_threads : int, optional
            Number of worker threads for async processing.
            If None, auto-detects CPU core count.
        corelet_pool_size : int, optional
            Number of corelet worker processes.
            If None, auto-detects CPU core count.
        """
        # Main handler registry: event_type -> [handler1, handler2, ...]
        self._handlers: Dict[str, List[basefunctions.EventHandler]] = {}
        self._logger = logging.getLogger(__name__)

        # Result storage
        self._results: List[Any] = []

        # Thread system (lazy initialization)
        self._task_queue: Optional[queue.Queue] = None
        self._output_queue: Optional[queue.Queue] = None
        self._worker_threads: List[threading.Thread] = []
        self._control_thread: Optional[threading.Thread] = None

        # Corelet system (lazy initialization)
        self._corelet_pool: Optional[basefunctions.CoreletPool] = None

        # System state
        self._running = True

        # Auto-detect optimal thread count
        if num_threads is None:
            cpu_cores = psutil.cpu_count(logical=False)  # Physical cores
            logical_cores = psutil.cpu_count(logical=True)  # Logical cores
            # Use logical cores for I/O-bound tasks like subprocess handling
            num_threads = logical_cores
            self._logger.info(f"Auto-detected {cpu_cores} physical, {logical_cores} logical cores")

        self._num_threads = num_threads

        # Auto-detect corelet pool size
        if corelet_pool_size is None:
            corelet_pool_size = min(psutil.cpu_count(logical=False), 8)  # Cap at 8 processes

        self._corelet_pool_size = corelet_pool_size

        # Control handler
        self._control_handler = ControlHandler(self)

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
        """
        if not isinstance(handler, basefunctions.EventHandler):
            raise TypeError("Handler must be an instance of EventHandler")

        # Initialize handler list for this event type if needed
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        # Check for corelet handlers in __main__
        if handler.execution_mode == 2:  # corelet
            module_name = handler.__class__.__module__
            if module_name == "__main__":
                raise ValueError(
                    f"Corelet handlers cannot be defined in __main__. "
                    f"Move {handler.__class__.__name__} to a separate module."
                )

        # Add the handler to the registry
        self._handlers[event_type].append(handler)

        # Setup async infrastructure if needed
        if handler.execution_mode == 1:  # thread
            if self._task_queue is None:
                self._setup_thread_system()
        elif handler.execution_mode == 2:  # corelet
            if self._corelet_pool is None:
                self._setup_corelet_system()

        # Register control handler for control events
        if event_type.startswith("control."):
            if self._control_handler not in self._handlers[event_type]:
                self._handlers[event_type].append(self._control_handler)

        return True

    def unregister(self, event_type: str, handler: basefunctions.EventHandler) -> bool:
        """
        Unregister a handler from an event type.

        Parameters
        ----------
        event_type : str
            The event type to unregister from.
        handler : EventHandler
            The handler to unregister.

        Returns
        -------
        bool
            True if the handler was unregistered, False if it wasn't registered.
        """
        if event_type not in self._handlers:
            return False

        try:
            self._handlers[event_type].remove(handler)
            return True
        except ValueError:
            return False

    def publish(self, event: basefunctions.Event) -> None:
        """
        Publish an event to all registered handlers.

        Parameters
        ----------
        event : Event
            The event to publish.
        """
        event_type = event.type

        if event_type not in self._handlers:
            return

        # Process each handler for this event type
        for handler in self._handlers[event_type]:
            if handler.execution_mode == 0:  # sync
                try:
                    result = handler.handle(event)
                    self._results.append(result)
                except Exception as e:
                    self._logger.error("Error in sync handler: %s", str(e))
                    self._results.append(f"exception: {str(e)}")
            elif handler.execution_mode == 1:  # thread
                # Thread - put in task queue
                self._task_queue.put((handler, event))
            elif handler.execution_mode == 2:  # corelet
                # Corelet - submit to pool
                try:
                    future = self._corelet_pool.submit_task(event, handler)
                    # Store future for later collection
                    self._results.append(future)
                except Exception as e:
                    self._logger.error("Error submitting corelet task: %s", str(e))
                    self._results.append(f"exception: {str(e)}")

    def join(self) -> None:
        """
        Wait for all async tasks to complete and collect results.
        """
        # Wait for thread tasks
        if self._task_queue is not None:
            self._task_queue.join()
            self._collect_thread_results()

        # Wait for corelet tasks
        if self._corelet_pool is not None:
            self._collect_corelet_results()

    def get_results(
        self, success_only: bool = False, errors_only: bool = False
    ) -> Union[List[Any], Tuple[List[Any], List[str]]]:
        """
        Returns filtered results based on what you want.

        Parameters
        ----------
        success_only : bool
            Return only success results
        errors_only : bool
            Return only error messages
        Default: Return both as tuple

        Returns
        -------
        Union[List[Any], Tuple[List[Any], List[str]]]
            - Default: (success_results, error_results)
            - success_only=True: success_results
            - errors_only=True: error_results
        """
        all_results = self._results
        self._results = []

        success_results = []
        error_results = []

        for result in all_results:
            if isinstance(result, str) and result.startswith("exception: "):
                error_results.append(result)
            else:
                success_results.append(result)  # Includes None results

        if success_only:
            return success_results
        elif errors_only:
            return error_results
        else:
            return success_results, error_results

    def _setup_thread_system(self) -> None:
        """
        Initialize thread processing system on first thread handler registration.
        """
        if self._task_queue is not None:
            return  # Already initialized

        self._task_queue = queue.Queue()
        self._output_queue = queue.Queue()

        # Start worker threads
        for i in range(self._num_threads):
            self._add_worker_thread()

        # Start control thread
        self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self._control_thread.start()

        self._logger.info("Thread system initialized with %d worker threads", self._num_threads)

    def _setup_corelet_system(self) -> None:
        """
        Initialize corelet processing system on first corelet handler registration.
        """
        if self._corelet_pool is not None:
            return  # Already initialized

        # Initialize corelet pool
        self._corelet_pool = basefunctions.CoreletPool(pool_size=self._corelet_pool_size)

        # Start the pool
        self._corelet_pool.start()

        self._logger.info(
            "Corelet system initialized with %d worker processes", self._corelet_pool_size
        )

    def _add_worker_thread(self) -> None:
        """
        Add a new worker thread to the pool.
        """
        thread_id = len(self._worker_threads)
        thread = threading.Thread(
            target=self._worker_loop,
            name=f"EventWorker-{thread_id}",
            args=(thread_id,),
            daemon=True,
        )
        thread.start()
        self._worker_threads.append(thread)
        self._logger.info("Started new worker thread: %s", thread.name)

    def _worker_loop(self, thread_id: int) -> None:
        """
        Main worker thread loop for processing async events.

        Parameters
        ----------
        thread_id : int
            Unique identifier for this worker thread.
        """
        thread_local_data = threading.local()

        while True:
            try:
                # Get task from queue
                task = self._task_queue.get()
                if task is SENTINEL:
                    self._task_queue.task_done()
                    break

                handler, event = task

                # Process thread event
                result = self._process_event_thread(event, handler, thread_local_data)

                # Put result in output queue
                self._output_queue.put(result)

            except Exception as e:
                self._logger.error("Error in worker thread %d: %s", thread_id, str(e))
                self._output_queue.put(f"exception: {str(e)}")
            finally:
                self._task_queue.task_done()

    def _process_event_thread(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        thread_local_data: threading.local,
    ) -> Any:
        """
        Process event in thread with context.

        Parameters
        ----------
        event : Event
            Event to process.
        handler : EventHandler
            Handler to process the event.
        thread_local_data : threading.local
            Thread-local data storage.

        Returns
        -------
        Any
            Result data on success, exception string on error.
        """
        try:
            # Create thread context
            context = basefunctions.EventContext(
                execution_mode="thread",
                thread_local_data=thread_local_data,
                thread_id=threading.get_ident(),
            )

            return handler.handle(event, context)
        except Exception as e:
            return f"exception: {str(e)}"

    def _control_loop(self) -> None:
        """
        Control thread main loop for system monitoring.
        """
        while self._running:
            try:
                # Health check - send ping requests
                ping_event = basefunctions.Event("control.ping_request")
                # Note: In a full implementation, this would track responses

                # Check queue load and scale if needed
                if self._task_queue and self._task_queue.qsize() > self._num_threads * 2:
                    create_event = basefunctions.Event("control.thread_create")
                    self.publish(create_event)

                time.sleep(5)  # Health check interval

            except Exception as e:
                self._logger.error("Error in control loop: %s", str(e))

    def _collect_thread_results(self) -> None:
        """
        Collect results from thread output queue into results list.
        """
        while not self._output_queue.empty():
            try:
                result = self._output_queue.get_nowait()
                self._results.append(result)
            except queue.Empty:
                break

    def _collect_corelet_results(self) -> None:
        """
        Collect results from corelet futures into results list.
        """
        # Process futures in results list
        processed_results = []

        for result in self._results:
            if hasattr(result, "result"):  # Future object
                try:
                    # Wait for future to complete
                    actual_result = result.result(timeout=30.0)
                    processed_results.append(actual_result)
                except Exception as e:
                    processed_results.append(f"exception: {str(e)}")
            else:
                # Not a future, keep as is
                processed_results.append(result)

        self._results = processed_results

    def shutdown(self) -> None:
        """
        Shutdown the event bus and all async components.
        """
        self._running = False

        # Shutdown thread system
        if self._task_queue is not None:
            # Send sentinel messages to stop worker threads
            for _ in range(len(self._worker_threads)):
                self._task_queue.put(SENTINEL)

            # Wait briefly for threads to finish
            time.sleep(2)

        # Shutdown corelet system
        if self._corelet_pool is not None:
            self._corelet_pool.shutdown()

        self._logger.info("EventBus shutdown complete")

    def clear(self) -> None:
        """
        Clear all handler registrations.
        """
        self._handlers.clear()

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
            "thread_system_active": self._task_queue is not None,
            "corelet_system_active": self._corelet_pool is not None,
        }

        # Add thread stats
        if self._task_queue is not None:
            stats.update(
                {
                    "worker_threads": len(self._worker_threads),
                    "pending_thread_tasks": self._task_queue.qsize(),
                    "pending_thread_results": self._output_queue.qsize(),
                }
            )

        # Add corelet stats
        if self._corelet_pool is not None:
            stats.update(self._corelet_pool.get_stats())

        return stats


def get_event_bus() -> EventBus:
    """
    Get the default EventBus instance.

    Returns
    -------
    EventBus
        The default EventBus instance.
    """
    global _DEFAULT_INSTANCE
    if _DEFAULT_INSTANCE is None:
        _DEFAULT_INSTANCE = EventBus()
    return _DEFAULT_INSTANCE
