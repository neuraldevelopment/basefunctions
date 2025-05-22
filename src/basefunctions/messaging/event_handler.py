"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
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
from typing import Any, Optional
from datetime import datetime

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
        "execution_mode",
        "thread_local_data",
        "thread_id",
        "process_id",
        "timestamp",
        "event_data",
    )

    def __init__(self, execution_mode: str, **kwargs):
        """
        Initialize event context.

        Parameters
        ----------
        execution_mode : str
            The execution mode (sync, thread, corelet).
        **kwargs
            Additional context data specific to execution mode.
        """
        self.execution_mode = execution_mode

        # Thread-specific context
        self.thread_local_data = kwargs.get("thread_local_data")
        self.thread_id = kwargs.get("thread_id")

        # Corelet-specific context
        self.process_id = kwargs.get("process_id")
        self.timestamp = kwargs.get("timestamp", datetime.now())
        self.event_data = kwargs.get("event_data")


class EventHandler(ABC):
    """
    Interface for event handlers in the messaging system.

    Event handlers are responsible for processing events. They are registered
    with an EventBus to receive and handle specific types of events.
    """

    execution_mode = 0  # Default execution mode: 0=sync, 1=thread, 2=corelet

    @abstractmethod
    def handle(self, event: basefunctions.Event, context: Optional[EventContext] = None) -> Any:
        """
        Handle an event.

        This method is called by the EventBus when an event of the type
        this handler is registered for is published.

        Parameters
        ----------
        event : Event
            The event to handle.
        context : EventContext, optional
            Context data for event processing. None for sync mode,
            contains thread_local_data for thread mode, and process
            info for corelet mode.

        Returns
        -------
        Any
            Result data on success. Raise Exception on error.
            None return value indicates success with no data.
        """
        pass
