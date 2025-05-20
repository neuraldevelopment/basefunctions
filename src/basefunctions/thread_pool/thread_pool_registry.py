"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Registry for thread pool task handlers

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import os
from typing import Any, Dict, List, Optional, Type, Union
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
_DEFAULT_INSTANCE = None

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ThreadPoolRegistry:
    """
    Central registry for thread pool task handlers.

    This class provides a single point of registration for all thread
    and corelet handlers, ensuring consistent access across the application.
    """

    __slots__ = (
        "_thread_handlers",
        "_corelet_handlers",
        "_logger",
        "_worker_handler",
        "_corelet_handler",
    )

    def __init__(self):
        """
        Initialize a new thread pool registry.
        """
        self._thread_handlers: Dict[str, Type[basefunctions.ThreadPoolRequestInterface]] = {}
        self._corelet_handlers: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)

        # Create handlers for thread and corelet tasks
        self._worker_handler = basefunctions.ThreadPoolWorkerHandler()
        self._corelet_handler = basefunctions.ThreadPoolCoreletHandler()

        # Subscribe handlers to event bus
        self._subscribe_handlers()

    def _subscribe_handlers(self) -> None:
        """
        Subscribe worker and corelet handlers to the event bus.
        """
        event_bus = basefunctions.get_event_bus()

        # Subscribe worker handler
        event_bus.register(
            basefunctions.ThreadPoolTaskEvent.event_type,
            self._worker_handler,
            self._worker_handler.can_handle,
        )

        # Subscribe corelet handler
        event_bus.register(
            basefunctions.ThreadPoolTaskEvent.event_type,
            self._corelet_handler,
            self._corelet_handler.can_handle,
        )

        self._logger.info("Thread pool registry handlers subscribed to event bus")

    def register_thread_handler(
        self, task_type: str, handler_class: Type[basefunctions.ThreadPoolRequestInterface]
    ) -> None:
        """
        Register a thread-based task handler.

        Parameters
        ----------
        task_type : str
            The type of tasks this handler should process
        handler_class : Type[basefunctions.ThreadPoolRequestInterface]
            The handler class to register

        Raises
        ------
        TypeError
            If handler_class is not a ThreadPoolRequestInterface subclass
        """
        if not (
            isinstance(handler_class, type)
            and issubclass(handler_class, basefunctions.ThreadPoolRequestInterface)
        ):
            raise TypeError("Handler must be a ThreadPoolRequestInterface subclass")

        # Register with worker handler
        self._worker_handler.register_task_handler(task_type, handler_class)

        # Store in registry
        self._thread_handlers[task_type] = handler_class

        self._logger.info(
            f"Registered thread handler '{handler_class.__name__}' for task type '{task_type}'"
        )

    def register_corelet_handler(self, task_type: str, corelet_path: str) -> None:
        """
        Register a corelet-based task handler.

        Parameters
        ----------
        task_type : str
            The type of tasks this handler should process
        corelet_path : str
            Path to the corelet file

        Raises
        ------
        FileNotFoundError
            If the corelet file does not exist
        """
        if not os.path.exists(corelet_path):
            raise FileNotFoundError(f"Corelet file not found: {corelet_path}")

        # Register with corelet handler
        self._corelet_handler.register_corelet_handler(task_type, corelet_path)

        # Store in registry
        self._corelet_handlers[task_type] = corelet_path

        self._logger.info(
            f"Registered corelet handler at '{corelet_path}' for task type '{task_type}'"
        )

    def submit_task(
        self,
        task_type: str,
        content: Any = None,
        timeout: int = 5,
        retry_max: int = 3,
        corelet_filename: Optional[str] = None,
    ) -> str:
        """
        Submit a task for execution.

        Parameters
        ----------
        task_type : str
            The type of task to execute
        content : Any, optional
            The content/payload of the task
        timeout : int, default=5
            Timeout in seconds for task execution
        retry_max : int, default=3
            Maximum number of retry attempts
        corelet_filename : str, optional
            Path to corelet file for process-based execution

        Returns
        -------
        str
            The unique ID of the submitted task

        Raises
        ------
        ValueError
            If no handler is registered for the task type
        """
        # Check if a handler is registered
        if (
            task_type not in self._thread_handlers
            and task_type not in self._corelet_handlers
            and not corelet_filename
        ):
            raise ValueError(f"No handler registered for task type: {task_type}")

        # Create task request event
        task_event = basefunctions.ThreadPoolTaskEvent(
            task_type=task_type,
            content=content,
            source=self,
            timeout=timeout,
            retry_max=retry_max,
            corelet_filename=corelet_filename or self._corelet_handlers.get(task_type),
        )

        # Publish to event bus
        basefunctions.get_event_bus().publish(task_event)

        return task_event.task_id

    def get_thread_handlers(self) -> Dict[str, Type[basefunctions.ThreadPoolRequestInterface]]:
        """
        Get all registered thread handlers.

        Returns
        -------
        Dict[str, Type[basefunctions.ThreadPoolRequestInterface]]
            Dictionary mapping task types to handler classes
        """
        return self._thread_handlers.copy()

    def get_corelet_handlers(self) -> Dict[str, str]:
        """
        Get all registered corelet handlers.

        Returns
        -------
        Dict[str, str]
            Dictionary mapping task types to corelet paths
        """
        return self._corelet_handlers.copy()

    def get_handler_for_task(
        self, task_type: str
    ) -> Union[Type[basefunctions.ThreadPoolRequestInterface], str, None]:
        """
        Get the handler for a specific task type.

        Parameters
        ----------
        task_type : str
            The task type to get a handler for

        Returns
        -------
        Union[Type[basefunctions.ThreadPoolRequestInterface], str, None]
            Thread handler class, corelet path, or None if not found
        """
        # Check thread handlers first
        if task_type in self._thread_handlers:
            return self._thread_handlers[task_type]

        # Then check corelet handlers
        if task_type in self._corelet_handlers:
            return self._corelet_handlers[task_type]

        # No handler found
        return None


def get_thread_pool_registry() -> ThreadPoolRegistry:
    """
    Get the default ThreadPoolRegistry instance.

    Returns
    -------
    ThreadPoolRegistry
        The default thread pool registry instance
    """
    global _DEFAULT_INSTANCE
    if _DEFAULT_INSTANCE is None:
        _DEFAULT_INSTANCE = ThreadPoolRegistry()
    return _DEFAULT_INSTANCE
