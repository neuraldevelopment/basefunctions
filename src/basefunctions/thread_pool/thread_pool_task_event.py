"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Task event implementation for thread pool based on event system

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import uuid
from typing import Any, Dict, Optional
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


class ThreadPoolTaskEvent(basefunctions.Event):
    """
    Task event for thread pool execution based on the event system.

    This class extends the standard Event to include thread pool specific
    metadata such as retry count, timeout, and corelet information.
    """

    event_type = "basefunctions.threadpool.task"

    __slots__ = ("_retry_max", "_timeout", "_retry_count", "_corelet_filename")

    def __init__(
        self,
        task_type: str,
        content: Any = None,
        source: Optional[Any] = None,
        retry_max: int = 3,
        timeout: int = 5,
        corelet_filename: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new thread pool task event.

        Parameters
        ----------
        task_type : str
            The specific type of task to execute
        content : Any, optional
            The content/payload of the task
        source : Any, optional
            The source/originator of the task
        retry_max : int, default=3
            Maximum number of retry attempts
        timeout : int, default=5
            Timeout in seconds for task execution
        corelet_filename : str, optional
            Path to corelet file for process-based execution
        data : Dict[str, Any], optional
            Additional data associated with the task
        """
        # Create a unique ID for this task
        task_id = str(uuid.uuid4())

        # Initialize event data dictionary
        task_data = data or {}
        task_data.update({"task_id": task_id, "task_type": task_type, "content": content})

        # Initialize parent Event class
        super().__init__(self.event_type, source, task_data)

        # Initialize task-specific attributes
        self._retry_max = retry_max
        self._timeout = timeout
        self._retry_count = 0
        self._corelet_filename = corelet_filename

    @property
    def task_id(self) -> str:
        """
        Get the unique task identifier.

        Returns
        -------
        str
            The task's unique identifier
        """
        return self.get_data("task_id")

    @property
    def task_type(self) -> str:
        """
        Get the specific task type.

        This identifies what handler should process this task.

        Returns
        -------
        str
            The task type
        """
        return self.get_data("task_type")

    @property
    def content(self) -> Any:
        """
        Get the task content/payload.

        Returns
        -------
        Any
            The content of the task
        """
        return self.get_data("content")

    @property
    def retry_max(self) -> int:
        """
        Get the maximum number of retry attempts.

        Returns
        -------
        int
            Maximum retry count
        """
        return self._retry_max

    @property
    def timeout(self) -> int:
        """
        Get the timeout value for task execution.

        Returns
        -------
        int
            Timeout in seconds
        """
        return self._timeout

    @property
    def retry_count(self) -> int:
        """
        Get the current retry count.

        Returns
        -------
        int
            Current retry count
        """
        return self._retry_count

    @property
    def corelet_filename(self) -> Optional[str]:
        """
        Get the corelet filename for process-based execution.

        Returns
        -------
        Optional[str]
            Path to corelet file or None
        """
        return self._corelet_filename

    def increment_retry(self) -> None:
        """
        Increment the retry counter.
        """
        self._retry_count += 1

    def is_corelet_task(self) -> bool:
        """
        Check if this task should be executed as a corelet.

        Returns
        -------
        bool
            True if this is a corelet task, False otherwise
        """
        return self._corelet_filename is not None

    def can_retry(self) -> bool:
        """
        Check if this task can be retried.

        Returns
        -------
        bool
            True if task can be retried, False otherwise
        """
        return self._retry_count < self._retry_max
