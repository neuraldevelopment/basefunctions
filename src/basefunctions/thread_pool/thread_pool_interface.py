"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Interface definitions for thread pool task handlers

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any, Tuple
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


class ThreadPoolRequestInterface(ABC):
    """
    Interface for processing input messages in the thread pool.

    Task handlers must implement this interface to be registered
    with the thread pool for processing specific task types.
    """

    @abstractmethod
    def process_request(
        self, context: basefunctions.ThreadPoolContext, message: basefunctions.ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Process an incoming request message.

        Parameters
        ----------
        context : basefunctions.ThreadPoolContext
            Context object with execution-specific data
        message : basefunctions.ThreadPoolMessage
            Message to process

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data.
            The first element indicates whether processing was successful (True/False).
            The second element contains the result data or an error message.
        """
        pass


class ThreadPoolTaskHandler(ThreadPoolRequestInterface):
    """
    Base class for thread pool task handlers.

    This class provides a standardized implementation of the
    ThreadPoolRequestInterface with common functionality.
    """

    def process_request(
        self, context: basefunctions.ThreadPoolContext, message: basefunctions.ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Process an incoming request message by delegating to handle_task.

        Parameters
        ----------
        context : basefunctions.ThreadPoolContext
            Context object with execution-specific data
        message : basefunctions.ThreadPoolMessage
            Message to process

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data
        """
        try:
            result = self.handle_task(context, message.content)

            # Handle different return formats
            if isinstance(result, tuple) and len(result) == 2:
                success, data = result
            else:
                success, data = True, result

            # Ensure proper return type
            if not isinstance(success, bool):
                raise TypeError("handle_task function must return (bool, Any) or a result value")

            return success, data

        except Exception as e:
            # Log exception
            basefunctions.get_logger(__name__).error(
                "Exception in handler %s: %s", self.__class__.__name__, str(e)
            )
            return False, str(e)

    @abstractmethod
    def handle_task(self, context: basefunctions.ThreadPoolContext, content: Any) -> Any:
        """
        Handle a task with the given content.

        This is the main method that subclasses should implement.

        Parameters
        ----------
        context : basefunctions.ThreadPoolContext
            Context object with execution-specific data
        content : Any
            Content/payload of the task

        Returns
        -------
        Any
            Result of task processing. Can be:
            - A single value (assumed success)
            - A tuple (bool, Any) indicating success and result data
        """
        pass
