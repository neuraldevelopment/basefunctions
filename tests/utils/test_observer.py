"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for observer.py.
 Tests Observer pattern implementation with ABC Observer and Observable classes.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import pytest
from typing import Any, List
from unittest.mock import Mock, patch

# Project imports (relative to project root)
from basefunctions.utils.observer import Observer, Observable

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def concrete_observer_class() -> type:
    """
    Create a concrete Observer implementation for testing.

    Returns
    -------
    type
        Concrete Observer subclass with notify implementation

    Notes
    -----
    Creates a minimal viable Observer that tracks notify calls
    """

    # ARRANGE
    class ConcreteObserver(Observer):
        """Test implementation of Observer."""

        def __init__(self) -> None:
            """Initialize with call tracking."""
            self.notify_calls: List[tuple] = []

        def notify(self, message: Any, *args, **kwargs) -> None:
            """Record notify call for verification."""
            self.notify_calls.append((message, args, kwargs))

    # RETURN
    return ConcreteObserver


@pytest.fixture
def mock_observer(concrete_observer_class: type) -> Observer:
    """
    Create a mock Observer instance for testing.

    Parameters
    ----------
    concrete_observer_class : type
        Fixture providing concrete Observer implementation

    Returns
    -------
    Observer
        Instance of concrete Observer with notify tracking

    Notes
    -----
    Provides fresh Observer instance for each test
    """
    # RETURN
    return concrete_observer_class()


@pytest.fixture
def observable() -> Observable:
    """
    Create fresh Observable instance for testing.

    Returns
    -------
    Observable
        New Observable instance with empty observers

    Notes
    -----
    Ensures test isolation by providing clean Observable
    """
    # RETURN
    return Observable()


@pytest.fixture
def populated_observable(observable: Observable, mock_observer: Observer) -> Observable:
    """
    Create Observable with pre-registered observer.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    mock_observer : Observer
        Mock observer to register

    Returns
    -------
    Observable
        Observable with observer registered for 'test_event'

    Notes
    -----
    Used for testing detach and notify operations
    """
    # ARRANGE
    observable.attach_observer_for_event("test_event", mock_observer)

    # RETURN
    return observable


# -------------------------------------------------------------
# TEST CASES: Observer (Abstract Base Class)
# -------------------------------------------------------------


def test_observer_cannot_be_instantiated_directly() -> None:  # IMPORTANT TEST
    """
    Test Observer ABC cannot be instantiated without implementation.

    Tests that attempting to create Observer instance directly
    raises TypeError due to abstract notify method.

    Returns
    -------
    None
        Test passes if TypeError raised
    """
    # ACT & ASSERT
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        Observer()


def test_observer_can_be_subclassed_with_notify_implementation(
    concrete_observer_class: type,
) -> None:  # IMPORTANT TEST
    """
    Test Observer can be subclassed with notify implementation.

    Tests that concrete Observer subclass with notify method
    can be instantiated successfully.

    Parameters
    ----------
    concrete_observer_class : type
        Fixture providing concrete Observer implementation

    Returns
    -------
    None
        Test passes if instance created and notify callable
    """
    # ACT
    observer: Observer = concrete_observer_class()

    # ASSERT
    assert isinstance(observer, Observer)
    assert callable(observer.notify)


# -------------------------------------------------------------
# TEST CASES: Observable.__init__
# -------------------------------------------------------------


def test_observable_initializes_with_empty_observers_dict() -> None:  # IMPORTANT TEST
    """
    Test Observable initializes with empty observers dictionary.

    Tests that new Observable has empty _observers dict
    ready to accept event registrations.

    Returns
    -------
    None
        Test passes if _observers is empty dict
    """
    # ACT
    obs: Observable = Observable()

    # ASSERT
    assert hasattr(obs, "_observers")
    assert obs._observers == {}
    assert isinstance(obs._observers, dict)


def test_observable_init_accepts_arbitrary_args_kwargs() -> None:  # IMPORTANT TEST
    """
    Test Observable.__init__ accepts arbitrary args and kwargs.

    Tests that Observable constructor accepts but ignores
    additional arguments for future extensibility.

    Returns
    -------
    None
        Test passes if Observable created successfully
    """
    # ACT
    obs: Observable = Observable("arg1", "arg2", key1="value1", key2="value2")

    # ASSERT
    assert obs._observers == {}


# -------------------------------------------------------------
# TEST CASES: attach_observer_for_event
# -------------------------------------------------------------


