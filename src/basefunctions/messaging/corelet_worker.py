"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Worker process for corelet event processing
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import threading
import importlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from multiprocessing import connection

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

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CoreletWorker:
    """
    Worker process for handling corelet events in isolation.
    """

    __slots__ = (
        "_worker_id",
        "_task_pipe",
        "_result_pipe",
        "_handlers",
        "_logger",
        "_running",
        "_stats",
    )

    def __init__(
        self, worker_id: str, task_pipe: connection.Connection, result_pipe: connection.Connection
    ):
        """
        Initialize corelet worker.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        task_pipe : multiprocessing.Connection
            Pipe for receiving tasks.
        result_pipe : multiprocessing.Connection
            Pipe for sending results.
        """
        self._worker_id = worker_id
        self._task_pipe = task_pipe
        self._result_pipe = result_pipe
        self._handlers: Dict[str, basefunctions.EventHandler] = {}
        self._logger = logging.getLogger(f"{__name__}.{worker_id}")
        self._running = True
        self._stats = {
            "events_processed": 0,
            "errors_count": 0,
            "handlers_loaded": 0,
            "start_time": datetime.now(),
        }

    def run(self) -> None:
        """
        Main worker loop for processing events.
        """
        self._logger.info("Worker %s started (PID: %d)", self._worker_id, os.getpid())

        try:
            while self._running:
                try:
                    # Receive event from main process
                    data = self._receive_data()

                    if data is None:
                        continue

                    # Handle control events
                    if isinstance(data, basefunctions.Event):
                        if data.type == "corelet.shutdown":
                            self._logger.info("Received shutdown signal")
                            break
                        elif data.type == "corelet.register_handler":
                            self._handle_register_handler(data)
                            continue

                    # Handle business event tuple
                    if isinstance(data, tuple) and len(data) == 2:
                        event, handler_path = data
                        result = self._process_business_event(event, handler_path)
                        self._send_result(result, getattr(event, "_task_id", None))
                    else:
                        self._logger.error("Received invalid data format: %s", type(data))

                except Exception as e:
                    self._logger.error("Error in worker loop: %s", str(e))
                    self._stats["errors_count"] += 1
                    self._send_error(str(e), None)

        except KeyboardInterrupt:
            self._logger.info("Worker interrupted")
        finally:
            self._cleanup()
            self._logger.info("Worker %s stopped", self._worker_id)

    def _receive_data(self) -> Optional[Any]:
        """
        Receive data from task pipe.

        Returns
        -------
        Optional[Any]
            Received data or None if no data available.
        """
        try:
            if self._task_pipe.poll(timeout=1.0):
                return self._task_pipe.recv()
            return None
        except Exception as e:
            self._logger.error("Failed to receive data: %s", str(e))
            return None

    def _process_business_event(self, event: basefunctions.Event, handler_path: str) -> Any:
        """
        Process business event with appropriate handler.

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

            # Create execution context
            context = basefunctions.EventContext(
                execution_mode="corelet",
                process_id=os.getpid(),
                thread_id=threading.get_ident(),
                timestamp=datetime.now(),
            )

            # Execute handler
            result = handler.handle(event, context)
            self._stats["events_processed"] += 1

            return result

        except Exception as e:
            self._logger.error("Failed to process event: %s", str(e))
            raise

    def _get_or_load_handler(self, handler_path: str) -> basefunctions.EventHandler:
        """
        Get handler from cache or load dynamically.

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

        # Load handler dynamically
        try:
            module_name, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            handler_class = getattr(module, class_name)

            # Instantiate handler
            handler = handler_class()

            # Verify it's an EventHandler
            if not isinstance(handler, basefunctions.EventHandler):
                raise TypeError(f"Handler {handler_path} is not an EventHandler instance")

            # Cache handler
            self._handlers[handler_path] = handler
            self._stats["handlers_loaded"] += 1

            self._logger.debug("Loaded handler: %s", handler_path)
            return handler

        except Exception as e:
            self._logger.error("Failed to load handler %s: %s", handler_path, str(e))
            raise

    def _handle_register_handler(self, event: basefunctions.Event) -> None:
        """
        Handle handler registration event.

        Parameters
        ----------
        event : basefunctions.Event
            Registration event.
        """
        try:
            handler_path = event.data.get("handler_path")
            if not handler_path:
                raise ValueError("No handler_path in registration event")

            # Pre-load handler
            self._get_or_load_handler(handler_path)

            # Send confirmation
            self._send_result(f"Handler registered: {handler_path}", None)

        except Exception as e:
            self._logger.error("Failed to register handler: %s", str(e))
            self._send_error(f"Handler registration failed: {str(e)}", None)

    def _send_result(self, result: Any, task_id: Optional[str]) -> None:
        """
        Send result back to main process.

        Parameters
        ----------
        result : Any
            Result to send.
        task_id : str, optional
            Task identifier.
        """
        try:
            result_event = basefunctions.Event.result(result)
            if task_id:
                result_event._task_id = task_id
            self._result_pipe.send(result_event)
        except Exception as e:
            self._logger.error("Failed to send result: %s", str(e))

    def _send_error(self, error_message: str, task_id: Optional[str]) -> None:
        """
        Send error back to main process.

        Parameters
        ----------
        error_message : str
            Error message to send.
        task_id : str, optional
            Task identifier.
        """
        try:
            error_event = basefunctions.Event.error(error_message)
            if task_id:
                error_event._task_id = task_id
            self._result_pipe.send(error_event)
        except Exception as e:
            self._logger.error("Failed to send error: %s", str(e))

    def _cleanup(self) -> None:
        """
        Cleanup worker resources.
        """
        try:
            # Close pipes
            if self._task_pipe:
                self._task_pipe.close()
            if self._result_pipe:
                self._result_pipe.close()

            # Clear handlers
            self._handlers.clear()

            self._logger.debug("Worker cleanup completed")

        except Exception as e:
            self._logger.error("Error during cleanup: %s", str(e))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.

        Returns
        -------
        Dict[str, Any]
            Worker statistics.
        """
        runtime = datetime.now() - self._stats["start_time"]

        return {
            "worker_id": self._worker_id,
            "events_processed": self._stats["events_processed"],
            "errors_count": self._stats["errors_count"],
            "handlers_loaded": self._stats["handlers_loaded"],
            "runtime_seconds": runtime.total_seconds(),
            "process_id": os.getpid(),
        }


def worker_main(
    worker_id: str, task_pipe: connection.Connection, result_pipe: connection.Connection
):
    """
    Main entry point for worker process.

    Parameters
    ----------
    worker_id : str
        Unique worker identifier.
    task_pipe : multiprocessing.Connection
        Pipe for receiving tasks.
    result_pipe : multiprocessing.Connection
        Pipe for sending results.
    """
    try:
        worker = CoreletWorker(worker_id, task_pipe, result_pipe)
        worker.run()
    except Exception as e:
        logging.error("Worker process failed: %s", str(e))
        sys.exit(1)
