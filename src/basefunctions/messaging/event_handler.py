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
