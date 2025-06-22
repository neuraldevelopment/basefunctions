"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Unified event exception hierarchy for the messaging system

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
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


class EventError(Exception):
    """Base class for all event-related exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error
        self.context = context

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class EventValidationError(EventError):
    """Event or handler validation failed."""

    pass


class EventExecutionError(EventError):
    """Event execution, timeout or cmd execution failed."""

    pass


class EventConnectionError(EventError):
    """Event bus connection failed."""

    pass


# Error codes
class EventErrorCodes:
    VALIDATION_FAILED = "EVENT_VALIDATION_FAILED"
    EXECUTION_FAILED = "EVENT_EXECUTION_FAILED"
    TIMEOUT_EXCEEDED = "EVENT_TIMEOUT_EXCEEDED"
    CMD_EXECUTION_FAILED = "EVENT_CMD_EXECUTION_FAILED"
    CONNECTION_FAILED = "EVENT_CONNECTION_FAILED"
