"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Corelet worker with 3-pipe architecture for clean separation
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import pickle
import logging
import threading
import importlib
from typing import Any, Optional
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
    Corelet worker with 3-pipe architecture for business and health separation.
    """

    __slots__ = (
        "_worker_id",
        "_task_pipe",
        "_result_pipe",
        "_health_pipe",
        "_handlers",
        "_logger",
        "_running",
        "_health_thread",
    )

    def __init__(
        self,
        worker_id: str,
        task_pipe: connection.Connection,
        result_pipe: connection.Connection,
        health_pipe: connection.Connection,
    ):
        """
        Initialize corelet worker with 3-pipe architecture.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        task_pipe : multiprocessing.Connection
            Pipe for receiving business events.
        result_pipe : multiprocessing.Connection
            Pipe for sending business results.
        health_pipe : multiprocessing.Connection
            Pipe for bidirectional health/control communication.
        """
        self._worker_id = worker_id
        self._task_pipe = task_pipe
        self._result_pipe = result_pipe
        self._health_pipe = health_pipe
        self._handlers = {}
        self._logger = logging.getLogger(f"{__name__}.{worker_id}")
        self._running = True
        self._health_thread = None

    def run(self) -> None:
        """
        Main worker loop with separate business and health processing.
        """
        self._logger.info("Worker %s started (PID: %d)", self._worker_id, os.getpid())

        try:
            # Start health monitoring thread
            self._health_thread = threading.Thread(
                target=self._health_loop, name=f"Health-{self._worker_id}", daemon=True
            )
            self._health_thread.start()

            # Main business event loop
            while self._running:
                try:
                    # Wait for business events
                    pickled_data = self._task_pipe.recv()
                    event = pickle.loads(pickled_data)

                    # Process business event
                    if hasattr(event, "_handler_path"):
                        result = self._process_event(event, event._handler_path)
                        self._send_result(result)
                    else:
                        self._send_error("Event missing handler_path")

                except Exception as e:
                    self._logger.error("Error in business loop: %s", str(e))
                    self._send_error(str(e))

        except KeyboardInterrupt:
            self._logger.info("Worker interrupted")
        finally:
            self._cleanup()
            self._logger.info("Worker %s stopped", self._worker_id)

    def _health_loop(self) -> None:
        """
        Health monitoring loop for control events.
        """
        while self._running:
            try:
                # Check for health events with timeout
                if self._health_pipe.poll(timeout=1.0):
                    pickled_data = self._health_pipe.recv()
                    event = pickle.loads(pickled_data)

                    if event.type == "corelet.shutdown":
                        self._logger.info("Received shutdown signal")
                        self._send_shutdown_complete()
                        self._running = False
                        break
                    elif event.type == "corelet.ping":
                        self._send_pong()

            except Exception as e:
                self._logger.error("Error in health loop: %s", str(e))

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
        Get cached handler or load dynamically.

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
            module_name, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            handler_class = getattr(module, class_name)
            handler = handler_class()

            if not isinstance(handler, basefunctions.EventHandler):
                raise TypeError(f"Handler {handler_path} is not an EventHandler instance")

            self._handlers[handler_path] = handler
            self._logger.debug("Loaded handler: %s", handler_path)
            return handler

        except Exception as e:
            self._logger.error("Failed to load handler %s: %s", handler_path, str(e))
            raise

    def report_alive(self) -> None:
        """
        Send user-initiated alive signal during long computations.
        Called by handlers via context.report_alive().
        """
        self._send_alive()

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
            self._result_pipe.send(pickled_result)
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
            self._result_pipe.send(pickled_error)
        except Exception as e:
            self._logger.error("Failed to send error: %s", str(e))

    def _send_pong(self) -> None:
        """
        Send pong response via health pipe.
        """
        try:
            pong_event = basefunctions.Event("corelet.pong", data={"worker_id": self._worker_id})
            pickled_pong = pickle.dumps(pong_event)
            self._health_pipe.send(pickled_pong)
        except Exception as e:
            self._logger.error("Failed to send pong: %s", str(e))

    def _send_shutdown_complete(self) -> None:
        """
        Send shutdown completion via health pipe.
        """
        try:
            shutdown_event = basefunctions.Event(
                "corelet.shutdown_complete", data={"worker_id": self._worker_id}
            )
            pickled_shutdown = pickle.dumps(shutdown_event)
            self._health_pipe.send(pickled_shutdown)
        except Exception as e:
            self._logger.error("Failed to send shutdown complete: %s", str(e))

    def _send_alive(self) -> None:
        """
        Send alive signal via health pipe.
        """
        try:
            alive_event = basefunctions.Event("corelet.alive", data={"worker_id": self._worker_id})

            pickled_alive = pickle.dumps(alive_event)
            print("health event alive sent - before")
            self._health_pipe.send(pickled_alive)
            print("health event alive sent")
        except Exception as e:
            self._logger.error("Failed to send alive: %s", str(e))

    def _cleanup(self) -> None:
        """
        Cleanup worker resources.
        """
        try:
            if self._task_pipe:
                self._task_pipe.close()
            if self._result_pipe:
                self._result_pipe.close()
            if self._health_pipe:
                self._health_pipe.close()
            self._handlers.clear()
        except Exception as e:
            self._logger.error("Error during cleanup: %s", str(e))


def worker_main(
    worker_id: str,
    task_pipe: connection.Connection,
    result_pipe: connection.Connection,
    health_pipe: connection.Connection,
) -> None:
    """
    Main entry point for worker process with 3-pipe architecture.

    Parameters
    ----------
    worker_id : str
        Unique worker identifier.
    task_pipe : multiprocessing.Connection
        Pipe for receiving business events.
    result_pipe : multiprocessing.Connection
        Pipe for sending business results.
    health_pipe : multiprocessing.Connection
        Pipe for bidirectional health communication.
    """
    try:
        worker = CoreletWorker(worker_id, task_pipe, result_pipe, health_pipe)
        worker.run()
    except Exception as e:
        logging.error("Worker process failed: %s", str(e))
        sys.exit(1)
