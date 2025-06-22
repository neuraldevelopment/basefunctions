"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Factory for creating event handlers

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Type
import threading
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


@basefunctions.singleton
class EventFactory:
    """
    Factory for creating event handlers. Implements the Singleton pattern.
    Thread-safe implementation for concurrent access.
    """

    _lock = threading.RLock()
    _handler_registry: Dict[str, Type["basefunctions.EventHandler"]] = {}

    @classmethod
    def register_event_type(cls, event_type: str, event_handler_class: Type["basefunctions.EventHandler"]) -> None:
        """
        Register a new event handler type.

        Parameters
        ----------
        event_type : str
            Unique identifier for the event type
        event_handler_class : Type[basefunctions.EventHandler]
            Handler class implementing EventHandler interface

        Raises
        ------
        ValueError
            If parameters are invalid
        """
        if not event_type:
            raise ValueError("event_type cannot be empty")
        if not event_handler_class:
            raise ValueError("event_handler_class cannot be None")

        with cls._lock:
            cls._handler_registry[event_type] = event_handler_class

    @classmethod
    def create_handler(cls, event_type: str, *args, **kwargs) -> "basefunctions.EventHandler":
        """
        Create a handler instance for the specified event type.

        Parameters
        ----------
        event_type : str
            Event type identifier for which to create a handler
        *args
            Positional arguments passed to handler constructor
        **kwargs
            Keyword arguments passed to handler constructor

        Returns
        -------
        basefunctions.EventHandler
            New handler instance configured for the event type

        Raises
        ------
        ValueError
            If event_type is invalid or not registered
        RuntimeError
            If handler creation fails
        """
        if not event_type:
            raise ValueError("event_type cannot be empty")

        with cls._lock:
            if event_type not in cls._handler_registry:
                raise ValueError(f"No handler registered for event type '{event_type}'")

            try:
                handler_class = cls._handler_registry[event_type]
                handler = handler_class(*args, **kwargs)
                return handler
            except Exception as e:
                raise RuntimeError(f"Failed to create handler for event type '{event_type}': {str(e)}") from e

    @classmethod
    def is_handler_available(cls, event_type: str) -> bool:
        """
        Check if a handler is available for the specified event type.

        Parameters
        ----------
        event_type : str
            Event type identifier

        Returns
        -------
        bool
            True if handler is available, False otherwise
        """
        if not event_type:
            return False

        with cls._lock:
            return event_type in cls._handler_registry

    @classmethod
    def get_supported_event_types(cls) -> list[str]:
        """
        Get list of all supported event types.

        Returns
        -------
        list[str]
            List of supported event type identifiers
        """
        with cls._lock:
            return list(cls._handler_registry.keys())
