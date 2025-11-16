"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for EventFactory singleton.
 Tests handler registration, creation, metadata retrieval, and thread safety.

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
from unittest.mock import Mock

# Project imports
from basefunctions.events.event_factory import EventFactory
from basefunctions.events.event_handler import EventHandler, EventResult
from basefunctions.events.event import Event
from basefunctions.events.event_context import EventContext

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def fresh_factory() -> EventFactory:
    """
    Create fresh EventFactory instance for testing.

    Returns
    -------
    EventFactory
        Fresh factory instance

    Notes
    -----
    EventFactory is a singleton, so we clear its registry between tests
    """
    factory: EventFactory = EventFactory()
    # Clear registry for test isolation
    factory._handler_registry.clear()
    return factory


@pytest.fixture
def sample_handler_class() -> Type[EventHandler]:
    """
    Provide sample handler class for testing.

    Returns
    -------
    Type[EventHandler]
        Sample handler class
    """

    class SampleHandler(EventHandler):
        def handle(self, event: Event, context: EventContext) -> EventResult:
            return EventResult.business_result(event.event_id, True, "Sample result")

    return SampleHandler


@pytest.fixture
def another_handler_class() -> Type[EventHandler]:
    """
    Provide another handler class for testing.

    Returns
    -------
    Type[EventHandler]
        Another handler class
    """

    class AnotherHandler(EventHandler):
        def handle(self, event: Event, context: EventContext) -> EventResult:
            return EventResult.business_result(event.event_id, True, "Another result")

    return AnotherHandler


# -------------------------------------------------------------
# TESTS: EventFactory Singleton Pattern
# -------------------------------------------------------------


def test_event_factory_is_singleton() -> None:
    """Test EventFactory returns same instance (singleton pattern)."""
    # ACT
    factory1: EventFactory = EventFactory()
    factory2: EventFactory = EventFactory()

    # ASSERT
    assert factory1 is factory2


def test_event_factory_initialization() -> None:
    """Test EventFactory initializes with empty handler registry."""
    # ACT
    factory: EventFactory = EventFactory()

    # ASSERT
    assert hasattr(factory, "_handler_registry")
    assert hasattr(factory, "_lock")


# -------------------------------------------------------------
# TESTS: Handler Registration
# -------------------------------------------------------------


