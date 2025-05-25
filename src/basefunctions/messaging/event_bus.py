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
MAX_TASK_QUEUE_SIZE = 10000
MAX_OUTPUT_QUEUE_SIZE = 5000
THREAD_SHUTDOWN_TIMEOUT = 10.0
THREAD_SHUTDOWN_CHECK_INTERVAL = 0.5
THREAD_LOCAL_CLEANUP_INTERVAL = 300.0

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_DEFAULT_INSTANCE = None
SENTINEL = object()

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ResultCollector:
    """
    Unified result collection system for all execution modes.
    """

    __slots__ = ("_results", "_lock", "_max_results")

    def __init__(self, max_results: int = 50000):
        """
        Initialize result collector.

        Parameters
        ----------
        max_results : int
            Maximum number of results to store.
        """
        self._results: List[Any] = []
        self._lock = threading.Lock()
        self._max_results = max_results

    def add_result(self, result: Any) -> None:
        """
        Add result thread-safely.

        Parameters
        ----------
        result : Any
            Result to add.
        """
        with self._lock:
            self._results.append(result)

            if len(self._results) > self._max_results:
                cleanup_count = self._max_results // 5
                self._results = self._results[cleanup_count:]

    def get_results(
        self, clear: bool = True, success_only: bool = False, errors_only: bool = False
    ) -> Union[List[Any], Tuple[List[Any], List[str]]]:
        """
        Get results with filtering options.

        Parameters
        ----------
        clear : bool
            Clear results after getting them.
        success_only : bool
            Return only success results.
        errors_only : bool
            Return only error messages.

        Returns
        -------
        Union[List[Any], Tuple[List[Any], List[str]]]
            Filtered results.
        """
        with self._lock:
            all_results = self._results.copy()
            if clear:
                self._results.clear()

        success_results = []
        error_results = []

        for result in all_results:
            if isinstance(result, str) and result.startswith("exception: "):
                error_results.append(result)
            else:
                success_results.append(result)

        if success_only:
            return success_results
        elif errors_only:
            return error_results
        else:
            return success_results, error_results

    def count(self) -> int:
        """
        Get current result count.

        Returns
        -------
        int
            Number of results.
        """
        with self._lock:
            return len(self._results)

    def clear(self) -> int:
        """
        Clear all results and return count of cleared items.

        Returns
        -------
        int
            Number of results that were cleared.
        """
        with self._lock:
            count = len(self._results)
            self._results.clear()
            return count


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
        """Handle ping request."""
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


class ThreadLocalDataManager:
    """
    Manager for thread-local data with periodic cleanup.
    """

    def __init__(self):
        self._data = threading.local()
        self._last_cleanup = time.time()
        self._lock = threading.Lock()

    def get_data(self):
        """Get thread-local data."""
        if not hasattr(self._data, "storage"):
            self._data.storage = {}
        return self._data.storage

    def cleanup_if_needed(self):
        """Cleanup thread-local data periodically."""
        current_time = time.time()
        if current_time - self._last_cleanup > THREAD_LOCAL_CLEANUP_INTERVAL:
            with self._lock:
                if hasattr(self._data, "storage"):
                    self._data.storage.clear()
                self._last_cleanup = current_time


