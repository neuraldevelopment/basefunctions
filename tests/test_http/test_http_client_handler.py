"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Pytest test suite for http_client_handler.
  Tests HTTP event handler functionality including request execution,
  error handling, and EventFactory registration.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import pytest
from typing import Any, Dict, Optional
from unittest.mock import Mock, MagicMock, patch

# Project imports (relative to project root)
import basefunctions

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_event() -> Mock:
    """
    Create mock Event object with configurable event_data.

    Returns
    -------
    Mock
        Mock Event object with event_id and event_data attributes

    Notes
    -----
    By default, event_data is an empty dict. Tests should configure
    event_data as needed using event.event_data = {...}
    """
    # ARRANGE
    event: Mock = Mock(spec=basefunctions.Event)
    event.event_id = "test_event_123"
    event.event_data = {}

    # RETURN
    return event


@pytest.fixture
def mock_event_context() -> Mock:
    """
    Create mock EventContext object.

    Returns
    -------
    Mock
        Mock EventContext object

    Notes
    -----
    Context is currently unused by HttpClientHandler.handle() but
    provided for completeness and future compatibility.
    """
    # ARRANGE
    context: Mock = Mock(spec=basefunctions.EventContext)

    # RETURN
    return context


@pytest.fixture
def handler_instance() -> basefunctions.HttpClientHandler:
    """
    Create actual HttpClientHandler instance for testing.

    Returns
    -------
    basefunctions.HttpClientHandler
        Actual handler instance (not mocked)

    Notes
    -----
    Uses real handler instance to test actual behavior.
    External dependencies (requests) are mocked in individual tests.
    """
    # ARRANGE & RETURN
    return basefunctions.HttpClientHandler()


@pytest.fixture
def mock_requests_response() -> Mock:
    """
    Create mock requests Response object with default success values.

    Returns
    -------
    Mock
        Mock Response object with status_code=200 and text="response_content"

    Notes
    -----
    Tests should customize status_code, text, or raise_for_status behavior
    as needed for specific test scenarios.
    """
    # ARRANGE
    response: Mock = Mock()
    response.status_code = 200
    response.text = "response_content"
    response.raise_for_status = Mock()  # No-op by default

    # RETURN
    return response


# -------------------------------------------------------------
# TEST CLASS ATTRIBUTES
# -------------------------------------------------------------


def test_handler_has_thread_execution_mode() -> None:
    """
    Test HttpClientHandler declares THREAD execution mode.

    Tests that handler specifies EXECUTION_MODE_THREAD as required
    for HTTP operations that should not block the main event loop.

    Notes
    -----
    Thread mode prevents blocking EventBus when making network calls.
    """
    # ASSERT
    assert basefunctions.HttpClientHandler.execution_mode == basefunctions.EXECUTION_MODE_THREAD


