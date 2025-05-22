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
from typing import Any, Optional

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

    __slots__ = ("type", "data", "source", "timestamp")

    def __init__(self, type: str, data: Any = None, source: Optional[Any] = None):
        """
        Initialize a new event.

        Parameters
        ----------
        type : str
            The type of the event, used for routing to the appropriate handlers.
        data : Any, optional
            The data payload of the event.
        source : Any, optional
            The source/originator of the event.
        """
        self.type = type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        """
        Get a string representation of the event.

        Returns
        -------
        str
            A string representation of the event.
        """
        return f"Event(type={self.type}, time={self.timestamp}, source={self.source})"

    @classmethod
    def shutdown(cls) -> "Event":
        """
        Create shutdown control event for corelet workers.

        Returns
        -------
        Event
            Shutdown event.
        """
        return cls("corelet.shutdown")

    @classmethod
    def register_handler(cls, handler_path: str) -> "Event":
        """
        Create handler registration event for corelet workers.

        Parameters
        ----------
        handler_path : str
            Import path for handler class.

        Returns
        -------
        Event
            Handler registration event.
        """
        return cls("corelet.register_handler", data={"handler_path": handler_path})

    @classmethod
    def result(cls, result_data: Any) -> "Event":
        """
        Create result event for returning handler results.

        Parameters
        ----------
        result_data : Any
            Result from handler execution.

        Returns
        -------
        Event
            Result event.
        """
        return cls("corelet.result", data={"result": result_data})

    @classmethod
    def error(cls, error_message: str) -> "Event":
        """
        Create error event for reporting handler errors.

        Parameters
        ----------
        error_message : str
            Error description.

        Returns
        -------
        Event
            Error event.
        """
        return cls("corelet.error", data={"error": error_message})
