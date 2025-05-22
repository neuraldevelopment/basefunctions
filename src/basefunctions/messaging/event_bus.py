"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 EventBus implementation for high-performance event distribution
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
from typing import Dict, List

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
_DEFAULT_INSTANCE = None

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class EventBus:
    """
    Central event distribution system.

    The EventBus manages handler registrations and event publishing.
    It provides a high-performance implementation optimized for
    event processing scenarios.
    """

    __slots__ = ("_handlers", "_logger")

    def __init__(self):
        """
        Initialize a new EventBus.
        """
        # Main handler registry: event_type -> [handler1, handler2, ...]
        self._handlers: Dict[str, List[basefunctions.EventHandler]] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, event_type: str, handler: basefunctions.EventHandler) -> bool:
        """
        Register a handler for a specific event type.

        Parameters
        ----------
        event_type : str
            The type of events to handle.
        handler : basefunctions.EventHandler
            The handler to register.

        Returns
        -------
        bool
            True if registration was successful, False otherwise.

        Raises
        ------
        TypeError
            If handler is not an instance of EventHandler.
        """
        if not isinstance(handler, basefunctions.EventHandler):
            raise TypeError("Handler must be an instance of EventHandler")

        # Initialize handler list for this event type if needed
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        # Add the handler to the registry
        self._handlers[event_type].append(handler)
        return True

    def unregister(self, event_type: str, handler: basefunctions.EventHandler) -> bool:
        """
        Unregister a handler from an event type.

        Parameters
        ----------
        event_type : str
            The event type to unregister from.
        handler : basefunctions.EventHandler
            The handler to unregister.

        Returns
        -------
        bool
            True if the handler was unregistered, False if it wasn't registered.
        """
        if event_type not in self._handlers:
            return False

        # Find and remove handler
        try:
            self._handlers[event_type].remove(handler)
            return True
        except ValueError:
            return False

    def unregister_all(self, handler: basefunctions.EventHandler) -> None:
        """
        Unregister a handler from all event types.

        Parameters
        ----------
        handler : basefunctions.EventHandler
            The handler to unregister.
        """
        for event_type in list(self._handlers.keys()):
            self.unregister(event_type, handler)

    def publish(self, event: basefunctions.Event) -> None:
        """
        Publish an event to all registered handlers.

        Parameters
        ----------
        event : basefunctions.Event
            The event to publish.
        """
        event_type = event.type

        if event_type not in self._handlers:
            return

        # Call all handlers for this event type
        for handler in self._handlers[event_type]:
            try:
                handler.handle(event)
            except Exception as e:
                self._logger.error(
                    f"Error in handler {handler.__class__.__name__} while processing event {event_type}: {str(e)}"
                )

    def clear(self) -> None:
        """
        Clear all handler registrations.
        """
        self._handlers.clear()


def get_event_bus() -> EventBus:
    """
    Get the default EventBus instance.

    This function provides a singleton-like access to a default EventBus
    instance, creating it if it doesn't exist yet.

    Returns
    -------
    EventBus
        The default EventBus instance.
    """
    global _DEFAULT_INSTANCE
    if _DEFAULT_INSTANCE is None:
        _DEFAULT_INSTANCE = EventBus()
    return _DEFAULT_INSTANCE
