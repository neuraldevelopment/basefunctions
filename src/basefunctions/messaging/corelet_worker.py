"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

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
from pandas.core import base
import psutil
import importlib
import basefunctions
import threading

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
        "_redirector",
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

        log_file_name = f"./corelet_{worker_id}.log"
        self._redirector = basefunctions.OutputRedirector(basefunctions.FileTarget(log_file_name, mode="w"))
        self._redirector.start()  # <-- sys.stdout wird hier global umgeleitet
        print("finished init")

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
                        result = self._process_event(event, context)
                    else:
                        print("Poll timeout - no data available")

                except Exception as e:
                    print(f"Error type: {type(e).__name__}")
                    print(f"Error message: '{str(e)}'")
                    print(f"Error repr: {repr(e)}")
                    # Rest...
                    self._logger.error("Error in business loop: %s", str(e))
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
            # Handle special register events first - use new Event structure
            if event.event_type == basefunctions.INTERNAL_REGISTER_HANDLER_EVENT:
                return self._register_handler_class(event)

            # Normal event processing - use event.event_type from Event structure
            handler = self._get_handler(event.event_type, context)

            # Pass context as required parameter
            return handler.handle(event, context)

        except Exception as e:
            self._logger.error("Failed to process event: %s", str(e))
            raise

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

    def _register_handler_class(self, event: basefunctions.Event) -> basefunctions.EventResult:
        """
        Register handler class in corelet EventFactory via importlib.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing registration data with module_path, class_name and event_type.

        Returns
        -------
        EventResult
            Success or failure result with registration details
        """
        try:
            # Validate required event data
            required_keys = ["module_path", "class_name", "event_type"]
            if not all(key in event.event_data for key in required_keys):
                missing_keys = [key for key in required_keys if key not in event.event_data]
                error_msg = f"Missing required registration data: {missing_keys}"
                self._logger.error(error_msg)
                return basefunctions.EventResult.business_result(event.event_id, False, error_msg)

            module_path = event.event_data["module_path"]
            class_name = event.event_data["class_name"]
            event_type = event.event_data["event_type"]

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

            return basefunctions.EventResult.business_result(
                event.event_id, True, f"Handler {class_name} registered successfully"
            )

        except ImportError as e:
            error_msg = f"Failed to import module {event.event_data.get('module_path', 'unknown')}: {str(e)}"
            self._logger.error(error_msg)
            return basefunctions.EventResult.business_result(event.event_id, False, error_msg)
        except AttributeError as e:
            error_msg = f"Class {event.event_data.get('class_name', 'unknown')} not found in module: {str(e)}"
            self._logger.error(error_msg)
            return basefunctions.EventResult.business_result(event.event_id, False, error_msg)
        except Exception as e:
            error_msg = f"Handler registration failed: {str(e)}"
            self._logger.error(error_msg)
            return basefunctions.EventResult.business_result(event.event_id, False, error_msg)

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
