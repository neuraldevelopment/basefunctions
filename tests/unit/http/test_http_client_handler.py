"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Comprehensive tests for HttpClientHandler with >80% coverage

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from unittest.mock import Mock, patch, MagicMock

# Third-party
import pytest
import requests

# Project modules
from basefunctions.http.http_client_handler import HttpClientHandler, register_http_handlers
import basefunctions


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_event():
    """Provide mock Event with URL."""
    event = Mock(spec=basefunctions.Event)
    event.event_id = "test-123"
    event.event_data = {"url": "https://api.example.com/data", "method": "GET"}
    return event


@pytest.fixture
def mock_context():
    """Provide mock EventContext."""
    return Mock(spec=basefunctions.EventContext)


@pytest.fixture
def handler():
    """Provide HttpClientHandler instance."""
    return HttpClientHandler()


@pytest.fixture
def mock_response():
    """Provide mock Response object."""
    response = Mock(spec=requests.Response)
    response.text = '{"result": "success"}'
    response.status_code = 200
    response.raise_for_status = Mock()
    return response


# =============================================================================
# SUCCESS CASES
# =============================================================================


def test_handle_with_get_request_returns_response_content(handler, mock_event, mock_response):
    """Test GET request returns response content."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        assert result.data == '{"result": "success"}'
        assert result.event_id == "test-123"
        mock_session.request.assert_called_once_with("GET", "https://api.example.com/data", timeout=25)


def test_handle_with_post_request_uses_method_parameter(handler, mock_event, mock_response):
    """Test POST request with method parameter."""
    # Arrange
    mock_event.event_data = {"url": "https://api.example.com/submit", "method": "POST"}

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        mock_session.request.assert_called_once_with("POST", "https://api.example.com/submit", timeout=25)


def test_handle_with_https_request_works_correctly(handler, mock_event, mock_response):
    """Test HTTPS request works correctly (verify pooling for https)."""
    # Arrange
    mock_event.event_data = {"url": "https://secure.example.com/api", "method": "GET"}

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        assert result.data == '{"result": "success"}'
        mock_session.request.assert_called_once_with("GET", "https://secure.example.com/api", timeout=25)


def test_handle_with_http_request_works_correctly(handler, mock_event, mock_response):
    """Test HTTP request works correctly (verify pooling for http)."""
    # Arrange
    mock_event.event_data = {"url": "http://api.example.com/data", "method": "GET"}

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        mock_session.request.assert_called_once_with("GET", "http://api.example.com/data", timeout=25)


def test_handle_with_context_none_works_correctly(handler, mock_event, mock_response):
    """Test context parameter None works correctly."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event, context=None)

        # Assert
        assert result.success is True
        assert result.data == '{"result": "success"}'


def test_handle_with_context_not_none_works_correctly(handler, mock_event, mock_context, mock_response):
    """Test context parameter not None works correctly."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event, context=mock_context)

        # Assert
        assert result.success is True
        assert result.data == '{"result": "success"}'


def test_handle_with_default_method_uses_get(handler, mock_event, mock_response):
    """Test default method is GET when not specified."""
    # Arrange
    mock_event.event_data = {"url": "https://api.example.com/data"}  # No method

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        mock_session.request.assert_called_once_with("GET", "https://api.example.com/data", timeout=25)


def test_handle_with_lowercase_method_converts_to_uppercase(handler, mock_event, mock_response):
    """Test lowercase method is converted to uppercase."""
    # Arrange
    mock_event.event_data = {"url": "https://api.example.com/data", "method": "post"}

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        mock_session.request.assert_called_once_with("POST", "https://api.example.com/data", timeout=25)


# =============================================================================
# ERROR CASES
# =============================================================================


def test_handle_with_missing_url_returns_business_result_false(handler, mock_event):
    """Test missing URL in event_data returns business_result with False."""
    # Arrange
    mock_event.event_data = {}  # No URL

    # Act
    result = handler.handle(mock_event)

    # Assert
    assert result.success is False
    assert result.data == "Missing URL"
    assert result.event_id == "test-123"


def test_handle_with_empty_url_string_returns_business_result_false(handler, mock_event):
    """Test empty URL string returns False result."""
    # Arrange
    mock_event.event_data = {"url": ""}  # Empty string

    # Act
    result = handler.handle(mock_event)

    # Assert
    assert result.success is False
    assert result.data == "Missing URL"


def test_handle_with_none_url_returns_business_result_false(handler, mock_event):
    """Test None URL returns False result."""
    # Arrange
    mock_event.event_data = {"url": None}

    # Act
    result = handler.handle(mock_event)

    # Assert
    assert result.success is False
    assert result.data == "Missing URL"


def test_handle_with_connection_timeout_returns_http_error(handler, mock_event):
    """Test network error (connection timeout) returns HTTP error message."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.side_effect = requests.exceptions.Timeout("Connection timeout")

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is False
        assert "HTTP error: Connection timeout" in result.data


def test_handle_with_connection_error_returns_http_error(handler, mock_event):
    """Test connection error returns HTTP error message."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is False
        assert "HTTP error: Failed to connect" in result.data


def test_handle_with_http_error_returns_http_error_message(handler, mock_event):
    """Test HTTPError (non-200 status) returns HTTP error."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is False
        assert "HTTP error: 404 Not Found" in result.data


