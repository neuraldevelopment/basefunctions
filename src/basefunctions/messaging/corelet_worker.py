"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Corelet worker with queue-based health monitoring

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import pickle
import logging
import importlib
import threading
import queue
import platform
import psutil
import signal
import time
from typing import Any, Optional
from datetime import datetime
from multiprocessing import connection

import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
HANDLER_CACHE_CLEANUP_INTERVAL = 300.0  # 5 minutes
MAX_CACHED_HANDLERS = 50  # Limit handler cache size

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CoreletWorker:
    """
    Corelet worker with queue-based health monitoring architecture.
    """

    __slots__ = (
        "_worker_id",
        "_task_pipe_b",
        "_result_pipe_b",
        "_health_pipe_b",
        "_handlers",
        "_logger",
        "_running",
        "_alive_queue",
        "_health_thread",
        "_ping_without_alive_count",
        "_shutdown_requested",
        "_last_handler_cleanup",
        "_signal_handlers_setup",
    )

    def __init__(
        self,
        worker_id: str,
        task_pipe_b: connection.Connection,
        result_pipe_b: connection.Connection,
        health_pipe_b: connection.Connection,
    ):
        """
        Initialize corelet worker with queue-based health monitoring.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        task_pipe_b : multiprocessing.Connection
            Pipe for receiving business events.
        result_pipe_b : multiprocessing.Connection
            Pipe for sending business results.
        health_pipe_b : multiprocessing.Connection
            Pipe for bidirectional health/control communication.
        """
        self._worker_id = worker_id
        self._task_pipe_b = task_pipe_b
        self._result_pipe_b = result_pipe_b
        self._health_pipe_b = health_pipe_b
        self._handlers = {}
        self._logger = logging.getLogger(f"{__name__}.{worker_id}")
        self._running = True
        self._alive_queue = queue.Queue()
        self._health_thread = None
        self._ping_without_alive_count = 0
        self._shutdown_requested = False
        self._last_handler_cleanup = time.time()
        self._signal_handlers_setup = False

    def run(self) -> None:
        """
        Main worker loop for business event processing.
        """
        self._logger.info("Worker %s started (PID: %d)", self._worker_id, os.getpid())

        try:
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Set low priority for this worker process
            self._set_process_priority()

            # Start health monitoring thread
            self._health_thread = threading.Thread(
                target=self._health_loop, name=f"Health-{self._worker_id}", daemon=True
            )
            self._health_thread.start()

            # Main business event loop
            while self._running and not self._shutdown_requested:
                try:
                    # Periodic handler cache cleanup
                    self._cleanup_handler_cache_if_needed()

                    # Wait for business events with timeout
                    if self._task_pipe_b.poll(timeout=5.0):
                        pickled_data = self._task_pipe_b.recv()
                        event = pickle.loads(pickled_data)

                        if event.type == "corelet.shutdown":
                            self._shutdown_requested = True
                            self._running = False
                            break

                        # Process business event
                        if hasattr(event, "_handler_path"):
                            result = self._process_event(event, event._handler_path)
                            self._send_result(result)
                        else:
                            self._send_error("Event missing handler_path")
                    else:
                        # 5 second timeout - send alive signal
                        self.send_alive_event("waiting_for_tasks")

                except Exception as e:
                    self._logger.error("Error in business loop: %s", str(e))
                    self._send_error(str(e))

        except KeyboardInterrupt:
            self._logger.info("Worker interrupted")
        except SystemExit:
            self._logger.info("Worker received system exit")
        finally:
            self._cleanup()
            self._logger.info("Worker %s stopped", self._worker_id)

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.
        """
        if self._signal_handlers_setup:
            return

        try:

            def signal_handler(signum, frame):
                self._logger.info("Worker %s received signal %d", self._worker_id, signum)
                self._shutdown_requested = True
                self._running = False

            # Register handlers for graceful shutdown
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

            # Windows doesn't have SIGHUP
            if hasattr(signal, "SIGHUP"):
                signal.signal(signal.SIGHUP, signal_handler)

            self._signal_handlers_setup = True
            self._logger.debug("Signal handlers setup for worker %s", self._worker_id)

        except Exception as e:
            self._logger.warning("Failed to setup signal handlers: %s", str(e))

    def _set_process_priority(self) -> None:
        """
        Set low priority for this worker process.
        """
        try:
            if platform.system() == "Windows":
                proc = psutil.Process(os.getpid())
                proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            else:
                # Linux/macOS
                os.setpriority(os.PRIO_PROCESS, os.getpid(), 10)
            self._logger.debug("Set low priority for worker %s", self._worker_id)
        except Exception as e:
            self._logger.warning(
                "Failed to set priority for worker %s: %s", self._worker_id, str(e)
            )

    def _cleanup_handler_cache_if_needed(self) -> None:
        """
        Cleanup handler cache periodically to prevent memory leaks.
        """
        current_time = time.time()

        # Check if cleanup is needed
        if (
            current_time - self._last_handler_cleanup < HANDLER_CACHE_CLEANUP_INTERVAL
            and len(self._handlers) < MAX_CACHED_HANDLERS
        ):
            return

        try:
            # If cache is too large, clear oldest handlers
            if len(self._handlers) >= MAX_CACHED_HANDLERS:
                # Simple approach: clear half the cache
                handlers_to_remove = len(self._handlers) // 2
                handler_items = list(self._handlers.items())

                for i in range(handlers_to_remove):
                    handler_path, handler = handler_items[i]
                    try:
                        # Cleanup handler resources if it has cleanup method
                        if hasattr(handler, "cleanup"):
                            handler.cleanup()
                    except Exception as e:
                        self._logger.warning(
                            "Error cleaning up handler %s: %s", handler_path, str(e)
                        )

                    del self._handlers[handler_path]

                self._logger.info(
                    "Cleaned up %d handlers from cache (was %d, now %d)",
                    handlers_to_remove,
                    len(handler_items),
                    len(self._handlers),
                )

            self._last_handler_cleanup = current_time

        except Exception as e:
            self._logger.error("Error during handler cache cleanup: %s", str(e))

    def send_alive_event(self, computation_status: Optional[str] = None) -> None:
        """
        Send alive signal during long computations.
        Called by business logic to signal it's still working.

        Parameters
        ----------
        computation_status : str, optional
            Optional status message about current computation progress.
        """
        try:
            alive_message = {
                "timestamp": datetime.now(),
                "worker_id": self._worker_id,
                "computation_status": computation_status,
            }
            self._alive_queue.put(alive_message)
            self._logger.debug("Added alive message to queue with status: %s", computation_status)
        except Exception as e:
            self._logger.error("Failed to send alive event: %s", str(e))

    def _health_loop(self) -> None:
        """
        Health monitoring loop for control events.
        """
        while self._running and not self._shutdown_requested:
            try:
                # Poll with timeout to avoid deadlock on shutdown
                if self._health_pipe_b.poll(timeout=5.0):
                    pickled_data = self._health_pipe_b.recv()
                    health_event = pickle.loads(pickled_data)

                    if health_event.type == "corelet.shutdown":
                        self._logger.info("Health thread received shutdown signal")
                        self._send_shutdown_complete()
                        self._shutdown_requested = True
                        self._running = False
                        break
                    elif health_event.type == "corelet.ping":
                        self._handle_ping()

            except Exception as e:
                self._logger.error("Error in health loop: %s", str(e))
                break

    def _handle_ping(self) -> None:
        """
        Handle ping request from pool with graceful first-time logic.
        """
        try:
            # Drain alive queue and get latest message
            latest_alive = None
            while not self._alive_queue.empty():
                try:
                    latest_alive = self._alive_queue.get_nowait()
                except queue.Empty:
                    break

            if latest_alive:
                # Got alive message - send pong with alive timestamp
                self._send_pong(latest_alive["timestamp"], latest_alive)
                self._ping_without_alive_count = 0  # Reset counter
                self._logger.debug("Sent pong with alive timestamp: %s", latest_alive["timestamp"])
            else:
                # No alive messages in queue
                self._ping_without_alive_count += 1

                if self._ping_without_alive_count == 1:
                    # First ping without alive - be graceful
                    self._send_pong(datetime.now())
                    self._logger.warning("First ping without alive message - being graceful")
                else:
                    # Second ping without alive - worker is dead
                    self._send_died()
                    self._logger.error("Second ping without alive message - worker declared dead")

        except Exception as e:
            self._logger.error("Error handling ping: %s", str(e))

    def _send_pong(self, alive_timestamp=None, alive_data=None) -> None:
        """
        Send pong response via health pipe.

        Parameters
        ----------
        alive_timestamp : datetime, optional
            Timestamp from latest alive message.
        alive_data : dict, optional
            Data from latest alive message.
        """
        try:
            pong_data = {"worker_id": self._worker_id}

            if alive_timestamp:
                pong_data["last_alive_timestamp"] = alive_timestamp

            if alive_data and "computation_status" in alive_data:
                pong_data["computation_status"] = alive_data["computation_status"]

            pong_event = basefunctions.Event("corelet.pong", data=pong_data)
            pickled_pong = pickle.dumps(pong_event)
            self._health_pipe_b.send(pickled_pong)

        except Exception as e:
            self._logger.error("Failed to send pong: %s", str(e))

    def _send_died(self) -> None:
        """
        Send died signal via health pipe.
        """
        try:
            died_event = basefunctions.Event("corelet.died", data={"worker_id": self._worker_id})
            pickled_died = pickle.dumps(died_event)
            self._health_pipe_b.send(pickled_died)

        except Exception as e:
            self._logger.error("Failed to send died signal: %s", str(e))

    def _send_shutdown_complete(self) -> None:
        """
        Send shutdown completion via health pipe.
        """
        try:
            shutdown_event = basefunctions.Event(
                "corelet.shutdown_complete", data={"worker_id": self._worker_id}
            )
            pickled_shutdown = pickle.dumps(shutdown_event)
            self._health_pipe_b.send(pickled_shutdown)

        except Exception as e:
            self._logger.error("Failed to send shutdown complete: %s", str(e))

    def _process_event(self, event: basefunctions.Event, handler_path: str) -> Any:
        """
        Process business event with handler.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler_path : str
            Handler import path.

        Returns
        -------
        Any
            Result from handler execution.
        """
        try:
            # Get or load handler
            handler = self._get_or_load_handler(handler_path)

            # Create corelet context with worker reference
            context = basefunctions.EventContext(
                execution_mode="corelet",
                process_id=os.getpid(),
                timestamp=event.timestamp,
                worker=self,
            )

            # Execute handler
            return handler.handle(event, context)

        except Exception as e:
            self._logger.error("Failed to process event: %s", str(e))
            raise

    def _get_or_load_handler(self, handler_path: str) -> basefunctions.EventHandler:
        """
        Get cached handler or load dynamically with cache management.

        Parameters
        ----------
        handler_path : str
            Import path for handler class.

        Returns
        -------
        basefunctions.EventHandler
            Handler instance.
        """
        if handler_path in self._handlers:
            return self._handlers[handler_path]

        try:
            # Check cache size before adding new handler
            if len(self._handlers) >= MAX_CACHED_HANDLERS:
                self._logger.warning(
                    "Handler cache full (%d handlers), forcing cleanup", len(self._handlers)
                )
                self._cleanup_handler_cache_if_needed()

            module_name, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            handler_class = getattr(module, class_name)
            handler = handler_class()

            if not isinstance(handler, basefunctions.EventHandler):
                raise TypeError(f"Handler {handler_path} is not an EventHandler instance")

            self._handlers[handler_path] = handler
            self._logger.debug(
                "Loaded handler: %s (cache size: %d)", handler_path, len(self._handlers)
            )
            return handler

        except Exception as e:
            self._logger.error("Failed to load handler %s: %s", handler_path, str(e))
            raise

    def _send_result(self, result: Any) -> None:
        """
        Send business result via result pipe.

        Parameters
        ----------
        result : Any
            Result to send.
        """
        try:
            result_event = basefunctions.Event("corelet.result", data={"result": result})
            pickled_result = pickle.dumps(result_event)
            self._result_pipe_b.send(pickled_result)
        except Exception as e:
            self._logger.error("Failed to send result: %s", str(e))

    def _send_error(self, error_message: str) -> None:
        """
        Send business error via result pipe.

        Parameters
        ----------
        error_message : str
            Error message.
        """
        try:
            error_event = basefunctions.Event("corelet.error", data={"error": error_message})
            pickled_error = pickle.dumps(error_event)
            self._result_pipe_b.send(pickled_error)
        except Exception as e:
            self._logger.error("Failed to send error: %s", str(e))

    def _cleanup(self) -> None:
        """
        Cleanup worker resources with detailed logging.
        """
        self._logger.info("Starting cleanup for worker %s", self._worker_id)
        cleanup_errors = []

        try:
            # Stop running flag
            self._running = False
            self._shutdown_requested = True

            # Cleanup handlers with their resources
            handlers_cleaned = 0
            for handler_path, handler in list(self._handlers.items()):
                try:
                    # Call cleanup method if handler supports it
                    if hasattr(handler, "cleanup"):
                        handler.cleanup()
                    handlers_cleaned += 1
                except Exception as e:
                    cleanup_errors.append(f"Handler {handler_path} cleanup: {str(e)}")

            self._handlers.clear()
            self._logger.info("Cleaned up %d handlers", handlers_cleaned)

            # Clear alive queue
            try:
                queue_size = 0
                while not self._alive_queue.empty():
                    try:
                        self._alive_queue.get_nowait()
                        queue_size += 1
                    except queue.Empty:
                        break
                if queue_size > 0:
                    self._logger.debug("Cleared %d items from alive queue", queue_size)
            except Exception as e:
                cleanup_errors.append(f"Alive queue cleanup: {str(e)}")

            # Close pipes with individual error handling
            pipes = [
                ("task_pipe_b", self._task_pipe_b),
                ("result_pipe_b", self._result_pipe_b),
                ("health_pipe_b", self._health_pipe_b),
            ]

            for pipe_name, pipe_obj in pipes:
                try:
                    if pipe_obj and not pipe_obj.closed:
                        pipe_obj.close()
                        self._logger.debug("Closed %s", pipe_name)
                except Exception as e:
                    cleanup_errors.append(f"{pipe_name} close: {str(e)}")

            # Log cleanup results
            if cleanup_errors:
                self._logger.warning(
                    "Cleanup completed with %d errors: %s", len(cleanup_errors), cleanup_errors
                )
            else:
                self._logger.info("Cleanup completed successfully")

        except Exception as e:
            self._logger.error("Critical error during cleanup: %s", str(e))


def worker_main(
    worker_id: str,
    task_pipe_b: connection.Connection,
    result_pipe_b: connection.Connection,
    health_pipe_b: connection.Connection,
) -> None:
    """
    Main entry point for worker process with queue-based health monitoring.

    Parameters
    ----------
    worker_id : str
        Unique worker identifier.
    task_pipe_b : multiprocessing.Connection
        Pipe for receiving business events.
    result_pipe_b : multiprocessing.Connection
        Pipe for sending business results.
    health_pipe_b : multiprocessing.Connection
        Pipe for bidirectional health communication.
    """
    try:
        worker = CoreletWorker(worker_id, task_pipe_b, result_pipe_b, health_pipe_b)
        worker.run()
    except Exception as e:
        logging.error("Worker process failed: %s", str(e))
        sys.exit(1)
    finally:
        # Ensure clean exit
        try:
            logging.info("Worker process %s exiting", worker_id)
        except:
            pass
        sys.exit(0)
