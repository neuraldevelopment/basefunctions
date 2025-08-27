"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Event handler interface for the messaging system with execution modes

  Log:
  v1.0 : Initial implementation
  v1.1 : Added file logging support for DefaultCmdHandler
  v1.2 : Centralized subprocess execution with timeout support
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any
from abc import ABC, abstractmethod
from multiprocessing import Process
from multiprocessing.connection import Connection
import subprocess
import pickle
import threading
import multiprocessing
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
basefunctions.setup_logger(__name__)
logger = basefunctions.get_logger(__name__)

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ExceptionResult:
    """
    Container for exception information in unified return format.
    """

    __slots__ = ("exception_type", "exception_message", "exception_details")

    def __init__(self, exception: Exception):
        """
        Initialize exception result.

        Parameters
        ----------
        exception : Exception
            The exception to wrap
        """
        self.exception_type = type(exception).__name__
        self.exception_message = str(exception)
        self.exception_details = {
            "module": getattr(exception, "__module__", None),
            "traceback": None,  # Optional: add traceback if needed
        }

    def __str__(self) -> str:
        return f"{self.exception_type}: {self.exception_message}"


class EventResult:
    """
    Unified result container with separate fields for different result types.
    """

    __slots__ = ("event_id", "success", "data", "exception")

    def __init__(
        self,
        event_id: str,
        success: bool,
        data: Any = None,
        exception: ExceptionResult = None,
    ):
        """
        Initialize event result.

        Parameters
        ----------
        event_id : str
            Event ID for tracking and correlation
        success : bool
            True for successful operations, False for errors/exceptions
        data : Any, optional
            Result data for success=True or business error data for success=False
        exception : ExceptionResult, optional
            Exception information when technical error occurred
        """
        self.event_id = event_id
        self.success = success
        self.data = data
        self.exception = exception

    @classmethod
    def business_result(
        cls,
        event_id: str,
        success: bool,
        data: Any = None,
        exception: ExceptionResult = None,
    ) -> "EventResult":
        """
        Create business result (success or error).

        Parameters
        ----------
        event_id : str
            Event ID for tracking
        success : bool
            Success flag
        data : Any, optional
            Business data or error data
        exception : ExceptionResult, optional
            Exception information

        Returns
        -------
        EventResult
            Business result instance
        """
        return cls(event_id=event_id, success=success, data=data, exception=exception)

    @classmethod
    def exception_result(cls, event_id: str, exception: Exception) -> "EventResult":
        """
        Create exception result.

        Parameters
        ----------
        event_id : str
            Event ID for tracking
        exception : Exception
            The exception that occurred

        Returns
        -------
        EventResult
            Exception result instance
        """
        return cls(event_id=event_id, success=False, exception=ExceptionResult(exception))

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        data_preview = str(self.data)[:50] + "..." if self.data else "None"
        exception_info = str(self.exception) if self.exception else "None"
        return f"EventResult({self.event_id}, {status}, data={data_preview}, exception={exception_info})"


class EventHandler(ABC):
    """
    Interface for event handlers in the messaging system.

    Event handlers are responsible for processing events. They are registered
    with an EventBus to receive and handle specific types of events.
    """

    @abstractmethod
    def handle(
        self,
        event: "basefunctions.Event",
        context: "basefunctions.EventContext",
    ) -> EventResult:
        """
        Handle an event.

        This method is called by the EventBus when an event of the type
        this handler is registered for is published.

        Parameters
        ----------
        event : Event
            The event to handle.
        context : basefunctions.EventContext
            Context data for event processing. Contains thread_local_data
            for thread mode, and process info for corelet mode.

        Returns
        -------
        EventResult
            Unified result containing success flag, data, and optional exception info.
        """
        return EventResult.exception_result(
            event.event_id, NotImplementedError("Subclasses must implement handle method")
        )


