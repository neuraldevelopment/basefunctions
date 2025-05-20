"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Worker handler for thread pool task execution

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import threading
from typing import Dict, Type
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


class ThreadPoolWorkerHandler(basefunctions.EventHandler):
    """
    Event handler for executing thread-based tasks.

    This handler processes ThreadPoolTaskEvents by invoking the appropriate
    handler from the registry.
    """

    __slots__ = ("_task_registry", "_logger", "_thread_local_data")

    def __init__(self):
        """
        Initialize a new thread pool worker handler.
        """
        self._task_registry: Dict[str, Type[basefunctions.ThreadPoolRequestInterface]] = {}
        self._logger = logging.getLogger(__name__)
        self._thread_local_data = threading.local()

    def register_task_handler(
        self, task_type: str, handler_class: Type[basefunctions.ThreadPoolRequestInterface]
    ) -> None:
        """
        Register a handler for a specific task type.

        Parameters
        ----------
        task_type : str
            The type of tasks this handler can process
        handler_class : Type[basefunctions.ThreadPoolRequestInterface]
            The handler class for processing tasks

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

        self._task_registry[task_type] = handler_class
        self._logger.info(
            f"Registered task handler '{handler_class.__name__}' for task type '{task_type}'"
        )

    def handle(self, event: basefunctions.Event) -> None:
        """
        Handle a task request event.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle (should be a ThreadPoolTaskEvent)
        """
        if not isinstance(event, basefunctions.ThreadPoolTaskEvent):
            return

        task_type = event.task_type
        thread_id = threading.get_ident()

        if task_type not in self._task_registry:
            self._logger.error(f"No handler registered for task type: {task_type}")

            # Create error result
            result = basefunctions.ThreadPoolResultEvent(
                original_task=event,
                success=False,
                error=f"No handler registered for task type: {task_type}",
            )

            # Publish result
            basefunctions.get_event_bus().publish(result)
            return

        # Initialize result variables
        success = False
        result_data = None
        error = None
        exception_type = None
        exception = None

        # Process with retry
        for attempt in range(event.retry_max):
            # Update retry count
            event.increment_retry()

            try:
                # Create context
                context = basefunctions.ThreadPoolContext(
                    thread_local_data=self._thread_local_data
                )

                # Use TimerThread as context manager to enforce timeout
                with basefunctions.TimerThread(event.timeout, thread_id):
                    # Get handler class
                    handler_class = self._task_registry[task_type]

                    # Create handler instance
                    handler = handler_class()

                    # Create thread pool message for backward compatibility
                    message = basefunctions.ThreadPoolMessage(
                        id=event.task_id,
                        message_type=event.task_type,
                        content=event.content,
                        retry=event.retry_count,
                        retry_max=event.retry_max,
                        timeout=event.timeout,
                    )

                    # Execute handler
                    success, result_data = handler.process_request(context, message)

                # If successful, break the retry loop
                if success:
                    break

            except TimeoutError as e:
                success = False
                result_data = None
                error = f"Task execution timed out after {event.timeout} seconds"
                exception_type = "TimeoutError"
                exception = e
                self._logger.error(
                    f"Timeout processing task {event.task_id} (attempt {attempt+1}/{event.retry_max})"
                )

            except Exception as e:
                success = False
                result_data = None
                error = str(e)
                exception_type = type(e).__name__
                exception = e
                self._logger.error(
                    f"Error processing task {event.task_id} (attempt {attempt+1}/{event.retry_max}): {error}"
                )

            # If we're not retrying or max retries reached, break
            if success or attempt >= event.retry_max - 1:
                break

            self._logger.info(f"Retrying task {event.task_id} ({attempt+1}/{event.retry_max})")

        # Create result
        result = basefunctions.ThreadPoolResultEvent(
            original_task=event,
            success=success,
            data=result_data,
            error=error,
            exception_type=exception_type,
            exception=exception,
        )

        # Publish result
        basefunctions.get_event_bus().publish(result)

    def can_handle(self, event: basefunctions.Event) -> bool:
        """
        Check if this handler can handle the given event.

        Parameters
        ----------
        event : basefunctions.Event
            The event to check

        Returns
        -------
        bool
            True if this handler can handle the event, False otherwise
        """
        return (
            isinstance(event, basefunctions.ThreadPoolTaskEvent)
            and event.task_type in self._task_registry
            and not event.is_corelet_task()
        )

    def get_priority(self) -> int:
        """
        Get the priority of this handler.

        Returns
        -------
        int
            The priority of this handler (higher is executed first)
        """
        return 50  # Medium priority for thread worker handler
