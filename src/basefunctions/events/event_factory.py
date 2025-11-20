"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Factory for creating event handlers

 Log:
 v1.0 : Initial implementation
 v2.0 : Converted from class methods to instance methods for proper singleton pattern
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Type
import threading
from basefunctions.utils.logging import setup_logger
import basefunctions

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


@basefunctions.singleton
class EventFactory:
    """
    Singleton factory for managing event handler registration and creation.

    EventFactory provides a centralized registry for event handler classes
    and creates handler instances on demand. It implements the Factory pattern
    with singleton behavior to ensure a single global handler registry across
    the application.

    The factory is thread-safe and supports concurrent registration and handler
    creation. Handlers are registered by event_type and can be instantiated with
    custom constructor arguments.

    Attributes
    ----------
    _handler_registry : Dict[str, Type[EventHandler]]
        Thread-safe registry mapping event types to handler classes
    _lock : threading.RLock
        Reentrant lock for thread-safe registry operations

    Notes
    -----
    **Singleton Pattern:**
    - Only one EventFactory instance exists per process
    - Decorator ensures thread-safe singleton creation
    - Shared across EventBus, CoreletWorker, and user code

    **Handler Registration:**
    - Handlers registered before events can be published
    - Registration is permanent (no unregister support)
    - Duplicate registrations overwrite previous handlers
    - Internal handlers (_shutdown, _cmd_execution) auto-registered

    **Thread Safety:**
    - All public methods protected by RLock
    - Safe for concurrent registration and creation
    - Handler classes must be thread-safe if used in THREAD mode

    **Corelet Support:**
    - get_handler_meta() provides serializable handler metadata
    - Enables dynamic handler loading in worker processes
    - Handler classes must be importable in worker process

    Examples
    --------
    Register custom event handler:

    >>> factory = EventFactory()
    >>> factory.register_event_type("data_process", DataProcessHandler)

    Create handler instance:

    >>> handler = factory.create_handler("data_process")
    >>> isinstance(handler, DataProcessHandler)
    True

    Check handler availability:

    >>> factory.is_handler_available("data_process")
    True
    >>> factory.is_handler_available("unknown_event")
    False

    Get handler metadata for corelet:

    >>> meta = factory.get_handler_meta("data_process")
    >>> meta['module_path']
    'myapp.handlers'
    >>> meta['class_name']
    'DataProcessHandler'

    List all registered event types:

    >>> factory.get_supported_event_types()
    ['data_process', 'file_upload', '_shutdown', '_cmd_execution']

    See Also
    --------
    EventBus : Uses factory to create handlers for events
    CoreletWorker : Uses factory metadata for dynamic handler loading
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handler_registry: dict[str, type[basefunctions.EventHandler]] = {}

    def register_event_type(self, event_type: str, event_handler_class: type[basefunctions.EventHandler]) -> None:
        """
        Register a new event handler type.

        Parameters
        ----------
        event_type : str
            Unique identifier for the event type
        event_handler_class : Type[basefunctions.EventHandler]
            Handler class implementing EventHandler interface

        Raises
        ------
        ValueError
            If parameters are invalid
        """
        if not event_type:
            raise ValueError("event_type cannot be empty")
        if not event_handler_class:
            raise ValueError("event_handler_class cannot be None")

        with self._lock:
            self._handler_registry[event_type] = event_handler_class

    def create_handler(self, event_type: str, *args, **kwargs) -> basefunctions.EventHandler:
        """
        Create a handler instance for the specified event type.

        Parameters
        ----------
        event_type : str
            Event type identifier for which to create a handler
        *args
            Positional arguments passed to handler constructor
        **kwargs
            Keyword arguments passed to handler constructor

        Returns
        -------
        basefunctions.EventHandler
            New handler instance configured for the event type

        Raises
        ------
        ValueError
            If event_type is invalid or not registered
        RuntimeError
            If handler creation fails
        """
        if not event_type:
            raise ValueError("event_type cannot be empty")

        with self._lock:
            if event_type not in self._handler_registry:
                raise ValueError(f"No handler registered for event type '{event_type}'")

            try:
                handler_class = self._handler_registry[event_type]
                handler = handler_class(*args, **kwargs)
                return handler
            except Exception as e:
                raise RuntimeError(f"Failed to create handler for event type '{event_type}': {str(e)}") from e

    def is_handler_available(self, event_type: str) -> bool:
        """
        Check if a handler is available for the specified event type.

        Parameters
        ----------
        event_type : str
            Event type identifier

        Returns
        -------
        bool
            True if handler is available, False otherwise
        """
        if not event_type:
            return False

        with self._lock:
            return event_type in self._handler_registry

    def get_handler_type(self, event_type: str) -> type[basefunctions.EventHandler]:
        """
        Get the handler class for the specified event type.

        Parameters
        ----------
        event_type : str
            Event type identifier

        Returns
        -------
        Type[basefunctions.EventHandler]
            Handler class registered for the event type

        Raises
        ------
        ValueError
            If event_type is not registered
        """
        if event_type in self._handler_registry.keys():
            return self._handler_registry[event_type]

        raise ValueError(f"No handler registered for event type '{event_type}'")

    def get_handler_meta(self, event_type: str) -> dict[str, str]:
        """
        Get handler metadata for corelet registration.

        Parameters
        ----------
        event_type : str
            Event type identifier

        Returns
        -------
        dict
            Handler metadata with module_path and class_name

        Raises
        ------
        ValueError
            If event_type is not registered
        """
        if not event_type:
            raise ValueError("event_type cannot be empty")

        with self._lock:
            if event_type not in self._handler_registry:
                raise ValueError(f"No handler registered for event type '{event_type}'")

            handler_class = self._handler_registry[event_type]
            return {
                "module_path": handler_class.__module__,
                "class_name": handler_class.__name__,
                "event_type": event_type,
            }

    def get_supported_event_types(self) -> list[str]:
        """
        Get list of all supported event types.

        Returns
        -------
        list[str]
            List of supported event type identifiers
        """
        with self._lock:
            return list(self._handler_registry.keys())
