"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Event classes for the messaging system with corelet factory methods

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from datetime import datetime
from typing import Any, Optional, Type
import uuid
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
EXECUTION_MODE_SYNC = "sync"
EXECUTION_MODE_THREAD = "thread"
EXECUTION_MODE_CORELET = "corelet"
EXECUTION_MODE_CMD = "cmd"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class Event:
    """
    Base class for all events in the messaging system.

    Events are objects that carry information about something that has
    happened in the system. They are used to communicate between
    components in a decoupled way.
    """

    __slots__ = (
        "event_id",
        "event_type",
        "event_data",
        "event_source",
        "event_target",
        "max_retries",
        "timeout",
        "timestamp",
        "_corelet_handler_path",
        "event_exec_mode",
        "event_name",
    )

    def __init__(
        self,
        event_type: str,
        event_id: Optional[str] = None,
        event_exec_mode: str = EXECUTION_MODE_THREAD,
        event_name: Optional[str] = None,
        event_source: Optional[Any] = None,
        event_target: Any = None,
        event_data: Any = None,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
        _corelet_handler_path: Optional[str] = None,
    ):
        """
        Initialize a new event.

        Parameters
        ----------
        event_type : str
            The type of the event, used for routing to the appropriate handlers.
        event_id : str, optional
            Unique identifier for event tracking. Auto-generated if None.
        event_exec_mode : str, optional
            Execution mode for event processing. Defaults to thread mode.
        event_name : str, optional
            Human-readable name for the event.
        event_source : Any, optional
            The source/originator of the event.
        event_target : Any, optional
            The target destination for event routing in the messaging system.
        event_data : Any, optional
            The data payload of the event.
        max_retries : int, optional
            Maximum number of retry attempts for failed event processing.
        timeout : int, optional
            Timeout in seconds for event processing.
        _corelet_handler_path : str, optional
            Internal handler path for corelet serialization and routing.
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.event_exec_mode = event_exec_mode
        self.event_name = event_name
        self.event_source = event_source
        self.event_target = event_target
        self.event_data = event_data
        self.timeout = timeout
        self.max_retries = max_retries
        self.timestamp = datetime.now()
        self._corelet_handler_path = _corelet_handler_path

    def __str__(self) -> str:
        """
        Get a string representation of the event.

        Returns
        -------
        str
            A string representation of the event.
        """
        return (
            f"Event(id={self.event_id}, type={self.event_type}, name={self.event_name}, "
            f"exec_type={self.event_exec_mode}, source={self.event_source}, target={self.event_target}, "
            f"timeout={self.timeout}, max_retries={self.max_retries}, time={self.timestamp}, "
            f"_corelet_handler_path={self._corelet_handler_path})"
        )

    @classmethod
    def register_handler(cls, event_type: str, module_path: str, class_name: str) -> "Event":
        """
        Create register handler event for corelet synchronization.

        Parameters
        ----------
        event_type : str
            Event type identifier for handler registration.
        module_path : str
            Full module path where handler class is defined.
        class_name : str
            Handler class name.

        Returns
        -------
        Event
            Register event containing handler registration data.
        """
        return cls(
            "__register_handler",
            event_data={"event_type": event_type, "module_path": module_path, "class_name": class_name},
        )

    @classmethod
    def shutdown(cls) -> "Event":
        """
        Create shutdown control event.

        Returns
        -------
        Event
            Shutdown event for system termination.
        """
        return cls("shutdown")

    @classmethod
    def cleanup(cls) -> "Event":
        """
        Create cleanup control event.

        Returns
        -------
        Event
            Cleanup event for system termination.
        """
        return cls("cleanup")

    @classmethod
    def result(cls, event_id: str, result_success: bool, result_data: Any) -> "Event":
        """
        Create result event for returning handler results.

        Parameters
        ----------
        event_id : str
            ID of the original event this result belongs to.
        result_success : bool
            Whether the handler execution was successful.
        result_data : Any
            The result data from handler execution.

        Returns
        -------
        Event
            Result event containing handler execution results.
        """
        return cls("__result", event_id=event_id, event_data={"success": result_success, "data": result_data})

    @classmethod
    def error(cls, event_id: str, error_message: str, exception: Optional[Exception] = None) -> "Event":
        """
        Create error event for reporting handler errors.

        Parameters
        ----------
        event_id : str
            ID of the original event this error belongs to.
        error_message : str
            Error description message.
        exception : Exception, optional
            Exception instance that caused the error.

        Returns
        -------
        Event
            Error event containing error information.
        """
        return cls(
            "__error",
            event_id=event_id,
            event_data={"error": error_message, "exception": str(exception) if exception else None},
        )
