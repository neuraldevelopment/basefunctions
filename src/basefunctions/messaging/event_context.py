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
