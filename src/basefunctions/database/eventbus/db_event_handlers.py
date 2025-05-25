"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Event handlers for asynchronous database operations using the new Event system
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pandas as pd
from typing import Dict, Any, Optional, List, Union
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


class DbQueryHandler(basefunctions.EventHandler):
    """
    Handler for database query operations in thread execution mode.
    Optimized for medium-complexity database queries with connection pooling.
    """

    execution_mode = 1  # thread

    def __init__(self):
        """Initialize database query handler."""
        self._logger = basefunctions.get_logger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle database query events.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing query details
        context : Optional[basefunctions.EventContext]
            Thread context with thread-local storage

        Returns
        -------
        Any
            Query results or error information

        Raises
        ------
        Exception
            If query execution fails
        """
        try:
            # Extract event data
            data = event.data
            if not data:
                raise ValueError("no event data provided")

            # Extract required parameters
            task_id = data.get("task_id")
            instance_name = data.get("instance_name")
            database = data.get("database")
            query = data.get("query")
            parameters = data.get("parameters", ())
            query_type = data.get("query_type", "all")

            # Validate required parameters
            if not query:
                raise ValueError("no query provided")
            if not instance_name:
                raise ValueError("no instance name provided")
            if not database:
                raise ValueError("no database name provided")

            # Initialize thread-local database connections if needed
            if context and context.thread_local_data:
                if not hasattr(context.thread_local_data, "db_connections"):
                    context.thread_local_data["db_connections"] = {}

                # Get or create database connection
                db_key = f"{instance_name}:{database}"
                if db_key not in context.thread_local_data["db_connections"]:
                    try:
                        # Get database manager
                        db_manager = basefunctions.DbManager()

                        # Get instance and database
                        instance = db_manager.get_instance(instance_name)
                        db = instance.get_database(database)

                        # Store for reuse
                        context.thread_local_data["db_connections"][db_key] = db
                    except Exception as e:
                        raise Exception(f"failed to connect to database: {str(e)}")

                # Get database connection
                db = context.thread_local_data["db_connections"][db_key]
            else:
                # Fallback for sync execution or missing context
                db_manager = basefunctions.DbManager()
                instance = db_manager.get_instance(instance_name)
                db = instance.get_database(database)

            # Execute query based on query type
            if query_type == "to_dataframe":
                result = db.query_to_dataframe(query, parameters)
            elif query_type == "one":
                result = db.query_one(query, parameters)
            elif query_type == "execute":
                db.execute(query, parameters)
                result = "query executed successfully"
            else:
                # Default: query all rows
                result = db.query_all(query, parameters)

            # Return result with task_id for callback processing
            return {"task_id": task_id, "result": result, "success": True}

        except Exception as e:
            self._logger.error("error executing database query: %s", str(e))
            # Return error with task_id for callback processing
            return {
                "task_id": data.get("task_id") if data else None,
                "error": str(e),
                "success": False,
            }


class DataFrameHandler(basefunctions.EventHandler):
    """
    Handler for DataFrame operations in thread execution mode.
    Supports writing DataFrames to database tables and advanced pandas operations.
    """

    execution_mode = 1  # thread

    def __init__(self):
        """Initialize DataFrame handler."""
        self._logger = basefunctions.get_logger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle DataFrame operation events.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing operation details
        context : Optional[basefunctions.EventContext]
            Thread context with thread-local storage

        Returns
        -------
        Any
            Operation results or error information

        Raises
        ------
        Exception
            If operation fails
        """
        try:
            # Extract event data
            data = event.data
            if not data:
                raise ValueError("no event data provided")

            # Extract required parameters
            task_id = data.get("task_id")
            instance_name = data.get("instance_name")
            database = data.get("database")
            operation = data.get("operation")

            # Validate required parameters
            if not operation:
                raise ValueError("no operation specified")
            if not instance_name:
                raise ValueError("no instance name provided")
            if not database:
                raise ValueError("no database name provided")

            # Get database connection (with thread-local caching if available)
            db = self._get_database_connection(instance_name, database, context)

            # Process based on operation type
            if operation == "write":
                result = self._handle_write_dataframe(db, data)
            elif operation == "flush_cache":
                result = self._handle_flush_cache(db, data)
            elif operation == "query_to_dataframe":
                result = self._handle_query_to_dataframe(db, data)
            elif operation == "bulk_insert":
                result = self._handle_bulk_insert(db, data)
            else:
                raise ValueError(f"unknown operation: {operation}")

            # Return result with task_id for callback processing
            return {"task_id": task_id, "result": result, "success": True}

        except Exception as e:
            self._logger.error("error in DataFrame operation: %s", str(e))
            # Return error with task_id for callback processing
            return {
                "task_id": data.get("task_id") if data else None,
                "error": str(e),
                "success": False,
            }

    def _get_database_connection(
        self, instance_name: str, database: str, context: Optional[basefunctions.EventContext]
    ) -> "basefunctions.Db":
        """
        Get database connection with thread-local caching.

        Parameters
        ----------
        instance_name : str
            Database instance name
        database : str
            Database name
        context : Optional[basefunctions.EventContext]
            Thread context

        Returns
        -------
        basefunctions.Db
            Database connection
        """
        # Use thread-local caching if context available
        if context and context.thread_local_data:
            if not hasattr(context.thread_local_data, "db_connections"):
                context.thread_local_data["db_connections"] = {}

            db_key = f"{instance_name}:{database}"
            if db_key not in context.thread_local_data["db_connections"]:
                db_manager = basefunctions.DbManager()
                instance = db_manager.get_instance(instance_name)
                db = instance.get_database(database)
                context.thread_local_data["db_connections"][db_key] = db
            return context.thread_local_data["db_connections"][db_key]
        else:
            # Fallback for sync execution
            db_manager = basefunctions.DbManager()
            instance = db_manager.get_instance(instance_name)
            return instance.get_database(database)

    def _handle_write_dataframe(self, db: "basefunctions.Db", data: Dict[str, Any]) -> str:
        """
        Handle writing a DataFrame to a database table.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Operation data

        Returns
        -------
        str
            Success message
        """
        table_name = data.get("table_name")
        dataframe = data.get("dataframe")
        if_exists = data.get("if_exists", "append")
        cached = data.get("cached", False)

        if not table_name:
            raise ValueError("no table name provided")
        if dataframe is None:
            raise ValueError("no dataframe provided")

        if cached:
            # Use database's caching mechanism
            db.add_dataframe(table_name, dataframe, cached=True)
            return f"cached {len(dataframe)} rows for {table_name}"
        else:
            # Write directly
            db.add_dataframe(table_name, dataframe, cached=False)
            return f"wrote {len(dataframe)} rows to {table_name}"

    def _handle_flush_cache(self, db: "basefunctions.Db", data: Dict[str, Any]) -> str:
        """
        Handle flushing cached DataFrames to database tables.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Operation data

        Returns
        -------
        str
            Success message
        """
        table_name = data.get("table_name")

        if table_name:
            # Flush specific table
            db.flush_dataframe_cache(table_name)
            return f"flushed cache for table {table_name}"
        else:
            # Flush all tables
            stats = db.get_dataframe_cache_stats()
            db.flush_dataframe_cache()
            total_tables = len(stats)
            total_rows = sum(stat["total_rows"] for stat in stats.values())
            return f"flushed cache for {total_tables} tables with {total_rows} total rows"

    def _handle_query_to_dataframe(
        self, db: "basefunctions.Db", data: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Handle executing a query and returning results as a DataFrame.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Operation data

        Returns
        -------
        pd.DataFrame
            Query results as DataFrame
        """
        query = data.get("query")
        parameters = data.get("parameters", ())

        if not query:
            raise ValueError("no query provided")

        return db.query_to_dataframe(query, parameters)

    def _handle_bulk_insert(self, db: "basefunctions.Db", data: Dict[str, Any]) -> str:
        """
        Handle bulk insert operations for large DataFrames.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Operation data

        Returns
        -------
        str
            Success message
        """
        table_name = data.get("table_name")
        dataframe = data.get("dataframe")
        chunk_size = data.get("chunk_size", 10000)

        if not table_name:
            raise ValueError("no table name provided")
        if dataframe is None:
            raise ValueError("no dataframe provided")

        # Process in chunks for better memory management
        total_rows = len(dataframe)
        chunks_processed = 0

        for i in range(0, total_rows, chunk_size):
            chunk = dataframe.iloc[i : i + chunk_size]
            db.add_dataframe(table_name, chunk, cached=False)
            chunks_processed += 1

        return f"bulk inserted {total_rows} rows in {chunks_processed} chunks to {table_name}"


class DbTransactionHandler(basefunctions.EventHandler):
    """
    Handler for database transaction operations in sync execution mode.
    Ensures ACID compliance for multi-query transactions.
    """

    execution_mode = 0  # sync

    def __init__(self):
        """Initialize transaction handler."""
        self._logger = basefunctions.get_logger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle database transaction events.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing transaction details
        context : Optional[basefunctions.EventContext]
            Event context (unused for sync mode)

        Returns
        -------
        Any
            Transaction results or error information

        Raises
        ------
        Exception
            If transaction fails
        """
        try:
            # Extract event data
            data = event.data
            if not data:
                raise ValueError("no event data provided")

            # Extract required parameters
            task_id = data.get("task_id")
            instance_name = data.get("instance_name")
            database = data.get("database")
            queries = data.get("queries", [])

            # Validate required parameters
            if not instance_name:
                raise ValueError("no instance name provided")
            if not database:
                raise ValueError("no database name provided")
            if not queries:
                raise ValueError("no queries provided")

            # Get database connection
            db_manager = basefunctions.DbManager()
            instance = db_manager.get_instance(instance_name)
            db = instance.get_database(database)

            # Execute transaction
            results = []
            with db.transaction():
                for i, query_info in enumerate(queries):
                    query = query_info.get("query")
                    parameters = query_info.get("parameters", ())
                    query_type = query_info.get("type", "execute")

                    if not query:
                        raise ValueError(f"no query provided for operation {i}")

                    if query_type == "execute":
                        db.execute(query, parameters)
                        results.append(f"query {i} executed successfully")
                    elif query_type == "one":
                        result = db.query_one(query, parameters)
                        results.append(result)
                    elif query_type == "all":
                        result = db.query_all(query, parameters)
                        results.append(result)
                    else:
                        raise ValueError(f"unknown query type: {query_type}")

            # Return results with task_id for callback processing
            return {
                "task_id": task_id,
                "result": {"transaction_results": results, "queries_executed": len(queries)},
                "success": True,
            }

        except Exception as e:
            self._logger.error("error executing database transaction: %s", str(e))
            # Return error with task_id for callback processing
            return {
                "task_id": data.get("task_id") if data else None,
                "error": str(e),
                "success": False,
            }


class DbBulkOperationHandler(basefunctions.EventHandler):
    """
    Handler for heavy bulk database operations in corelet execution mode.
    Optimized for CPU-intensive operations that benefit from process isolation.
    """

    execution_mode = 2  # corelet

    def __init__(self):
        """Initialize bulk operation handler."""
        self._logger = basefunctions.get_logger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle bulk database operation events.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing bulk operation details
        context : Optional[basefunctions.EventContext]
            Corelet context with process information

        Returns
        -------
        Any
            Bulk operation results or error information

        Raises
        ------
        Exception
            If bulk operation fails
        """
        try:
            # Extract event data
            data = event.data
            if not data:
                raise ValueError("no event data provided")

            # Extract required parameters
            task_id = data.get("task_id")
            instance_name = data.get("instance_name")
            database = data.get("database")
            operation = data.get("operation")
            operation_data = data.get("data")

            # Validate required parameters
            if not operation:
                raise ValueError("no operation specified")
            if not instance_name:
                raise ValueError("no instance name provided")
            if not database:
                raise ValueError("no database name provided")

            # Report alive for long operations
            if context:
                context.report_alive()

            # Get database connection
            db_manager = basefunctions.DbManager()
            instance = db_manager.get_instance(instance_name)
            db = instance.get_database(database)

            # Process based on operation type
            if operation == "bulk_import":
                result = self._handle_bulk_import(db, operation_data, context)
            elif operation == "data_migration":
                result = self._handle_data_migration(db, operation_data, context)
            elif operation == "large_aggregation":
                result = self._handle_large_aggregation(db, operation_data, context)
            elif operation == "batch_processing":
                result = self._handle_batch_processing(db, operation_data, context)
            else:
                raise ValueError(f"unknown bulk operation: {operation}")

            # Return result with task_id for callback processing
            return {"task_id": task_id, "result": result, "success": True}

        except Exception as e:
            self._logger.error("error in bulk database operation: %s", str(e))
            # Return error with task_id for callback processing
            return {
                "task_id": data.get("task_id") if data else None,
                "error": str(e),
                "success": False,
            }

    def _handle_bulk_import(
        self,
        db: "basefunctions.Db",
        data: Dict[str, Any],
        context: Optional[basefunctions.EventContext],
    ) -> Dict[str, Any]:
        """
        Handle bulk data import operations.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Operation data
        context : Optional[basefunctions.EventContext]
            Corelet context

        Returns
        -------
        Dict[str, Any]
            Import results
        """
        file_path = data.get("file_path")
        table_name = data.get("table_name")
        chunk_size = data.get("chunk_size", 50000)

        if not file_path:
            raise ValueError("no file path provided")
        if not table_name:
            raise ValueError("no table name provided")

        # Read and process file in chunks
        total_rows = 0
        chunks_processed = 0

        # Report progress periodically
        if context:
            context.report_alive()

        # Simulate bulk import processing
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            db.add_dataframe(table_name, chunk, cached=False)
            total_rows += len(chunk)
            chunks_processed += 1

            # Report alive every 10 chunks
            if context and chunks_processed % 10 == 0:
                context.report_alive()

        return {
            "operation": "bulk_import",
            "rows_imported": total_rows,
            "chunks_processed": chunks_processed,
            "target_table": table_name,
        }

    def _handle_data_migration(
        self,
        db: "basefunctions.Db",
        data: Dict[str, Any],
        context: Optional[basefunctions.EventContext],
    ) -> Dict[str, Any]:
        """
        Handle data migration between tables or databases.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Migration data
        context : Optional[basefunctions.EventContext]
            Corelet context

        Returns
        -------
        Dict[str, Any]
            Migration results
        """
        source_query = data.get("source_query")
        target_table = data.get("target_table")
        batch_size = data.get("batch_size", 10000)

        if not source_query:
            raise ValueError("no source query provided")
        if not target_table:
            raise ValueError("no target table provided")

        # Process migration in batches
        offset = 0
        total_migrated = 0

        if context:
            context.report_alive()

        while True:
            # Add LIMIT and OFFSET to query
            paginated_query = f"{source_query} LIMIT {batch_size} OFFSET {offset}"
            batch_data = db.query_to_dataframe(paginated_query)

            if batch_data.empty:
                break

            # Write batch to target table
            db.add_dataframe(target_table, batch_data, cached=False)
            total_migrated += len(batch_data)
            offset += batch_size

            # Report alive every batch
            if context:
                context.report_alive()

        return {
            "operation": "data_migration",
            "rows_migrated": total_migrated,
            "target_table": target_table,
            "batches_processed": offset // batch_size,
        }

    def _handle_large_aggregation(
        self,
        db: "basefunctions.Db",
        data: Dict[str, Any],
        context: Optional[basefunctions.EventContext],
    ) -> Dict[str, Any]:
        """
        Handle large aggregation operations.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Aggregation data
        context : Optional[basefunctions.EventContext]
            Corelet context

        Returns
        -------
        Dict[str, Any]
            Aggregation results
        """
        query = data.get("query")
        result_table = data.get("result_table")

        if not query:
            raise ValueError("no aggregation query provided")

        if context:
            context.report_alive()

        # Execute aggregation query
        result = db.query_to_dataframe(query)

        # Save results if target table specified
        if result_table:
            db.add_dataframe(result_table, result, cached=False)

        if context:
            context.report_alive()

        return {
            "operation": "large_aggregation",
            "rows_processed": len(result),
            "result_table": result_table,
            "aggregation_complete": True,
        }

    def _handle_batch_processing(
        self,
        db: "basefunctions.Db",
        data: Dict[str, Any],
        context: Optional[basefunctions.EventContext],
    ) -> Dict[str, Any]:
        """
        Handle batch processing operations.

        Parameters
        ----------
        db : basefunctions.Db
            Database connection
        data : Dict[str, Any]
            Batch processing data
        context : Optional[basefunctions.EventContext]
            Corelet context

        Returns
        -------
        Dict[str, Any]
            Batch processing results
        """
        operations = data.get("operations", [])
        batch_size = data.get("batch_size", 1000)

        if not operations:
            raise ValueError("no operations provided")

        total_processed = 0
        batches_completed = 0

        if context:
            context.report_alive()

        # Process operations in batches
        for i in range(0, len(operations), batch_size):
            batch = operations[i : i + batch_size]

            # Process each operation in the batch
            for operation in batch:
                query = operation.get("query")
                parameters = operation.get("parameters", ())

                if query:
                    db.execute(query, parameters)
                    total_processed += 1

            batches_completed += 1

            # Report alive every batch
            if context and batches_completed % 10 == 0:
                context.report_alive()

        return {
            "operation": "batch_processing",
            "operations_processed": total_processed,
            "batches_completed": batches_completed,
            "processing_complete": True,
        }