def test_handle_with_non_200_status_code_raises_for_status(handler, mock_event):
    """Test non-200 status codes trigger raise_for_status."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is False
        assert "HTTP error: 500 Server Error" in result.data
        mock_response.raise_for_status.assert_called_once()


def test_handle_with_unexpected_exception_returns_exception_result(handler, mock_event):
    """Test unexpected exceptions return exception_result."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        test_exception = ValueError("Unexpected error")
        mock_session.request.side_effect = test_exception

        # Act
        result = handler.handle(mock_event)

        # Assert
        # EventResult.exception_result sets success to False
        assert result.success is False
        # exception_result stores the exception in exception field
        assert result.exception is not None
        assert "Unexpected error" in str(result.exception)


# =============================================================================
# EDGE CASES
# =============================================================================


def test_handle_with_very_large_response_captures_content_correctly(handler, mock_event):
    """Test very large response text is captured correctly."""
    # Arrange
    large_text = "x" * 100000  # 100KB response
    mock_response = Mock()
    mock_response.text = large_text
    mock_response.raise_for_status = Mock()

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        assert result.data == large_text
        assert len(result.data) == 100000


def test_handle_with_invalid_http_method_passes_to_requests(handler, mock_event):
    """Test invalid HTTP method is passed to requests (requests handles validation)."""
    # Arrange
    mock_event.event_data = {"url": "https://api.example.com/data", "method": "INVALID"}

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.side_effect = requests.exceptions.RequestException("Invalid method")

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is False
        assert "HTTP error: Invalid method" in result.data
        # Verify the invalid method was passed to requests
        mock_session.request.assert_called_once_with("INVALID", "https://api.example.com/data", timeout=25)


def test_handle_with_special_characters_in_url_works_correctly(handler, mock_event, mock_response):
    """Test URL with special characters works correctly."""
    # Arrange
    special_url = "https://api.example.com/search?q=test%20query&filter=active"
    mock_event.event_data = {"url": special_url}

    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        result = handler.handle(mock_event)

        # Assert
        assert result.success is True
        mock_session.request.assert_called_once_with("GET", special_url, timeout=25)


# =============================================================================
# PERFORMANCE / POOLING VERIFICATION
# =============================================================================


def test_session_singleton_uses_http_adapter_for_http_protocol():
    """Test Session singleton mounts HTTPAdapter for http://."""
    # Arrange
    from basefunctions.http.http_client_handler import _SESSION, _ADAPTER

    # Act
    http_adapter = _SESSION.get_adapter("http://example.com")

    # Assert
    assert http_adapter is _ADAPTER


def test_session_singleton_uses_http_adapter_for_https_protocol():
    """Test Session singleton mounts HTTPAdapter for https://."""
    # Arrange
    from basefunctions.http.http_client_handler import _SESSION, _ADAPTER

    # Act
    https_adapter = _SESSION.get_adapter("https://example.com")

    # Assert
    assert https_adapter is _ADAPTER


def test_http_adapter_pool_sizes_are_correct():
    """Test pool size constants are configured correctly (100, 100)."""
    # Arrange
    from basefunctions.http.http_client_handler import _POOL_CONNECTIONS, _POOL_MAXSIZE

    # Assert
    # Verify pool configuration constants are set to expected values
    assert _POOL_CONNECTIONS == 100
    assert _POOL_MAXSIZE == 100


def test_handler_uses_session_singleton_not_new_session(handler, mock_event, mock_response):
    """Test handler uses _SESSION singleton, not creating new Session."""
    # Arrange
    with patch("basefunctions.http.http_client_handler._SESSION") as mock_session:
        mock_session.request.return_value = mock_response

        # Act
        handler.handle(mock_event)
        handler.handle(mock_event)  # Call twice

        # Assert
        # Should reuse same session (called twice on same mock)
        assert mock_session.request.call_count == 2


# =============================================================================
# HANDLER CONFIGURATION
# =============================================================================


def test_handler_has_correct_execution_mode():
    """Test handler has EXECUTION_MODE_THREAD."""
    # Arrange
    handler = HttpClientHandler()

    # Assert
    assert handler.execution_mode == basefunctions.EXECUTION_MODE_THREAD


# =============================================================================
# REGISTRATION FUNCTION
# =============================================================================


def test_register_http_handlers_registers_with_event_factory():
    """Test register_http_handlers registers handler with EventFactory."""
    # Arrange
    with patch("basefunctions.EventFactory") as mock_factory_class:
        mock_factory_instance = Mock()
        mock_factory_class.return_value = mock_factory_instance

        # Act
        register_http_handlers()

        # Assert
        mock_factory_class.assert_called_once()
        mock_factory_instance.register_event_type.assert_called_once_with(
            "http_request", HttpClientHandler
        )


def test_register_http_handlers_uses_correct_event_type_name():
    """Test register_http_handlers uses 'http_request' as event type."""
    # Arrange
    with patch("basefunctions.EventFactory") as mock_factory_class:
        mock_factory_instance = Mock()
        mock_factory_class.return_value = mock_factory_instance

        # Act
        register_http_handlers()

        # Assert
        call_args = mock_factory_instance.register_event_type.call_args[0]
        assert call_args[0] == "http_request"
        assert call_args[1] == HttpClientHandler
