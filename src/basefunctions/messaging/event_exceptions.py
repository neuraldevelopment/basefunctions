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

from typing import Dict, Any, Optional, cast

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------

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
    """
    Base class for all event-related exceptions.

    All event operations should raise exceptions derived from this class
    to provide consistent error handling across the event messaging system.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize event error with enhanced context.

        Parameters
        ----------
        message : str
            Human-readable error message
        error_code : str, optional
            Machine-readable error code for programmatic handling
        original_error : Exception, optional
            Original exception that caused this error (for chaining)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error message with optional error code."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        class_name = self.__class__.__name__
        if self.error_code:
            return f"{class_name}(message='{self.message}', error_code='{self.error_code}')"
        return f"{class_name}(message='{self.message}')"


class EventConnectError(EventError):
    """
    Error establishing or maintaining event bus connections.

    Raised when:
    - Initial connection to event bus fails
    - Connection is lost during operation
    - Connection parameters are invalid
    - Network connectivity issues for distributed event systems
    - Communication protocol problems
    """

    def __init__(
        self,
        message: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        service: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize connection error with server context.

        Parameters
        ----------
        message : str
            Error message
        host : str, optional
            Event service host that failed
        port : int, optional
            Event service port that failed
        service : str, optional
            Event service name that failed
        **kwargs
            Additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.host = host
        self.port = port
        self.service = service


# =============================================================================
# ERROR CODE CONSTANTS
# =============================================================================


class EventErrorCodes:
    """Constants for event error codes to enable programmatic error handling."""

    # Connection errors
    CONNECTION_FAILED = "EVENT_CONNECTION_FAILED"
    CONNECTION_LOST = "EVENT_CONNECTION_LOST"
    CONNECTION_TIMEOUT = "EVENT_CONNECTION_TIMEOUT"
    CONNECTION_REFUSED = "EVENT_CONNECTION_REFUSED"
    SSL_ERROR = "EVENT_SSL_ERROR"


# =============================================================================
# EXCEPTION FACTORY FUNCTIONS
# =============================================================================


def create_connection_error(
    message: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    service: Optional[str] = None,
    original_error: Optional[Exception] = None,
) -> EventConnectError:
    """
    Factory function for creating connection errors with context.

    Parameters
    ----------
    message : str
        Base error message
    host : str, optional
        Event service host that failed
    port : int, optional
        Event service port that failed
    service : str, optional
        Event service name that failed
    original_error : Exception, optional
        Underlying exception

    Returns
    -------
    EventConnectError
        Configured connection error
    """
    context_parts = []
    if host:
        context_parts.append(f"host={host}")
    if port:
        context_parts.append(f"port={port}")
    if service:
        context_parts.append(f"service={service}")

    if context_parts:
        enhanced_message = f"{message} ({', '.join(context_parts)})"
    else:
        enhanced_message = message

    return EventConnectError(
        enhanced_message,
        host=host,
        port=port,
        service=service,
        error_code=EventErrorCodes.CONNECTION_FAILED,
        original_error=original_error,
    )


def format_error_context(error: Exception) -> Dict[str, Any]:
    """
    Extract context information from an event error for logging.

    Parameters
    ----------
    error : Exception
        Exception to extract context from

    Returns
    -------
    Dict[str, Any]
        Context information
    """
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_category": get_error_category(error),
        "retryable": is_retryable_error(error),
    }

    if isinstance(error, EventError) and error.error_code:
        context["error_code"] = error.error_code

    if isinstance(error, EventConnectError):
        if error.host:
            context["host"] = error.host
        if error.port:
            context["port"] = error.port
        if error.service:
            context["service"] = error.service

    return context
