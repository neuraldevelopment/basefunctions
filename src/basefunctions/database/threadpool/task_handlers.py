"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Task handlers for asynchronous database operations
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Any, Optional, Tuple, List, Callable, Union
import pandas as pd
import threading
import basefunctions
from basefunctions import ThreadPoolRequestInterface, ThreadPoolContext, ThreadPoolMessage

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


@basefunctions.thread_handler("database_query")
def db_query_handler(context: ThreadPoolContext, message: ThreadPoolMessage) -> Tuple[bool, Any]:
    """
    Handler for database query operations.

    parameters
    ----------
    context : ThreadPoolContext
        thread context with thread-local storage
    message : ThreadPoolMessage
        message with query details

    returns
    -------
    Tuple[bool, Any]
        success flag and query results or error message
    """
    try:
        # Extract content from message
        content = message.content
        if not content:
            return False, "no content provided"

        # Extract query parameters
        query = content.get("query")
        parameters = content.get("parameters", ())
        instance_name = content.get("instance_name")
        database = content.get("database")
        callback = content.get("callback")

        if not query:
            return False, "no query provided"
        if not instance_name:
            return False, "no instance name provided"
        if not database:
            return False, "no database name provided"

        # Initialize thread-local database connections if needed
        if not hasattr(context.thread_local_data, "db_connections"):
            context.thread_local_data.db_connections = {}

        # Get or create database connection
        db_key = f"{instance_name}:{database}"
        if db_key not in context.thread_local_data.db_connections:
            try:
                # Get database manager
                db_manager = basefunctions.DbManager()

                # Get instance and database
                instance = db_manager.get_instance(instance_name)
                db = instance.get_database(database)

                # Store for reuse
                context.thread_local_data.db_connections[db_key] = db
            except Exception as e:
                return False, f"failed to connect to database: {str(e)}"

        # Get database connection
        db = context.thread_local_data.db_connections[db_key]

        # Execute query based on query type
        if content.get("query_type") == "to_dataframe":
            # Query and convert to DataFrame
            result = db.query_to_dataframe(query, parameters)
        elif content.get("query_type") == "one":
            # Query single row
            result = db.query_one(query, parameters)
        else:
            # Default: query all rows
            result = db.query_all(query, parameters)

        # Execute callback if provided
        if callback and callable(callback):
            try:
                callback(True, result)
            except Exception as e:
                basefunctions.get_logger(__name__).warning(f"error in callback: {str(e)}")

        return True, result

    except Exception as e:
        basefunctions.get_logger(__name__).critical(f"error executing database query: {str(e)}")

        # Try to execute callback even on error
        if message and message.content and message.content.get("callback"):
            try:
                message.content["callback"](False, str(e))
            except:
                pass

        return False, f"error executing database query: {str(e)}"