def test_attach_observer_adds_observer_to_new_event_type(observable: Observable, mock_observer: Observer) -> None:
    """
    Test attach_observer creates new event type and adds observer.

    Tests that attaching observer to non-existent event type
    creates the event type and registers the observer.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    mock_observer : Observer
        Mock observer to attach

    Returns
    -------
    None
        Test passes if observer registered correctly
    """
    # ARRANGE
    event_type: str = "new_event"

    # ACT
    observable.attach_observer_for_event(event_type, mock_observer)

    # ASSERT
    assert event_type in observable._observers
    assert mock_observer in observable._observers[event_type]
    assert len(observable._observers[event_type]) == 1


def test_attach_observer_adds_observer_to_existing_event_type(
    populated_observable: Observable, concrete_observer_class: type
) -> None:
    """
    Test attach_observer adds second observer to existing event.

    Tests that attaching another observer to existing event type
    appends to the observer list without replacing.

    Parameters
    ----------
    populated_observable : Observable
        Observable with one observer already registered
    concrete_observer_class : type
        Observer class for creating second observer

    Returns
    -------
    None
        Test passes if both observers registered
    """
    # ARRANGE
    second_observer: Observer = concrete_observer_class()
    event_type: str = "test_event"
    initial_count: int = len(populated_observable._observers[event_type])

    # ACT
    populated_observable.attach_observer_for_event(event_type, second_observer)

    # ASSERT
    assert len(populated_observable._observers[event_type]) == initial_count + 1
    assert second_observer in populated_observable._observers[event_type]


def test_attach_observer_same_observer_twice_is_idempotent(observable: Observable, mock_observer: Observer) -> None:
    """
    Test attaching same observer twice does not duplicate.

    Tests that re-attaching same observer to same event type
    is idempotent and maintains single registration.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    mock_observer : Observer
        Observer to attach twice

    Returns
    -------
    None
        Test passes if observer appears only once
    """
    # ARRANGE
    event_type: str = "test_event"

    # ACT
    observable.attach_observer_for_event(event_type, mock_observer)
    observable.attach_observer_for_event(event_type, mock_observer)

    # ASSERT
    assert len(observable._observers[event_type]) == 1
    assert observable._observers[event_type][0] is mock_observer


def test_attach_observer_raises_typeerror_when_not_observer_instance(
    observable: Observable,
) -> None:  # CRITICAL TEST
    """
    Test attach_observer raises TypeError for non-Observer object.

    Tests that attempting to attach arbitrary object that doesn't
    inherit from Observer raises TypeError with clear message.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance

    Returns
    -------
    None
        Test passes if TypeError raised
    """
    # ARRANGE
    invalid_observer: str = "not an observer"
    event_type: str = "test_event"

    # ACT & ASSERT
    with pytest.raises(TypeError, match="observer must be an instance of Observer"):
        observable.attach_observer_for_event(event_type, invalid_observer)


def test_attach_observer_raises_typeerror_for_none(observable: Observable) -> None:  # CRITICAL TEST
    """
    Test attach_observer raises TypeError when observer is None.

    Tests that passing None as observer raises TypeError
    preventing null reference issues.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance

    Returns
    -------
    None
        Test passes if TypeError raised
    """
    # ARRANGE
    event_type: str = "test_event"

    # ACT & ASSERT
    with pytest.raises(TypeError, match="observer must be an instance of Observer"):
        observable.attach_observer_for_event(event_type, None)


def test_attach_observer_raises_typeerror_for_arbitrary_object(
    observable: Observable,
) -> None:  # CRITICAL TEST
    """
    Test attach_observer rejects objects without Observer inheritance.

    Tests that objects implementing notify but not inheriting
    from Observer are rejected with TypeError.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance

    Returns
    -------
    None
        Test passes if TypeError raised
    """

    # ARRANGE
    class FakeObserver:
        """Object with notify method but not Observer subclass."""

        def notify(self, message: Any) -> None:
            """Fake notify method."""
            pass

    fake_observer: FakeObserver = FakeObserver()
    event_type: str = "test_event"

    # ACT & ASSERT
    with pytest.raises(TypeError, match="observer must be an instance of Observer"):
        observable.attach_observer_for_event(event_type, fake_observer)


def test_attach_observer_with_empty_string_event_type(observable: Observable, mock_observer: Observer) -> None:
    """
    Test attach_observer handles empty string event type.

    Tests that empty string is valid event type identifier
    and observer can be registered to it.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    mock_observer : Observer
        Mock observer to attach

    Returns
    -------
    None
        Test passes if observer registered to empty string event
    """
    # ARRANGE
    event_type: str = ""

    # ACT
    observable.attach_observer_for_event(event_type, mock_observer)

    # ASSERT
    assert "" in observable._observers
    assert mock_observer in observable._observers[""]


