"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

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
from typing import Tuple, Any, Optional
from datetime import datetime

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
        "worker",
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

        # Worker reference for corelet mode
        self.worker = kwargs.get("worker")


class EventHandler(ABC):
    """
    Interface for event handlers in the messaging system.

    Event handlers are responsible for processing events. They are registered
    with an EventBus to receive and handle specific types of events.
    """

    execution_mode = EXECUTION_MODE_SYNC  # Default execution mode: sync, thread, corelet

    @classmethod
    def get_execution_mode(cls):
        return cls.execution_mode

    @abstractmethod
    def handle(
        self,
        event: "basefunctions.Event",
        context: Optional[EventContext] = None,
    ) -> Tuple[bool, Any]:
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
        Tuple[bool, Any]
            A tuple containing:
            - bool: Success flag, True for successful execution, False for unsuccessful execution
            - Any: Result data on success, None indicates success with no data

        Raises
        ------
        Exception
            Any exception raised during event processing will be caught and handled by the EventBus
        """
        raise NotImplementedError("Subclasses must implement handle method")
