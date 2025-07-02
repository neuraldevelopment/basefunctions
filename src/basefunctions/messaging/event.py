"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Event classes for the messaging system with corelet factory methods

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Optional
from datetime import datetime
import uuid
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
EXECUTION_MODE_SYNC = "sync"
EXECUTION_MODE_THREAD = "thread"
EXECUTION_MODE_CORELET = "corelet"
EXECUTION_MODE_CMD = "cmd"

VALID_EXECUTION_MODES = {EXECUTION_MODE_SYNC, EXECUTION_MODE_THREAD, EXECUTION_MODE_CORELET, EXECUTION_MODE_CMD}

DEFAULT_PRIORITY = 5
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

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
        "event_id",
        "event_type",
        "event_exec_mode",
        "event_name",
        "event_source",
        "event_target",
        "event_data",
        "max_retries",
        "timeout",
        "priority",
        "timestamp",
        "corelet_meta",
    )

    def __init__(
        self,
        event_type: str,
        event_exec_mode: str = EXECUTION_MODE_THREAD,
        event_name: Optional[str] = None,
        event_source: Optional[Any] = None,
        event_target: Any = None,
        event_data: Any = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: int = DEFAULT_TIMEOUT,
        priority: int = DEFAULT_PRIORITY,
        corelet_meta: Optional[dict] = None,
    ):
        """
        Initialize a new event.

        Parameters
        ----------
        event_type : str
            The type of the event, used for routing to the appropriate handlers.
        event_exec_mode : str, optional
            Execution mode for event processing. Defaults to thread mode.
        event_name : str, optional
            Human-readable name for the event.
        event_source : Any, optional
            The source/originator of the event.
        event_target : Any, optional
            The target destination for event routing in the messaging system.
        event_data : Any, optional
            The data payload of the event.
        max_retries : int, optional
            Maximum number of retry attempts for failed event processing.
        timeout : int, optional
            Timeout in seconds for event processing.
        priority : int, optional
            Execution priority (0-10, higher = more important).
        corelet_meta : dict, optional
            Handler metadata for corelet registration. Auto-populated for corelet mode.
        """
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.event_exec_mode = event_exec_mode
        self.event_name = event_name
        self.event_source = event_source
        self.event_target = event_target
        self.event_data = event_data
        self.max_retries = max_retries
        self.timeout = timeout
        self.priority = priority
        self.timestamp = datetime.now()

        # Auto-populate corelet metadata for corelet execution mode
        if event_exec_mode == EXECUTION_MODE_CORELET and corelet_meta is None:
            try:
                self.corelet_meta = basefunctions.EventFactory.get_handler_meta(event_type)
            except (ValueError, ImportError):
                # Handler not registered yet or import issues - will be handled later
                self.corelet_meta = None
        else:
            self.corelet_meta = corelet_meta

        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate event parameters."""
        if not self.event_type:
            raise ValueError("event_type cannot be empty")

        if self.event_exec_mode not in VALID_EXECUTION_MODES:
            raise ValueError(f"Invalid execution mode: {self.event_exec_mode}")

    def __repr__(self) -> str:
        """
        Get detailed string representation for debugging.

        Returns
        -------
        str
            Detailed event representation
        """
        return (
            f"Event(id={self.event_id}, type={self.event_type}, name={self.event_name}, "
            f"exec_mode={self.event_exec_mode}, priority={self.priority}, "
            f"source={self.event_source}, target={self.event_target}, "
            f"timeout={self.timeout}, max_retries={self.max_retries}, "
            f"timestamp={self.timestamp}, corelet_meta={self.corelet_meta})"
        )
