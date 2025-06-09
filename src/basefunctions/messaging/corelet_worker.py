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
from typing import Any, Tuple
from multiprocessing import connection
import signal
import time
import os
import sys
import pickle
import logging
import platform
import psutil
import importlib
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
        "_input_pipe",
        "_output_pipe",
        "_handlers",
        "_logger",
        "_running",
        "_last_handler_cleanup",
        "_signal_handlers_setup",
        "_registered_handlers",
    )

    def __init__(
        self,
        worker_id: str,
        input_pipe: connection.Connection,
        output_pipe: connection.Connection,
    ):
        """
        Initialize corelet worker for thread integration.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        input_pipe : multiprocessing.Connection
            Pipe for receiving business events.
        output_pipe : multiprocessing.Connection
            Pipe for sending business results.
        """
        self._worker_id = worker_id
        self._input_pipe = input_pipe
        self._output_pipe = output_pipe
        self._handlers = {}
        self._logger = logging.getLogger(f"{__name__}.{worker_id}")
        self._running = True
        self._last_handler_cleanup = time.time()
        self._signal_handlers_setup = False
        self._registered_handlers = set()

    def run(self) -> None:
        """
        Main worker loop for business event processing.
        """
        self._logger.debug("Worker %s started (PID: %d)", self._worker_id, os.getpid())

        try:
            self._setup_signal_handlers()
            self._set_process_priority()

            while self._running:
                try:
                    if self._input_pipe.poll(timeout=5.0):
                        pickled_data = self._input_pipe.recv()
                        event = pickle.loads(pickled_data)

                        # Process event using event type instead of handler path
                        result = self._process_event(event, event.type)
                        self._send_result(event, result)

                except Exception as e:
                    if str(e).strip():
                        self._logger.error("Error in business loop: %s", str(e))
                        # Send error result for unknown event
                        dummy_event = basefunctions.Event("unknown")
                        self._send_result(dummy_event, (False, str(e)))
                    else:
                        self._logger.debug("Business loop interrupted by signal")

        except KeyboardInterrupt:
            self._logger.debug("Worker interrupted")
        except SystemExit:
            self._logger.debug("Worker received system exit")
        finally:
            self._logger.debug("Worker %s stopped", self._worker_id)

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.
        """
        if self._signal_handlers_setup:
            return

        try:

            def signal_handler(signum, frame):
                self._logger.debug(
                    "Worker %s received signal %d, shutting down",
                    self._worker_id,
                    signum,
                )
                self._running = False

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

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
                proc.nice(1)
            else:
                os.setpriority(os.PRIO_PROCESS, os.getpid(), 10)
            self._logger.debug("Set low priority for worker %s", self._worker_id)
        except Exception as e:
            self._logger.warning("Failed to set priority for worker %s: %s", self._worker_id, str(e))

    def _process_event(self, event: basefunctions.Event, event_type: str) -> Tuple[bool, Any]:
        """
        Process business event with handler.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        event_type : str
            Event type for handler lookup.

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result from handler execution.
        """
        try:
            # Handle special register events first
            if event.type == "__register_handler":
                return self._register_handler_class(event.data)

            # Normal event processing
            handler = self._get_handler(event_type)

            context = basefunctions.EventContext(
                execution_mode=basefunctions.EXECUTION_MODE_CORELET,
                process_id=os.getpid(),
                timestamp=event.timestamp,
                worker=self,
            )

            return handler.handle(event, context)

        except Exception as e:
            self._logger.error("Failed to process event: %s", str(e))
            raise

    def _register_handler_class(self, data: dict) -> Tuple[bool, str]:
        """
        Register handler class in corelet EventFactory via importlib.

        Parameters
        ----------
        data : dict
            Registration data containing module_path, class_name and event_type.

        Returns
        -------
        Tuple[bool, str]
            Success flag and confirmation message.
        """
        try:

            module_path = data["module_path"]
            class_name = data["class_name"]
            event_type = data["event_type"]

            # Import module and get handler class
            module = importlib.import_module(module_path)
            handler_class = getattr(module, class_name)

            # Validate handler class
            if not issubclass(handler_class, basefunctions.EventHandler):
                raise TypeError(f"Class {class_name} is not a subclass of EventHandler")

            # Register in local EventFactory
            basefunctions.EventFactory.register_event_type(event_type, handler_class)

            self._logger.debug("Registered handler %s.%s for event type %s", module_path, class_name, event_type)

            return (True, f"Handler {class_name} registered successfully")

        except ImportError as e:
            error_msg = f"Failed to import module {data.get('module_path', 'unknown')}: {str(e)}"
            self._logger.error(error_msg)
            return (False, error_msg)
        except AttributeError as e:
            error_msg = f"Class {data.get('class_name', 'unknown')} not found in module: {str(e)}"
            self._logger.error(error_msg)
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Handler registration failed: {str(e)}"
            self._logger.error(error_msg)
            return (False, error_msg)

    def _get_handler(self, event_type: str) -> basefunctions.EventHandler:
        """
        Get cached handler or create via factory.

        Parameters
        ----------
        event_type : str
            Event type for handler lookup.

        Returns
        -------
        basefunctions.EventHandler
            Handler instance.
        """
        if event_type in self._handlers:
            return self._handlers[event_type]

        try:
            # Use EventFactory instead of importlib
            handler = basefunctions.EventFactory.create_handler(event_type)

            if not isinstance(handler, basefunctions.EventHandler):
                raise TypeError(f"Handler for {event_type} is not an EventHandler instance")

            self._handlers[event_type] = handler
            self._logger.debug("Created handler for %s (cache size: %d)", event_type, len(self._handlers))
            return handler

        except Exception as e:
            self._logger.error("Failed to create handler for %s: %s", event_type, str(e))
            raise

    def _send_result(self, event: basefunctions.Event, result: Tuple[bool, Any]) -> None:
        """
        Send business result via output pipe.

        Parameters
        ----------
        event : basefunctions.Event
            Original event for ID tracking.
        result : Tuple[bool, Any]
            Result tuple from handler execution (success, data).
        """
        try:
            success, data = result

            if success:
                # Success - send result event with original event ID
                result_event = basefunctions.Event.result(event.id, success, data)
            else:
                # Failure - send error event with original event ID
                error_event = basefunctions.Event.error(event.id, str(data), exception=data)
                result_event = error_event

            pickled_result = pickle.dumps(result_event)
            self._output_pipe.send(pickled_result)

        except BrokenPipeError:
            pass
        except Exception as e:
            self._logger.error("Failed to send result: %s", str(e))


def worker_main(
    worker_id: str,
    input_pipe: connection.Connection,
    output_pipe: connection.Connection,
) -> None:
    """
    Main entry point for worker process.

    Parameters
    ----------
    worker_id : str
        Unique worker identifier.
    input_pipe : multiprocessing.Connection
        Pipe for receiving business events.
    output_pipe : multiprocessing.Connection
        Pipe for sending business results.
    """
    try:
        worker = CoreletWorker(worker_id, input_pipe, output_pipe)
        worker.run()
    except Exception as e:
        logging.error("Worker process failed: %s", str(e))
        sys.exit(1)
    finally:
        try:
            logging.debug("Worker process %s exiting", worker_id)
        except:
            pass
        sys.exit(0)
