"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for Event class.
 Tests event creation, validation, execution modes, and parameter handling.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
import uuid
from datetime import datetime
from typing import Any, Optional
from unittest.mock import Mock, patch

# Project imports
from basefunctions.events.event import (
    Event,
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET,
    EXECUTION_MODE_CMD,
    VALID_EXECUTION_MODES,
    DEFAULT_PRIORITY,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_event_type() -> str:
    """
    Provide sample event type.

    Returns
    -------
    str
        Sample event type identifier
    """
    return "test_event"


@pytest.fixture
def sample_event_data() -> dict:
    """
    Provide sample event data.

    Returns
    -------
    dict
        Sample event payload
    """
    return {"key": "value", "count": 42}


# -------------------------------------------------------------
# TESTS: Event Initialization - Happy Path
# -------------------------------------------------------------


def test_event_minimal_initialization(sample_event_type: str) -> None:
    """Test Event can be initialized with minimal parameters."""
    # ACT
    event: Event = Event(event_type=sample_event_type)

    # ASSERT
    assert event.event_type == sample_event_type
    assert event.event_exec_mode == EXECUTION_MODE_THREAD  # Default
    assert event.event_id is not None
    assert event.priority == DEFAULT_PRIORITY
    assert event.timeout == DEFAULT_TIMEOUT
    assert event.max_retries == DEFAULT_MAX_RETRIES
    assert isinstance(event.timestamp, datetime)


def test_event_generates_unique_event_id() -> None:
    """Test Event generates unique UUID for event_id."""
    # ACT
    event1: Event = Event(event_type="type1")
    event2: Event = Event(event_type="type2")

    # ASSERT
    assert event1.event_id != event2.event_id
    # Validate UUID format
    assert uuid.UUID(event1.event_id)
    assert uuid.UUID(event2.event_id)


def test_event_with_all_parameters(sample_event_type: str, sample_event_data: dict) -> None:
    """Test Event initialization with all parameters."""
    # ARRANGE
    event_name: str = "Test Event"
    event_source: str = "test_source"
    event_target: str = "test_target"
    corelet_meta: dict = {"module_path": "test.module", "class_name": "TestHandler"}

    # ACT
    event: Event = Event(
        event_type=sample_event_type,
        event_exec_mode=EXECUTION_MODE_SYNC,
        event_name=event_name,
        event_source=event_source,
        event_target=event_target,
        event_data=sample_event_data,
        max_retries=5,
        timeout=60,
        priority=8,
        corelet_meta=corelet_meta,
        progress_steps=10,
    )

    # ASSERT
    assert event.event_type == sample_event_type
    assert event.event_exec_mode == EXECUTION_MODE_SYNC
    assert event.event_name == event_name
    assert event.event_source == event_source
    assert event.event_target == event_target
    assert event.event_data == sample_event_data
    assert event.max_retries == 5
    assert event.timeout == 60
    assert event.priority == 8
    assert event.corelet_meta == corelet_meta
    assert event.progress_steps == 10


# -------------------------------------------------------------
# TESTS: Event Validation - CRITICAL
# -------------------------------------------------------------


def test_event_validation_raises_error_when_event_type_empty() -> None:  # CRITICAL TEST
    """Test Event raises ValueError when event_type is empty string."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        Event(event_type="")


def test_event_validation_raises_error_when_execution_mode_invalid() -> None:  # CRITICAL TEST
    """Test Event raises ValueError for invalid execution mode."""
    # ARRANGE
    invalid_mode: str = "invalid_mode"

    # ACT & ASSERT
    with pytest.raises(ValueError, match=f"Invalid execution mode: {invalid_mode}"):
        Event(event_type="test", event_exec_mode=invalid_mode)


@pytest.mark.parametrize(
    "invalid_mode",
    [
        "async",
        "parallel",
        "sequential",
        "",
        "SYNC",  # Case sensitivity
        "Thread",  # Case sensitivity
    ],
)
def test_event_validation_rejects_various_invalid_modes(invalid_mode: str) -> None:  # CRITICAL TEST
    """Test Event rejects various invalid execution modes."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="Invalid execution mode"):
        Event(event_type="test", event_exec_mode=invalid_mode)


# -------------------------------------------------------------
# TESTS: Execution Modes
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "exec_mode",
    [
        EXECUTION_MODE_SYNC,
        EXECUTION_MODE_THREAD,
        EXECUTION_MODE_CORELET,
        EXECUTION_MODE_CMD,
    ],
)
def test_event_accepts_all_valid_execution_modes(exec_mode: str) -> None:
    """Test Event accepts all valid execution modes."""
    # ACT
    event: Event = Event(event_type="test", event_exec_mode=exec_mode)

    # ASSERT
    assert event.event_exec_mode == exec_mode


def test_event_default_execution_mode_is_thread() -> None:
    """Test Event defaults to THREAD execution mode."""
    # ACT
    event: Event = Event(event_type="test")

    # ASSERT
    assert event.event_exec_mode == EXECUTION_MODE_THREAD


