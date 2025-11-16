"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.

  Description:
  Pytest test suite for http_client module.
  Tests HttpClient class for HTTP request handling with EventBus integration.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard library imports
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import Mock, patch, MagicMock

# External imports
import pytest

# Project imports
from basefunctions.http.http_client import HttpClient

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_event() -> Mock:
    """
    Create mock Event object.

    Returns
    -------
    Mock
        Mock Event with event_id attribute

    Notes
    -----
    Simulates basefunctions.Event with unique event_id
    """
    # ARRANGE
    event: Mock = Mock()
    event.event_id = "test-event-id-123"
    event.event_type = "http_request"
    event.event_data = {"method": "GET", "url": "https://example.com"}

    # RETURN
    return event


@pytest.fixture
def mock_event_bus() -> Mock:
    """
    Create mock EventBus singleton.

    Returns
    -------
    Mock
        Mock EventBus with publish, join, get_results methods

    Notes
    -----
    Mocks all EventBus methods needed by HttpClient
    """
    # ARRANGE
    event_bus: Mock = Mock()
    event_bus.publish = Mock()
    event_bus.join = Mock()
    event_bus.get_results = Mock(return_value={})

    # RETURN
    return event_bus


@pytest.fixture
def mock_event_result_success() -> Mock:
    """
    Create mock successful event result.

    Returns
    -------
    Mock
        Mock result with success=True and data

    Notes
    -----
    Simulates successful HTTP response
    """
    # ARRANGE
    result: Mock = Mock()
    result.success = True
    result.data = {"status": "ok", "content": "response data"}
    result.exception = None

    # RETURN
    return result


@pytest.fixture
def mock_event_result_failure() -> Mock:
    """
    Create mock failed event result.

    Returns
    -------
    Mock
        Mock result with success=False and exception

    Notes
    -----
    Simulates failed HTTP response with exception
    """
    # ARRANGE
    result: Mock = Mock()
    result.success = False
    result.data = None
    result.exception = RuntimeError("Connection timeout")

    # RETURN
    return result


@pytest.fixture
def sample_url() -> str:
    """
    Provide valid test URL.

    Returns
    -------
    str
        Valid HTTPS URL for testing

    Notes
    -----
    Uses example.com domain reserved for testing
    """
    # RETURN
    return "https://example.com/api/test"


@pytest.fixture
def http_client_with_mocks(
    monkeypatch: pytest.MonkeyPatch, mock_event_bus: Mock, mock_event: Mock
) -> Generator[HttpClient, None, None]:
    """
    Create HttpClient instance with mocked dependencies.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event

    Yields
    ------
    HttpClient
        HttpClient instance with mocked EventBus and Event

    Notes
    -----
    Patches basefunctions.EventBus and basefunctions.Event
    """
    # ARRANGE
    with patch("basefunctions.EventBus", return_value=mock_event_bus):
        with patch("basefunctions.Event", return_value=mock_event):
            client: HttpClient = HttpClient()

            # YIELD
            yield client


# -------------------------------------------------------------
# TEST CASES - __init__
# -------------------------------------------------------------


def test_init_creates_instance_successfully() -> None:  # IMPORTANT TEST
    """
    Test __init__ creates HttpClient instance successfully.

    Tests that HttpClient can be instantiated without errors.

    Returns
    -------
    None
        Test passes if instance is created
    """
    # ARRANGE & ACT
    with patch("basefunctions.EventBus"):
        client: HttpClient = HttpClient()

    # ASSERT
    assert isinstance(client, HttpClient)


def test_init_initializes_event_bus(mock_event_bus: Mock) -> None:  # IMPORTANT TEST
    """
    Test __init__ initializes EventBus correctly.

    Tests that HttpClient creates EventBus instance on initialization.

    Parameters
    ----------
    mock_event_bus : Mock
        Mocked EventBus fixture

    Returns
    -------
    None
        Test passes if EventBus is initialized
    """
    # ARRANGE & ACT
    with patch("basefunctions.EventBus", return_value=mock_event_bus) as mock_bus_class:
        client: HttpClient = HttpClient()

    # ASSERT
    mock_bus_class.assert_called_once()
    assert client.event_bus is mock_event_bus