class EventBus:
    """
    Central event distribution system with unified messaging support.

    The EventBus manages handler registrations and event publishing
    across sync, thread, and corelet execution modes.
    """

    __slots__ = (
        "_handlers",
        "_logger",
        "_result_collector",
        "_task_queue",
        "_output_queue",
        "_worker_threads",
        "_control_thread",
        "_corelet_pool",
        "_running",
        "_num_threads",
        "_corelet_pool_size",
        "_control_handler",
        "_shutdown_in_progress",
        "_thread_local_manager",
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
        self._handlers: Dict[str, List[basefunctions.EventHandler]] = {}
        self._logger = logging.getLogger(__name__)

        self._result_collector = ResultCollector()

        self._task_queue: Optional[queue.Queue] = None
        self._output_queue: Optional[queue.Queue] = None
        self._worker_threads: List[threading.Thread] = []
        self._control_thread: Optional[threading.Thread] = None

        self._corelet_pool: Optional[basefunctions.CoreletPool] = None

        self._running = True
        self._shutdown_in_progress = False

        self._thread_local_manager = ThreadLocalDataManager()

        if num_threads is None:
            cpu_cores = psutil.cpu_count(logical=False)
            logical_cores = psutil.cpu_count(logical=True)
            num_threads = logical_cores
            self._logger.info(f"Auto-detected {cpu_cores} physical, {logical_cores} logical cores")

        self._num_threads = num_threads

        if corelet_pool_size is None:
            corelet_pool_size = min(psutil.cpu_count(logical=False), 8)

        self._corelet_pool_size = corelet_pool_size

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

        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler.execution_mode == 2:  # corelet
            module_name = handler.__class__.__module__
            if module_name == "__main__":
                raise ValueError(
                    f"Corelet handlers cannot be defined in __main__. "
                    f"Move {handler.__class__.__name__} to a separate module."
                )

        self._handlers[event_type].append(handler)

        if handler.execution_mode == 1:  # thread
            if self._task_queue is None:
                self._setup_thread_system()
        elif handler.execution_mode == 2:  # corelet
            if self._corelet_pool is None:
                self._setup_corelet_system()

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
        if self._shutdown_in_progress:
            self._logger.warning("Ignoring event during shutdown: %s", event.type)
            return

        event_type = event.type

        if event_type not in self._handlers:
            return

        for handler in self._handlers[event_type]:
            if handler.execution_mode == 0:  # sync
                try:
                    result = handler.handle(event)
                    self._result_collector.add_result(result)
                except Exception as e:
                    self._logger.error("Error in sync handler: %s", str(e))
                    self._result_collector.add_result(f"exception: {str(e)}")
            elif handler.execution_mode == 1:  # thread
                if self._task_queue.qsize() >= MAX_TASK_QUEUE_SIZE:
                    self._logger.warning("Task queue full, dropping event: %s", event.type)
                    self._result_collector.add_result("exception: Task queue full")
                else:
                    self._task_queue.put((handler, event, self._result_collector))
            elif handler.execution_mode == 2:  # corelet
                try:
                    task_id = self._corelet_pool.submit_task_async(event, handler)
                    self._logger.debug("Submitted corelet task %s", task_id)
                except Exception as e:
                    self._logger.error("Error submitting corelet task: %s", str(e))
                    self._result_collector.add_result(f"exception: {str(e)}")

    def join(self) -> None:
        """
        Wait for all async tasks to complete and collect results.
        """
        if self._task_queue is not None:
            self._task_queue.join()

        if self._corelet_pool is not None:
            self._logger.debug("Waiting for corelet tasks to complete...")
            success = self._corelet_pool.wait_for_completion(timeout=300.0)
            if not success:
                self._logger.warning("Corelet tasks did not complete within timeout")

            corelet_results = self._corelet_pool.collect_results()
            for result in corelet_results:
                self._result_collector.add_result(result)
            self._logger.debug("Collected %d corelet results", len(corelet_results))

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
        return self._result_collector.get_results(
            clear=True, success_only=success_only, errors_only=errors_only
        )

    def _setup_thread_system(self) -> None:
        """
        Initialize thread processing system on first thread handler registration.
        """
        if self._task_queue is not None:
            return

        self._task_queue = queue.Queue(maxsize=MAX_TASK_QUEUE_SIZE)
        self._output_queue = queue.Queue(maxsize=MAX_OUTPUT_QUEUE_SIZE)

        for i in range(self._num_threads):
            self._add_worker_thread()

        self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self._control_thread.start()

        self._logger.info("Thread system initialized with %d worker threads", self._num_threads)

    def _setup_corelet_system(self) -> None:
        """
        Initialize corelet processing system on first corelet handler registration.
        """
        if self._corelet_pool is not None:
            return

        self._corelet_pool = basefunctions.CoreletPool(pool_size=self._corelet_pool_size)
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
        self._logger.debug("Worker thread %d started", thread_id)

        while True:
            task = None
            try:
                self._thread_local_manager.cleanup_if_needed()

                task = self._task_queue.get(timeout=5.0)
                if task is SENTINEL:
                    break

                handler, event, result_collector = task
                result = self._process_event_thread(event, handler, thread_id)
                result_collector.add_result(result)

            except queue.Empty:
                continue
            except Exception as e:
                self._logger.error("Error in worker thread %d: %s", thread_id, str(e))
                if task and len(task) >= 3:
                    result_collector = task[2]
                    result_collector.add_result(f"exception: {str(e)}")
            finally:
                if task is not None:
                    self._task_queue.task_done()

        try:
            thread_local_data = self._thread_local_manager.get_data()
            thread_local_data.clear()
        except Exception as e:
            self._logger.warning("Error cleaning thread-local data: %s", str(e))

        self._logger.debug("Worker thread %d stopped", thread_id)

    def _process_event_thread(
        self,
        event: basefunctions.Event,
        handler: basefunctions.EventHandler,
        thread_id: int,
    ) -> Any:
        """
        Process event in thread with context.

        Parameters
        ----------
        event : Event
            Event to process.
        handler : EventHandler
            Handler to process the event.
        thread_id : int
            Thread identifier.

        Returns
        -------
        Any
            Result data on success, exception string on error.
        """
        try:
            thread_local_data = self._thread_local_manager.get_data()
            context = basefunctions.EventContext(
                execution_mode="thread",
                thread_local_data=thread_local_data,
                thread_id=thread_id,
            )

            return handler.handle(event, context)
        except Exception as e:
            return f"exception: {str(e)}"

    def _control_loop(self) -> None:
        """
        Control thread main loop for system monitoring.
        """
        while self._running and not self._shutdown_in_progress:
            try:
                ping_event = basefunctions.Event("control.ping_request")

                if self._task_queue and self._task_queue.qsize() > self._num_threads * 2:
                    create_event = basefunctions.Event("control.thread_create")
                    self.publish(create_event)

                time.sleep(5)

            except Exception as e:
                self._logger.error("Error in control loop: %s", str(e))

    def _graceful_thread_shutdown(self) -> bool:
        """
        Gracefully shutdown worker threads.

        Returns
        -------
        bool
            True if all threads shut down gracefully, False if timeout.
        """
        if not self._worker_threads:
            return True

        queue_size = self._task_queue.qsize() if self._task_queue else 0
        adaptive_timeout = min(THREAD_SHUTDOWN_TIMEOUT, max(2.0, queue_size * 0.1))

        self._logger.info(
            "Graceful thread shutdown: %d threads, %d queued tasks, timeout: %.1fs",
            len(self._worker_threads),
            queue_size,
            adaptive_timeout,
        )

        for _ in range(len(self._worker_threads)):
            try:
                self._task_queue.put(SENTINEL, timeout=1.0)
            except queue.Full:
                self._logger.warning("Queue full during shutdown")
                break

        start_time = time.time()

        while (time.time() - start_time) < adaptive_timeout:
            threads_alive = [t for t in self._worker_threads if t.is_alive()]
            if not threads_alive:
                self._logger.info("All worker threads shut down gracefully")
                return True

            time.sleep(THREAD_SHUTDOWN_CHECK_INTERVAL)

        threads_alive = [t for t in self._worker_threads if t.is_alive()]
        if threads_alive:
            self._logger.warning(
                "Graceful shutdown timeout: %d threads still alive", len(threads_alive)
            )

        return len(threads_alive) == 0

    def shutdown(self) -> None:
        """
        Shutdown the event bus and all async components.
        """
        if self._shutdown_in_progress:
            self._logger.warning("Shutdown already in progress")
            return

        self._logger.info("EventBus shutdown initiated")
        self._shutdown_in_progress = True
        self._running = False

        if self._task_queue is not None:
            graceful_success = self._graceful_thread_shutdown()
            if not graceful_success:
                self._logger.warning("Some threads did not shut down gracefully")

        if self._corelet_pool is not None:
            try:
                self._corelet_pool.shutdown()
            except Exception as e:
                self._logger.error("Error shutting down corelet pool: %s", str(e))

        cleared_results = self._result_collector.clear()
        if cleared_results > 0:
            self._logger.info("Cleared %d pending results during shutdown", cleared_results)

        handler_count = sum(len(handlers) for handlers in self._handlers.values())
        self._handlers.clear()

        self._logger.info("EventBus shutdown complete. Cleared %d handlers", handler_count)

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
            "pending_results": self._result_collector.count(),
            "shutdown_in_progress": self._shutdown_in_progress,
        }

        if self._task_queue is not None:
            alive_threads = sum(1 for t in self._worker_threads if t.is_alive())
            stats.update(
                {
                    "worker_threads": len(self._worker_threads),
                    "alive_threads": alive_threads,
                    "pending_thread_tasks": self._task_queue.qsize(),
                    "max_task_queue_size": MAX_TASK_QUEUE_SIZE,
                    "max_output_queue_size": MAX_OUTPUT_QUEUE_SIZE,
                }
            )

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
