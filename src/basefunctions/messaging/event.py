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


class Event:
    """
    Base class for all events in the messaging system.

    Events are objects that carry information about something that has
    happened in the system. They are used to communicate between
    components in a decoupled way.
    """

    __slots__ = (
        "type",
        "data",
        "source",
        "target",
        "timeout",
        "max_retries",
        "timestamp",
        "_handler_path",
    )

    def __init__(
        self,
        type: str,
        source: Optional[Any] = None,
        target: Any = None,
        data: Any = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        _handler_path: Optional[str] = None,
    ):
        """
        Initialize a new event.

        Parameters
        ----------
        type : str
            The type of the event, used for routing to the appropriate handlers.
        source : Any, optional
            The source/originator of the event.
        target : Any, optional
            The target destination for event routing in the messaging system.
        data : Any, optional
            The data payload of the event.
        timeout : int, optional
            Timeout in seconds for event processing.
        max_retries : int, optional
            Maximum number of retry attempts for failed event processing.
        _handler_path : str, optional
            Internal handler path for corelet serialization and routing.
        """
        self.type = type
        self.source = source
        self.target = target
        self.data = data
        self.timeout = timeout
        self.max_retries = max_retries
        self.timestamp = datetime.now()
        self._handler_path = _handler_path

    def __str__(self) -> str:
        """
        Get a string representation of the event.

        Returns
        -------
        str
            A string representation of the event.
        """
        return (
            f"Event(type={self.type}, source={self.source}, target={self.target}, "
            f"timeout={self.timeout}, max_retries={self.max_retries}, time={self.timestamp}, "
            f"_handler_path={self._handler_path})"
        )

    @classmethod
    def register_handler(cls, event_type: str, handler: "EventHandler") -> "Event":
        """
        Create register handler event for corelet synchronization.

        Parameters
        ----------
        event_type : str
            Event type identifier for handler registration.
        handler : EventHandler
            Handler instance to register in corelet processes.

        Returns
        -------
        Event
            Register event containing handler registration data.
        """
        handler_class_path = f"{handler.__class__.__module__}.{handler.__class__.__name__}"
        return cls("__register_handler", data={"event_type": event_type, "handler_class_path": handler_class_path})

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
    def result(cls, result_success: bool, result_data: Any) -> "Event":
        """
        Create result event for returning handler results.

        Parameters
        ----------
        result_success : bool
            Success flag indicating whether handler execution was successful.
        result_data : Any
            Result data from handler execution.

        Returns
        -------
        Event
            Result event containing handler execution results.
        """
        return cls("result", data={"result_success": result_success, "result_data": result_data})

    @classmethod
    def error(cls, error_message: str, exception: Optional[Exception] = None) -> "Event":
        """
        Create error event for reporting handler errors.

        Parameters
        ----------
        error_message : str
            Error description message.
        exception : Exception, optional
            Exception instance that caused the error.

        Returns
        -------
        Event
            Error event containing error information.
        """
        return cls("error", data={"error": error_message, "exception": type(exception).__name__})
