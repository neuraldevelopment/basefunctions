"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Message type definitions for the unified task pool system
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


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
@dataclass
class UnifiedTaskPoolMessage:
    """
    Message object used for communication between threads and processes.

    Attributes
    ----------
    id : str
        Unique identifier for the message.
    message_type : str
        Type of message to determine handler.
    execution_type : str
        Execution type - "thread" or "core".
    corelet_path : Optional[str]
        Optional path to the corelet containing the handler.
    retry_max : int
        Maximum number of retries on failure.
    timeout : int
        Timeout per request in seconds.
    content : Any
        Content payload of the message.
    retry : int
        Current retry count.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: str = ""
    execution_type: str = "thread"  # "thread" or "core"
    corelet_path: Optional[str] = None  # Path for dynamic module
    retry_max: int = 3
    timeout: int = 5
    content: Any = None
    retry: int = 0


@dataclass
class UnifiedTaskPoolResult:
    """
    Result object representing the outcome of task processing.

    Attributes
    ----------
    message_type : str
        Type of message processed.
    id : str
        Identifier of the original message.
    success : bool
        Whether processing was successful.
    data : Any
        Result data from processing.
    metadata : Dict[str, Any]
        Additional metadata.
    original_message : Optional[UnifiedTaskPoolMessage]
        Reference to the original message.
    error : Optional[str]
        Error message, if any.
    exception_type : Optional[str]
        Type of exception, if any.
    retry_counter : int
        Number of attempts made.
    exception : Optional[Exception]
        Captured exception object.
    """

    message_type: str
    id: str
    success: bool = False
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    original_message: Optional[UnifiedTaskPoolMessage] = None
    error: Optional[str] = None
    exception_type: Optional[str] = None
    retry_counter: int = 0
    exception: Optional[Exception] = None