def test_register_event_type_adds_handler_to_registry(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test register_event_type() adds handler to registry."""
    # ARRANGE
    event_type: str = "test_event"

    # ACT
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ASSERT
    assert event_type in fresh_factory._handler_registry
    assert fresh_factory._handler_registry[event_type] == sample_handler_class


def test_register_event_type_allows_overwriting(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler], another_handler_class: Type[EventHandler]
) -> None:
    """Test register_event_type() allows overwriting existing handler."""
    # ARRANGE
    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ACT
    fresh_factory.register_event_type(event_type, another_handler_class)

    # ASSERT
    assert fresh_factory._handler_registry[event_type] == another_handler_class


def test_register_event_type_raises_error_when_event_type_empty(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:  # CRITICAL TEST
    """Test register_event_type() raises ValueError for empty event_type."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        fresh_factory.register_event_type("", sample_handler_class)


def test_register_event_type_raises_error_when_handler_class_none(
    fresh_factory: EventFactory,
) -> None:  # CRITICAL TEST
    """Test register_event_type() raises ValueError for None handler_class."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_handler_class cannot be None"):
        fresh_factory.register_event_type("test_event", None)


# -------------------------------------------------------------
# TESTS: Handler Creation
# -------------------------------------------------------------


def test_create_handler_returns_handler_instance(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test create_handler() returns handler instance."""
    # ARRANGE
    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ACT
    handler: EventHandler = fresh_factory.create_handler(event_type)

    # ASSERT
    assert isinstance(handler, EventHandler)
    assert isinstance(handler, sample_handler_class)


def test_create_handler_creates_new_instance_each_time(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test create_handler() creates new instance each time."""
    # ARRANGE
    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ACT
    handler1: EventHandler = fresh_factory.create_handler(event_type)
    handler2: EventHandler = fresh_factory.create_handler(event_type)

    # ASSERT
    assert handler1 is not handler2


def test_create_handler_raises_error_when_event_type_empty(fresh_factory: EventFactory) -> None:  # CRITICAL TEST
    """Test create_handler() raises ValueError for empty event_type."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        fresh_factory.create_handler("")


def test_create_handler_raises_error_when_event_type_not_registered(
    fresh_factory: EventFactory,
) -> None:  # CRITICAL TEST
    """Test create_handler() raises ValueError for unregistered event_type."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="No handler registered for event type"):
        fresh_factory.create_handler("unregistered_event")


def test_create_handler_with_constructor_arguments(fresh_factory: EventFactory) -> None:
    """Test create_handler() passes arguments to handler constructor."""

    # ARRANGE
    class HandlerWithArgs(EventHandler):
        def __init__(self, arg1: str, arg2: int):
            self.arg1 = arg1
            self.arg2 = arg2

        def handle(self, event: Event, context: EventContext) -> EventResult:
            return EventResult.business_result(event.event_id, True, None)

    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, HandlerWithArgs)

    # ACT
    handler: HandlerWithArgs = fresh_factory.create_handler(event_type, "test", 42)

    # ASSERT
    assert handler.arg1 == "test"
    assert handler.arg2 == 42


def test_create_handler_raises_runtime_error_when_handler_construction_fails(
    fresh_factory: EventFactory,
) -> None:  # CRITICAL TEST
    """Test create_handler() raises RuntimeError when handler construction fails."""

    # ARRANGE
    class BrokenHandler(EventHandler):
        def __init__(self):
            raise ValueError("Construction failed")

        def handle(self, event: Event, context: EventContext) -> EventResult:
            return EventResult.business_result(event.event_id, True, None)

    event_type: str = "broken_event"
    fresh_factory.register_event_type(event_type, BrokenHandler)

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Failed to create handler"):
        fresh_factory.create_handler(event_type)


# -------------------------------------------------------------
# TESTS: Handler Availability
# -------------------------------------------------------------


def test_is_handler_available_returns_true_when_registered(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test is_handler_available() returns True for registered handler."""
    # ARRANGE
    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ACT
    available: bool = fresh_factory.is_handler_available(event_type)

    # ASSERT
    assert available is True


def test_is_handler_available_returns_false_when_not_registered(fresh_factory: EventFactory) -> None:
    """Test is_handler_available() returns False for unregistered handler."""
    # ACT
    available: bool = fresh_factory.is_handler_available("unregistered_event")

    # ASSERT
    assert available is False


def test_is_handler_available_returns_false_for_empty_event_type(fresh_factory: EventFactory) -> None:
    """Test is_handler_available() returns False for empty event_type."""
    # ACT
    available: bool = fresh_factory.is_handler_available("")

    # ASSERT
    assert available is False


# -------------------------------------------------------------
# TESTS: Handler Metadata
# -------------------------------------------------------------


def test_get_handler_meta_returns_metadata(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test get_handler_meta() returns handler metadata."""
    # ARRANGE
    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ACT
    meta: dict = fresh_factory.get_handler_meta(event_type)

    # ASSERT
    assert "module_path" in meta
    assert "class_name" in meta
    assert "event_type" in meta
    assert meta["event_type"] == event_type
    assert meta["class_name"] == sample_handler_class.__name__


def test_get_handler_meta_raises_error_when_event_type_empty(fresh_factory: EventFactory) -> None:  # CRITICAL TEST
    """Test get_handler_meta() raises ValueError for empty event_type."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="event_type cannot be empty"):
        fresh_factory.get_handler_meta("")


def test_get_handler_meta_raises_error_when_event_type_not_registered(
    fresh_factory: EventFactory,
) -> None:  # CRITICAL TEST
    """Test get_handler_meta() raises ValueError for unregistered event_type."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="No handler registered for event type"):
        fresh_factory.get_handler_meta("unregistered_event")


# -------------------------------------------------------------
# TESTS: Supported Event Types
# -------------------------------------------------------------


def test_get_supported_event_types_returns_empty_list_initially(fresh_factory: EventFactory) -> None:
    """Test get_supported_event_types() returns empty list initially."""
    # ACT
    supported: list = fresh_factory.get_supported_event_types()

    # ASSERT
    assert supported == []


def test_get_supported_event_types_returns_registered_types(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler], another_handler_class: Type[EventHandler]
) -> None:
    """Test get_supported_event_types() returns all registered event types."""
    # ARRANGE
    fresh_factory.register_event_type("event1", sample_handler_class)
    fresh_factory.register_event_type("event2", another_handler_class)

    # ACT
    supported: list = fresh_factory.get_supported_event_types()

    # ASSERT
    assert len(supported) == 2
    assert "event1" in supported
    assert "event2" in supported


# -------------------------------------------------------------
# TESTS: Get Handler Type
# -------------------------------------------------------------


def test_get_handler_type_returns_handler_class(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test get_handler_type() returns handler class."""
    # ARRANGE
    event_type: str = "test_event"
    fresh_factory.register_event_type(event_type, sample_handler_class)

    # ACT
    handler_type: Type[EventHandler] = fresh_factory.get_handler_type(event_type)

    # ASSERT
    assert handler_type == sample_handler_class


def test_get_handler_type_raises_error_when_not_registered(fresh_factory: EventFactory) -> None:  # CRITICAL TEST
    """Test get_handler_type() raises ValueError for unregistered event_type."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="No handler registered for event type"):
        fresh_factory.get_handler_type("unregistered_event")


# -------------------------------------------------------------
# TESTS: Thread Safety
# -------------------------------------------------------------


def test_event_factory_registration_is_thread_safe(
    fresh_factory: EventFactory, sample_handler_class: Type[EventHandler]
) -> None:
    """Test EventFactory handler registration is thread-safe."""
    # ARRANGE
    import threading

    results: list = []

    def register_handler(event_type: str):
        fresh_factory.register_event_type(event_type, sample_handler_class)
        results.append(event_type)

    # ACT
    threads: list = [threading.Thread(target=register_handler, args=(f"event_{i}",)) for i in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert len(results) == 10
    assert len(fresh_factory.get_supported_event_types()) == 10


# -------------------------------------------------------------
# TESTS: Edge Cases
# -------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_event_type",
    [
        None,
        123,
        [],
        {},
    ],
)
def test_is_handler_available_handles_invalid_types(fresh_factory: EventFactory, invalid_event_type: any) -> None:
    """Test is_handler_available() handles invalid event_type types gracefully."""
    # ACT
    available: bool = fresh_factory.is_handler_available(invalid_event_type)

    # ASSERT
    assert available is False