def test_init_initializes_empty_pending_list() -> None:  # IMPORTANT TEST
    """
    Test __init__ initializes empty pending event IDs list.

    Tests that _pending_event_ids is initialized as empty list.

    Returns
    -------
    None
        Test passes if pending list is empty
    """
    # ARRANGE & ACT
    with patch("basefunctions.EventBus"):
        client: HttpClient = HttpClient()

    # ASSERT
    assert client._pending_event_ids == []
    assert isinstance(client._pending_event_ids, list)


# -------------------------------------------------------------
# TEST CASES - get_sync
# -------------------------------------------------------------


def test_get_sync_returns_data_when_successful(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event: Mock,
    mock_event_result_success: Mock,
    sample_url: str,
) -> None:  # CRITICAL TEST
    """
    Test get_sync returns data when request is successful.

    Tests that get_sync correctly returns response data from successful HTTP request.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if correct data is returned
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    result: Any = http_client_with_mocks.get_sync(sample_url)

    # ASSERT
    assert result == mock_event_result_success.data
    assert result["status"] == "ok"


def test_get_sync_publishes_event_correctly(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event: Mock,
    mock_event_result_success: Mock,
    sample_url: str,
) -> None:  # CRITICAL TEST
    """
    Test get_sync publishes event with correct parameters.

    Tests that Event is created with correct method and URL.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if event is published correctly
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    with patch("basefunctions.Event", return_value=mock_event) as mock_event_class:
        http_client_with_mocks.get_sync(sample_url)

        # ASSERT
        mock_event_class.assert_called_once()
        call_kwargs: Dict[str, Any] = mock_event_class.call_args.kwargs
        assert call_kwargs["event_type"] == "http_request"
        assert call_kwargs["event_data"]["method"] == "GET"
        assert call_kwargs["event_data"]["url"] == sample_url


def test_get_sync_waits_for_event_with_join(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event: Mock,
    mock_event_result_success: Mock,
    sample_url: str,
) -> None:  # CRITICAL TEST
    """
    Test get_sync calls join to wait for event completion.

    Tests that get_sync synchronously waits for event processing.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if join is called
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    http_client_with_mocks.get_sync(sample_url)

    # ASSERT
    mock_event_bus.join.assert_called_once()


def test_get_sync_raises_runtime_error_when_no_response(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_sync raises RuntimeError when no response received.

    Tests that empty results dict triggers error.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {}

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="No response received for event"):
        http_client_with_mocks.get_sync(sample_url)


def test_get_sync_raises_runtime_error_when_result_not_success(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event: Mock,
    mock_event_result_failure: Mock,
    sample_url: str,
) -> None:  # CRITICAL TEST
    """
    Test get_sync raises RuntimeError when result indicates failure.

    Tests that success=False triggers error with exception message.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_failure : Mock
        Mocked failed result
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if RuntimeError is raised
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_failure}

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Connection timeout"):
        http_client_with_mocks.get_sync(sample_url)


def test_get_sync_raises_runtime_error_with_data_message(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_sync raises RuntimeError with data message when no exception.

    Tests error handling when result has data but no exception.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if RuntimeError with data message is raised
    """
    # ARRANGE
    result: Mock = Mock()
    result.success = False
    result.exception = None
    result.data = "Custom error message"

    mock_event_bus.get_results.return_value = {mock_event.event_id: result}

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Custom error message"):
        http_client_with_mocks.get_sync(sample_url)


def test_get_sync_raises_runtime_error_with_default_message(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_sync raises RuntimeError with default message.

    Tests error handling when result has neither exception nor data.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if RuntimeError with default message is raised
    """
    # ARRANGE
    result: Mock = Mock()
    result.success = False
    result.exception = None
    result.data = None

    mock_event_bus.get_results.return_value = {mock_event.event_id: result}

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match=f"HTTP request failed for URL: {sample_url}"):
        http_client_with_mocks.get_sync(sample_url)


