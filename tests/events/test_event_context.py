"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for EventContext class.
 Tests context initialization, thread-local storage, and attribute handling.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
import threading
from datetime import datetime
from typing import Any

# Project imports
from basefunctions.events.event_context import EventContext

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def thread_local_data() -> threading.local:
    """
    Create thread-local storage for testing.

    Returns
    -------
    threading.local
        Thread-local data object
    """
    return threading.local()


@pytest.fixture
def sample_thread_id() -> str:
    """
    Provide sample thread ID.

    Returns
    -------
    str
        Sample thread identifier
    """
    return "thread-123"


@pytest.fixture
def sample_process_id() -> str:
    """
    Provide sample process ID.

    Returns
    -------
    str
        Sample process identifier
    """
    return "12345"


@pytest.fixture
def sample_timestamp() -> datetime:
    """
    Provide sample timestamp.

    Returns
    -------
    datetime
        Sample timestamp object
    """
    return datetime(2025, 1, 1, 12, 0, 0)


# -------------------------------------------------------------
# TESTS: EventContext Initialization
# -------------------------------------------------------------


def test_event_context_minimal_initialization() -> None:
    """Test EventContext can be initialized with minimal parameters."""
    # ACT
    context: EventContext = EventContext()

    # ASSERT
    assert context.thread_local_data is None
    assert context.thread_id is None
    assert context.process_id is None
    assert context.event_data is None
    assert context.worker is None
    assert isinstance(context.timestamp, datetime)


def test_event_context_with_thread_local_data(thread_local_data: threading.local) -> None:
    """Test EventContext initialization with thread_local_data."""
    # ACT
    context: EventContext = EventContext(thread_local_data=thread_local_data)

    # ASSERT
    assert context.thread_local_data is thread_local_data


def test_event_context_with_thread_id(sample_thread_id: str) -> None:
    """Test EventContext initialization with thread_id."""
    # ACT
    context: EventContext = EventContext(thread_id=sample_thread_id)

    # ASSERT
    assert context.thread_id == sample_thread_id


def test_event_context_with_process_id(sample_process_id: str) -> None:
    """Test EventContext initialization with process_id."""
    # ACT
    context: EventContext = EventContext(process_id=sample_process_id)

    # ASSERT
    assert context.process_id == sample_process_id


def test_event_context_with_custom_timestamp(sample_timestamp: datetime) -> None:
    """Test EventContext initialization with custom timestamp."""
    # ACT
    context: EventContext = EventContext(timestamp=sample_timestamp)

    # ASSERT
    assert context.timestamp == sample_timestamp


def test_event_context_timestamp_defaults_to_now() -> None:
    """Test EventContext timestamp defaults to current time when not provided."""
    # ARRANGE
    before: datetime = datetime.now()

    # ACT
    context: EventContext = EventContext()

    # ARRANGE (continued)
    after: datetime = datetime.now()

    # ASSERT
    assert before <= context.timestamp <= after


def test_event_context_with_event_data() -> None:
    """Test EventContext initialization with event_data."""
    # ARRANGE
    event_data: dict = {"key": "value", "count": 42}

    # ACT
    context: EventContext = EventContext(event_data=event_data)

    # ASSERT
    assert context.event_data == event_data


def test_event_context_with_worker_reference() -> None:
    """Test EventContext initialization with worker reference."""
    # ARRANGE
    mock_worker: object = object()

    # ACT
    context: EventContext = EventContext(worker=mock_worker)

    # ASSERT
    assert context.worker is mock_worker


def test_event_context_with_all_parameters(
    thread_local_data: threading.local, sample_thread_id: str, sample_process_id: str, sample_timestamp: datetime
) -> None:
    """Test EventContext initialization with all parameters."""
    # ARRANGE
    event_data: dict = {"test": "data"}
    mock_worker: object = object()

    # ACT
    context: EventContext = EventContext(
        thread_local_data=thread_local_data,
        thread_id=sample_thread_id,
        process_id=sample_process_id,
        timestamp=sample_timestamp,
        event_data=event_data,
        worker=mock_worker,
    )

    # ASSERT
    assert context.thread_local_data is thread_local_data
    assert context.thread_id == sample_thread_id
    assert context.process_id == sample_process_id
    assert context.timestamp == sample_timestamp
    assert context.event_data == event_data
    assert context.worker is mock_worker


# -------------------------------------------------------------
# TESTS: Thread-Local Storage Behavior
# -------------------------------------------------------------


def test_thread_local_data_can_store_attributes(thread_local_data: threading.local) -> None:
    """Test thread_local_data can store custom attributes."""
    # ARRANGE
    context: EventContext = EventContext(thread_local_data=thread_local_data)

    # ACT
    context.thread_local_data.custom_attribute = "test_value"

    # ASSERT
    assert hasattr(context.thread_local_data, "custom_attribute")
    assert context.thread_local_data.custom_attribute == "test_value"