def test_valid_execution_modes_constant_contains_all_modes() -> None:
    """Test VALID_EXECUTION_MODES contains all expected modes."""
    # ASSERT
    assert EXECUTION_MODE_SYNC in VALID_EXECUTION_MODES
    assert EXECUTION_MODE_THREAD in VALID_EXECUTION_MODES
    assert EXECUTION_MODE_CORELET in VALID_EXECUTION_MODES
    assert EXECUTION_MODE_CMD in VALID_EXECUTION_MODES
    assert len(VALID_EXECUTION_MODES) == 4


# -------------------------------------------------------------
# TESTS: Corelet Metadata Auto-Population
# -------------------------------------------------------------


@patch("basefunctions.EventFactory")
def test_event_auto_populates_corelet_meta_for_corelet_mode(mock_factory_class: Mock) -> None:
    """Test Event auto-populates corelet_meta for CORELET execution mode."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_factory.get_handler_meta.return_value = {
        "module_path": "test.module",
        "class_name": "TestHandler",
        "event_type": "test_event",
    }
    mock_factory_class.return_value = mock_factory

    # ACT
    event: Event = Event(event_type="test_event", event_exec_mode=EXECUTION_MODE_CORELET)

    # ASSERT
    mock_factory.get_handler_meta.assert_called_once_with("test_event")
    assert event.corelet_meta is not None
    assert event.corelet_meta["class_name"] == "TestHandler"


@patch("basefunctions.EventFactory")
def test_event_does_not_auto_populate_corelet_meta_for_non_corelet_mode(mock_factory_class: Mock) -> None:
    """Test Event does not auto-populate corelet_meta for non-CORELET modes."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_factory_class.return_value = mock_factory

    # ACT
    event: Event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_THREAD)

    # ASSERT
    mock_factory.get_handler_meta.assert_not_called()
    assert event.corelet_meta is None


@patch("basefunctions.EventFactory")
def test_event_handles_factory_error_when_auto_populating_corelet_meta(mock_factory_class: Mock) -> None:
    """Test Event handles EventFactory errors gracefully when auto-populating corelet_meta."""
    # ARRANGE
    mock_factory: Mock = Mock()
    mock_factory.get_handler_meta.side_effect = ValueError("Handler not registered")
    mock_factory_class.return_value = mock_factory

    # ACT
    event: Event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_CORELET)

    # ASSERT
    assert event.corelet_meta is None  # Gracefully falls back to None


def test_event_uses_explicit_corelet_meta_when_provided() -> None:
    """Test Event uses explicit corelet_meta instead of auto-populating."""
    # ARRANGE
    explicit_meta: dict = {"module_path": "explicit.module", "class_name": "ExplicitHandler"}

    # ACT
    event: Event = Event(event_type="test", event_exec_mode=EXECUTION_MODE_CORELET, corelet_meta=explicit_meta)

    # ASSERT
    assert event.corelet_meta == explicit_meta


# -------------------------------------------------------------
# TESTS: Default Values
# -------------------------------------------------------------


def test_event_default_values() -> None:
    """Test Event uses correct default values for optional parameters."""
    # ACT
    event: Event = Event(event_type="test")

    # ASSERT
    assert event.event_exec_mode == EXECUTION_MODE_THREAD
    assert event.event_name is None
    assert event.event_source is None
    assert event.event_target is None
    assert event.event_data is None
    assert event.max_retries == DEFAULT_MAX_RETRIES
    assert event.timeout == DEFAULT_TIMEOUT
    assert event.priority == DEFAULT_PRIORITY
    assert event.corelet_meta is None
    assert event.progress_tracker is None
    assert event.progress_steps == 0


def test_default_constants_have_expected_values() -> None:
    """Test default constants have expected values."""
    # ASSERT
    assert DEFAULT_PRIORITY == 5
    assert DEFAULT_TIMEOUT == 30
    assert DEFAULT_MAX_RETRIES == 3


# -------------------------------------------------------------
# TESTS: Progress Tracking
# -------------------------------------------------------------


def test_event_with_progress_tracker() -> None:
    """Test Event can store progress_tracker and progress_steps."""
    # ARRANGE
    mock_tracker: Mock = Mock()

    # ACT
    event: Event = Event(event_type="test", progress_tracker=mock_tracker, progress_steps=5)

    # ASSERT
    assert event.progress_tracker is mock_tracker
    assert event.progress_steps == 5


def test_event_progress_steps_defaults_to_zero() -> None:
    """Test Event progress_steps defaults to 0 when not provided."""
    # ACT
    event: Event = Event(event_type="test")

    # ASSERT
    assert event.progress_steps == 0


# -------------------------------------------------------------
# TESTS: Event Representation
# -------------------------------------------------------------


def test_event_repr_contains_key_information() -> None:
    """Test Event __repr__ contains key event information."""
    # ACT
    event: Event = Event(
        event_type="test_type", event_name="Test Event", event_exec_mode=EXECUTION_MODE_SYNC, priority=7
    )

    # ARRANGE
    repr_str: str = repr(event)

    # ASSERT
    assert "test_type" in repr_str
    assert "Test Event" in repr_str
    assert EXECUTION_MODE_SYNC in repr_str
    assert "priority=7" in repr_str
    assert event.event_id in repr_str


