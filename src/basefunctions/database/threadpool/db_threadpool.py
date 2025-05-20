"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  ThreadPool extension for database operations with specialized handlers
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Any, Optional, List, Type, Callable, Union
import threading
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
DEFAULT_NUM_THREADS = 5

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbThreadPool:
    """
    ThreadPool extension for database operations with specialized handlers.
    Leverages the base ThreadPool implementation with database-specific enhancements.
    Thread-safe implementation.
    """

    def __init__(self, num_threads: int = DEFAULT_NUM_THREADS) -> None:
        """
        Initialize DbThreadPool with specified number of threads.

        parameters
        ----------
        num_threads : int, optional
            number of worker threads, by default DEFAULT_NUM_THREADS
        """
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

        # Create and configure base ThreadPool
        self.thread_pool = basefunctions.ThreadPool(num_threads)

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """
        Register default handlers for database operations.
        """
        try:
            # Import handlers
            from basefunctions import DbQueryTaskHandler, DataFrameTaskHandler

            # Register query handler
            self.thread_pool.register_handler("database_query", DbQueryTaskHandler, "thread")
            self.logger.warning("registered database query handler")

            # Register dataframe handler
            self.thread_pool.register_handler(
                "dataframe_operation", DataFrameTaskHandler, "thread"
            )
            self.logger.warning("registered dataframe operation handler")

        except Exception as e:
            self.logger.critical(f"failed to register default handlers: {str(e)}")

    def submit_task(
        self, message_type: str, content: Any = None, timeout: int = 60, retry_max: int = 3
    ) -> str:
        """
        Submit a task to the ThreadPool.

        parameters
        ----------
        message_type : str
            type of message to process
        content : Any, optional
            message content, by default None
        timeout : int, optional
            task timeout in seconds, by default 60
        retry_max : int, optional
            maximum number of retries, by default 3

        returns
        -------
        str
            task ID

        raises
        ------
        ValueError
            if handler for message_type is not registered
        """
        with self.lock:
            return self.thread_pool.submit_task(
                message_type=message_type, content=content, timeout=timeout, retry_max=retry_max
            )

    def register_handler(
        self,
        message_type: str,
        handler: Union[Type["basefunctions.ThreadPoolRequestInterface"], str],
        handler_type: str,
    ) -> None:
        """
        Register a handler for a specific message type.

        parameters
        ----------
        message_type : str
            type of message the handler processes
        handler : Union[Type[basefunctions.ThreadPoolRequestInterface], str]
            handler class or path to handler file
        handler_type : str
            either "thread" or "core"

        raises
        ------
        ValueError
            if handler_type is invalid
        TypeError
            if handler has wrong type
        """
        with self.lock:
            self.thread_pool.register_handler(message_type, handler, handler_type)

    def get_results(self) -> List["basefunctions.ThreadPoolResult"]:
        """
        Get all available results from the output queue.

        returns
        -------
        List[basefunctions.ThreadPoolResult]
            list of task results
        """
        with self.lock:
            return self.thread_pool.get_results_from_output_queue()

    def wait_for_all(self) -> None:
        """
        Wait for all tasks to complete.
        """
        self.thread_pool.wait_for_all()

    def stop(self) -> None:
        """
        Stop the ThreadPool and all worker threads.
        """
        self.thread_pool.stop_threads()

    def wait_for_task(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Optional["basefunctions.ThreadPoolResult"]:
        """
        Wait for a specific task to complete.

        parameters
        ----------
        task_id : str
            ID of the task to wait for
        timeout : Optional[float], optional
            maximum time to wait in seconds, by default None

        returns
        -------
        Optional[basefunctions.ThreadPoolResult]
            task result or None if timeout occurred
        """
        start_time = basefunctions.time_utils.utc_timestamp()

        while timeout is None or basefunctions.time_utils.utc_timestamp() - start_time < timeout:
            # Check output queue for results
            results = self.get_results()

            # Look for matching task ID
            for result in results:
                if result.id == task_id:
                    return result

            # Small delay to avoid busy waiting
            import time

            time.sleep(0.1)

        return None  # Timeout occurred

    def add_callback(
        self,
        message_type: str,
        callback: Callable[
            ["basefunctions.ThreadPoolMessage", "basefunctions.ThreadPoolResult"], None
        ],
    ) -> None:
        """
        Add a callback function for a specific message type.

        parameters
        ----------
        message_type : str
            type of message to register callback for
        callback : Callable[[basefunctions.ThreadPoolMessage, basefunctions.ThreadPoolResult], None]
            function to call when task completes
        """
        self.thread_pool.add_observer(f"stop_{message_type}", callback)
