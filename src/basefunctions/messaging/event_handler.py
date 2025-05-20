"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Event handler interfaces and base implementations for the messaging system

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Type, Union

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


class EventHandler(ABC):
    """
    Interface for event handlers in the messaging system.

    Event handlers are responsible for processing events. They are registered
    with an EventBus to receive and handle specific types of events.
    """

    @abstractmethod
    def handle(self, event: basefunctions.Event) -> None:
        """
        Handle an event.

        This method is called by the EventBus when an event of the type
        this handler is registered for is published.

        Parameters
        ----------
        event : Event
            The event to handle.
        """
        pass

    def can_handle(self, event: basefunctions.Event) -> bool:
        """
        Check if this handler can handle the given event.

        By default, all handlers can handle all events. Override this method
        to implement specific filtering logic.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if this handler can handle the event, False otherwise.
        """
        return True

    def get_priority(self) -> int:
        """
        Get the priority of this handler.

        Handlers with higher priority values are executed first.
        Default priority is 0.

        Returns
        -------
        int
            The priority of this handler.
        """
        return 0


class TypedEventHandler(EventHandler, ABC):
    """
    Base class for handlers that only process specific event types.

    This abstract class simplifies creating handlers for specific event types
    by automatically implementing the can_handle method based on event type.
    """

    def __init__(
        self,
        event_types: Union[
            str, Type[basefunctions.Event], list[Union[str, Type[basefunctions.Event]]]
        ],
    ):
        """
        Initialize a typed event handler.

        Parameters
        ----------
        event_types : Union[str, Type[Event], list[Union[str, Type[Event]]]]
            The event type(s) this handler can process. Can be a string,
            an Event class, or a list of strings and/or Event classes.
        """
        if isinstance(event_types, (str, type)):
            event_types = [event_types]

        self._event_types = []
        for et in event_types:
            if isinstance(et, type) and issubclass(et, basefunctions.Event):
                self._event_types.append(et.event_type)
            else:
                self._event_types.append(str(et))

    def can_handle(self, event: basefunctions.Event) -> bool:
        """
        Check if this handler can handle the given event based on its type.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the event type matches one of the types this handler
            was initialized with, False otherwise.
        """
        return event.type in self._event_types


class PrioritizedEventHandler(EventHandler):
    """
    Decorator class for adding priority to existing event handlers.

    This class wraps an existing event handler and adds a priority value.
    """

    def __init__(self, handler: EventHandler, priority: int):
        """
        Initialize a prioritized event handler.

        Parameters
        ----------
        handler : EventHandler
            The event handler to wrap.
        priority : int
            The priority value for this handler.
        """
        self._handler = handler
        self._priority = priority

    def handle(self, event: basefunctions.Event) -> None:
        """
        Handle an event by delegating to the wrapped handler.

        Parameters
        ----------
        event : Event
            The event to handle.
        """
        self._handler.handle(event)

    def can_handle(self, event: basefunctions.Event) -> bool:
        """
        Check if the wrapped handler can handle the given event.

        Parameters
        ----------
        event : Event
            The event to check.

        Returns
        -------
        bool
            True if the wrapped handler can handle the event, False otherwise.
        """
        return self._handler.can_handle(event)

    def get_priority(self) -> int:
        """
        Get the priority of this handler.

        Returns
        -------
        int
            The priority value set during initialization.
        """
        return self._priority
