"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unit tests for EventBus class
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import Mock, patch
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
class TestEventBus:
    """Tests for the EventBus class."""

    def test_initialization(self):
        """Test that EventBus initializes properly."""
        event_bus = basefunctions.EventBus()

        # Verify internal state
        assert hasattr(event_bus, "_handlers")
        assert hasattr(event_bus, "_handler_methods")
        assert len(event_bus._handlers) == 0
        assert len(event_bus._handler_methods) == 0

    def test_get_event_bus(self):
        """Test the singleton-like get_event_bus function."""
        # Get the default instance
        bus1 = basefunctions.get_event_bus()
        assert isinstance(bus1, basefunctions.EventBus)

        # Get it again and verify it's the same instance
        bus2 = basefunctions.get_event_bus()
        assert bus1 is bus2

    def test_register_handler(self):
        """Test registering a handler for an event type."""
        event_bus = basefunctions.EventBus()
        handler = Mock(spec=basefunctions.EventHandler)
        # Set priority value for sorting
        handler.get_priority.return_value = 0

        # Register the handler
        subscription = event_bus.register("test_event", handler)

        # Verify registration
        assert "test_event" in event_bus._handlers
        assert len(event_bus._handlers["test_event"]) == 1
        assert event_bus._handlers["test_event"][0][0] is handler

        # Verify subscription is returned
        assert isinstance(subscription, basefunctions.Subscription)

    def test_register_invalid_handler(self):
        """Test that registering a non-EventHandler raises TypeError."""
        event_bus = basefunctions.EventBus()
        not_a_handler = object()

        with pytest.raises(TypeError):
            event_bus.register("test_event", not_a_handler)

    def test_publish_event(self):
        """Test publishing an event to registered handlers."""
        event_bus = basefunctions.EventBus()

        # Create mock handler
        handler = Mock(spec=basefunctions.EventHandler)
        handler.get_priority.return_value = 0

        # Register handler
        event_bus.register("test_event", handler)

        # Create and publish event
        event = basefunctions.Event("test_event")
        event_bus.publish(event)

        # Verify handler was called with the event
        handler.handle.assert_called_once_with(event)

    def test_publish_event_with_filter(self):
        """Test publishing an event with a filter function."""
        event_bus = basefunctions.EventBus()

        # Create mock handler
        handler = Mock(spec=basefunctions.EventHandler)
        handler.get_priority.return_value = 0

        # Create mock filter functions
        pass_filter = Mock(return_value=True)
        block_filter = Mock(return_value=False)

        # Register with filters
        event_bus.register("test_event", handler, pass_filter)

        # Create and publish event
        event = basefunctions.Event("test_event")
        event_bus.publish(event)

        # Verify filter and handler were called
        pass_filter.assert_called_once_with(event)
        handler.handle.assert_called_once_with(event)

        # Reset mocks
        handler.reset_mock()
        pass_filter.reset_mock()

        # Register with blocking filter
        event_bus.clear()
        event_bus.register("test_event", handler, block_filter)

        # Publish again
        event_bus.publish(event)

        # Verify filter was called but handler was not
        block_filter.assert_called_once_with(event)
        handler.handle.assert_not_called()

    def test_publish_to_multiple_handlers(self):
        """Test publishing to multiple handlers for the same event type."""
        event_bus = basefunctions.EventBus()

        # Create mock handlers
        handler1 = Mock(spec=basefunctions.EventHandler)
        handler2 = Mock(spec=basefunctions.EventHandler)
        handler1.get_priority.return_value = 0
        handler2.get_priority.return_value = 0

        # Register handlers
        event_bus.register("test_event", handler1)
        event_bus.register("test_event", handler2)

        # Create and publish event
        event = basefunctions.Event("test_event")
        event_bus.publish(event)

        # Verify both handlers were called
        handler1.handle.assert_called_once_with(event)
        handler2.handle.assert_called_once_with(event)

    def test_handler_exception_handling(self):
        """Test that exceptions in handlers are caught and don't block other handlers."""
        event_bus = basefunctions.EventBus()

        # Create handlers - one that raises exception
        handler1 = Mock(spec=basefunctions.EventHandler)
        handler1.handle.side_effect = Exception("Test exception")
        handler1.get_priority.return_value = 0

        handler2 = Mock(spec=basefunctions.EventHandler)
        handler2.get_priority.return_value = 0

        # Register handlers
        event_bus.register("test_event", handler1)
        event_bus.register("test_event", handler2)

        # Create and publish event - should not raise exception
        event = basefunctions.Event("test_event")
        event_bus.publish(event)

        # Verify both handlers were called
        handler1.handle.assert_called_once_with(event)
        handler2.handle.assert_called_once_with(event)

    def test_handler_priority(self):
        """Test that handlers are called in priority order."""
        event_bus = basefunctions.EventBus()

        # Create handlers with different priorities
        handler_low = Mock(spec=basefunctions.EventHandler)
        handler_low.get_priority.return_value = 0

        handler_high = Mock(spec=basefunctions.EventHandler)
        handler_high.get_priority.return_value = 10

        # Register in reverse priority order
        event_bus.register("test_event", handler_low)
        event_bus.register("test_event", handler_high)

        # Keep track of call order
        call_order = []
        handler_low.handle.side_effect = lambda e: call_order.append("low")
        handler_high.handle.side_effect = lambda e: call_order.append("high")

        # Create and publish event
        event = basefunctions.Event("test_event")
        event_bus.publish(event)

        # Verify handlers were called in priority order (high first)
        assert call_order == ["high", "low"]

    def test_unregister_handler(self):
        """Test that handlers can be unregistered."""
        event_bus = basefunctions.EventBus()

        # Create and register handler
        handler = Mock(spec=basefunctions.EventHandler)
        handler.get_priority.return_value = 0

        event_bus.register("test_event", handler)

        # Unregister
        result = event_bus.unregister("test_event", handler)

        # Verify unregistration
        assert result is True
        assert len(event_bus._handlers.get("test_event", [])) == 0

        # Publish and verify handler not called
        event = basefunctions.Event("test_event")
        event_bus.publish(event)
        handler.handle.assert_not_called()

        # Try to unregister again
        result = event_bus.unregister("test_event", handler)
        assert result is False

    def test_unregister_all(self):
        """Test unregistering a handler from all event types."""
        event_bus = basefunctions.EventBus()

        # Create and register handler for multiple events
        handler = Mock(spec=basefunctions.EventHandler)
        handler.get_priority.return_value = 0

        event_bus.register("event1", handler)
        event_bus.register("event2", handler)

        # Unregister from all
        event_bus.unregister_all(handler)

        # Verify unregistration
        assert len(event_bus._handlers.get("event1", [])) == 0
        assert len(event_bus._handlers.get("event2", [])) == 0

    def test_clear(self):
        """Test clearing all handlers."""
        event_bus = basefunctions.EventBus()

        # Register multiple handlers
        handler1 = Mock(spec=basefunctions.EventHandler)
        handler1.get_priority.return_value = 0

        handler2 = Mock(spec=basefunctions.EventHandler)
        handler2.get_priority.return_value = 0

        event_bus.register("event1", handler1)
        event_bus.register("event2", handler2)

        # Clear all
        event_bus.clear()

        # Verify all handlers cleared
        assert len(event_bus._handlers) == 0
        assert len(event_bus._handler_methods) == 0


class TestEventBusPerformance:
    """Performance tests for EventBus."""

    def test_large_handler_registration(self):
        """Test registering many handlers."""
        event_bus = basefunctions.EventBus()
        handlers = [Mock(spec=basefunctions.EventHandler) for _ in range(100)]

        for i, handler in enumerate(handlers):
            handler.get_priority.return_value = 0
            event_bus.register(f"event{i % 10}", handler)

        # Verify registrations
        assert len(event_bus._handlers) == 10  # 10 event types
        for i in range(10):
            assert len(event_bus._handlers[f"event{i}"]) == 10  # 10 handlers per type

    def test_publish_performance(self):
        """Test publishing events to many handlers."""
        event_bus = basefunctions.EventBus()

        # Register multiple handlers
        handlers = [Mock(spec=basefunctions.EventHandler) for _ in range(10)]
        for handler in handlers:
            handler.get_priority.return_value = 0
            event_bus.register("test_event", handler)

        # Publish multiple events
        for _ in range(100):
            event = basefunctions.Event("test_event")
            event_bus.publish(event)

        # Verify all handlers were called appropriate number of times
        for handler in handlers:
            assert handler.handle.call_count == 100