class DataFrameTaskHandler(ThreadPoolRequestInterface):
    """
    Handler for asynchronous DataFrame operations.
    Supports writing DataFrames to database tables and cache flushing.
    """

    def process_request(
        self, context: ThreadPoolContext, message: ThreadPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Process a DataFrame operation request.

        parameters
        ----------
        context : ThreadPoolContext
            thread context with thread-local storage
        message : ThreadPoolMessage
            message with operation details

        returns
        -------
        Tuple[bool, Any]
            success flag and operation results or error message
        """
        try:
            # Extract content from message
            content = message.content
            if not content:
                return False, "no content provided"

            # Extract operation type
            operation = content.get("operation")
            if not operation:
                return False, "no operation specified"

            # Common parameters
            instance_name = content.get("db_instance")
            db_name = content.get("db_name")
            callback = content.get("callback")

            if not instance_name:
                return False, "no instance name provided"
            if not db_name:
                return False, "no database name provided"

            # Initialize thread-local database connections if needed
            if not hasattr(context.thread_local_data, "db_connections"):
                context.thread_local_data.db_connections = {}

            # Get or create database connection
            db_key = f"{instance_name}:{db_name}"
            if db_key not in context.thread_local_data.db_connections:
                try:
                    # Get database manager
                    db_manager = basefunctions.DbManager()

                    # Get instance and database
                    instance = db_manager.get_instance(instance_name)
                    db = instance.get_database(db_name)

                    # Store for reuse
                    context.thread_local_data.db_connections[db_key] = db
                except Exception as e:
                    return False, f"failed to connect to database: {str(e)}"

            # Get database connection
            db = context.thread_local_data.db_connections[db_key]

            # Process based on operation type
            if operation == "write_dataframe":
                return self._handle_write_dataframe(db, content)
            elif operation == "flush_cache":
                return self._handle_flush_cache(db, content)
            elif operation == "query_to_dataframe":
                return self._handle_query_to_dataframe(db, content)
            else:
                return False, f"unknown operation: {operation}"

        except Exception as e:
            basefunctions.get_logger(__name__).critical(
                f"error in DataFrame task handler: {str(e)}"
            )

            # Try to execute callback even on error
            if message and message.content and message.content.get("callback"):
                try:
                    message.content["callback"](False, str(e))
                except:
                    pass

            return False, f"error in DataFrame task handler: {str(e)}"

    def _handle_write_dataframe(
        self, db: "basefunctions.Db", content: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Handle writing a DataFrame to a database table.

        parameters
        ----------
        db : basefunctions.Db
            database to write to
        content : Dict[str, Any]
            operation content

        returns
        -------
        Tuple[bool, str]
            success flag and result message
        """
        table_name = content.get("table_name")
        df = content.get("dataframe")
        callback = content.get("callback")

        if not table_name:
            return False, "no table name provided"
        if df is None:
            return False, "no dataframe provided"

        try:
            # Get connection from database
            connection = db.instance.get_connection().get_connection()

            # Write DataFrame to database
            df.to_sql(table_name, connection, if_exists="append", index=False)

            # Execute callback if provided
            if callback and callable(callback):
                try:
                    callback(True, f"wrote {len(df)} rows to {table_name}")
                except Exception as e:
                    basefunctions.get_logger(__name__).warning(f"error in callback: {str(e)}")

            return True, f"wrote {len(df)} rows to {table_name}"

        except Exception as e:
            # Execute callback on error
            if callback and callable(callback):
                try:
                    callback(False, str(e))
                except:
                    pass

            return False, f"failed to write dataframe to {table_name}: {str(e)}"

    def _handle_flush_cache(
        self, db: "basefunctions.Db", content: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Handle flushing cached DataFrames to database tables.

        parameters
        ----------
        db : basefunctions.Db
            database to write to
        content : Dict[str, Any]
            operation content

        returns
        -------
        Tuple[bool, str]
            success flag and result message
        """
        cache = content.get("cache", {})
        callback = content.get("callback")

        if not cache:
            return True, "cache is empty, nothing to flush"

        try:
            # Get connection from database
            connection = db.instance.get_connection().get_connection()

            # Track statistics
            stats = {"tables": 0, "frames": 0, "rows": 0}

            # Process each table in cache
            for table_name, frames in cache.items():
                if not frames:
                    continue

                # Combine all DataFrames for this table
                combined_df = pd.concat(frames, ignore_index=True)

                # Write to database
                combined_df.to_sql(table_name, connection, if_exists="append", index=False)

                # Update statistics
                stats["tables"] += 1
                stats["frames"] += len(frames)
                stats["rows"] += len(combined_df)

            # Execute callback if provided
            if callback and callable(callback):
                try:
                    callback(
                        True,
                        f"flushed {stats['frames']} frames with {stats['rows']} rows from {stats['tables']} tables",
                    )
                except Exception as e:
                    basefunctions.get_logger(__name__).warning(f"error in callback: {str(e)}")

            return (
                True,
                f"flushed {stats['frames']} frames with {stats['rows']} rows from {stats['tables']} tables",
            )

        except Exception as e:
            # Execute callback on error
            if callback and callable(callback):
                try:
                    callback(False, str(e))
                except:
                    pass

            return False, f"failed to flush cache: {str(e)}"

    def _handle_query_to_dataframe(
        self, db: "basefunctions.Db", content: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """
        Handle executing a query and returning results as a DataFrame.

        parameters
        ----------
        db : basefunctions.Db
            database to query
        content : Dict[str, Any]
            operation content

        returns
        -------
        Tuple[bool, Any]
            success flag and DataFrame or error message
        """
        query = content.get("query")
        parameters = content.get("parameters", ())
        callback = content.get("callback")

        if not query:
            return False, "no query provided"

        try:
            # Execute query and get DataFrame
            df = db.query_to_dataframe(query, parameters)

            # Execute callback if provided
            if callback and callable(callback):
                try:
                    callback(True, df)
                except Exception as e:
                    basefunctions.get_logger(__name__).warning(f"error in callback: {str(e)}")

            return True, df

        except Exception as e:
            # Execute callback on error
            if callback and callable(callback):
                try:
                    callback(False, str(e))
                except:
                    pass

            return False, f"failed to execute query to DataFrame: {str(e)}"
