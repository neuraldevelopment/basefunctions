"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Result event implementation for thread pool tasks

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any, Dict, Optional, Type
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


class ThreadPoolResultEvent(basefunctions.Event):
    """
    Result event for thread pool task execution.

    This class represents the outcome of a task execution and contains
    information about success status, result data, and any errors that
    occurred during execution.
    """

    event_type = "basefunctions.threadpool.result"

    __slots__ = ("_original_task", "_exception")

    def __init__(
        self,
        original_task: basefunctions.ThreadPoolTaskEvent,
        success: bool = False,
        data: Any = None,
        error: Optional[str] = None,
        exception_type: Optional[str] = None,
        exception: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new thread pool result event.

        Parameters
        ----------
        original_task : basefunctions.ThreadPoolTaskEvent
            The original task that was executed
        success : bool, default=False
            Whether the task execution was successful
        data : Any, optional
            The result data from task execution
        error : str, optional
            Error message if task failed
        exception_type : str, optional
            Type of exception if task failed
        exception : Exception, optional
            Exception object if task failed
        metadata : Dict[str, Any], optional
            Additional metadata for the result
        """
        # Create result data dictionary
        result_data = {
            "task_id": original_task.task_id,
            "task_type": original_task.task_type,
            "success": success,
            "data": data,
            "error": error,
            "exception_type": exception_type,
            "retry_count": original_task.retry_count,
            "metadata": metadata or {},
        }

        # Initialize parent Event class
        super().__init__(self.event_type, source=original_task.source, data=result_data)

        # Store references to original task and exception
        self._original_task = original_task
        self._exception = exception

    @property
    def original_task(self) -> basefunctions.ThreadPoolTaskEvent:
        """
        Get the original task event.

        Returns
        -------
        basefunctions.ThreadPoolTaskEvent
            The original task that was executed
        """
        return self._original_task

    @property
    def task_id(self) -> str:
        """
        Get the task identifier.

        Returns
        -------
        str
            The task's unique identifier
        """
        return self.get_data("task_id")

    @property
    def task_type(self) -> str:
        """
        Get the task type.

        Returns
        -------
        str
            The task type
        """
        return self.get_data("task_type")

    @property
    def success(self) -> bool:
        """
        Check if task execution was successful.

        Returns
        -------
        bool
            True if successful, False otherwise
        """
        return self.get_data("success")

    @property
    def result_data(self) -> Any:
        """
        Get the result data from task execution.

        Returns
        -------
        Any
            Result data from task execution
        """
        return self.get_data("data")

    @property
    def error(self) -> Optional[str]:
        """
        Get the error message if task failed.

        Returns
        -------
        Optional[str]
            Error message or None if task succeeded
        """
        return self.get_data("error")

    @property
    def exception_type(self) -> Optional[str]:
        """
        Get the exception type name if task failed.

        Returns
        -------
        Optional[str]
            Exception type name or None if task succeeded
        """
        return self.get_data("exception_type")

    @property
    def exception(self) -> Optional[Exception]:
        """
        Get the exception object if task failed.

        Returns
        -------
        Optional[Exception]
            Exception object or None if task succeeded
        """
        return self._exception

    @property
    def retry_count(self) -> int:
        """
        Get the number of retries that were performed.

        Returns
        -------
        int
            Retry count
        """
        return self.get_data("retry_count")

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get additional metadata about the task result.

        Returns
        -------
        Dict[str, Any]
            Result metadata
        """
        return self.get_data("metadata")