def test_thread_local_data_isolates_between_contexts() -> None:
    """Test thread_local_data is isolated between different contexts."""
    # ARRANGE
    context1: EventContext = EventContext(thread_local_data=threading.local())
    context2: EventContext = EventContext(thread_local_data=threading.local())

    # ACT
    context1.thread_local_data.value = "context1"
    context2.thread_local_data.value = "context2"

    # ASSERT
    assert context1.thread_local_data.value == "context1"
    assert context2.thread_local_data.value == "context2"


def test_thread_local_data_can_store_handler_cache(thread_local_data: threading.local) -> None:
    """Test thread_local_data can store handler cache dictionary."""
    # ARRANGE
    context: EventContext = EventContext(thread_local_data=thread_local_data)

    # ACT
    context.thread_local_data.handlers = {}
    context.thread_local_data.handlers["event_type_1"] = "handler_1"
    context.thread_local_data.handlers["event_type_2"] = "handler_2"

    # ASSERT
    assert len(context.thread_local_data.handlers) == 2
    assert context.thread_local_data.handlers["event_type_1"] == "handler_1"


# -------------------------------------------------------------
# TESTS: Attribute Access
# -------------------------------------------------------------


def test_event_context_attributes_are_readable() -> None:
    """Test all EventContext attributes are readable."""
    # ARRANGE
    context: EventContext = EventContext(
        thread_local_data=threading.local(), thread_id="thread-1", process_id="12345", event_data={"key": "value"}
    )

    # ACT & ASSERT
    assert context.thread_local_data is not None
    assert context.thread_id == "thread-1"
    assert context.process_id == "12345"
    assert context.event_data == {"key": "value"}
    assert context.worker is None
    assert isinstance(context.timestamp, datetime)


def test_event_context_attributes_are_writable() -> None:
    """Test EventContext attributes can be modified after initialization."""
    # ARRANGE
    context: EventContext = EventContext()

    # ACT
    context.thread_id = "new-thread-id"
    context.process_id = "99999"
    context.event_data = {"new": "data"}

    # ASSERT
    assert context.thread_id == "new-thread-id"
    assert context.process_id == "99999"
    assert context.event_data == {"new": "data"}


# -------------------------------------------------------------
# TESTS: Edge Cases
# -------------------------------------------------------------


def test_event_context_with_none_values() -> None:
    """Test EventContext handles None values for all optional parameters."""
    # ACT
    context: EventContext = EventContext(
        thread_local_data=None, thread_id=None, process_id=None, timestamp=None, event_data=None, worker=None
    )

    # ASSERT
    assert context.thread_local_data is None
    assert context.thread_id is None
    assert context.process_id is None
    assert context.event_data is None
    assert context.worker is None
    # timestamp should default to current time even when explicitly None
    assert isinstance(context.timestamp, datetime)


def test_event_context_with_empty_event_data() -> None:
    """Test EventContext handles empty event_data."""
    # ARRANGE
    empty_data: dict = {}

    # ACT
    context: EventContext = EventContext(event_data=empty_data)

    # ASSERT
    assert context.event_data == {}
    assert len(context.event_data) == 0


def test_event_context_event_data_can_be_complex_object() -> None:
    """Test EventContext event_data can hold complex objects."""
    # ARRANGE
    complex_data: dict = {"nested": {"key": "value"}, "list": [1, 2, 3], "object": object(), "function": lambda x: x}

    # ACT
    context: EventContext = EventContext(event_data=complex_data)

    # ASSERT
    assert context.event_data == complex_data
    assert context.event_data["nested"]["key"] == "value"
    assert context.event_data["list"] == [1, 2, 3]


# -------------------------------------------------------------
# TESTS: Usage Patterns
# -------------------------------------------------------------


def test_event_context_sync_mode_pattern(thread_local_data: threading.local) -> None:
    """Test EventContext pattern for SYNC execution mode."""
    # ARRANGE & ACT
    context: EventContext = EventContext(thread_local_data=thread_local_data)

    # ASSERT
    assert context.thread_local_data is not None
    assert context.thread_id is None  # Not tracked in sync mode
    assert context.process_id is None  # Main process


def test_event_context_thread_mode_pattern(thread_local_data: threading.local, sample_thread_id: str) -> None:
    """Test EventContext pattern for THREAD execution mode."""
    # ARRANGE & ACT
    context: EventContext = EventContext(thread_local_data=thread_local_data, thread_id=sample_thread_id)

    # ASSERT
    assert context.thread_local_data is not None
    assert context.thread_id == sample_thread_id
    assert context.process_id is None  # Main process


def test_event_context_corelet_mode_pattern(thread_local_data: threading.local, sample_process_id: str) -> None:
    """Test EventContext pattern for CORELET execution mode."""
    # ARRANGE
    mock_worker: object = object()

    # ACT
    context: EventContext = EventContext(
        thread_local_data=thread_local_data, process_id=sample_process_id, worker=mock_worker
    )

    # ASSERT
    assert context.thread_local_data is not None
    assert context.thread_id is None  # Worker process main thread
    assert context.process_id == sample_process_id
    assert context.worker is mock_worker
