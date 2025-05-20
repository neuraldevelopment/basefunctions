"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Base event classes for the messaging system

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC
from datetime import datetime
from typing import Any, Dict, Optional

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

    __slots__ = ("_type", "_timestamp", "_source", "_processed", "_data")

    def __init__(
        self, event_type: str, source: Optional[Any] = None, data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new event.

        Parameters
        ----------
        event_type : str
            The type of the event, used for routing to the appropriate handlers.
        source : Any, optional
            The source/originator of the event.
        data : Dict[str, Any], optional
            Additional data associated with the event.
        """
        self._type = event_type
        self._timestamp = datetime.now()
        self._source = source
        self._processed = False
        self._data = data or {}

    @property
    def type(self) -> str:
        """
        Get the event type.

        Returns
        -------
        str
            The event type.
        """
        return self._type

    @property
    def timestamp(self) -> datetime:
        """
        Get the event timestamp.

        Returns
        -------
        datetime
            The time when the event was created.
        """
        return self._timestamp

    @property
    def source(self) -> Any:
        """
        Get the event source.

        Returns
        -------
        Any
            The source/originator of the event.
        """
        return self._source

    @property
    def processed(self) -> bool:
        """
        Check if the event has been processed.

        Returns
        -------
        bool
            True if the event has been processed, False otherwise.
        """
        return self._processed

    def mark_processed(self) -> None:
        """
        Mark the event as processed.
        """
        self._processed = True

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get a data item associated with the event.

        Parameters
        ----------
        key : str
            The key of the data item.
        default : Any, optional
            The default value to return if the key does not exist.

        Returns
        -------
        Any
            The data item value or the default value.
        """
        return self._data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """
        Set a data item for the event.

        Parameters
        ----------
        key : str
            The key of the data item.
        value : Any
            The value to associate with the key.
        """
        self._data[key] = value

    def get_all_data(self) -> Dict[str, Any]:
        """
        Get all data associated with the event.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing all event data.
        """
        return self._data.copy()

    def __str__(self) -> str:
        """
        Get a string representation of the event.

        Returns
        -------
        str
            A string representation of the event.
        """
        return f"Event(type={self._type}, time={self._timestamp}, source={self._source}, processed={self._processed})"


class TypedEvent(Event):
    """
    Base class for creating strongly typed events.

    Subclasses should define a class variable 'event_type' to specify
    the type of the event.
    """

    event_type = "base.typed_event"

    def __init__(self, source: Optional[Any] = None, data: Optional[Dict[str, Any]] = None):
        """
        Initialize a new typed event.

        Parameters
        ----------
        source : Any, optional
            The source/originator of the event.
        data : Dict[str, Any], optional
            Additional data associated with the event.
        """
        super().__init__(self.__class__.event_type, source, data)
