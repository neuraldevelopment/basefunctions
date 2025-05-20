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
from typing import Callable, Dict, List, Optional, Tuple

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
    backtesting and other high-frequency event processing scenarios.
    """

    __slots__ = ("_handlers", "_handler_methods", "_logger")

    def __init__(self):
        """
        Initialize a new EventBus.
        """
        # Main handler registry: event_type -> [(handler, filter_func)]
        self._handlers: Dict[
            str,
            List[
                Tuple[
                    basefunctions.EventHandler,
                    Optional[Callable[[basefunctions.Event], bool]],
                ]
            ],
        ] = {}

        # Direct method references for optimized dispatch:
        # event_type -> [(handler, method_ref, filter_func)]
        self._handler_methods: Dict[
            str,
            List[
                Tuple[
                    basefunctions.EventHandler,
                    Callable[[basefunctions.Event], None],
                    Optional[Callable[[basefunctions.Event], bool]],
                ]
            ],
        ] = {}

        self._logger = logging.getLogger(__name__)

    def register(
        self,
        event_type: str,
        handler: basefunctions.EventHandler,
        filter_func: Optional[Callable[[basefunctions.Event], bool]] = None,
    ) -> basefunctions.Subscription:
        """
        Register a handler for a specific event type.

        Parameters
        ----------
        event_type : str
            The type of events to handle.
        handler : basefunctions.messaging.handler.EventHandler
            The handler to register.
        filter_func : Callable[[basefunctions.messaging.event.Event], bool], optional
            Optional function to filter events before handling.

        Returns
        -------
        basefunctions.messaging.subscription.Subscription
            A subscription object that can be used to unregister the handler.

        Raises
        ------
        TypeError
            If handler is not an instance of EventHandler.
        """
        if not isinstance(handler, basefunctions.EventHandler):
            raise TypeError("Handler must be an instance of EventHandler")

        # Store direct reference to handler method for optimized dispatch
        handle_method = handler.handle

        # Initialize handler list for this event type if needed
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            self._handler_methods[event_type] = []

        # Add the handler to the registry
        handler_entry = (handler, filter_func)
        method_entry = (handler, handle_method, filter_func)

        self._handlers[event_type].append(handler_entry)
        self._handler_methods[event_type].append(method_entry)

        # Sort handlers by priority (higher priority first)
        self._sort_handlers(event_type)

        self._logger.debug(
            f"Registered handler {handler.__class__.__name__} for event type '{event_type}'"
        )

        # Return a subscription for unregistration
        return basefunctions.Subscription(self, event_type, handler_entry, method_entry)

    def _sort_handlers(self, event_type: str) -> None:
        """
        Sort handlers by priority.

        Parameters
        ----------
        event_type : str
            The event type whose handlers should be sorted.
        """
        if event_type in self._handlers:
            # Sort the handler list by priority (descending)
            self._handlers[event_type].sort(key=lambda x: x[0].get_priority(), reverse=True)

            # Sort the method list to match
            self._handler_methods[event_type].sort(key=lambda x: x[0].get_priority(), reverse=True)

    def unregister(self, event_type: str, handler: basefunctions.EventHandler) -> bool:
        """
        Unregister a handler from an event type.

        Parameters
        ----------
        event_type : str
            The event type to unregister from.
        handler : basefunctions.messaging.handler.EventHandler
            The handler to unregister.

        Returns
        -------
        bool
            True if the handler was unregistered, False if it wasn't registered.
        """
        if event_type not in self._handlers:
            return False

        # Find entries to remove
        to_remove = None
        for idx, (h, _) in enumerate(self._handlers[event_type]):
            if h is handler:
                to_remove = idx
                break

        if to_remove is None:
            return False

        # Remove from both registries
        self._handlers[event_type].pop(to_remove)
        self._handler_methods[event_type].pop(to_remove)

        self._logger.debug(
            f"Unregistered handler {handler.__class__.__name__} from event type '{event_type}'"
        )
        return True

    def unregister_all(self, handler: basefunctions.EventHandler) -> None:
        """
        Unregister a handler from all event types.

        Parameters
        ----------
        handler : basefunctions.messaging.handler.EventHandler
            The handler to unregister.
        """
        for event_type in list(self._handlers.keys()):
            self.unregister(event_type, handler)

    def publish(self, event: basefunctions.Event) -> None:
        """
        Publish an event to all registered handlers.

        This method uses optimized dispatch with direct method references
        for maximum performance.

        Parameters
        ----------
        event : basefunctions.messaging.event.Event
            The event to publish.
        """
        event_type = event.type

        if event_type not in self._handler_methods:
            return

        # Use optimized direct method references
        for handler, handle_method, filter_func in self._handler_methods[event_type]:
            try:
                # Apply filter if provided
                if filter_func is None or filter_func(event):
                    # Direct method call without dynamic lookup
                    handle_method(event)
            except Exception as e:
                self._logger.error(
                    f"Error in handler {handler.__class__.__name__} while processing event {event_type}: {str(e)}"
                )

    def clear(self) -> None:
        """
        Clear all handler registrations.
        """
        self._handlers.clear()
        self._handler_methods.clear()
        self._logger.debug("EventBus cleared")


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