# -------------------------------------------------------------
# TEST CASES: detach_observer_for_event
# -------------------------------------------------------------


def test_detach_observer_removes_observer_from_event_type(
    populated_observable: Observable, mock_observer: Observer
) -> None:
    """
    Test detach_observer removes observer from event type.

    Tests that detaching registered observer removes it
    from the event type's observer list.

    Parameters
    ----------
    populated_observable : Observable
        Observable with observer already registered
    mock_observer : Observer
        Observer to detach

    Returns
    -------
    None
        Test passes if observer removed successfully
    """
    # ARRANGE
    event_type: str = "test_event"
    assert mock_observer in populated_observable._observers[event_type]

    # ACT
    populated_observable.detach_observer_for_event(event_type, mock_observer)

    # ASSERT
    assert mock_observer not in populated_observable._observers[event_type]
    assert len(populated_observable._observers[event_type]) == 0


def test_detach_observer_for_nonexistent_event_type_does_nothing(
    observable: Observable, mock_observer: Observer
) -> None:
    """
    Test detach_observer handles non-existent event type gracefully.

    Tests that attempting to detach observer from non-existent
    event type does not raise exception or modify state.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    mock_observer : Observer
        Observer to detach

    Returns
    -------
    None
        Test passes if no exception raised
    """
    # ARRANGE
    event_type: str = "nonexistent_event"

    # ACT (no exception expected)
    observable.detach_observer_for_event(event_type, mock_observer)

    # ASSERT
    assert event_type not in observable._observers


def test_detach_observer_not_in_list_does_nothing(
    populated_observable: Observable, concrete_observer_class: type
) -> None:
    """
    Test detach_observer handles observer not in list gracefully.

    Tests that attempting to detach observer not registered
    to event type does not raise exception.

    Parameters
    ----------
    populated_observable : Observable
        Observable with different observer registered
    concrete_observer_class : type
        Observer class for creating unregistered observer

    Returns
    -------
    None
        Test passes if no exception raised and list unchanged
    """
    # ARRANGE
    event_type: str = "test_event"
    different_observer: Observer = concrete_observer_class()
    initial_count: int = len(populated_observable._observers[event_type])

    # ACT (no exception expected)
    populated_observable.detach_observer_for_event(event_type, different_observer)

    # ASSERT
    assert len(populated_observable._observers[event_type]) == initial_count


def test_detach_observer_leaves_other_observers_intact(observable: Observable, concrete_observer_class: type) -> None:
    """
    Test detach_observer removes only specified observer.

    Tests that detaching one observer from event type
    leaves other observers registered and functional.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    concrete_observer_class : type
        Observer class for creating multiple observers

    Returns
    -------
    None
        Test passes if only target observer removed
    """
    # ARRANGE
    event_type: str = "test_event"
    observer1: Observer = concrete_observer_class()
    observer2: Observer = concrete_observer_class()
    observer3: Observer = concrete_observer_class()

    observable.attach_observer_for_event(event_type, observer1)
    observable.attach_observer_for_event(event_type, observer2)
    observable.attach_observer_for_event(event_type, observer3)

    # ACT
    observable.detach_observer_for_event(event_type, observer2)

    # ASSERT
    assert observer1 in observable._observers[event_type]
    assert observer2 not in observable._observers[event_type]
    assert observer3 in observable._observers[event_type]
    assert len(observable._observers[event_type]) == 2


# -------------------------------------------------------------
# TEST CASES: notify_observers
# -------------------------------------------------------------


def test_notify_observers_calls_all_registered_observers(
    observable: Observable, concrete_observer_class: type
) -> None:  # CRITICAL TEST
    """
    Test notify_observers invokes all registered observers.

    Tests that notifying event type calls notify method
    on all observers registered to that event.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    concrete_observer_class : type
        Observer class for creating multiple observers

    Returns
    -------
    None
        Test passes if all observers received notification
    """
    # ARRANGE
    event_type: str = "test_event"
    observer1: Observer = concrete_observer_class()
    observer2: Observer = concrete_observer_class()
    observer3: Observer = concrete_observer_class()

    observable.attach_observer_for_event(event_type, observer1)
    observable.attach_observer_for_event(event_type, observer2)
    observable.attach_observer_for_event(event_type, observer3)

    message: str = "test message"

    # ACT
    observable.notify_observers(event_type, message)

    # ASSERT
    assert len(observer1.notify_calls) == 1
    assert len(observer2.notify_calls) == 1
    assert len(observer3.notify_calls) == 1


