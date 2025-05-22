"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 EventBus implementation with unified messaging system
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import threading
import queue
import subprocess
import pickle
import time
import sys
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
        # Update health status
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
        "_active_corelet_processes",
        "_running",
        "_num_threads",
        "_control_handler",
    )

    def __init__(self, num_threads: Optional[int] = None):
        """
        Initialize a new EventBus.

        Parameters
        ----------
        num_threads : int, optional
            Number of worker threads for async processing.
            If None, auto-detects CPU core count.
        """
        # Main handler registry: event_type -> [handler1, handler2, ...]
        self._handlers: Dict[str, List[basefunctions.EventHandler]] = {}
        self._logger = logging.getLogger(__name__)

        # Result storage
        self._results: List[Any] = []

        # Async system (lazy initialization)
        self._task_queue: Optional[queue.Queue] = None
        self._output_queue: Optional[queue.Queue] = None
        self._worker_threads: List[threading.Thread] = []
        self._control_thread: Optional[threading.Thread] = None
        self._active_corelet_processes: List[subprocess.Popen] = []

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
        if handler.execution_mode in [1, 2]:  # thread, corelet
            if self._task_queue is None:
                self._setup_async_system()

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
            else:
                # Thread/Corelet - put in task queue
                self._task_queue.put((handler, event))

    def join(self) -> None:
        """
        Wait for all async tasks to complete and collect results.
        """
        if self._task_queue is not None:
            self._task_queue.join()
            self._collect_async_results()

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

    def _setup_async_system(self) -> None:
        """
        Initialize async processing system on first async handler registration.
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

        self._logger.info("Async system initialized with %d worker threads", self._num_threads)

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

                # Process based on execution mode
                if handler.execution_mode == 1:  # thread
                    result = self._process_event_thread(event, handler, thread_local_data)
                elif handler.execution_mode == 2:  # corelet
                    result = self._process_event_corelet(event, handler)
                else:
                    result = f"exception: Unknown execution mode: {handler.execution_mode}"

                # Put result in output queue
                self._output_queue.put(result)

            except Exception as e:
                self._logger.error("Error in worker thread %d: %s", thread_id, str(e))
                self._output_queue.put(f"exception: {str(e)}")
            finally:
                self._task_queue.task_done()

    def _process_event_sync(
        self, event: basefunctions.Event, handler: basefunctions.EventHandler
    ) -> Any:
        """
        Process event synchronously.

        Parameters
        ----------
        event : Event
            Event to process.
        handler : EventHandler
            Handler to process the event.

        Returns
        -------
        Any
            Result data on success, raise Exception on error.
        """
        return handler.handle(event)

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

    def _process_event_corelet(
        self, event: basefunctions.Event, handler: basefunctions.EventHandler
    ) -> Any:
        """
        Process event in subprocess corelet.

        Parameters
        ----------
        event : Event
            Event to process.
        handler : EventHandler
            Handler to process the event.

        Returns
        -------
        Any
            Result data on success, exception string on error.
        """
        try:
            # Get handler import path
            handler_path = f"{handler.__class__.__module__}.{handler.__class__.__name__}"

            # Set PYTHONPATH for subprocess
            current_dir = os.getcwd()
            env = os.environ.copy()
            env["PYTHONPATH"] = current_dir + ":" + env.get("PYTHONPATH", "")

            # Start corelet subprocess
            process = subprocess.Popen(
                [
                    "python",
                    os.path.join(os.path.dirname(__file__), "corelet_base.py"),
                    handler_path,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=current_dir,
            )

            # Track process for cleanup
            self._active_corelet_processes.append(process)

            try:
                # Send event data to subprocess
                event_data = pickle.dumps(event)
                process.stdin.write(event_data)
                process.stdin.flush()
                process.stdin.close()  # Send EOF signal

                # Read result from stdout
                result_data = process.stdout.read()
                return_code = process.wait()

                if return_code != 0:
                    error_output = process.stderr.read()
                    self._logger.error(
                        "Corelet process exited with code %d: %s", return_code, error_output
                    )
                    return f"exception: Corelet process failed with exit code {return_code}"

                if result_data:
                    result = pickle.loads(result_data)
                    return result
                else:
                    return f"exception: No result received from corelet process"

            finally:
                # Remove from active processes
                if process in self._active_corelet_processes:
                    self._active_corelet_processes.remove(process)

        except Exception as e:
            self._logger.error("Error in corelet processing: %s", str(e))
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
                if self._task_queue.qsize() > self._num_threads * 2:
                    create_event = basefunctions.Event("control.thread_create")
                    self.publish(create_event)

                time.sleep(5)  # Health check interval

            except Exception as e:
                self._logger.error("Error in control loop: %s", str(e))

    def _collect_async_results(self) -> None:
        """
        Collect results from async output queue into results list.
        """
        while not self._output_queue.empty():
            try:
                result = self._output_queue.get_nowait()
                self._results.append(result)
            except queue.Empty:
                break

    def shutdown(self) -> None:
        """
        Shutdown the event bus and all async components.
        """
        self._running = False

        if self._task_queue is not None:
            # Send sentinel messages to stop worker threads
            for _ in range(len(self._worker_threads)):
                self._task_queue.put(SENTINEL)

            # Wait briefly for threads to finish
            time.sleep(2)

            # Kill all active corelet processes
            for process in self._active_corelet_processes:
                try:
                    process.kill()
                except:
                    pass

            # Clear active processes
            self._active_corelet_processes.clear()

            # Wait a bit more
            time.sleep(1)

        self._logger.info("EventBus shutdown complete")

    def clear(self) -> None:
        """
        Clear all handler registrations.
        """
        self._handlers.clear()


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