# -------------------------------------------------------------
# TESTS: Event Attributes Immutability (via __slots__)
# -------------------------------------------------------------


def test_event_uses_slots_for_memory_efficiency() -> None:
    """Test Event uses __slots__ for memory efficiency."""
    # ARRANGE
    event: Event = Event(event_type="test")

    # ACT & ASSERT
    assert hasattr(Event, "__slots__")
    with pytest.raises(AttributeError):
        event.unknown_attribute = "value"


def test_event_slots_contain_all_expected_attributes() -> None:
    """Test Event __slots__ contains all expected attributes."""
    # ARRANGE
    expected_slots: set = {
        "event_id",
        "event_type",
        "event_exec_mode",
        "event_name",
        "event_source",
        "event_target",
        "event_data",
        "max_retries",
        "timeout",
        "priority",
        "timestamp",
        "corelet_meta",
        "progress_tracker",
        "progress_steps",
        "_requeue_count",
    }

    # ACT
    actual_slots: set = set(Event.__slots__)

    # ASSERT
    assert actual_slots == expected_slots


# -------------------------------------------------------------
# TESTS: Timestamp Behavior
# -------------------------------------------------------------


def test_event_timestamp_is_set_on_creation() -> None:
    """Test Event timestamp is set to current time on creation."""
    # ARRANGE
    before: datetime = datetime.now()

    # ACT
    event: Event = Event(event_type="test")

    # ARRANGE (continued)
    after: datetime = datetime.now()

    # ASSERT
    assert before <= event.timestamp <= after


def test_event_timestamps_differ_for_different_events() -> None:
    """Test different events have different timestamps."""
    # ACT
    event1: Event = Event(event_type="test1")
    event2: Event = Event(event_type="test2")

    # ASSERT
    # Timestamps should be close but may differ slightly
    assert event1.timestamp <= event2.timestamp


# -------------------------------------------------------------
# TESTS: Edge Cases - CRITICAL
# -------------------------------------------------------------


def test_event_handles_none_event_data() -> None:
    """Test Event handles None event_data gracefully."""
    # ACT
    event: Event = Event(event_type="test", event_data=None)

    # ASSERT
    assert event.event_data is None


def test_event_handles_empty_event_data() -> None:
    """Test Event handles empty dict as event_data."""
    # ACT
    event: Event = Event(event_type="test", event_data={})

    # ASSERT
    assert event.event_data == {}


def test_event_handles_complex_event_data() -> None:
    """Test Event handles complex nested event_data."""
    # ARRANGE
    complex_data: dict = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "tuple": (4, 5, 6),
        "mixed": {"inner": [{"deep": "value"}]},
    }

    # ACT
    event: Event = Event(event_type="test", event_data=complex_data)

    # ASSERT
    assert event.event_data == complex_data
    assert event.event_data["nested"]["key"] == "value"


def test_event_with_zero_priority() -> None:
    """Test Event handles priority of 0."""
    # ACT
    event: Event = Event(event_type="test", priority=0)

    # ASSERT
    assert event.priority == 0


def test_event_with_high_priority() -> None:
    """Test Event handles high priority value."""
    # ACT
    event: Event = Event(event_type="test", priority=10)

    # ASSERT
    assert event.priority == 10


def test_event_with_negative_priority() -> None:
    """Test Event handles negative priority (for shutdown events)."""
    # ACT
    event: Event = Event(event_type="test", priority=-1)

    # ASSERT
    assert event.priority == -1


def test_event_with_zero_timeout() -> None:
    """Test Event handles timeout of 0."""
    # ACT
    event: Event = Event(event_type="test", timeout=0)

    # ASSERT
    assert event.timeout == 0


def test_event_with_zero_max_retries() -> None:
    """Test Event handles max_retries of 0 (no retries)."""
    # ACT
    event: Event = Event(event_type="test", max_retries=0)

    # ASSERT
    assert event.max_retries == 0


# -------------------------------------------------------------
# TESTS: Parameter Types
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "event_data",
    [
        {"key": "value"},
        [1, 2, 3],
        "string_data",
        42,
        3.14,
        True,
        None,
    ],
)
def test_event_accepts_various_event_data_types(event_data: Any) -> None:
    """Test Event accepts various types as event_data."""
    # ACT
    event: Event = Event(event_type="test", event_data=event_data)

    # ASSERT
    assert event.event_data == event_data


def test_event_event_source_can_be_any_type() -> None:
    """Test Event event_source accepts any type."""
    # ARRANGE
    sources: list = ["string", 123, {"key": "value"}, object(), None]

    # ACT & ASSERT
    for source in sources:
        event: Event = Event(event_type="test", event_source=source)
        assert event.event_source == source


def test_event_event_target_can_be_any_type() -> None:
    """Test Event event_target accepts any type."""
    # ARRANGE
    targets: list = ["string", 456, ["list"], object(), None]

    # ACT & ASSERT
    for target in targets:
        event: Event = Event(event_type="test", event_target=target)
        assert event.event_target == target
