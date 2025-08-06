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

    Raised when:
    - Schema validation fails
    - Type checking errors
    - Business rule violations
    - Missing required fields
    """

    pass


class EventExecutionError(Exception):
    """
    Event execution failed.

    Raised when:
    - Handler execution errors
    - Command execution failures
    - Processing timeouts
    - Runtime exceptions
    """

    pass


class EventConnectionError(Exception):
    """
    Event bus connection failed.

    Raised when:
    - Network connection issues
    - Database connection failures
    - Service unavailable
    - Authentication errors
    """

    pass


class EventShutdownError(Exception):
    """
    EventBus shutdown operation failed.

    Raised when:
    - Publishing to shutting down bus
    - Graceful shutdown timeout
    - Resource cleanup failures
    - Pending events exist
    """

    pass


class NoHandlerError(Exception):
    """
    No handler available for event type.

    Raised when:
    - Unregistered event types
    - Handler registration failures
    - Missing event processors
    - Dynamic handler lookup fails
    """

    pass


class InvalidEventError(Exception):
    """
    Event is invalid or malformed.

    Raised when:
    - Missing event attributes
    - Invalid event structure
    - Unsupported event format
    - Event serialization failures
    """

    pass
