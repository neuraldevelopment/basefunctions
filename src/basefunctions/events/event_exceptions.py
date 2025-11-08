"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Event context for processing across different execution modes

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import basefunctions

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
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------


class EventValidationError(Exception):
    """
    Event or handler validation failed.

    Raised when event or handler validation fails due to schema violations,
    type checking errors, business rule violations, or missing required fields.

    Examples
    --------
    >>> raise EventValidationError("Missing required field: event_type")
    """

    pass


class EventExecutionError(Exception):
    """
    Event execution failed.

    Raised when event execution fails due to handler errors, command execution
    failures, processing timeouts, or runtime exceptions during event processing.

    Examples
    --------
    >>> raise EventExecutionError("Handler execution failed: division by zero")
    """

    pass


class EventConnectionError(Exception):
    """
    Event bus connection failed.

    Raised when connection to EventBus or external services fails due to
    network issues, database connection failures, service unavailability,
    or authentication errors.

    Examples
    --------
    >>> raise EventConnectionError("Unable to connect to event bus")
    """

    pass


class EventShutdownError(Exception):
    """
    EventBus shutdown operation failed.

    Raised during EventBus shutdown when operations fail, such as publishing
    to a shutting down bus, graceful shutdown timeout, resource cleanup
    failures, or when pending events still exist.

    Examples
    --------
    >>> raise EventShutdownError("Cannot publish during shutdown")
    """

    pass


class NoHandlerAvailableError(Exception):
    """
    No handler available for event type.

    Raised when no handler is registered for a given event type, handler
    registration fails, event processors are missing, or dynamic handler
    lookup fails.

    Attributes
    ----------
    event_type : str
        The event type for which no handler was found (optional)

    Examples
    --------
    >>> raise NoHandlerAvailableError("data_process")
    """

    def __init__(self, event_type: str = None):
        """
        Initialize NoHandlerAvailableError.

        Parameters
        ----------
        event_type : str, optional
            The event type for which no handler was found
        """
        if event_type:
            super().__init__(f"No handler available for event type: {event_type}")
        else:
            super().__init__("No handler available")


class InvalidEventError(Exception):
    """
    Event is invalid or malformed.

    Raised when event validation fails due to missing event attributes,
    invalid event structure, unsupported event format, or event
    serialization failures.

    Examples
    --------
    >>> raise InvalidEventError("Event must have a valid event_type")
    """

    pass
