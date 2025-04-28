"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Tests for the observer pattern in basefunctions

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import basefunctions as bf

# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DummyObserver(bf.Observer):
    def __init__(self):
        self.received = []

    def notify(self, message, *args, **kwargs):
        self.received.append((message, args, kwargs))


def test_attach_and_notify():
    subject = bf.Subject()
    observer = DummyObserver()

    subject.attach_observer(observer)
    subject.notify_observers("test_message", 1, 2, key="value")

    assert len(observer.received) == 1
    msg, args, kwargs = observer.received[0]
    assert msg == "test_message"
    assert args == (1, 2)
    assert kwargs == {"key": "value"}


def test_detach_observer():
    subject = bf.Subject()
    observer = DummyObserver()

    subject.attach_observer(observer)
    subject.detach_observer(observer)
    subject.notify_observers("another_message")

    assert len(observer.received) == 0


def test_attach_invalid_observer():
    subject = bf.Subject()
    with pytest.raises(TypeError):
        subject.attach_observer(object())


def test_multiple_observers_notification():
    subject = bf.Subject()
    observer1 = DummyObserver()
    observer2 = DummyObserver()

    subject.attach_observer(observer1)
    subject.attach_observer(observer2)

    subject.notify_observers("multi_message", 42)

    assert len(observer1.received) == 1
    assert len(observer2.received) == 1
    assert observer1.received[0][0] == "multi_message"
    assert observer2.received[0][0] == "multi_message"


def test_multiple_attach_same_observer():
    subject = bf.Subject()
    observer = DummyObserver()

    subject.attach_observer(observer)
    subject.attach_observer(observer)
    subject.notify_observers("only_once")

    assert len(observer.received) == 1
    assert observer.received[0][0] == "only_once"
