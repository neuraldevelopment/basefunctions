"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for event system custom exceptions.
 Tests exception hierarchy, error messages, and exception attributes.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import Type

# Project imports
from basefunctions.events.event_exceptions import (
    EventValidationError,
    EventExecutionError,
    EventConnectionError,
    EventShutdownError,
    NoHandlerAvailableError,
    InvalidEventError,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_event_type() -> str:
    """
    Provide sample event type for exception testing.

    Returns
    -------
    str
        Sample event type identifier
    """
    return "test_event_type"


# -------------------------------------------------------------
# TESTS: EventValidationError
# -------------------------------------------------------------


def test_event_validation_error_inherits_from_exception() -> None:
    """Test EventValidationError inherits from Exception."""
    # ASSERT
    assert issubclass(EventValidationError, Exception)


def test_event_validation_error_can_be_raised_with_message() -> None:
    """Test EventValidationError can be raised with custom message."""
    # ARRANGE
    error_message: str = "Missing required field: event_type"

    # ACT & ASSERT
    with pytest.raises(EventValidationError, match=error_message):
        raise EventValidationError(error_message)


def test_event_validation_error_preserves_message() -> None:
    """Test EventValidationError preserves error message."""
    # ARRANGE
    error_message: str = "Schema validation failed"

    # ACT
    error: EventValidationError = EventValidationError(error_message)

    # ASSERT
    assert str(error) == error_message


# -------------------------------------------------------------
# TESTS: EventExecutionError
# -------------------------------------------------------------


def test_event_execution_error_inherits_from_exception() -> None:
    """Test EventExecutionError inherits from Exception."""
    # ASSERT
    assert issubclass(EventExecutionError, Exception)


def test_event_execution_error_can_be_raised_with_message() -> None:
    """Test EventExecutionError can be raised with custom message."""
    # ARRANGE
    error_message: str = "Handler execution failed: division by zero"

    # ACT & ASSERT
    with pytest.raises(EventExecutionError, match=error_message):
        raise EventExecutionError(error_message)


# -------------------------------------------------------------
# TESTS: EventConnectionError
# -------------------------------------------------------------


def test_event_connection_error_inherits_from_exception() -> None:
    """Test EventConnectionError inherits from Exception."""
    # ASSERT
    assert issubclass(EventConnectionError, Exception)


def test_event_connection_error_can_be_raised_with_message() -> None:
    """Test EventConnectionError can be raised with custom message."""
    # ARRANGE
    error_message: str = "Unable to connect to event bus"

    # ACT & ASSERT
    with pytest.raises(EventConnectionError, match=error_message):
        raise EventConnectionError(error_message)


# -------------------------------------------------------------
# TESTS: EventShutdownError
# -------------------------------------------------------------


def test_event_shutdown_error_inherits_from_exception() -> None:
    """Test EventShutdownError inherits from Exception."""
    # ASSERT
    assert issubclass(EventShutdownError, Exception)


def test_event_shutdown_error_can_be_raised_with_message() -> None:
    """Test EventShutdownError can be raised with custom message."""
    # ARRANGE
    error_message: str = "Cannot publish during shutdown"

    # ACT & ASSERT
    with pytest.raises(EventShutdownError, match=error_message):
        raise EventShutdownError(error_message)


# -------------------------------------------------------------
# TESTS: NoHandlerAvailableError
# -------------------------------------------------------------


def test_no_handler_available_error_inherits_from_exception() -> None:
    """Test NoHandlerAvailableError inherits from Exception."""
    # ASSERT
    assert issubclass(NoHandlerAvailableError, Exception)


def test_no_handler_available_error_with_event_type(sample_event_type: str) -> None:
    """Test NoHandlerAvailableError with event_type parameter."""
    # ACT
    error: NoHandlerAvailableError = NoHandlerAvailableError(sample_event_type)

    # ASSERT
    assert sample_event_type in str(error)
    assert "No handler available for event type" in str(error)


def test_no_handler_available_error_without_event_type() -> None:
    """Test NoHandlerAvailableError without event_type parameter."""
    # ACT
    error: NoHandlerAvailableError = NoHandlerAvailableError()

    # ASSERT
    assert str(error) == "No handler available"


def test_no_handler_available_error_can_be_raised(sample_event_type: str) -> None:
    """Test NoHandlerAvailableError can be raised with event type."""
    # ARRANGE
    expected_message: str = f"No handler available for event type: {sample_event_type}"

    # ACT & ASSERT
    with pytest.raises(NoHandlerAvailableError, match=expected_message):
        raise NoHandlerAvailableError(sample_event_type)


def test_no_handler_available_error_none_event_type() -> None:
    """Test NoHandlerAvailableError with None event_type."""
    # ACT
    error: NoHandlerAvailableError = NoHandlerAvailableError(None)

    # ASSERT
    assert str(error) == "No handler available"


# -------------------------------------------------------------
# TESTS: InvalidEventError
# -------------------------------------------------------------


def test_invalid_event_error_inherits_from_exception() -> None:
    """Test InvalidEventError inherits from Exception."""
    # ASSERT
    assert issubclass(InvalidEventError, Exception)


def test_invalid_event_error_can_be_raised_with_message() -> None:
    """Test InvalidEventError can be raised with custom message."""
    # ARRANGE
    error_message: str = "Event must have a valid event_type"

    # ACT & ASSERT
    with pytest.raises(InvalidEventError, match=error_message):
        raise InvalidEventError(error_message)


# -------------------------------------------------------------
# TESTS: Exception Hierarchy
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "exception_class,expected_base",
    [
        (EventValidationError, Exception),
        (EventExecutionError, Exception),
        (EventConnectionError, Exception),
        (EventShutdownError, Exception),
        (NoHandlerAvailableError, Exception),
        (InvalidEventError, Exception),
    ],
)
def test_all_exceptions_inherit_from_exception(
    exception_class: Type[Exception], expected_base: Type[Exception]
) -> None:
    """Test all event exceptions inherit from Exception base class."""
    # ASSERT
    assert issubclass(exception_class, expected_base)


# -------------------------------------------------------------
# TESTS: Exception Instantiation
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "exception_class,error_message",
    [
        (EventValidationError, "Validation failed"),
        (EventExecutionError, "Execution failed"),
        (EventConnectionError, "Connection failed"),
        (EventShutdownError, "Shutdown failed"),
        (InvalidEventError, "Invalid event"),
    ],
)
def test_exceptions_can_be_instantiated_with_message(exception_class: Type[Exception], error_message: str) -> None:
    """Test all exceptions can be instantiated with error message."""
    # ACT
    error: Exception = exception_class(error_message)

    # ASSERT
    assert str(error) == error_message


# -------------------------------------------------------------
# TESTS: Exception Catching
# -------------------------------------------------------------


def test_all_event_exceptions_can_be_caught_as_exception() -> None:
    """Test all event exceptions can be caught as generic Exception."""
    # ARRANGE
    exceptions: list = [
        EventValidationError("test"),
        EventExecutionError("test"),
        EventConnectionError("test"),
        EventShutdownError("test"),
        NoHandlerAvailableError("test"),
        InvalidEventError("test"),
    ]

    # ACT & ASSERT
    for exc in exceptions:
        try:
            raise exc
        except Exception as caught:
            assert isinstance(caught, Exception)
