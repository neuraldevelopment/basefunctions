"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Unit tests for Observer and Observable classes

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import Mock, patch
import basefunctions
from basefunctions import Observer, Observable

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
class ConcreteObserver(Observer):
    """Concrete implementation of the Observer interface for testing."""

    def __init__(self):
        """Initialize tracking variables."""
        self.notifications = []
        self.last_message = None
        self.last_args = None
        self.last_kwargs = None

    def notify(self, message, *args, **kwargs):
        """Record notification details."""
        self.notifications.append((message, args, kwargs))
        self.last_message = message
        self.last_args = args
        self.last_kwargs = kwargs


class TestObserver:
    """Tests for the Observer interface and implementations."""

    def test_concrete_observer_implements_interface(self):
        """Test that concrete observer properly implements the interface."""
        observer = ConcreteObserver()
        assert isinstance(observer, Observer)

    def test_observer_notify_method(self):
        """Test that notify method properly records notifications."""
        observer = ConcreteObserver()
        observer.notify("test_message", 1, 2, key="value")

        assert len(observer.notifications) == 1
        assert observer.last_message == "test_message"
        assert observer.last_args == (1, 2)
        assert observer.last_kwargs == {"key": "value"}

        # Test multiple notifications
        observer.notify("another_message")
        assert len(observer.notifications) == 2


class TestObservable:
    """Tests for the Observable class."""

    def test_initialization(self):
        """Test that Observable initializes properly."""
        observable = Observable()
        assert hasattr(observable, "_observers")
        assert isinstance(observable._observers, dict)
        assert len(observable._observers) == 0

    def test_attach_observer_for_event(self):
        """Test attaching observers to specific events."""
        observable = Observable()
        observer = ConcreteObserver()

        # Attach observer to event
        observable.attach_observer_for_event("test_event", observer)

        # Verify observer was attached
        assert "test_event" in observable._observers
        assert observer in observable._observers["test_event"]
        assert len(observable._observers["test_event"]) == 1

        # Attach same observer again (should not duplicate)
        observable.attach_observer_for_event("test_event", observer)
        assert len(observable._observers["test_event"]) == 1

        # Attach to different event
        observable.attach_observer_for_event("another_event", observer)
        assert "another_event" in observable._observers
        assert observer in observable._observers["another_event"]

    def test_attach_invalid_observer(self):
        """Test that attaching a non-Observer raises TypeError."""
        observable = Observable()
        not_an_observer = object()

        with pytest.raises(TypeError):
            observable.attach_observer_for_event("test_event", not_an_observer)

    def test_detach_observer_for_event(self):
        """Test detaching observers from events."""
        observable = Observable()
        observer = ConcreteObserver()

        # Attach and then detach
        observable.attach_observer_for_event("test_event", observer)
        observable.detach_observer_for_event("test_event", observer)

        # Verify observer was detached
        assert "test_event" in observable._observers
        assert observer not in observable._observers["test_event"]

        # Detach from non-existent event (should not error)
        observable.detach_observer_for_event("nonexistent_event", observer)

        # Detach non-attached observer (should not error)
        other_observer = ConcreteObserver()
        observable.detach_observer_for_event("test_event", other_observer)

    @patch("basefunctions.get_logger")
    def test_logging_on_attach_detach(self, mock_get_logger):
        """Test that attach and detach operations are logged."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        observable = Observable()
        observer = ConcreteObserver()

        # Test attach logging
        observable.attach_observer_for_event("test_event", observer)
        mock_logger.info.assert_called_with(
            "attached observer %s for event %s", "ConcreteObserver", "test_event"
        )

        # Test detach logging
        observable.detach_observer_for_event("test_event", observer)
        mock_logger.info.assert_called_with(
            "detached observer %s from event %s", "ConcreteObserver", "test_event"
        )

    def test_notify_observers(self):
        """Test notifying observers for specific events."""
        observable = Observable()
        observer1 = ConcreteObserver()
        observer2 = ConcreteObserver()

        # Attach multiple observers to different events
        observable.attach_observer_for_event("event1", observer1)
        observable.attach_observer_for_event("event2", observer2)
        observable.attach_observer_for_event("event1", observer2)

        # Notify event1 observers
        test_message = "test_message"
        test_arg = 42
        test_kwarg = {"key": "value"}
        observable.notify_observers("event1", test_message, test_arg, **test_kwarg)

        # Verify event1 observers received notification
        assert observer1.last_message == test_message
        assert observer1.last_args == (test_arg,)
        assert observer1.last_kwargs == test_kwarg

        assert observer2.last_message == test_message
        assert observer2.last_args == (test_arg,)
        assert observer2.last_kwargs == test_kwarg

        # Reset observer2
        observer2.last_message = None
        observer2.last_args = None
        observer2.last_kwargs = None

        # Notify event2 observers
        new_message = "new_message"
        observable.notify_observers("event2", new_message)

        # Verify only event2 observers got the new notification
        assert observer1.last_message == test_message  # unchanged
        assert observer2.last_message == new_message

        # Notify for non-existent event (should not error)
        observable.notify_observers("nonexistent_event", "message")

    def test_observer_integration(self):
        """Integration test of the complete Observer pattern."""
        observable = Observable()
        observer1 = ConcreteObserver()
        observer2 = ConcreteObserver()

        # Setup observation
        observable.attach_observer_for_event("event", observer1)
        observable.attach_observer_for_event("event", observer2)

        # Initial notification
        observable.notify_observers("event", "initial")
        assert observer1.notifications[-1][0] == "initial"
        assert observer2.notifications[-1][0] == "initial"

        # Detach observ
