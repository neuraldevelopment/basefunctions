"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Context object for thread pool task execution

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import queue
import threading
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


class ThreadPoolContext:
    """
    Context object for thread pool task execution.

    This class provides a consistent interface for task handlers to access
    thread-local data and other context-specific information.
    """

    __slots__ = ("_thread_local_data", "_input_queue", "_process_info", "_metadata")

    def __init__(
        self,
        thread_local_data: Optional[threading.local] = None,
        input_queue: Optional[queue.Queue] = None,
        process_info: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new thread pool context.

        Parameters
        ----------
        thread_local_data : threading.local, optional
            Thread-local storage for handler instances
        input_queue : queue.Queue, optional
            Input queue for the thread pool
        process_info : Dict[str, Any], optional
            Information about the process executing the task
        metadata : Dict[str, Any], optional
            Additional metadata for the context
        """
        self._thread_local_data = thread_local_data
        self._input_queue = input_queue
        self._process_info = process_info or {}
        self._metadata = metadata or {}

    @property
    def thread_local_data(self) -> Optional[threading.local]:
        """
        Get the thread-local data storage.

        Returns
        -------
        Optional[threading.local]
            Thread-local storage object
        """
        return self._thread_local_data

    @property
    def input_queue(self) -> Optional[queue.Queue]:
        """
        Get the input queue for the thread pool.

        Returns
        -------
        Optional[queue.Queue]
            Input queue for the thread pool
        """
        return self._input_queue

    @property
    def process_info(self) -> Dict[str, Any]:
        """
        Get information about the process executing the task.

        Returns
        -------
        Dict[str, Any]
            Process information dictionary
        """
        return self._process_info

    @process_info.setter
    def process_info(self, value: Dict[str, Any]) -> None:
        """
        Set the process information dictionary.

        Parameters
        ----------
        value : Dict[str, Any]
            Process information dictionary
        """
        self._process_info = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value by key.

        Parameters
        ----------
        key : str
            The metadata key
        default : Any, optional
            Default value to return if key is not found

        Returns
        -------
        Any
            The metadata value or default
        """
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.

        Parameters
        ----------
        key : str
            The metadata key
        value : Any
            The value to set
        """
        self._metadata[key] = value

    def get_all_metadata(self) -> Dict[str, Any]:
        """
        Get all metadata as a dictionary.

        Returns
        -------
        Dict[str, Any]
            All metadata as a dictionary
        """
        return self._metadata.copy()
