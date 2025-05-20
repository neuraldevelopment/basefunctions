"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unit tests for Subscription and CompositeSubscription classes
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
class TestSubscription:
    """Tests for the Subscription class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = Mock(spec=basefunctions.EventBus)
        self.handler = Mock(spec=basefunctions.EventHandler)
        self.filter_func = Mock(return_value=True)

        self.handler_entry = (self.handler, self.filter_func)
        self.method_entry = (self.handler, self.handler.handle, self.filter_func)

        self.subscription = basefunctions.Subscription(
            self.event_bus, "test_event", self.handler_entry, self.method_entry
        )

    def test_initialization(self):
        """Test subscription initialization."""
        # Verify internal state
        assert self.subscription._event_bus is self.event_bus
        assert self.subscription._event_type == "test_event"
        assert self.subscription._handler_entry is self.handler_entry
        assert self.subscription._method_entry is self.method_entry
        assert self.subscription._active is True

        # Check properties
        assert self.subscription.is_active is True
        assert self.subscription.event_type == "test_event"
        assert self.subscription.handler is self.handler

    def test_unsubscribe(self):
        """Test unsubscribing the handler."""
        # Configure mocks
        self.event_bus.unregister.return_value = True

        # Unsubscribe
        result = self.subscription.unsubscribe()

        # Verify
        self.event_bus.unregister.assert_called_once_with("test_event", self.handler)
        assert result is True
        assert self.subscription.is_active is False

    def test_unsubscribe_inactive(self):
        """Test unsubscribing an already inactive subscription."""
        # Make subscription inactive
        self.subscription._active = False

        # Unsubscribe
        result = self.subscription.unsubscribe()

        # Verify
        self.event_bus.unregister.assert_not_called()
        assert result is False

    def test_update_filter(self):
        """Test updating the filter function."""
        # Create a new filter
        new_filter = Mock()

        # Save original entries for comparison
        original_handler_entry = self.handler_entry
        original_method_entry = self.method_entry

        # Update filter
        result = self.subscription.update_filter(new_filter)

        # Verify
        assert result is True

        # The originals should remain unchanged (tuples are immutable)
        assert self.handler_entry is original_handler_entry
        assert self.method_entry is original_method_entry

        # But the subscription's internal entries should be updated
        assert self.subscription._handler_entry[1] is new_filter
        assert self.subscription._method_entry[2] is new_filter

        # The internal entries should be new tuples, not the originals
        assert self.subscription._handler_entry is not original_handler_entry
        assert self.subscription._method_entry is not original_method_entry

    def test_update_filter_inactive(self):
        """Test updating filter of inactive subscription."""
        # Make subscription inactive
        self.subscription._active = False

        # Update filter
        new_filter = Mock()
        result = self.subscription.update_filter(new_filter)

        # Verify
        assert result is False
        assert self.handler_entry[1] is self.filter_func  # Unchanged

    def test_context_manager(self):
        """Test using subscription as a context manager."""
        # Configure mocks
        self.event_bus.unregister.return_value = True

        # Use as context manager
        with self.subscription as sub:
            # Verify it returns self
            assert sub is self.subscription
            # Verify it's active inside the block
            assert self.subscription.is_active is True

        # Verify it's unsubscribed after the block
        self.event_bus.unregister.assert_called_once_with("test_event", self.handler)
        assert self.subscription.is_active is False


class TestCompositeSubscription:
    """Tests for the CompositeSubscription class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock subscriptions
        self.sub1 = Mock(spec=basefunctions.Subscription)
        self.sub1.is_active = True

        self.sub2 = Mock(spec=basefunctions.Subscription)
        self.sub2.is_active = True

        # Create composite
        self.composite = basefunctions.CompositeSubscription()

    def test_initialization(self):
        """Test composite subscription initialization."""
        # Verify it starts empty
        assert hasattr(self.composite, "_subscriptions")
        assert len(self.composite._subscriptions) == 0

    def test_add(self):
        """Test adding subscriptions."""
        # Add subscriptions
        result1 = self.composite.add(self.sub1)
        result2 = self.composite.add(self.sub2)

        # Verify
        assert result1 is self.composite  # Returns self for chaining
        assert result2 is self.composite
        assert len(self.composite._subscriptions) == 2
        assert self.sub1 in self.composite._subscriptions
        assert self.sub2 in self.composite._subscriptions

    def test_is_active(self):
        """Test checking if any subscription is active."""
        # Empty composite
        assert self.composite.is_active is False

        # With active subscriptions
        self.composite.add(self.sub1)
        assert self.composite.is_active is True

        # With one inactive subscription
        self.sub1.is_active = False
        assert self.composite.is_active is False

        # With mixed subscriptions
        self.composite.add(self.sub2)
        self.sub1.is_active = False
        self.sub2.is_active = True
        assert self.composite.is_active is True

    def test_unsubscribe_all(self):
        """Test unsubscribing all subscriptions."""
        # Add subscriptions
        self.composite.add(self.sub1)
        self.composite.add(self.sub2)

        # Unsubscribe all
        self.composite.unsubscribe_all()

        # Verify
        self.sub1.unsubscribe.assert_called_once()
        self.sub2.unsubscribe.assert_called_once()
        assert len(self.composite._subscriptions) == 0

    def test_context_manager(self):
        """Test using composite subscription as a context manager."""
        # Add subscriptions
        self.composite.add(self.sub1)
        self.composite.add(self.sub2)

        # Use as context manager
        with self.composite as comp:
            # Verify it returns self
            assert comp is self.composite
            # Verify subscriptions are unchanged inside the block
            assert len(self.composite._subscriptions) == 2

        # Verify all are unsubscribed after the block
        self.sub1.unsubscribe.assert_called_once()
        self.sub2.unsubscribe.assert_called_once()
        assert len(self.composite._subscriptions) == 0

    def test_chained_operations(self):
        """Test chaining operations."""
        # Configure mock
        sub3 = Mock(spec=basefunctions.Subscription)

        # Chain operations
        result = self.composite.add(self.sub1).add(self.sub2).add(sub3)

        # Verify
        assert result is self.composite
        assert len(self.composite._subscriptions) == 3