# -------------------------------------------------------------
# TEST CASES: HttpClientHandler.handle() - HAPPY PATH
# -------------------------------------------------------------


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_success_for_valid_get_request(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns success EventResult for valid GET request.

    Tests that handler correctly makes GET request and returns
    successful EventResult with response text content.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/data"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    assert result.data == "response_content"
    assert result.event_id == "test_event_123"
    mock_session.request.assert_called_once_with("GET", "https://api.example.com/data", timeout=25)


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_success_for_valid_post_request(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns success EventResult for valid POST request.

    Tests that handler correctly makes POST request when method
    is explicitly specified in event data.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/submit", "method": "POST"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    assert result.data == "response_content"
    mock_session.request.assert_called_once_with("POST", "https://api.example.com/submit", timeout=25)


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_uses_default_method_get_when_not_specified(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:
    """
    Test handle defaults to GET method when method not specified.

    Tests that handler uses GET as default HTTP method when
    event_data does not include a method field.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/default"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    mock_session.request.assert_called_once_with("GET", "https://api.example.com/default", timeout=25)


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_response_text_content(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:
    """
    Test handle returns response.text content, not response object.

    Tests that handler extracts and returns the text content from
    the HTTP response rather than the response object itself.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context

    Notes
    -----
    This verifies v1.2 change: return content instead of response object.
    """
    # ARRANGE
    response: Mock = Mock()
    response.text = "custom_response_text_12345"
    response.raise_for_status = Mock()
    mock_session.request.return_value = response
    mock_event.event_data = {"url": "https://api.example.com/text"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    assert result.data == "custom_response_text_12345"
    assert not isinstance(result.data, Mock)  # Ensure it's not the response object


# -------------------------------------------------------------
# TEST CASES: HttpClientHandler.handle() - ERROR HANDLING
# -------------------------------------------------------------


def test_handle_returns_failure_when_url_missing(
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure EventResult when URL missing from event_data.

    Tests that handler validates URL presence and returns business
    failure result with appropriate error message.

    Parameters
    ----------
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    mock_event.event_data = {}  # No URL

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert result.data == "Missing URL"
    assert result.event_id == "test_event_123"


def test_handle_returns_failure_when_url_empty(
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure EventResult when URL is empty string.

    Tests that handler validates URL is not empty and returns
    business failure result.

    Parameters
    ----------
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    mock_event.event_data = {"url": ""}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert result.data == "Missing URL"


def test_handle_returns_failure_when_url_none(
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure EventResult when URL is None.

    Tests that handler validates URL is not None and returns
    business failure result.

    Parameters
    ----------
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    mock_event.event_data = {"url": None}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert result.data == "Missing URL"


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_failure_when_request_exception_raised(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure when requests.RequestException raised.

    Tests that handler catches RequestException and returns business
    failure result with error message.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    import requests

    mock_session.request.side_effect = requests.exceptions.RequestException("Connection failed")
    mock_event.event_data = {"url": "https://api.example.com/error"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert "HTTP error: Connection failed" in result.data


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_failure_when_http_404_error(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure when HTTP 404 error occurs.

    Tests that handler catches HTTPError from raise_for_status()
    and returns business failure result.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    import requests

    response: Mock = Mock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_session.request.return_value = response
    mock_event.event_data = {"url": "https://api.example.com/notfound"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert "HTTP error: 404 Not Found" in result.data


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_failure_when_http_500_error(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure when HTTP 500 server error occurs.

    Tests that handler catches HTTPError for server errors
    and returns business failure result.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    import requests

    response: Mock = Mock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Internal Server Error")
    mock_session.request.return_value = response
    mock_event.event_data = {"url": "https://api.example.com/servererror"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert "HTTP error: 500 Internal Server Error" in result.data


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_failure_when_timeout_error(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns failure when request timeout occurs.

    Tests that handler catches Timeout exception and returns
    business failure result with timeout message.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    import requests

    mock_session.request.side_effect = requests.exceptions.Timeout("Request timed out after 30 seconds")
    mock_event.event_data = {"url": "https://api.example.com/slow"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert "HTTP error: Request timed out" in result.data


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_returns_exception_result_when_unexpected_error(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle returns exception EventResult for unexpected errors.

    Tests that handler catches unexpected exceptions (non-RequestException)
    and returns exception result instead of business failure.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    mock_session.request.side_effect = ValueError("Unexpected internal error")
    mock_event.event_data = {"url": "https://api.example.com/data"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    # Exception results store the exception object in exception attribute, data is None
    assert result.data is None
    assert isinstance(result.exception, ValueError)
    assert "Unexpected internal error" in str(result.exception)


# -------------------------------------------------------------
# TEST CASES: HttpClientHandler.handle() - EDGE CASES
# -------------------------------------------------------------


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_normalizes_method_to_uppercase(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:
    """
    Test handle normalizes HTTP method to uppercase.

    Tests that handler converts lowercase method names to uppercase
    before making the request (e.g., "post" -> "POST").

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/data", "method": "post"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    mock_session.request.assert_called_once_with("POST", "https://api.example.com/data", timeout=25)


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_sets_timeout_to_25_seconds(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:
    """
    Test handle sets request timeout to 25 seconds.

    Tests that handler always includes timeout=25 parameter
    in requests to prevent indefinite hanging.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/data"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    # Verify timeout parameter was passed
    call_args = mock_session.request.call_args
    assert call_args.kwargs["timeout"] == 25


@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_raises_for_status_on_response(
    mock_session: Mock,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:
    """
    Test handle calls raise_for_status to check HTTP status codes.

    Tests that handler invokes response.raise_for_status() to
    automatically raise exceptions for 4xx/5xx status codes.

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/data"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    mock_requests_response.raise_for_status.assert_called_once()


# -------------------------------------------------------------
# TEST CASES: HttpClientHandler.handle() - PARAMETRIZED
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "method",
    [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
    ],
)
@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_various_http_methods(
    mock_session: Mock,
    method: str,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
    mock_requests_response: Mock,
) -> None:
    """
    Test handle supports various HTTP methods.

    Tests that handler correctly processes different HTTP method types
    (GET, POST, PUT, DELETE, PATCH).

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    method : str
        HTTP method to test
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    mock_requests_response : Mock
        Mock HTTP response object
    """
    # ARRANGE
    mock_session.request.return_value = mock_requests_response
    mock_event.event_data = {"url": "https://api.example.com/data", "method": method}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is True
    mock_session.request.assert_called_once_with(method, "https://api.example.com/data", timeout=25)


@pytest.mark.parametrize(
    "exception_class,error_message",
    [
        (
            "requests.exceptions.ConnectionError",
            "Connection refused",
        ),
        (
            "requests.exceptions.Timeout",
            "Request timed out",
        ),
        (
            "requests.exceptions.TooManyRedirects",
            "Too many redirects",
        ),
        (
            "requests.exceptions.HTTPError",
            "404 Client Error",
        ),
    ],
)
@patch("basefunctions.http.http_client_handler._SESSION")
def test_handle_various_error_scenarios(
    mock_session: Mock,
    exception_class: str,
    error_message: str,
    handler_instance: basefunctions.HttpClientHandler,
    mock_event: Mock,
    mock_event_context: Mock,
) -> None:  # CRITICAL TEST
    """
    Test handle gracefully handles various request exceptions.

    Tests that handler catches and properly handles different types
    of requests exceptions (ConnectionError, Timeout, HTTPError, etc.).

    Parameters
    ----------
    mock_session : Mock
        Mocked Session object
    exception_class : str
        Full exception class path to test
    error_message : str
        Error message for the exception
    handler_instance : HttpClientHandler
        Handler instance under test
    mock_event : Mock
        Mock event with test data
    mock_event_context : Mock
        Mock event context
    """
    # ARRANGE
    import requests

    # Dynamically get exception class from string path
    exc_parts = exception_class.split(".")
    exc_module = requests.exceptions
    exception_type = getattr(exc_module, exc_parts[-1])

    mock_session.request.side_effect = exception_type(error_message)
    mock_event.event_data = {"url": "https://api.example.com/error"}

    # ACT
    result: basefunctions.EventResult = handler_instance.handle(mock_event, mock_event_context)

    # ASSERT
    assert result.success is False
    assert "HTTP error:" in result.data
    assert error_message in result.data


# -------------------------------------------------------------
# TEST CASES: register_http_handlers()
# -------------------------------------------------------------


@patch("basefunctions.EventFactory")
def test_register_http_handlers_registers_event_type(mock_factory_class: Mock) -> None:  # IMPORTANT TEST
    """
    Test register_http_handlers registers http_request event type.

    Tests that registration function creates EventFactory instance
    and registers HttpClientHandler for "http_request" event type.

    Parameters
    ----------
    mock_factory_class : Mock
        Mocked EventFactory class
    """
    # ARRANGE
    mock_factory_instance: Mock = Mock()
    mock_factory_class.return_value = mock_factory_instance

    # ACT
    basefunctions.register_http_handlers()

    # ASSERT
    mock_factory_class.assert_called_once()
    mock_factory_instance.register_event_type.assert_called_once_with("http_request", basefunctions.HttpClientHandler)


@patch("basefunctions.EventFactory")
def test_register_http_handlers_uses_correct_handler_class(mock_factory_class: Mock) -> None:  # IMPORTANT TEST
    """
    Test register_http_handlers uses HttpClientHandler class.

    Tests that registration function passes the correct handler class
    (not an instance) to EventFactory.register_event_type().

    Parameters
    ----------
    mock_factory_class : Mock
        Mocked EventFactory class
    """
    # ARRANGE
    mock_factory_instance: Mock = Mock()
    mock_factory_class.return_value = mock_factory_instance

    # ACT
    basefunctions.register_http_handlers()

    # ASSERT
    call_args = mock_factory_instance.register_event_type.call_args
    assert call_args[0][0] == "http_request"
    assert call_args[0][1] == basefunctions.HttpClientHandler
    # Ensure it's the class, not an instance
    assert isinstance(call_args[0][1], type)
