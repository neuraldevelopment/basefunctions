"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Subscription management for the event system

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Callable, Optional, Tuple, TypeVar, TYPE_CHECKING

import basefunctions

# Avoid circular imports while maintaining type hints
if TYPE_CHECKING:
    from basefunctions.messaging.event_bus import EventBus
    from basefunctions.messaging.event import Event
    from basefunctions.messaging.handler import EventHandler

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


class Subscription:
    """
    Manages the subscription of an event handler to an event type.

    A Subscription object is returned when a handler is registered with
    an EventBus. It can be used to unregister the handler or update
    its filtering logic.
    """

    __slots__ = ("_event_bus", "_event_type", "_handler_entry", "_method_entry", "_active")

    def __init__(
        self,
        event_bus: "EventBus",
        event_type: str,
        handler_entry: Tuple["EventHandler", Optional[Callable[["Event"], bool]]],
        method_entry: Tuple[
            "EventHandler", Callable[["Event"], None], Optional[Callable[["Event"], bool]]
        ],
    ):
        """
        Initialize a subscription.

        Parameters
        ----------
        event_bus : EventBus
            The event bus this subscription is associated with.
        event_type : str
            The event type this subscription is for.
        handler_entry : Tuple[EventHandler, Optional[Callable[[Event], bool]]]
            The handler entry in the event bus registry.
        method_entry : Tuple[EventHandler, Callable[[Event], None], Optional[Callable[[Event], bool]]]
            The method entry in the event bus optimized registry.
        """
        self._event_bus = event_bus
        self._event_type = event_type
        self._handler_entry = handler_entry
        self._method_entry = method_entry
        self._active = True

    @property
    def is_active(self) -> bool:
        """
        Check if this subscription is still active.

        Returns
        -------
        bool
            True if the subscription is active, False otherwise.
        """
        return self._active

    @property
    def event_type(self) -> str:
        """
        Get the event type this subscription is for.

        Returns
        -------
        str
            The event type.
        """
        return self._event_type

    @property
    def handler(self) -> "EventHandler":
        """
        Get the handler associated with this subscription.

        Returns
        -------
        EventHandler
            The event handler.
        """
        return self._handler_entry[0]

    def unsubscribe(self) -> bool:
        """
        Unsubscribe the handler from the event type.

        This effectively removes the handler registration from the
        event bus for the specified event type.

        Returns
        -------
        bool
            True if the unsubscription was successful, False otherwise.
        """
        if not self._active:
            return False

        # Use the event bus' unregister method
        result = self._event_bus.unregister(self._event_type, self._handler_entry[0])

        # Mark this subscription as inactive regardless of the result
        self._active = False

        return result

    def update_filter(self, filter_func: Optional[Callable[["Event"], bool]]) -> bool:
        """
        Update the filter function for this subscription.

        Parameters
        ----------
        filter_func : Optional[Callable[[Event], bool]]
            The new filter function, or None to remove filtering.

        Returns
        -------
        bool
            True if the filter was updated, False if the subscription is inactive.
        """
        if not self._active:
            return False

        # Since tuples are immutable, we need to create new entries
        handler, _ = self._handler_entry
        self._handler_entry = (handler, filter_func)

        handler, handle_method, _ = self._method_entry
        self._method_entry = (handler, handle_method, filter_func)

        return True

    def __enter__(self) -> "Subscription":
        """
        Context manager protocol support - enter.

        This allows using a subscription with a 'with' statement.

        Returns
        -------
        Subscription
            This subscription object.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager protocol support - exit.

        When exiting a 'with' block, the subscription is automatically
        unsubscribed.
        """
        self.unsubscribe()


class CompositeSubscription:
    """
    Manages multiple subscriptions as a single unit.

    This is useful when registering multiple handlers or handlers for
    multiple event types, and wanting to unsubscribe them all at once.
    """

    def __init__(self):
        """
        Initialize a composite subscription.
        """
        self._subscriptions = []

    def add(self, subscription: Subscription) -> "CompositeSubscription":
        """
        Add a subscription to this composite.

        Parameters
        ----------
        subscription : Subscription
            The subscription to add.

        Returns
        -------
        CompositeSubscription
            This composite subscription (for method chaining).
        """
        self._subscriptions.append(subscription)
        return self

    def unsubscribe_all(self) -> None:
        """
        Unsubscribe all subscriptions in this composite.
        """
        for subscription in self._subscriptions:
            subscription.unsubscribe()

        self._subscriptions.clear()

    @property
    def is_active(self) -> bool:
        """
        Check if any subscription in this composite is still active.

        Returns
        -------
        bool
            True if any subscription is active, False otherwise.
        """
        return any(subscription.is_active for subscription in self._subscriptions)

    def __enter__(self) -> "CompositeSubscription":
        """
        Context manager protocol support - enter.

        Returns
        -------
        CompositeSubscription
            This composite subscription object.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager protocol support - exit.

        When exiting a 'with' block, all subscriptions are automatically
        unsubscribed.
        """
        self.unsubscribe_all()
