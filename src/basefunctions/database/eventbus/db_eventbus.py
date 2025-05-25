"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  EventBus extension for database operations with specialized handlers
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Union
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_NUM_THREADS = 5
DEFAULT_CORELET_POOL_SIZE = 4

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbEventBus:
    """
    EventBus extension for database operations with specialized handlers.
    Leverages the unified Event system with database-specific enhancements.
    Thread-safe implementation supporting sync, thread, and corelet execution modes.
    """

    __slots__ = (
        "_event_bus",
        "_logger",
        "_lock",
        "_handlers_registered",
        "_result_collector",
        "_task_callbacks",
    )

    def __init__(
        self, num_threads: Optional[int] = None, corelet_pool_size: Optional[int] = None
    ) -> None:
        """
        Initialize DbEventBus with specified configuration.

        Parameters
        ----------
        num_threads : int, optional
            Number of worker threads for async processing.
            If None, auto-detects CPU cores.
        corelet_pool_size : int, optional
            Number of corelet worker processes for heavy operations.
            If None, uses DEFAULT_CORELET_POOL_SIZE.
        """
        self._logger = basefunctions.get_logger(__name__)
        self._lock = threading.RLock()
        self._handlers_registered = False
        self._task_callbacks: Dict[str, List[Callable]] = {}

        # Use defaults if not specified
        if num_threads is None:
            num_threads = DEFAULT_NUM_THREADS
        if corelet_pool_size is None:
            corelet_pool_size = DEFAULT_CORELET_POOL_SIZE

        # Create EventBus with database-optimized configuration
        self._event_bus = basefunctions.EventBus(
            num_threads=num_threads, corelet_pool_size=corelet_pool_size
        )

        # Get result collector from EventBus
        self._result_collector = self._event_bus._result_collector

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """
        Register default handlers for database operations.
        """
        with self._lock:
            if self._handlers_registered:
                return

            try:
                # Import and register handlers
                from basefunctions import (
                    DbQueryHandler,
                    DataFrameHandler,
                    DbTransactionHandler,
                    DbBulkOperationHandler,
                )

                # Register query handler (thread mode for medium operations)
                self._event_bus.register("database.query", DbQueryHandler())
                self._logger.info("registered database query handler")

                # Register DataFrame handler (thread mode for pandas operations)
                self._event_bus.register("database.dataframe", DataFrameHandler())
                self._logger.info("registered DataFrame operation handler")

                # Register transaction handler (sync mode for ACID compliance)
                self._event_bus.register("database.transaction", DbTransactionHandler())
                self._logger.info("registered transaction handler")

                # Register bulk operation handler (corelet mode for heavy operations)
                self._event_bus.register("database.bulk", DbBulkOperationHandler())
                self._logger.info("registered bulk operation handler")

                self._handlers_registered = True

            except Exception as e:
                self._logger.error("failed to register default handlers: %s", str(e))
                raise

    def submit_query_async(
        self,
        instance_name: str,
        database: str,
        query: str,
        parameters: Union[tuple, dict] = (),
        query_type: str = "all",
        callback: Optional[Callable] = None,
        execution_mode: str = "thread",
    ) -> str:
        """
        Submit a database query for asynchronous execution.

        Parameters
        ----------
        instance_name : str
            Database instance name
        database : str
            Database name
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            Query parameters
        query_type : str, optional
            Type of query ('all', 'one', 'to_dataframe'), default 'all'
        callback : Optional[Callable], optional
            Callback function for result processing
        execution_mode : str, optional
            Execution mode ('sync', 'thread', 'corelet'), default 'thread'

        Returns
        -------
        str
            Task ID for tracking
        """
        with self._lock:
            # Generate unique task ID
            task_id = f"db_query_{int(time.time() * 1000000)}"

            # Create event data
            event_data = {
                "task_id": task_id,
                "instance_name": instance_name,
                "database": database,
                "query": query,
                "parameters": parameters,
                "query_type": query_type,
                "execution_mode": execution_mode,
            }

            # Store callback if provided
            if callback:
                if task_id not in self._task_callbacks:
                    self._task_callbacks[task_id] = []
                self._task_callbacks[task_id].append(callback)

            # Create and publish event
            event = basefunctions.Event("database.query", data=event_data)
            self._event_bus.publish(event)

            return task_id

    def submit_dataframe_operation(
        self,
        instance_name: str,
        database: str,
        operation: str,
        table_name: Optional[str] = None,
        dataframe: Optional[Any] = None,
        query: Optional[str] = None,
        parameters: Union[tuple, dict] = (),
        callback: Optional[Callable] = None,
        execution_mode: str = "thread",
    ) -> str:
        """
        Submit a DataFrame operation for asynchronous execution.

        Parameters
        ----------
        instance_name : str
            Database instance name
        database : str
            Database name
        operation : str
            Operation type ('write', 'flush_cache', 'query_to_dataframe')
        table_name : Optional[str], optional
            Target table name for write operations
        dataframe : Optional[Any], optional
            DataFrame to write
        query : Optional[str], optional
            SQL query for query_to_dataframe operation
        parameters : Union[tuple, dict], optional
            Query parameters
        callback : Optional[Callable], optional
            Callback function for result processing
        execution_mode : str, optional
            Execution mode ('sync', 'thread', 'corelet'), default 'thread'

        Returns
        -------
        str
            Task ID for tracking
        """
        with self._lock:
            # Generate unique task ID
            task_id = f"db_dataframe_{int(time.time() * 1000000)}"

            # Create event data
            event_data = {
                "task_id": task_id,
                "instance_name": instance_name,
                "database": database,
                "operation": operation,
                "table_name": table_name,
                "dataframe": dataframe,
                "query": query,
                "parameters": parameters,
                "execution_mode": execution_mode,
            }

            # Store callback if provided
            if callback:
                if task_id not in self._task_callbacks:
                    self._task_callbacks[task_id] = []
                self._task_callbacks[task_id].append(callback)

            # Create and publish event
            event = basefunctions.Event("database.dataframe", data=event_data)
            self._event_bus.publish(event)

            return task_id

    def submit_bulk_operation(
        self,
        instance_name: str,
        database: str,
        operation: str,
        data: Any,
        callback: Optional[Callable] = None,
    ) -> str:
        """
        Submit a bulk operation for corelet execution (heavy operations).

        Parameters
        ----------
        instance_name : str
            Database instance name
        database : str
            Database name
        operation : str
            Bulk operation type
        data : Any
            Operation data
        callback : Optional[Callable], optional
            Callback function for result processing

        Returns
        -------
        str
            Task ID for tracking
        """
        with self._lock:
            # Generate unique task ID
            task_id = f"db_bulk_{int(time.time() * 1000000)}"

            # Create event data
            event_data = {
                "task_id": task_id,
                "instance_name": instance_name,
                "database": database,
                "operation": operation,
                "data": data,
                "execution_mode": "corelet",
            }

            # Store callback if provided
            if callback:
                if task_id not in self._task_callbacks:
                    self._task_callbacks[task_id] = []
                self._task_callbacks[task_id].append(callback)

            # Create and publish event
            event = basefunctions.Event("database.bulk", data=event_data)
            self._event_bus.publish(event)

            return task_id

    def execute_transaction(
        self,
        instance_name: str,
        database: str,
        queries: List[Dict[str, Any]],
        callback: Optional[Callable] = None,
    ) -> str:
        """
        Execute multiple queries in a transaction (sync mode for ACID compliance).

        Parameters
        ----------
        instance_name : str
            Database instance name
        database : str
            Database name
        queries : List[Dict[str, Any]]
            List of query dictionaries with 'query' and 'parameters' keys
        callback : Optional[Callable], optional
            Callback function for result processing

        Returns
        -------
        str
            Task ID for tracking
        """
        with self._lock:
            # Generate unique task ID
            task_id = f"db_transaction_{int(time.time() * 1000000)}"

            # Create event data
            event_data = {
                "task_id": task_id,
                "instance_name": instance_name,
                "database": database,
                "queries": queries,
                "execution_mode": "sync",
            }

            # Store callback if provided
            if callback:
                if task_id not in self._task_callbacks:
                    self._task_callbacks[task_id] = []
                self._task_callbacks[task_id].append(callback)

            # Create and publish event
            event = basefunctions.Event("database.transaction", data=event_data)
            self._event_bus.publish(event)

            return task_id

    def register_handler(self, event_type: str, handler: "basefunctions.EventHandler") -> bool:
        """
        Register a custom event handler.

        Parameters
        ----------
        event_type : str
            Type of events to handle
        handler : basefunctions.EventHandler
            Handler instance

        Returns
        -------
        bool
            True if registration was successful
        """
        with self._lock:
            return self._event_bus.register(event_type, handler)

    def get_results(
        self, success_only: bool = False, errors_only: bool = False
    ) -> Union[List[Any], tuple]:
        """
        Get results from completed operations.

        Parameters
        ----------
        success_only : bool, optional
            Return only successful results, default False
        errors_only : bool, optional
            Return only error results, default False

        Returns
        -------
        Union[List[Any], tuple]
            Results based on filtering options
        """
        with self._lock:
            results = self._event_bus.get_results(
                success_only=success_only, errors_only=errors_only
            )

            # Process callbacks for completed tasks
            self._process_result_callbacks(results)

            return results

    def _process_result_callbacks(self, results: Union[List[Any], tuple]) -> None:
        """
        Process callbacks for completed tasks.

        Parameters
        ----------
        results : Union[List[Any], tuple]
            Results to process for callbacks
        """
        # Handle different result formats
        if isinstance(results, tuple):
            success_results, error_results = results
            all_results = success_results + error_results
        else:
            all_results = results

        # Process callbacks
        for result in all_results:
            # Extract task_id if available
            task_id = None
            if hasattr(result, "get") and callable(result.get):
                task_id = result.get("task_id")
            elif isinstance(result, dict):
                task_id = result.get("task_id")

            if task_id and task_id in self._task_callbacks:
                callbacks = self._task_callbacks.pop(task_id)
                for callback in callbacks:
                    try:
                        if isinstance(result, str) and result.startswith("exception:"):
                            callback(False, result)
                        else:
                            callback(True, result)
                    except Exception as e:
                        self._logger.warning("error in result callback: %s", str(e))

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all active operations to complete.

        Parameters
        ----------
        timeout : Optional[float], optional
            Maximum time to wait in seconds

        Returns
        -------
        bool
            True if all operations completed, False if timeout
        """
        self._event_bus.join()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about database operations.

        Returns
        -------
        Dict[str, Any]
            Statistics from EventBus and database-specific metrics
        """
        with self._lock:
            stats = self._event_bus.get_stats()

            # Add database-specific statistics
            stats.update(
                {
                    "db_handlers_registered": self._handlers_registered,
                    "pending_callbacks": len(self._task_callbacks),
                    "total_callback_tasks": sum(len(cbs) for cbs in self._task_callbacks.values()),
                }
            )

            return stats

    def shutdown(self) -> None:
        """
        Shutdown the EventBus and all database operations.
        """
        with self._lock:
            # Clear pending callbacks
            cleared_callbacks = len(self._task_callbacks)
            self._task_callbacks.clear()

            if cleared_callbacks > 0:
                self._logger.info(
                    "cleared %d pending callbacks during shutdown", cleared_callbacks
                )

            # Shutdown EventBus
            self._event_bus.shutdown()
            self._logger.info("DbEventBus shutdown complete")

    def clear_handlers(self) -> None:
        """
        Clear all registered handlers.
        """
        with self._lock:
            self._event_bus.clear()
            self._handlers_registered = False

    def start(self) -> None:
        """
        Explicitly start the EventBus systems if not auto-started.
        """
        # EventBus systems start automatically when handlers are registered
        # This method exists for compatibility and explicit control
        pass
