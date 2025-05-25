"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Unit tests for EventHandler classes

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import Mock
import basefunctions

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
class ConcreteEventHandler(basefunctions.EventHandler):
    """Concrete implementation of EventHandler for testing."""

    def __init__(self):
        """Initialize tracking variables."""
        self.events_handled = []
        self.priority = 0

    def handle(self, event):
        """Track handled events."""
        self.events_handled.append(event)

    def get_priority(self):
        """Return the handler's priority."""
        return self.priority


class ConcreteTypedEventHandler(basefunctions.TypedEventHandler):
    """Concrete implementation of TypedEventHandler for testing."""

    def __init__(self, event_types):
        """Initialize the handler with specified event types."""
        super().__init__(event_types)
        self.events_handled = []

    def handle(self, event):
        """Track handled events."""
        self.events_handled.append(event)


class TestEventHandler:
    """Tests for the EventHandler interface and implementations."""

    def test_abstract_interface(self):
        """Test that EventHandler is an abstract interface."""
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            basefunctions.EventHandler()

    def test_concrete_handler(self):
        """Test concrete implementation of EventHandler."""
        handler = ConcreteEventHandler()

        # Verify it's an EventHandler
        assert isinstance(handler, basefunctions.EventHandler)

        # Test handling events
        event = basefunctions.Event("test_event")
        handler.handle(event)

        assert len(handler.events_handled) == 1
        assert handler.events_handled[0] is event

    def test_can_handle_default(self):
        """Test the default can_handle method."""
        handler = ConcreteEventHandler()
        event = basefunctions.Event("test_event")

        # Default implementation should return True for all events
        assert handler.can_handle(event) is True

    def test_get_priority_default(self):
        """Test the default get_priority method."""
        handler = ConcreteEventHandler()

        # Default implementation should return 0
        assert handler.get_priority() == 0

        # Test custom priority
        handler.priority = 10
        assert handler.get_priority() == 10


class CustomEvent(basefunctions.TypedEvent):
    """Custom event type for testing."""

    event_type = "custom.event"


class OtherEvent(basefunctions.TypedEvent):
    """Another custom event type for testing."""

    event_type = "other.event"


class TestTypedEventHandler:
    """Tests for the TypedEventHandler class."""

    def test_initialization_with_string(self):
        """Test initializing with string event type."""
        handler = ConcreteTypedEventHandler("test.event")

        # Verify it's both EventHandler and TypedEventHandler
        assert isinstance(handler, basefunctions.EventHandler)
        assert isinstance(handler, basefunctions.TypedEventHandler)

        # Check that _event_types was properly initialized
        assert hasattr(handler, "_event_types")
        assert "test.event" in handler._event_types

    def test_initialization_with_event_class(self):
        """Test initializing with Event subclass."""
        handler = ConcreteTypedEventHandler(CustomEvent)

        # Check that event_type from class was extracted
        assert "custom.event" in handler._event_types

    def test_initialization_with_list(self):
        """Test initializing with a list of event types."""
        handler = ConcreteTypedEventHandler(["test.event", CustomEvent, OtherEvent])

        # Check that all event types were extracted
        assert "test.event" in handler._event_types
        assert "custom.event" in handler._event_types
        assert "other.event" in handler._event_types

    def test_can_handle_implementation(self):
        """Test the can_handle method implementation."""
        handler = ConcreteTypedEventHandler(["event1", "event2"])

        # Should handle matching events
        event1 = basefunctions.Event("event1")
        event2 = basefunctions.Event("event2")
        assert handler.can_handle(event1) is True
        assert handler.can_handle(event2) is True

        # Should not handle non-matching events
        event3 = basefunctions.Event("event3")
        assert handler.can_handle(event3) is False

    def test_handle_method(self):
        """Test that handle method still works normally."""
        handler = ConcreteTypedEventHandler(["event1"])

        # Handle an event
        event = basefunctions.Event("event1")
        handler.handle(event)

        # Verify it was tracked
        assert len(handler.events_handled) == 1
        assert handler.events_handled[0] is event


class TestPrioritizedEventHandler:
    """Tests for the PrioritizedEventHandler class."""

    def test_initialization(self):
        """Test initializing with a handler and priority."""
        inner_handler = ConcreteEventHandler()
        prioritized = basefunctions.PrioritizedEventHandler(inner_handler, 10)

        # Verify it's an EventHandler
        assert isinstance(prioritized, basefunctions.EventHandler)

        # Check internal state
        assert hasattr(prioritized, "_handler")
        assert hasattr(prioritized, "_priority")
        assert prioritized._handler is inner_handler
        assert prioritized._priority == 10

    def test_handle_delegation(self):
        """Test that handle delegates to the wrapped handler."""
        inner_handler = ConcreteEventHandler()
        prioritized = basefunctions.PrioritizedEventHandler(inner_handler, 10)

        # Handle an event
        event = basefunctions.Event("test_event")
        prioritized.handle(event)

        # Verify inner handler received it
        assert len(inner_handler.events_handled) == 1
        assert inner_handler.events_handled[0] is event

    def test_can_handle_delegation(self):
        """Test that can_handle delegates to the wrapped handler."""
        inner_handler = Mock(spec=basefunctions.EventHandler)
        inner_handler.can_handle.return_value = False

        prioritized = basefunctions.PrioritizedEventHandler(inner_handler, 10)

        # Check can_handle
        event = basefunctions.Event("test_event")
        result = prioritized.can_handle(event)

        # Verify delegation
        inner_handler.can_handle.assert_called_once_with(event)
        assert result is False

    def test_get_priority(self):
        """Test that get_priority returns the set priority."""
        inner_handler = ConcreteEventHandler()
        inner_handler.priority = 0  # Different from prioritized

        prioritized = basefunctions.PrioritizedEventHandler(inner_handler, 10)

        # Check priority
        assert prioritized.get_priority() == 10

        # Verify it ignores inner handler's priority
        inner_handler.priority = 5
        assert prioritized.get_priority() == 10
