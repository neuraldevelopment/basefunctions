"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Corelet worker with queue-based health monitoring

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from datetime import datetime
from typing import Optional, Any
from basefunctions.utils.logging import setup_logger

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
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class EventContext:
    """
    Context data container for event processing across different execution modes.

    EventContext provides execution context information to event handlers,
    including thread-local storage for caching, process identification for
    corelet mode, and optional worker references. The context is passed to
    every handler.handle() call to enable stateless handler implementations
    with access to thread/process-specific state.

    Attributes
    ----------
    thread_local_data : Optional[Any]
        Thread-local storage object (threading.local()) for handler caching
        and thread-specific state. Each thread gets its own isolated storage.
    thread_id : Optional[str]
        Thread identifier for the executing thread
    process_id : Optional[str]
        Process identifier for corelet worker processes
    timestamp : datetime
        Timestamp when context was created (defaults to current time)
    event_data : Optional[Any]
        Additional event-specific context data
    worker : Optional[Any]
        Reference to CoreletWorker instance (corelet mode only)

    Notes
    -----
    **Usage by Execution Mode:**

    SYNC mode:
    - Single context shared across all sync events
    - thread_local_data: threading.local() for handler cache
    - thread_id: None (not tracked)
    - process_id: None (main process)

    THREAD mode:
    - Context created per worker thread
    - thread_local_data: threading.local() for handler cache
    - thread_id: Worker thread ID
    - process_id: None (main process)

    CORELET mode:
    - Context created per worker process
    - thread_local_data: threading.local() for handler cache
    - thread_id: None (worker process main thread)
    - process_id: Worker process PID
    - worker: Reference to CoreletWorker instance

    **Handler Caching Pattern:**
    Handlers use thread_local_data to cache expensive resources:

    >>> if not hasattr(context.thread_local_data, 'db_connection'):
    ...     context.thread_local_data.db_connection = create_db_connection()
    >>> return context.thread_local_data.db_connection

    **Thread Safety:**
    - thread_local_data is thread-safe by design (threading.local())
    - Each thread/process gets isolated storage
    - No locking required for thread_local_data access

    Examples
    --------
    Create context for sync execution:

    >>> context = EventContext(thread_local_data=threading.local())

    Create context for worker thread:

    >>> context = EventContext(
    ...     thread_local_data=threading.local(),
    ...     thread_id=threading.get_ident()
    ... )

    Create context for corelet worker:

    >>> context = EventContext(
    ...     thread_local_data=threading.local(),
    ...     process_id=os.getpid(),
    ...     worker=worker_instance
    ... )

    See Also
    --------
    EventHandler : Uses context for stateless handler implementation
    EventBus : Creates and manages contexts for different execution modes
    """

    __slots__ = (
        "thread_local_data",
        "thread_id",
        "process_id",
        "timestamp",
        "event_data",
        "worker",
    )

    def __init__(
        self,
        thread_local_data: Optional[Any] = None,
        thread_id: Optional[str] = None,
        process_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        event_data: Optional[Any] = None,
        worker: Optional[Any] = None,
    ):
        """
        Initialize event context.

        Parameters
        ----------
        thread_local_data : Optional[Any], default=None
            Thread-specific context data.
        thread_id : Optional[str], default=None
            Thread identifier.
        process_id : Optional[str], default=None
            Process identifier for corelet-specific context.
        timestamp : Optional[datetime], default=None
            Event timestamp. If None, uses current time.
        event_data : Optional[Any], default=None
            Event-specific data.
        worker : Optional[Any], default=None
            Worker reference for corelet mode.
        """
        # Thread-specific context
        self.thread_local_data = thread_local_data
        self.thread_id = thread_id
        # Corelet-specific context
        self.process_id = process_id
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.event_data = event_data
        # Worker reference for corelet mode
        self.worker = worker