class DefaultCmdHandler(EventHandler):
    """
    Default handler for CMD mode events with timeout support.
    Executes subprocess commands based on event data.
    """

    def handle(
        self,
        event,
        context: "basefunctions.EventContext",
    ) -> EventResult:
        """
        Execute subprocess command from event data with timeout support.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing executable, args, cwd, and optional stdout_file/stderr_file in event_data
        context : basefunctions.EventContext
            Execution context with cmd mode information

        Returns
        -------
        EventResult
            Success flag and execution result dictionary
        """
        try:
            # Extract subprocess parameters from event.event_data
            executable = event.event_data.get("executable")
            args = event.event_data.get("args", [])
            cwd = event.event_data.get("cwd")
            stdout_file = event.event_data.get("stdout_file")
            stderr_file = event.event_data.get("stderr_file")

            if not executable:
                return EventResult.business_result(event.event_id, False, "Missing executable in event data")

            # Build command
            cmd = [executable] + args

            # Prepare output parameters
            stdout_handle = None
            stderr_handle = None
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
            capture_output = False

            try:
                # Open file handles if specified
                if stdout_file:
                    stdout_handle = open(stdout_file, "w")
                    stdout = stdout_handle

                if stderr_file:
                    stderr_handle = open(stderr_file, "w")
                    stderr = stderr_handle
                elif stdout_file:
                    # Use stdout file for stderr if only stdout specified
                    stderr = stdout_handle

                if not stdout_file and not stderr_file:
                    capture_output = True

                # Single subprocess execution
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    timeout=event.timeout,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    capture_output=capture_output,
                )

                # Build result dictionary
                if stdout_file or stderr_file:
                    cmd_result = {
                        "stdout": stdout_file if stdout_file else "",
                        "stderr": stderr_file if stderr_file else "",
                        "returncode": result.returncode,
                    }
                else:
                    cmd_result = {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    }

            finally:
                # Close file handles
                if stdout_handle:
                    stdout_handle.close()
                if stderr_handle and stderr_handle != stdout_handle:
                    stderr_handle.close()

            # Shell convention: 0 = success, != 0 = error
            if result.returncode == 0:
                return EventResult.business_result(event.event_id, True, cmd_result)
            else:
                return EventResult.business_result(event.event_id, False, cmd_result)

        except subprocess.TimeoutExpired as e:
            logger.warning(f"Subprocess timeout after {event.timeout}s: {executable}")
            return EventResult.exception_result(event.event_id, e)
        except FileNotFoundError as e:
            logger.error(f"Executable not found: {executable}")
            return EventResult.exception_result(event.event_id, e)
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            return EventResult.exception_result(event.event_id, e)


class CoreletHandle:
    """
    Wrapper for corelet process communication.

    This class provides a simple interface for EventBus to communicate
    with corelet worker processes via pipes.
    """

    __slots__ = ("process", "input_pipe", "output_pipe")

    def __init__(
        self,
        process: Process,
        input_pipe: Connection,
        output_pipe: Connection,
    ):
        """
        Initialize corelet handle.

        Parameters
        ----------
        process : multiprocessing.Process
            Corelet worker process.
        input_pipe : multiprocessing.Connection
            Pipe for sending events to corelet.
        output_pipe : multiprocessing.Connection
            Pipe for receiving results from corelet.
        """
        self.process = process
        self.input_pipe = input_pipe
        self.output_pipe = output_pipe


class CoreletForwardingHandler(EventHandler):
    """
    Handler for forwarding events to corelet processes via pipe communication.
    Manages corelet lifecycle and communication.
    """

    def handle(self, event, context) -> EventResult:
        """
        Forward event to corelet process for execution.

        Parameters
        ----------
        event : basefunctions.Event
            Event to forward to corelet
        context : basefunctions.EventContext
            Context with thread_local_data for corelet management

        Returns
        -------
        EventResult
            Result from corelet execution
        """
        try:
            # Ensure corelet is running
            corelet_handle = self._get_corelet(context)

            # Send event to corelet - corelet handles registration automatically
            pickled_event = pickle.dumps(event)
            corelet_handle.input_pipe.send(pickled_event)

            # Wait for result with timeout
            if corelet_handle.output_pipe.poll(timeout=event.timeout):
                pickled_result = corelet_handle.output_pipe.recv()
                return pickle.loads(pickled_result)
            else:
                raise TimeoutError(f"No response from corelet within {event.timeout} seconds")

        except TimeoutError as e:
            # For shutdown events: Force-kill corelet on timeout
            if event.event_type == basefunctions.INTERNAL_SHUTDOWN_EVENT:
                self._terminate_corelet(context)
            raise e
        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)

    def _get_corelet(self, context: basefunctions.EventContext) -> CoreletHandle:
        """
        Get corelet worker is running for current thread.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing thread_local_data

        Returns
        -------
        CoreletHandle
            Corelet handle for process communication
        """
        # Check if corelet already exists for this thread
        if hasattr(context.thread_local_data, "corelet_handle"):
            return context.thread_local_data.corelet_handle

        # Create new corelet worker
        corelet_handle = self._create_corelet_worker()
        context.thread_local_data.corelet_handle = corelet_handle
        return corelet_handle

    def _create_corelet_worker(self) -> CoreletHandle:
        """
        Create a new corelet worker process.

        Returns
        -------
        CoreletHandle
            New corelet handle for process communication
        """
        # Create pipes for bidirectional communication
        input_pipe_a, input_pipe_b = multiprocessing.Pipe()
        output_pipe_a, output_pipe_b = multiprocessing.Pipe()

        # Start corelet process
        process = Process(
            target=basefunctions.worker_main,
            args=(f"corelet_{threading.current_thread().ident}", input_pipe_b, output_pipe_b),
            daemon=True,
        )
        process.start()

        # Return handle for communication
        return CoreletHandle(process, input_pipe_a, output_pipe_a)

    def _terminate_corelet(self, context: basefunctions.EventContext) -> None:
        """
        terminate corelet process and cleanup resources.

        Parameters
        ----------
        context : basefunctions.EventContext
            Context containing corelet_handle to kill
        """
        if hasattr(context.thread_local_data, "corelet_handle"):
            corelet_handle = context.thread_local_data.corelet_handle
            corelet_handle.process.terminate()
            corelet_handle.input_pipe.close()
            corelet_handle.output_pipe.close()
            delattr(context.thread_local_data, "corelet_handle")
