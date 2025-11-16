"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Observer pattern implementation for component communication

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Dict, List
from abc import ABC, abstractmethod

from basefunctions.utils.logging import setup_logger, get_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class Observer(ABC):
    """
    The Observer interface declares the notify method, used by observables.
    """

    @abstractmethod
    def notify(self, message: Any, *args, **kwargs) -> None:
        """
        Receive notification from observable.

        Parameters
        ----------
        message : Any
            The message sent by the observable to the observers.
        args : Any
            Additional arguments passed from the observable.
        kwargs : Any
            Additional keyword arguments passed from the observable.
        """
        pass


class Observable:
    """
    The Observable class manages observers and notifies them of events.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the dictionary of observers by event type.
        """
        self._observers: Dict[str, List[Observer]] = {}

    def attach_observer_for_event(self, event_type: str, observer: Observer) -> None:
        """
        Attaches an observer for a specific event type.

        Parameters
        ----------
        event_type : str
            The specific event type to observe.
        observer : Observer
            The observer to attach.
        """
        if not isinstance(observer, Observer):
            raise TypeError("observer must be an instance of Observer")

        if event_type not in self._observers:
            self._observers[event_type] = []

        if observer not in self._observers[event_type]:
            self._observers[event_type].append(observer)
            get_logger(__name__).info("attached observer %s for event %s", type(observer).__name__, event_type)

    def detach_observer_for_event(self, event_type: str, observer: Observer) -> None:
        """
        Detach an observer from a specific event type.

        Parameters
        ----------
        event_type : str
            The specific event type.
        observer : Observer
            The observer to detach.
        """
        if event_type in self._observers and observer in self._observers[event_type]:
            self._observers[event_type].remove(observer)
            get_logger(__name__).info("detached observer %s from event %s", type(observer).__name__, event_type)

    def notify_observers(self, event_type: str, message: Any, *args, **kwargs) -> None:
        """
        Notify all observers for a specific event type.

        Parameters
        ----------
        event_type : str
            The event type to notify about.
        message : Any
            The message to send to observers.
        args : Any
            Additional arguments to pass to observers.
        kwargs : Any
            Additional keyword arguments to pass to observers.
        """
        if event_type in self._observers:
            for observer in self._observers[event_type]:
                observer.notify(message, *args, **kwargs)
