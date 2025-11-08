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
  v1.1 : Added progress tracking support (progress_tracker, progress_steps)
  v1.2 : Fixed circular import with TYPE_CHECKING
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Optional, TYPE_CHECKING
from datetime import datetime
import uuid
import basefunctions

# Import only for type checking, not at runtime
if TYPE_CHECKING:
    from basefunctions.progress_tracker import ProgressTracker

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
    components in a decoupled way. Each event has a unique ID, type,
    execution mode, and optional payload data.

    The Event class supports three execution modes (SYNC, THREAD, CORELET),
    priority-based scheduling, timeout handling, automatic retry logic,
    and optional progress tracking integration.

    Attributes
    ----------
    event_id : str
        Unique identifier (UUID) for this event instance
    event_type : str
        Event type identifier used for handler routing
    event_exec_mode : str
        Execution mode: "sync", "thread", "corelet", or "cmd"
    event_name : Optional[str]
        Human-readable name for the event
    event_source : Optional[Any]
        The source/originator of the event
    event_target : Any
        The target destination for event routing
    event_data : Any
        The data payload of the event
    max_retries : int
        Maximum number of retry attempts for failed event processing
    timeout : int
        Timeout in seconds for event processing
    priority : int
        Execution priority (0-10, higher = more important)
    timestamp : datetime
        Timestamp when event was created
    corelet_meta : Optional[dict]
        Handler metadata for corelet registration
    progress_tracker : Optional[ProgressTracker]
        Progress tracker instance for automatic progress updates
    progress_steps : int
        Number of steps to advance progress tracker after event completion

    Notes
    -----
    - Event IDs are automatically generated as UUIDs
    - For corelet mode, corelet_meta is auto-populated from EventFactory
    - Events are immutable after creation (enforced via __slots__)
    - Thread-safe when used with EventBus
    - Progress tracking is optional and integrated with EventBus

    Examples
    --------
    Create a simple synchronous event:

    >>> event = Event(
    ...     event_type="data_processing",
    ...     event_exec_mode=EXECUTION_MODE_SYNC,
    ...     event_data={"input": "test.csv"}
    ... )

    Create a threaded event with custom priority and timeout:

    >>> event = Event(
    ...     event_type="heavy_computation",
    ...     event_exec_mode=EXECUTION_MODE_THREAD,
    ...     priority=8,
    ...     timeout=60,
    ...     event_data={"batch_size": 1000}
    ... )

    Create a corelet event with progress tracking:

    >>> tracker = ProgressTracker(total=100)
    >>> event = Event(
    ...     event_type="distributed_task",
    ...     event_exec_mode=EXECUTION_MODE_CORELET,
    ...     progress_tracker=tracker,
    ...     progress_steps=10
    ... )
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
        "progress_tracker",
        "progress_steps",
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
        progress_tracker: Optional["ProgressTracker"] = None,
        progress_steps: int = 0,
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
        progress_tracker : ProgressTracker, optional
            Progress tracker instance for automatic progress updates after event completion.
        progress_steps : int, optional
            Number of steps to advance progress tracker after event completion. Default is 0 (disabled).
        """
        # Generate unique event ID for tracking and correlation
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
        self.progress_tracker = progress_tracker
        self.progress_steps = progress_steps

        # Auto-populate corelet metadata for corelet execution mode
        # This allows corelet workers to dynamically load the correct handler class
        if event_exec_mode == EXECUTION_MODE_CORELET and corelet_meta is None:
            try:
                self.corelet_meta = basefunctions.EventFactory().get_handler_meta(event_type)
            except (ValueError, ImportError):
                # Handler not registered yet or import issues - will be handled later
                # CoreletWorker can still register handler via corelet_meta in the event
                self.corelet_meta = None
        else:
            self.corelet_meta = corelet_meta

        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """
        Validate event parameters for correctness.

        Raises
        ------
        ValueError
            If event_type is empty or execution mode is invalid
        """
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
            f"timestamp={self.timestamp}, corelet_meta={self.corelet_meta}, "
            f"progress_steps={self.progress_steps})"
        )
