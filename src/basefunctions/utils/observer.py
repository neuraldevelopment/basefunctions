"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any

# -------------------------------------------------------------
#  FUNCTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------


class Observer(ABC):
    """
    The Observer interface declares the notify method, used by subjects.
    """

    @abstractmethod
    def notify(self, message: Any, *args, **kwargs) -> None:
        """
        Receive notification from subject.

        Parameters
        ----------
        message : Any
            The message sent by the subject to the observers.
        args : Any
            Additional arguments passed from the subject.
        kwargs : Any
            Additional keyword arguments passed from the subject.
        """
        pass


class Subject:
    """
    The Subject class manages observers and notifies them of events.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the list of observers.
        """
        self._observers = []

    def attach_observer(self, observer: Observer) -> None:
        """
        Attach an observer to the subject if it's not already attached.

        Parameters
        ----------
        observer : Observer
            The observer to attach to the subject.
        """
        if not isinstance(observer, Observer):
            raise TypeError("observer must be an instance of Observer")
        if observer not in self._observers:
            self._observers.append(observer)

    def detach_observer(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.

        Parameters
        ----------
        observer : Observer
            The observer to detach from the subject.
        """
        self._observers.remove(observer)

    def notify_observers(self, message: Any, *args, **kwargs) -> None:
        """
        Notify all observers about an event.

        Parameters
        ----------
        message : Any
            The message to send to the observers.
        args : Any
            Additional arguments to pass to the observers.
        kwargs : Any
            Additional keyword arguments to pass to the observers.
        """
        for observer in self._observers:
            observer.notify(message, *args, **kwargs)
