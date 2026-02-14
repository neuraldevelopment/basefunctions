"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Corelet worker with queue-based health monitoring

  Log:
  v1.1 : Improved exception handling with specific exception types
  v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import importlib
import logging
import os
import pickle
import platform
import signal
import sys
import threading
import time
import traceback
from datetime import datetime
from multiprocessing.connection import Connection

import psutil

import basefunctions
from basefunctions.utils.logging import setup_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
HANDLER_CACHE_CLEANUP_INTERVAL = 300.0  # 5 minutes
MAX_CACHED_HANDLERS = 50  # Limit handler cache size
IDLE_TIMEOUT = 600.0  # 10 minutes - terminate worker after inactivity

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


class CoreletWorker:
    """
    Isolated worker process for executing event handlers in separate process space.

    CoreletWorker implements a process-based event execution model that provides
    isolation, fault tolerance, and parallel processing capabilities. Each worker
    runs in its own process with dedicated handler cache and event processing loop.

    The worker receives pickled events via input pipe, dynamically loads and
    executes the appropriate handler, and sends results back via output pipe.
    Handlers can be auto-registered via corelet_meta or pre-registered in the
    worker's EventFactory.

    Attributes
    ----------
    _worker_id : str
        Unique identifier for this worker instance
    _input_pipe : multiprocessing.Connection
        Pipe for receiving pickled events from EventBus
    _output_pipe : multiprocessing.Connection
        Pipe for sending pickled results back to EventBus
    _handlers : dict
        Registry of handler classes for dynamic loading
    _running : bool
        Worker loop control flag
    _registered_handlers : set
        Set of registered event types for tracking

    Notes
    -----
    **Isolation Benefits:**
    - Memory isolation (no GIL contention)
    - Crash isolation (worker crash doesn't affect main process)
    - Resource isolation (separate file descriptors, memory space)

    **Handler Registration:**
    - Auto-registration: Handler loaded via event.corelet_meta
    - Pre-registration: Handler registered in worker's EventFactory
    - Dynamic loading: Handler class imported on-demand

    **Process Lifecycle:**
    - Created on first corelet event for a thread
    - Runs until shutdown event received
    - WARNING: Currently no automatic cleanup (see process leak issue)

    **Signal Handling:**
    - SIGTERM: Graceful shutdown
    - SIGINT: Immediate shutdown
    - Process priority lowered to avoid CPU contention

    Examples
    --------
    Worker is typically created by CoreletForwardingHandler:

    >>> # Internal usage - normally created by EventBus
    >>> worker = CoreletWorker("worker-1", input_pipe, output_pipe)
    >>> worker.run()  # Blocks until shutdown

    Direct invocation via worker_main:

    >>> # Entry point for multiprocessing.Process
    >>> worker_main("worker-1", input_pipe, output_pipe)

    See Also
    --------
    CoreletForwardingHandler : Creates and manages CoreletWorker processes
    EventBus : Routes events to corelet workers
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
    ) -> None:
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
        Main worker loop for event processing.

        Runs indefinitely, receiving events via input pipe, processing them,
        and sending results via output pipe. Loop exits on shutdown event
        or fatal error.
        """
        self._logger.debug("Worker %s started (PID: %d)", self._worker_id, os.getpid())
        event = None
        result = None

        try:
            # Setup signal handlers for graceful shutdown (SIGTERM, SIGINT)
            self._setup_signal_handlers()
            # Lower process priority to avoid CPU contention with main process
            self._set_process_priority()

            # Create context once for all events with thread_local_data for handler cache
            # This context is reused across all events in this worker to enable caching
            context = basefunctions.EventContext(
                process_id=str(os.getpid()),
                timestamp=datetime.now(),
                worker=self,
                thread_local_data=threading.local(),
            )

            # Track last activity for idle timeout
            last_activity_time = time.time()

            # Main event processing loop
            while self._running:
                try:
                    # Poll for events with 5 second timeout (allows signal checking)
                    if self._input_pipe.poll(timeout=5.0):
                        pickled_data = self._input_pipe.recv()
                        event = pickle.loads(pickled_data)

                        # Update activity timestamp
                        last_activity_time = time.time()

                        # Check for shutdown event - graceful termination
                        if event.event_type == basefunctions.INTERNAL_SHUTDOWN_EVENT:
                            shutdown_result = basefunctions.EventResult.business_result(
                                event.event_id, True, "Shutdown complete"
                            )
                            self._send_result(event, shutdown_result)
                            self._running = False
                            break

                        # Process event and send result
                        result = self._process_event(event, context)
                        self._send_result(event, result)
                    else:
                        # No event - check idle timeout
                        idle_time = time.time() - last_activity_time
                        if idle_time > IDLE_TIMEOUT:
                            self._logger.info(
                                "Worker %s idle for %.1f seconds - shutting down",
                                self._worker_id,
                                idle_time,
                            )
                            self._running = False
                            break
                except pickle.PickleError as e:
                    self._logger.error("Failed to unpickle event: %s", str(e))
                    # Cannot send result - event object is corrupted
                    result = None
                except (BrokenPipeError, EOFError, OSError) as e:
                    self._logger.error("Pipe communication error: %s", str(e))
                    # Pipe broken - worker should terminate
                    self._running = False
                    break
                except Exception as e:
                    # Catch-all for unexpected errors with full traceback
                    error_details = traceback.format_exc()
                    self._logger.error("Unexpected error in business loop: %s", error_details)
                    # Send exception result if we have an event
                    if event is not None:
                        result = basefunctions.EventResult.exception_result(event.event_id, e)
                    else:
                        result = None

        except KeyboardInterrupt:
            self._logger.debug("Worker interrupted")
        except SystemExit:
            self._logger.debug("Worker received system exit")
        finally:
            if event is not None:
                if not isinstance(result, basefunctions.EventResult):
                    result = basefunctions.EventResult.exception_result(
                        "unknown",
                        Exception("Worker terminated without processing event"),
                    )
                self._send_result(event, result)

    def _process_event(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
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
            # This enables dynamic handler loading when first corelet event arrives
            if not self._is_handler_registered(event.event_type) and event.corelet_meta:
                self._register_from_meta(event.corelet_meta)

            # Get handler from cache or create via factory
            # Handlers are cached per-thread to avoid repeated instantiation
            handler = self._get_handler(event.event_type, context)

            # Execute handler with context for thread-local state access
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

    def _register_from_meta(self, corelet_meta: dict[str, str]) -> None:
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
            basefunctions.EventFactory().register_event_type(event_type, handler_class)
            self._handlers[event_type] = handler_class
            self._logger.debug(
                "Registered handler %s.%s for event type %s",
                module_path,
                class_name,
                event_type,
            )

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

            def signal_handler(signum, _frame):
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
        context: basefunctions.EventContext,
    ) -> basefunctions.EventHandler:
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
            handler = basefunctions.EventFactory().create_handler(event_type)

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