def test_notify_observers_passes_message_correctly(
    populated_observable: Observable, mock_observer: Observer
) -> None:  # CRITICAL TEST
    """
    Test notify_observers passes message parameter correctly.

    Tests that message argument provided to notify_observers
    is forwarded to observer's notify method.

    Parameters
    ----------
    populated_observable : Observable
        Observable with observer registered
    mock_observer : Observer
        Observer tracking notify calls

    Returns
    -------
    None
        Test passes if message received correctly
    """
    # ARRANGE
    event_type: str = "test_event"
    message: dict = {"key": "value", "number": 42}

    # ACT
    populated_observable.notify_observers(event_type, message)

    # ASSERT
    assert len(mock_observer.notify_calls) == 1
    received_message, _, _ = mock_observer.notify_calls[0]
    assert received_message == message


def test_notify_observers_passes_args_and_kwargs_correctly(
    populated_observable: Observable, mock_observer: Observer
) -> None:  # CRITICAL TEST
    """
    Test notify_observers forwards args and kwargs correctly.

    Tests that additional positional and keyword arguments
    are passed through to observer's notify method.

    Parameters
    ----------
    populated_observable : Observable
        Observable with observer registered
    mock_observer : Observer
        Observer tracking notify calls

    Returns
    -------
    None
        Test passes if args and kwargs forwarded correctly
    """
    # ARRANGE
    event_type: str = "test_event"
    message: str = "message"
    extra_args: tuple = ("arg1", "arg2", 123)
    extra_kwargs: dict = {"key1": "value1", "key2": 456}

    # ACT
    populated_observable.notify_observers(event_type, message, *extra_args, **extra_kwargs)

    # ASSERT
    assert len(mock_observer.notify_calls) == 1
    received_message, received_args, received_kwargs = mock_observer.notify_calls[0]
    assert received_message == message
    assert received_args == extra_args
    assert received_kwargs == extra_kwargs


def test_notify_observers_for_nonexistent_event_type_does_nothing(observable: Observable) -> None:
    """
    Test notify_observers handles non-existent event type gracefully.

    Tests that notifying non-existent event type does not
    raise exception or cause errors.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance

    Returns
    -------
    None
        Test passes if no exception raised
    """
    # ARRANGE
    event_type: str = "nonexistent_event"
    message: str = "message"

    # ACT (no exception expected)
    observable.notify_observers(event_type, message)

    # ASSERT
    assert event_type not in observable._observers


def test_notify_observers_with_no_observers_does_nothing(observable: Observable) -> None:
    """
    Test notify_observers handles empty observer list gracefully.

    Tests that notifying event type with empty observer list
    completes without error.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance

    Returns
    -------
    None
        Test passes if no exception raised
    """
    # ARRANGE
    event_type: str = "test_event"
    observable._observers[event_type] = []  # Empty list
    message: str = "message"

    # ACT (no exception expected)
    observable.notify_observers(event_type, message)

    # ASSERT
    assert observable._observers[event_type] == []


def test_notify_observers_with_none_message(populated_observable: Observable, mock_observer: Observer) -> None:
    """
    Test notify_observers handles None message correctly.

    Tests that None can be passed as message parameter
    and is forwarded to observers correctly.

    Parameters
    ----------
    populated_observable : Observable
        Observable with observer registered
    mock_observer : Observer
        Observer tracking notify calls

    Returns
    -------
    None
        Test passes if None message received
    """
    # ARRANGE
    event_type: str = "test_event"
    message: None = None

    # ACT
    populated_observable.notify_observers(event_type, message)

    # ASSERT
    assert len(mock_observer.notify_calls) == 1
    received_message, _, _ = mock_observer.notify_calls[0]
    assert received_message is None