def test_get_sync_passes_kwargs_to_event_data(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event: Mock,
    mock_event_result_success: Mock,
    sample_url: str,
) -> None:  # CRITICAL TEST
    """
    Test get_sync passes additional kwargs to event_data.

    Tests that extra parameters are included in event data.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if kwargs are passed correctly
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    with patch("basefunctions.Event", return_value=mock_event) as mock_event_class:
        http_client_with_mocks.get_sync(sample_url, headers={"Authorization": "Bearer token"}, timeout=30)

        # ASSERT
        call_kwargs: Dict[str, Any] = mock_event_class.call_args.kwargs
        assert call_kwargs["event_data"]["headers"] == {"Authorization": "Bearer token"}
        assert call_kwargs["event_data"]["timeout"] == 30


# -------------------------------------------------------------
# TEST CASES - get_async
# -------------------------------------------------------------


def test_get_async_returns_event_id(
    http_client_with_mocks: HttpClient, mock_event: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_async returns event ID.

    Tests that get_async returns event_id for tracking.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event : Mock
        Mocked Event
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if event_id is returned
    """
    # ACT
    result: str = http_client_with_mocks.get_async(sample_url)

    # ASSERT
    assert result == mock_event.event_id
    assert isinstance(result, str)


def test_get_async_publishes_event_without_join(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_async publishes event without waiting.

    Tests that get_async does not call join (async behavior).

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if event published without join
    """
    # ACT
    http_client_with_mocks.get_async(sample_url)

    # ASSERT
    mock_event_bus.publish.assert_called_once_with(mock_event)
    mock_event_bus.join.assert_not_called()


def test_get_async_adds_event_id_to_pending_list(
    http_client_with_mocks: HttpClient, mock_event: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_async adds event_id to pending list.

    Tests that event_id is tracked in _pending_event_ids.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event : Mock
        Mocked Event
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if event_id is added to pending list
    """
    # ARRANGE
    assert len(http_client_with_mocks._pending_event_ids) == 0

    # ACT
    event_id: str = http_client_with_mocks.get_async(sample_url)

    # ASSERT
    assert event_id in http_client_with_mocks._pending_event_ids
    assert len(http_client_with_mocks._pending_event_ids) == 1


def test_get_async_appends_multiple_event_ids_correctly(
    mock_event_bus: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_async appends multiple event IDs correctly.

    Tests that multiple async calls accumulate event IDs.

    Parameters
    ----------
    mock_event_bus : Mock
        Mocked EventBus
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if all event IDs are tracked
    """
    # ARRANGE
    with patch("basefunctions.EventBus", return_value=mock_event_bus):
        client: HttpClient = HttpClient()

        event_ids: List[str] = []
        for i in range(3):
            mock_event: Mock = Mock()
            mock_event.event_id = f"event-id-{i}"

            # ACT
            with patch("basefunctions.Event", return_value=mock_event):
                event_id: str = client.get_async(f"{sample_url}/{i}")
                event_ids.append(event_id)

    # ASSERT
    assert len(client._pending_event_ids) == 3
    for event_id in event_ids:
        assert event_id in client._pending_event_ids


def test_get_async_passes_kwargs_to_event_data(
    http_client_with_mocks: HttpClient, mock_event: Mock, sample_url: str
) -> None:  # CRITICAL TEST
    """
    Test get_async passes additional kwargs to event_data.

    Tests that extra parameters are included in event data.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event : Mock
        Mocked Event
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if kwargs are passed correctly
    """
    # ACT
    with patch("basefunctions.Event", return_value=mock_event) as mock_event_class:
        http_client_with_mocks.get_async(sample_url, params={"key": "value"}, verify=False)

        # ASSERT
        call_kwargs: Dict[str, Any] = mock_event_class.call_args.kwargs
        assert call_kwargs["event_data"]["params"] == {"key": "value"}
        assert call_kwargs["event_data"]["verify"] is False


# -------------------------------------------------------------
# TEST CASES - get_pending_ids
# -------------------------------------------------------------


def test_get_pending_ids_returns_copy_of_list(
    http_client_with_mocks: HttpClient, sample_url: str
) -> None:  # IMPORTANT TEST
    """
    Test get_pending_ids returns copy of pending list.

    Tests that returned list is independent copy, not reference.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if returned list is copy
    """
    # ARRANGE
    http_client_with_mocks.get_async(sample_url)

    # ACT
    pending_ids: List[str] = http_client_with_mocks.get_pending_ids()
    pending_ids.append("manually-added-id")

    # ASSERT
    assert "manually-added-id" not in http_client_with_mocks._pending_event_ids
    assert len(http_client_with_mocks._pending_event_ids) == 1


def test_get_pending_ids_returns_empty_list_initially() -> None:  # IMPORTANT TEST
    """
    Test get_pending_ids returns empty list initially.

    Tests that new HttpClient has no pending IDs.

    Returns
    -------
    None
        Test passes if empty list is returned
    """
    # ARRANGE & ACT
    with patch("basefunctions.EventBus"):
        client: HttpClient = HttpClient()
        pending_ids: List[str] = client.get_pending_ids()

    # ASSERT
    assert pending_ids == []
    assert isinstance(pending_ids, list)


# -------------------------------------------------------------
# TEST CASES - set_pending_ids
# -------------------------------------------------------------


def test_set_pending_ids_updates_internal_list(http_client_with_mocks: HttpClient) -> None:  # IMPORTANT TEST
    """
    Test set_pending_ids updates internal pending list.

    Tests that new list replaces existing pending IDs.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies

    Returns
    -------
    None
        Test passes if internal list is updated
    """
    # ARRANGE
    new_ids: List[str] = ["id-1", "id-2", "id-3"]

    # ACT
    http_client_with_mocks.set_pending_ids(new_ids)

    # ASSERT
    assert http_client_with_mocks._pending_event_ids == new_ids


def test_set_pending_ids_stores_copy_not_reference(http_client_with_mocks: HttpClient) -> None:  # IMPORTANT TEST
    """
    Test set_pending_ids stores copy, not reference.

    Tests that modifying original list doesn't affect internal state.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies

    Returns
    -------
    None
        Test passes if internal list is independent
    """
    # ARRANGE
    original_ids: List[str] = ["id-1", "id-2"]

    # ACT
    http_client_with_mocks.set_pending_ids(original_ids)
    original_ids.append("id-3")

    # ASSERT
    assert "id-3" not in http_client_with_mocks._pending_event_ids
    assert len(http_client_with_mocks._pending_event_ids) == 2


def test_set_pending_ids_handles_empty_list(
    http_client_with_mocks: HttpClient, sample_url: str
) -> None:  # IMPORTANT TEST
    """
    Test set_pending_ids handles empty list correctly.

    Tests that empty list clears pending IDs.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if pending list is cleared
    """
    # ARRANGE
    http_client_with_mocks.get_async(sample_url)
    assert len(http_client_with_mocks._pending_event_ids) == 1

    # ACT
    http_client_with_mocks.set_pending_ids([])

    # ASSERT
    assert http_client_with_mocks._pending_event_ids == []


def test_set_pending_ids_replaces_existing_list(
    http_client_with_mocks: HttpClient, sample_url: str
) -> None:  # IMPORTANT TEST
    """
    Test set_pending_ids replaces existing list completely.

    Tests that new list overwrites all previous IDs.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    sample_url : str
        Test URL

    Returns
    -------
    None
        Test passes if list is completely replaced
    """
    # ARRANGE
    http_client_with_mocks.get_async(sample_url)
    old_id: str = http_client_with_mocks._pending_event_ids[0]

    # ACT
    http_client_with_mocks.set_pending_ids(["new-id-1", "new-id-2"])

    # ASSERT
    assert old_id not in http_client_with_mocks._pending_event_ids
    assert "new-id-1" in http_client_with_mocks._pending_event_ids
    assert "new-id-2" in http_client_with_mocks._pending_event_ids


# -------------------------------------------------------------
# TEST CASES - get_results
# -------------------------------------------------------------


def test_get_results_returns_structured_response(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results returns structured response dictionary.

    Tests that response contains data, metadata, and errors sections.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if structure is correct
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id]
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert "data" in result
    assert "metadata" in result
    assert "errors" in result
    assert isinstance(result["data"], dict)
    assert isinstance(result["metadata"], dict)
    assert isinstance(result["errors"], dict)


def test_get_results_uses_pending_ids_when_none_provided(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results uses pending IDs when none provided.

    Tests that event_ids=None fetches all pending events.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if pending IDs are used
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id, "other-id"]
    mock_event_bus.get_results.return_value = {
        mock_event.event_id: mock_event_result_success,
        "other-id": mock_event_result_success,
    }

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert len(result["data"]) == 2
    assert mock_event.event_id in result["data"]
    assert "other-id" in result["data"]


def test_get_results_uses_provided_event_ids(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results uses provided event_ids parameter.

    Tests that specific event_ids are fetched instead of pending list.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if provided IDs are used
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = ["pending-1", "pending-2"]
    specific_id: str = "specific-id"
    mock_event_bus.get_results.return_value = {specific_id: mock_event_result_success}

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results(event_ids=[specific_id])

    # ASSERT
    assert len(result["data"]) == 1
    assert specific_id in result["data"]
    assert "pending-1" not in result["data"]


def test_get_results_removes_fetched_ids_from_pending(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results removes fetched IDs from pending list.

    Tests that successfully fetched event IDs are removed from tracking.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if IDs are removed
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id, "other-id"]
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    http_client_with_mocks.get_results(event_ids=[mock_event.event_id])

    # ASSERT
    assert mock_event.event_id not in http_client_with_mocks._pending_event_ids
    assert "other-id" in http_client_with_mocks._pending_event_ids


def test_get_results_calls_join_before_when_true(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results calls EventBus.get_results with join_before=True.

    Tests that join_before parameter is passed correctly.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if join_before is passed
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id]
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    http_client_with_mocks.get_results(join_before=True)

    # ASSERT
    mock_event_bus.get_results.assert_called_once_with(event_ids=[mock_event.event_id], join_before=True)


def test_get_results_does_not_call_join_when_false(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results respects join_before=False.

    Tests that join_before=False is passed to EventBus.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if join_before=False is passed
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id]
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT
    http_client_with_mocks.get_results(join_before=False)

    # ASSERT
    mock_event_bus.get_results.assert_called_once_with(event_ids=[mock_event.event_id], join_before=False)


def test_get_results_returns_empty_structure_when_no_ids(http_client_with_mocks: HttpClient) -> None:  # CRITICAL TEST
    """
    Test get_results returns empty structure when no IDs to fetch.

    Tests that empty pending list returns valid empty structure.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies

    Returns
    -------
    None
        Test passes if empty structure is returned
    """
    # ARRANGE
    assert len(http_client_with_mocks._pending_event_ids) == 0

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert result["data"] == {}
    assert result["errors"] == {}
    assert result["metadata"]["total_requested"] == 0
    assert result["metadata"]["successful"] == 0
    assert result["metadata"]["failed"] == 0


def test_get_results_handles_empty_event_ids_list(http_client_with_mocks: HttpClient) -> None:  # CRITICAL TEST
    """
    Test get_results handles empty event_ids list parameter.

    Tests that explicitly passing empty list returns empty structure.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies

    Returns
    -------
    None
        Test passes if empty structure is returned
    """
    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results(event_ids=[])

    # ASSERT
    assert result["data"] == {}
    assert result["metadata"]["total_requested"] == 0


def test_get_results_handles_failed_events_with_exception(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock, mock_event_result_failure: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results handles failed events with exception.

    Tests that exceptions are captured in errors section.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_failure : Mock
        Mocked failed result

    Returns
    -------
    None
        Test passes if exception is in errors
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id]
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_failure}

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert mock_event.event_id in result["errors"]
    assert "Connection timeout" in result["errors"][mock_event.event_id]
    assert mock_event.event_id not in result["data"]


def test_get_results_handles_failed_events_with_data(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results handles failed events with data but no exception.

    Tests that data is used as error message when exception is None.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event

    Returns
    -------
    None
        Test passes if data is in errors
    """
    # ARRANGE
    result: Mock = Mock()
    result.success = False
    result.exception = None
    result.data = "Error data message"

    http_client_with_mocks._pending_event_ids = [mock_event.event_id]
    mock_event_bus.get_results.return_value = {mock_event.event_id: result}

    # ACT
    response: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert mock_event.event_id in response["errors"]
    assert "Error data message" in response["errors"][mock_event.event_id]


def test_get_results_handles_failed_events_with_no_result(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results handles failed events with no result.

    Tests that missing result triggers default error message.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event

    Returns
    -------
    None
        Test passes if default error is used
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = [mock_event.event_id]
    mock_event_bus.get_results.return_value = {}

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert mock_event.event_id in result["errors"]
    assert "No result received" in result["errors"][mock_event.event_id]


def test_get_results_handles_mixed_success_and_failure(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event_result_success: Mock,
    mock_event_result_failure: Mock,
) -> None:  # CRITICAL TEST
    """
    Test get_results handles mixed success and failure events.

    Tests that successes and failures are correctly categorized.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event_result_success : Mock
        Mocked successful result
    mock_event_result_failure : Mock
        Mocked failed result

    Returns
    -------
    None
        Test passes if both are handled correctly
    """
    # ARRANGE
    success_id: str = "success-id"
    failure_id: str = "failure-id"

    http_client_with_mocks._pending_event_ids = [success_id, failure_id]
    mock_event_bus.get_results.return_value = {
        success_id: mock_event_result_success,
        failure_id: mock_event_result_failure,
    }

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert success_id in result["data"]
    assert failure_id in result["errors"]
    assert result["metadata"]["successful"] == 1
    assert result["metadata"]["failed"] == 1
    assert result["metadata"]["total_requested"] == 2


def test_get_results_includes_timestamp_in_metadata(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results includes timestamp in metadata.

    Tests that timestamp is ISO format string.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus

    Returns
    -------
    None
        Test passes if timestamp is present and valid
    """
    # ARRANGE
    http_client_with_mocks._pending_event_ids = []

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert "timestamp" in result["metadata"]
    # Verify it's valid ISO format by parsing
    datetime.fromisoformat(result["metadata"]["timestamp"])


def test_get_results_counts_successful_and_failed_correctly(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, mock_event_result_success: Mock
) -> None:  # CRITICAL TEST
    """
    Test get_results counts successful and failed events correctly.

    Tests that metadata counters are accurate.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event_result_success : Mock
        Mocked successful result

    Returns
    -------
    None
        Test passes if counts are correct
    """
    # ARRANGE
    ids: List[str] = ["id-1", "id-2", "id-3"]
    http_client_with_mocks._pending_event_ids = ids

    mock_event_bus.get_results.return_value = {
        "id-1": mock_event_result_success,
        "id-2": mock_event_result_success,
        "id-3": mock_event_result_success,
    }

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert result["metadata"]["total_requested"] == 3
    assert result["metadata"]["successful"] == 3
    assert result["metadata"]["failed"] == 0


def test_get_results_includes_event_status_in_metadata(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event_result_success: Mock,
    mock_event_result_failure: Mock,
) -> None:  # CRITICAL TEST
    """
    Test get_results includes event status mapping in metadata.

    Tests that each event ID has success/failed status.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event_result_success : Mock
        Mocked successful result
    mock_event_result_failure : Mock
        Mocked failed result

    Returns
    -------
    None
        Test passes if event_ids mapping is correct
    """
    # ARRANGE
    success_id: str = "success-id"
    failure_id: str = "failure-id"

    http_client_with_mocks._pending_event_ids = [success_id, failure_id]
    mock_event_bus.get_results.return_value = {
        success_id: mock_event_result_success,
        failure_id: mock_event_result_failure,
    }

    # ACT
    result: Dict[str, Any] = http_client_with_mocks.get_results()

    # ASSERT
    assert "event_ids" in result["metadata"]
    assert result["metadata"]["event_ids"][success_id] == "success"
    assert result["metadata"]["event_ids"][failure_id] == "failed"


# -------------------------------------------------------------
# TEST CASES - Parametrized Tests
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "url,expected_valid",
    [
        ("https://example.com", True),
        ("http://localhost:8000", True),
        ("https://api.github.com/users", True),
        ("", True),  # Empty URL is technically allowed by get_sync
        ("not-a-url", True),  # URL validation is not HttpClient's responsibility
    ],
)
def test_get_sync_various_url_formats(
    http_client_with_mocks: HttpClient,
    mock_event_bus: Mock,
    mock_event: Mock,
    mock_event_result_success: Mock,
    url: str,
    expected_valid: bool,
) -> None:  # CRITICAL TEST
    """
    Test get_sync handles various URL formats.

    Tests that different URL formats are accepted.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    mock_event : Mock
        Mocked Event
    mock_event_result_success : Mock
        Mocked successful result
    url : str
        URL to test
    expected_valid : bool
        Whether URL should be accepted

    Returns
    -------
    None
        Test passes if URL handling is correct
    """
    # ARRANGE
    mock_event_bus.get_results.return_value = {mock_event.event_id: mock_event_result_success}

    # ACT & ASSERT
    if expected_valid:
        result: Any = http_client_with_mocks.get_sync(url)
        assert result is not None
    else:
        with pytest.raises(Exception):
            http_client_with_mocks.get_sync(url)


@pytest.mark.parametrize("result_scenario", ["all_success", "all_failed", "mixed", "empty"])
def test_get_results_various_scenarios(
    http_client_with_mocks: HttpClient, mock_event_bus: Mock, result_scenario: str
) -> None:  # CRITICAL TEST
    """
    Test get_results with various result scenarios.

    Tests different combinations of success/failure results.

    Parameters
    ----------
    http_client_with_mocks : HttpClient
        HttpClient with mocked dependencies
    mock_event_bus : Mock
        Mocked EventBus
    result_scenario : str
        Scenario to test (all_success/all_failed/mixed/empty)

    Returns
    -------
    None
        Test passes if scenario is handled correctly
    """
    # ARRANGE
    if result_scenario == "all_success":
        success_result: Mock = Mock()
        success_result.success = True
        success_result.data = {"status": "ok"}

        http_client_with_mocks._pending_event_ids = ["id-1", "id-2"]
        mock_event_bus.get_results.return_value = {"id-1": success_result, "id-2": success_result}

        # ACT
        result: Dict[str, Any] = http_client_with_mocks.get_results()

        # ASSERT
        assert result["metadata"]["successful"] == 2
        assert result["metadata"]["failed"] == 0
        assert len(result["data"]) == 2
        assert len(result["errors"]) == 0

    elif result_scenario == "all_failed":
        failed_result: Mock = Mock()
        failed_result.success = False
        failed_result.exception = RuntimeError("Failed")

        http_client_with_mocks._pending_event_ids = ["id-1", "id-2"]
        mock_event_bus.get_results.return_value = {"id-1": failed_result, "id-2": failed_result}

        # ACT
        result: Dict[str, Any] = http_client_with_mocks.get_results()

        # ASSERT
        assert result["metadata"]["successful"] == 0
        assert result["metadata"]["failed"] == 2
        assert len(result["data"]) == 0
        assert len(result["errors"]) == 2

    elif result_scenario == "mixed":
        success_result: Mock = Mock()
        success_result.success = True
        success_result.data = {"status": "ok"}

        failed_result: Mock = Mock()
        failed_result.success = False
        failed_result.exception = RuntimeError("Failed")

        http_client_with_mocks._pending_event_ids = ["id-1", "id-2"]
        mock_event_bus.get_results.return_value = {"id-1": success_result, "id-2": failed_result}

        # ACT
        result: Dict[str, Any] = http_client_with_mocks.get_results()

        # ASSERT
        assert result["metadata"]["successful"] == 1
        assert result["metadata"]["failed"] == 1
        assert len(result["data"]) == 1
        assert len(result["errors"]) == 1

    elif result_scenario == "empty":
        http_client_with_mocks._pending_event_ids = []

        # ACT
        result: Dict[str, Any] = http_client_with_mocks.get_results()

        # ASSERT
        assert result["metadata"]["total_requested"] == 0
        assert result["metadata"]["successful"] == 0
        assert result["metadata"]["failed"] == 0
        assert len(result["data"]) == 0
        assert len(result["errors"]) == 0
