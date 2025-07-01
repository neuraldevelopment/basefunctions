"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:
  Unified event exception hierarchy for the messaging system

  Log:
  v2.3 : Improved import style, added Enum for error codes, enhanced docstrings
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import enum
import typing
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
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class EventErrorCode(enum.Enum):
    """Error codes for event-related exceptions."""

    VALIDATION_FAILED = "EVENT_VALIDATION_FAILED"
    EXECUTION_FAILED = "EVENT_EXECUTION_FAILED"
    TIMEOUT_EXCEEDED = "EVENT_TIMEOUT_EXCEEDED"
    CMD_EXECUTION_FAILED = "EVENT_CMD_EXECUTION_FAILED"
    CONNECTION_FAILED = "EVENT_CONNECTION_FAILED"

    # EventBus-specific error codes
    EVENTBUS_SHUTDOWN = "EVENTBUS_SHUTDOWN"
    NO_HANDLER_AVAILABLE = "NO_HANDLER_AVAILABLE"
    INVALID_EVENT = "INVALID_EVENT"
    EVENTBUS_INIT_FAILED = "EVENTBUS_INIT_FAILED"


class EventError(Exception):
    """
    Base class for all event-related exceptions.

    Provides structured error information including error codes, original errors,
    and context data for better debugging and error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: typing.Optional[EventErrorCode] = None,
        original_error: typing.Optional[Exception] = None,
        context: typing.Optional[typing.Any] = None,
    ):
        """
        Initialize EventError with structured error information.

        Args:
            message: Human-readable error message
            error_code: Specific error code for categorization
            original_error: Original exception that caused this error
            context: Additional context data for debugging
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error
        self.context = context

    def __str__(self) -> str:
        """Return formatted error string with error code if available."""
        if self.error_code:
            return f"[{self.error_code.value}] {self.message}"
        return self.message


class EventValidationError(EventError):
    """
    Raised when event or handler validation fails.

    Used for schema validation, type checking, and business rule violations.
    """

    def __init__(self, message: str, context: typing.Optional[typing.Any] = None):
        super().__init__(message=message, error_code=EventErrorCode.VALIDATION_FAILED, context=context)


class EventExecutionError(EventError):
    """
    Raised when event execution, timeout, or command execution fails.

    Covers execution errors, timeouts, and command failures.
    """

    def __init__(self, message: str, original_error: typing.Optional[Exception] = None):
        super().__init__(message=message, error_code=EventErrorCode.EXECUTION_FAILED, original_error=original_error)


class EventConnectionError(EventError):
    """
    Raised when event bus connection fails.

    Used for network, database, or service connection issues.
    """

    def __init__(self, message: str, original_error: typing.Optional[Exception] = None):
        super().__init__(message=message, error_code=EventErrorCode.CONNECTION_FAILED, original_error=original_error)


# EventBus-specific exceptions
class EventBusError(EventError):
    """
    Base exception for EventBus-specific errors.

    Parent class for all EventBus-related exceptions.
    """

    pass


class EventBusShutdownError(EventBusError):
    """
    Raised when trying to publish to a shutting down EventBus.

    Prevents new events from being published during shutdown process.
    """

    def __init__(self, message: str = "EventBus is shutting down, cannot publish events"):
        super().__init__(
            message=message, error_code=EventErrorCode.EVENTBUS_SHUTDOWN, context="EventBus shutdown state"
        )


class NoHandlerAvailableError(EventBusError):
    """
    Raised when no handler is available for an event type.

    Indicates missing or unregistered event handlers.
    """

    def __init__(self, event_type: str):
        message = f"No handler available for event type: {event_type}"
        super().__init__(
            message=message, error_code=EventErrorCode.NO_HANDLER_AVAILABLE, context={"event_type": event_type}
        )


class InvalidEventError(EventBusError):
    """
    Raised when an event is invalid or missing required attributes.

    Used for malformed events or missing required fields.
    """

    def __init__(self, message: str, context: typing.Optional[typing.Any] = None):
        super().__init__(message=message, error_code=EventErrorCode.INVALID_EVENT, context=context)


class EventBusInitializationError(EventBusError):
    """
    Raised when EventBus initialization fails.

    Covers configuration errors, resource allocation failures, etc.
    """

    def __init__(self, message: str, original_error: typing.Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code=EventErrorCode.EVENTBUS_INIT_FAILED,
            original_error=original_error,
            context="EventBus initialization",
        )
