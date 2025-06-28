"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Event handler interface for the messaging system with execution modes

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Tuple, Any
from datetime import datetime
import subprocess
import pickle

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


class EventContext:
    """
    Context data for event processing across different execution modes.
    """

    __slots__ = (
        "thread_local_data",
        "thread_id",
        "process_id",
        "timestamp",
        "event_data",
        "worker",
    )

    def __init__(self, **kwargs):
        """
        Initialize event context.

        Parameters
        ----------
        **kwargs
            Context data for event processing.
        """
        # Thread-specific context
        self.thread_local_data = kwargs.get("thread_local_data")
        self.thread_id = kwargs.get("thread_id")

        # Corelet-specific context
        self.process_id = kwargs.get("process_id")
        self.timestamp = kwargs.get("timestamp", datetime.now())
        self.event_data = kwargs.get("event_data")

        # Worker reference for corelet mode
        self.worker = kwargs.get("worker")


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

    def __init__(self, event_id: str, success: bool, data: Any = None, exception: ExceptionResult = None):
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
        cls, event_id: str, success: bool, data: Any = None, exception: ExceptionResult = None
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
        context: EventContext,
        *args,
        **kwargs,
    ) -> EventResult:
        """
        Handle an event.

        This method is called by the EventBus when an event of the type
        this handler is registered for is published.

        Parameters
        ----------
        event : Event
            The event to handle.
        context : EventContext
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
    Default handler for CMD mode events.
    Executes subprocess commands based on event data.
    """

    def handle(self, event, context, *args, **kwargs) -> EventResult:
        """
        Execute subprocess command from event data.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing executable, args, and cwd in event_data
        context : EventContext
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

            if not executable:
                return EventResult.business_result(event.event_id, False, "Missing executable in event data")

            # Build command
            cmd = [executable] + args

            # Execute subprocess
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

            # Build return dict
            cmd_result = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

            # Shell convention: 0 = success, != 0 = error
            if result.returncode == 0:
                return EventResult.business_result(event.event_id, True, cmd_result)
            else:
                return EventResult.business_result(event.event_id, False, cmd_result)

        except subprocess.TimeoutExpired as e:
            return EventResult.exception_result(event.event_id, e)
        except FileNotFoundError as e:
            return EventResult.exception_result(event.event_id, e)
        except Exception as e:
            return EventResult.exception_result(event.event_id, e)


class CoreletForwardingHandler(EventHandler):
    """
    Handler for forwarding events to corelet processes via pipe communication.
    Manages corelet lifecycle, handler registration, and communication.
    """

    def handle(self, event, context, *args, **kwargs) -> EventResult:
        """
        Forward event to corelet process via pipe communication.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process in corelet mode
        context : EventContext
            Execution context containing thread_local_data for corelet management

        Returns
        -------
        EventResult
            Result from corelet execution or error result on failure
        """
        try:
            # Get thread-local corelet handle from context
            if not hasattr(context.thread_local_data, "corelet_worker"):
                corelet_handle = self._get_corelet_worker(context)
            else:
                corelet_handle = context.thread_local_data.corelet_worker

            # Check if handler is registered in corelet
            if not self._is_handler_registered_in_corelet(event.event_type, context.thread_local_data):
                # Get handler for registration info (not for execution)
                handler = basefunctions.EventFactory.create_handler(event.event_type)
                self._register_handler_in_corelet(event.event_type, handler, corelet_handle, context.thread_local_data)

            # Send event to corelet via pipe
            pickled_event = pickle.dumps(event)
            corelet_handle.input_pipe.send(pickled_event)

            # Receive result from corelet (blocking - TimerThread handles timeout)
            pickled_result = corelet_handle.output_pipe.recv()
            event_result = pickle.loads(pickled_result)

            # Corelet sends EventResult directly
            return event_result

        except Exception as e:
            # Cleanup defective corelet on any error
            self._cleanup_corelet(context)
            return EventResult.exception_result(event.event_id, e)

    def _get_corelet_worker(self, context):
        """
        Get or create a corelet worker for the current thread.

        Parameters
        ----------
        context : EventContext
            Event context containing thread_local_data

        Returns
        -------
        CoreletHandle
            New corelet handle for process communication
        """
        # Create pipes
        input_pipe_a, input_pipe_b = basefunctions.Pipe()
        output_pipe_a, output_pipe_b = basefunctions.Pipe()

        # Start corelet process
        process = basefunctions.Process(
            target=basefunctions.worker_main,
            args=(f"corelet_{basefunctions.threading.current_thread().ident}", input_pipe_b, output_pipe_b),
            daemon=True,
        )
        process.start()

        # Create wrapper handle
        corelet_handle = basefunctions.CoreletHandle(process, input_pipe_a, output_pipe_a)
        context.thread_local_data.corelet_worker = corelet_handle

        return corelet_handle

    def _is_handler_registered_in_corelet(self, event_type, thread_local_data):
        """
        Check if handler is already registered in the corelet process.

        Parameters
        ----------
        event_type : str
            Event type to check registration for
        thread_local_data : threading.local
            Thread-local data for tracking registrations

        Returns
        -------
        bool
            True if handler is registered, False otherwise
        """
        if not hasattr(thread_local_data, "registered_handlers"):
            thread_local_data.registered_handlers = set()

        return event_type in thread_local_data.registered_handlers

    def _register_handler_in_corelet(self, event_type, handler, corelet_handle, thread_local_data):
        """
        Register event handler in corelet process.

        Parameters
        ----------
        event_type : str
            Event type to register
        handler : basefunctions.EventHandler
            Handler instance for getting class information
        corelet_handle : CoreletHandle
            Corelet process handle
        thread_local_data : threading.local
            Thread-local data for tracking registrations
        """
        # Get handler class information
        handler_class = handler.__class__
        module_path = handler_class.__module__
        class_name = handler_class.__name__

        # Create registration event
        register_event = basefunctions.Event(
            "_register_handler",
            event_data={"event_type": event_type, "module_path": module_path, "class_name": class_name},
        )

        # Send registration to corelet
        pickled_event = pickle.dumps(register_event)
        corelet_handle.input_pipe.send(pickled_event)

        # Receive confirmation with timeout
        if corelet_handle.output_pipe.poll(basefunctions.DEFAULT_TIMEOUT):
            pickled_result = corelet_handle.output_pipe.recv()
            event_result = pickle.loads(pickled_result)
        else:
            raise TimeoutError(f"Corelet registration timeout for {event_type}")

        # Track registration
        if not hasattr(thread_local_data, "registered_handlers"):
            thread_local_data.registered_handlers = set()
        thread_local_data.registered_handlers.add(event_type)

    def _cleanup_corelet(self, context):
        """
        Cleanup defective corelet process and remove from thread-local data.

        Parameters
        ----------
        context : EventContext
            Event context containing thread_local_data with corelet worker
        """
        if hasattr(context.thread_local_data, "corelet_worker"):
            try:
                context.thread_local_data.corelet_worker.input_pipe.close()
                context.thread_local_data.corelet_worker.output_pipe.close()
                context.thread_local_data.corelet_worker.process.kill()
            except:
                pass  # Already dead

            # Remove from thread-local data for fresh corelet on next event
            delattr(context.thread_local_data, "corelet_worker")

            # Clear registered handlers as new corelet needs re-registration
            if hasattr(context.thread_local_data, "registered_handlers"):
                delattr(context.thread_local_data, "registered_handlers")
