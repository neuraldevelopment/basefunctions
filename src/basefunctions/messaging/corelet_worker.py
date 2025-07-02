"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Corelet worker with queue-based health monitoring

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from multiprocessing.connection import Connection
import signal
import time
import os
import sys
import pickle
import logging
import platform
import psutil
import importlib
import threading
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
HANDLER_CACHE_CLEANUP_INTERVAL = 300.0  # 5 minutes
MAX_CACHED_HANDLERS = 50  # Limit handler cache size

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

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
        "_redirector",
    )

    def __init__(
        self,
        worker_id: str,
        input_pipe: Connection,
        output_pipe: Connection,
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
        result = None

        try:
            self._setup_signal_handlers()
            self._set_process_priority()

            # Create context once for all events with thread_local_data for handler cache
            context = basefunctions.EventContext(
                process_id=os.getpid(),
                timestamp=time.time(),
                worker=self,
                thread_local_data=threading.local(),
            )
            while self._running:
                try:
                    if self._input_pipe.poll(timeout=5.0):
                        pickled_data = self._input_pipe.recv()
                        event = pickle.loads(pickled_data)

                        print(event)

                        # Check for shutdown event
                        if event.event_type == basefunctions.INTERNAL_SHUTDOWN_EVENT:
                            shutdown_result = basefunctions.EventResult.business_result(
                                event.event_id, True, "Shutdown complete"
                            )
                            self._send_result(event, shutdown_result)
                            self._running = False
                            break

                        result = self._process_event(event, context)
                        self._send_result(event, result)
                except Exception as e:
                    import traceback

                    error_details = traceback.format_exc()
                    self._logger.error("Error in business loop: %s", error_details)
                    # Send exception result for processing error
                    result = basefunctions.EventResult.exception_result("unknown", e)

        except KeyboardInterrupt:
            self._logger.debug("Worker interrupted")
        except SystemExit:
            self._logger.debug("Worker received system exit")
        finally:
            if not isinstance(result, basefunctions.EventResult):
                result = basefunctions.EventResult.exception_result(
                    "unknown", Exception("Worker terminated without processing event")
                )
            self._send_result(event, result)

    def _process_event(
        self,
        event: basefunctions.Event,
        context: "basefunctions.EventContext",
    ) -> "basefunctions.EventResult":
        """
        Process business event with handler.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        context : basefunctions.EventContext
            Context with thread_local_data for handler cache.

        Returns
        -------
        basefunctions.EventResult
            Result from handler execution.
        """
        try:
            # Auto-register handler if not known and corelet_meta available
            if not self._is_handler_registered(event.event_type) and event.corelet_meta:
                self._register_from_meta(event.corelet_meta)

            # Normal event processing
            handler = self._get_handler(event.event_type, context)

            # Pass context as required parameter
            return handler.handle(event, context)

        except Exception as e:
            self._logger.error("Failed to process event: %s", str(e))
            raise

    def _is_handler_registered(self, event_type: str) -> bool:
        """
        Check if handler is registered for event type.

        Parameters
        ----------
        event_type : str
            Event type to check

        Returns
        -------
        bool
            True if handler is registered
        """
        return event_type in self._handlers

    def _register_from_meta(self, corelet_meta: dict) -> None:
        """
        Register handler from corelet metadata.

        Parameters
        ----------
        corelet_meta : dict
            Handler metadata with module_path, class_name, event_type
        """
        try:
            module_path = corelet_meta["module_path"]
            class_name = corelet_meta["class_name"]
            event_type = corelet_meta["event_type"]

            # Import module and get handler class
            module = importlib.import_module(module_path)
            handler_class = getattr(module, class_name)

            # Validate handler class
            if not issubclass(handler_class, basefunctions.EventHandler):
                raise TypeError(f"Class {class_name} is not a subclass of EventHandler")

            # Register in local EventFactory
            basefunctions.EventFactory.register_event_type(event_type, handler_class)
            self._handlers[event_type] = handler_class
            self._logger.debug("Registered handler %s.%s for event type %s", module_path, class_name, event_type)

        except Exception as e:
            error_msg = f"Handler registration failed: {str(e)}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _send_result(self, event: basefunctions.Event, result: basefunctions.EventResult) -> None:
        """
        Send business result via output pipe.

        Parameters
        ----------
        event : basefunctions.Event
            Original event for ID tracking.
        result : basefunctions.EventResult
            Result from handler execution with success flag, data and optional exception.
        """
        try:
            # Ensure result has correct event ID
            result.event_id = event.event_id

            # Send result directly
            pickled_result = pickle.dumps(result)
            self._output_pipe.send(pickled_result)

        except BrokenPipeError:
            pass
        except Exception as e:
            self._logger.error("Failed to send result: %s", str(e))

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

    def _get_handler(
        self,
        event_type: str,
        context: "basefunctions.EventContext",
    ) -> "basefunctions.EventHandler":
        """
        Get cached handler or create via factory.

        Parameters
        ----------
        event_type : str
            Event type for handler lookup.
        context : basefunctions.EventContext
            Context with thread_local_data for handler cache.

        Returns
        -------
        basefunctions.EventHandler
            Handler instance.

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


def worker_main(
    worker_id: str,
    input_pipe: Connection,
    output_pipe: Connection,
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
    # Parameter validation
    if not worker_id or not input_pipe or not output_pipe:
        logging.error("Invalid parameters for worker %s", worker_id)
        sys.exit(1)

    try:
        worker = CoreletWorker(worker_id, input_pipe, output_pipe)
        worker.run()
    except Exception as e:
        logging.error("Worker process failed: %s", str(e))
        sys.exit(1)
    finally:
        try:
            logging.debug("Worker process %s exiting", worker_id)
        except Exception:  # Specific exception type
            pass
        # Remove redundant sys.exit(0) - let process exit naturally