def test_notify_observers_continues_on_observer_exception(
    observable: Observable, concrete_observer_class: type
) -> None:  # CRITICAL TEST
    """
    Test notify_observers continues when observer raises exception.

    Tests that if one observer's notify method raises exception,
    subsequent observers still receive notification.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    concrete_observer_class : type
        Observer class for creating observers

    Returns
    -------
    None
        Test passes if exception propagates but doesn't stop notification
    """

    # ARRANGE
    class FailingObserver(Observer):
        """Observer that raises exception on notify."""

        def notify(self, message: Any, *args, **kwargs) -> None:
            """Raise exception when notified."""
            raise RuntimeError("Observer failed")

    class TrackingObserver(Observer):
        """Observer that tracks notify calls."""

        def __init__(self) -> None:
            """Initialize tracking."""
            self.called: bool = False

        def notify(self, message: Any, *args, **kwargs) -> None:
            """Track notification."""
            self.called = True

    event_type: str = "test_event"
    failing_observer: Observer = FailingObserver()
    tracking_observer: Observer = TrackingObserver()

    observable.attach_observer_for_event(event_type, failing_observer)
    observable.attach_observer_for_event(event_type, tracking_observer)

    message: str = "test"

    # ACT & ASSERT
    # Note: Current implementation does NOT catch exceptions
    # This test documents actual behavior - exception propagates
    with pytest.raises(RuntimeError, match="Observer failed"):
        observable.notify_observers(event_type, message)

    # Second observer was not called due to exception
    assert tracking_observer.called is False


# -------------------------------------------------------------
# INTEGRATION TESTS
# -------------------------------------------------------------


def test_attach_notify_detach_workflow(observable: Observable, mock_observer: Observer) -> None:  # CRITICAL TEST
    """
    Test complete attach-notify-detach workflow.

    Tests that full observer lifecycle works correctly:
    attach observer, receive notifications, detach observer.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    mock_observer : Observer
        Mock observer for testing

    Returns
    -------
    None
        Test passes if workflow completes correctly
    """
    # ARRANGE
    event_type: str = "workflow_event"
    message1: str = "first message"
    message2: str = "second message"

    # ACT & ASSERT - Attach
    observable.attach_observer_for_event(event_type, mock_observer)
    assert mock_observer in observable._observers[event_type]

    # ACT & ASSERT - Notify while attached
    observable.notify_observers(event_type, message1)
    assert len(mock_observer.notify_calls) == 1
    assert mock_observer.notify_calls[0][0] == message1

    # ACT & ASSERT - Detach
    observable.detach_observer_for_event(event_type, mock_observer)
    assert mock_observer not in observable._observers[event_type]

    # ACT & ASSERT - Notify after detach (should not receive)
    observable.notify_observers(event_type, message2)
    assert len(mock_observer.notify_calls) == 1  # Still only 1 call


def test_multiple_event_types_with_different_observers(observable: Observable, concrete_observer_class: type) -> None:
    """
    Test multiple event types with separate observer sets.

    Tests that different event types maintain independent
    observer lists without interference.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    concrete_observer_class : type
        Observer class for creating observers

    Returns
    -------
    None
        Test passes if event types remain isolated
    """
    # ARRANGE
    observer1: Observer = concrete_observer_class()
    observer2: Observer = concrete_observer_class()
    observer3: Observer = concrete_observer_class()

    event_type_a: str = "event_a"
    event_type_b: str = "event_b"

    # ACT
    observable.attach_observer_for_event(event_type_a, observer1)
    observable.attach_observer_for_event(event_type_a, observer2)
    observable.attach_observer_for_event(event_type_b, observer3)

    observable.notify_observers(event_type_a, "message_a")
    observable.notify_observers(event_type_b, "message_b")

    # ASSERT
    assert len(observer1.notify_calls) == 1
    assert len(observer2.notify_calls) == 1
    assert len(observer3.notify_calls) == 1

    assert observer1.notify_calls[0][0] == "message_a"
    assert observer2.notify_calls[0][0] == "message_a"
    assert observer3.notify_calls[0][0] == "message_b"


def test_multiple_observers_for_same_event(observable: Observable, concrete_observer_class: type) -> None:
    """
    Test multiple observers receive same event notification.

    Tests that all observers registered to same event type
    receive identical notification with same message.

    Parameters
    ----------
    observable : Observable
        Fresh Observable instance
    concrete_observer_class : type
        Observer class for creating observers

    Returns
    -------
    None
        Test passes if all observers receive identical notification
    """
    # ARRANGE
    observers: List[Observer] = [concrete_observer_class() for _ in range(5)]
    event_type: str = "shared_event"
    message: dict = {"data": "shared", "count": 99}

    for obs in observers:
        observable.attach_observer_for_event(event_type, obs)

    # ACT
    observable.notify_observers(event_type, message)

    # ASSERT
    for obs in observers:
        assert len(obs.notify_calls) == 1
        received_message, _, _ = obs.notify_calls[0]
        assert received_message == message
        assert received_message is message  # Same object reference
