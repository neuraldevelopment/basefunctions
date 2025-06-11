"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Event handlers for DataFrame database operations with pandas integration
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Tuple, Any, Optional, Dict, Union
import pandas as pd
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


class DataFrameReadHandler(basefunctions.EventHandler):
    """
    Event handler for DataFrame read operations from database.

    Converts SQL query results to pandas DataFrames with proper error handling.
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle DataFrame read event.

        Expected event.data format:
        {
            "instance_name": "database_instance",
            "database_name": "target_database",
            "table_name": "target_table",
            "query": "SELECT * FROM table WHERE ...",  # Optional
            "params": [...],  # Optional query parameters
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing read request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        Tuple[bool, Any]
            (success, dataframe) where dataframe is pandas DataFrame on success
        """
        try:
            # Validate event data
            if not event.data or not isinstance(event.data, dict):
                return False, "Invalid event data: expected dictionary with read parameters"

            instance_name = event.data.get("instance_name")
            database_name = event.data.get("database_name")
            table_name = event.data.get("table_name")
            query = event.data.get("query")
            params = event.data.get("params", [])

            if not instance_name or not database_name or not table_name:
                return False, "Missing required parameters: instance_name, database_name, table_name"

            # Get database connection
            db = basefunctions.Db(instance_name, database_name)

            # Build query
            if query is None:
                # Read entire table
                final_query = f"SELECT * FROM {table_name}"
            else:
                # Use provided query
                final_query = query

            # Execute query and convert to DataFrame
            try:
                rows = db.query_all(final_query, params)

                if not rows:
                    # Return empty DataFrame with proper structure
                    return True, pd.DataFrame()

                # Convert to DataFrame
                dataframe = pd.DataFrame(rows)

                # Validate result
                if dataframe.empty:
                    return True, dataframe

                return True, dataframe

            except Exception as e:
                raise basefunctions.create_conversion_error(
                    f"Failed to convert query result to DataFrame",
                    conversion_direction="sql_to_dataframe",
                    original_error=e,
                )

        except basefunctions.DataFrameValidationError as e:
            return False, str(e)

        except basefunctions.DataFrameTableError as e:
            return False, str(e)

        except basefunctions.DataFrameConversionError as e:
            return False, str(e)

        except Exception as e:
            error_msg = f"Unexpected error in DataFrame read: {str(e)}"
            return False, error_msg


class DataFrameWriteHandler(basefunctions.EventHandler):
    """
    Event handler for DataFrame write operations to database.

    Converts pandas DataFrames to SQL and executes insert/update operations.
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle DataFrame write event.

        Expected event.data format:
        {
            "instance_name": "database_instance",
            "database_name": "target_database",
            "table_name": "target_table",
            "dataframe": pandas.DataFrame,
            "if_exists": "append",  # append, replace, fail
            "index": False,  # Whether to write DataFrame index
            "method": None,  # Insertion method
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing write request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        Tuple[bool, Any]
            (success, rows_written) where rows_written is int on success
        """
        try:
            # Validate event data
            if not event.data or not isinstance(event.data, dict):
                return False, "Invalid event data: expected dictionary with write parameters"

            instance_name = event.data.get("instance_name")
            database_name = event.data.get("database_name")
            table_name = event.data.get("table_name")
            dataframe = event.data.get("dataframe")
            if_exists = event.data.get("if_exists", "append")
            index = event.data.get("index", False)
            method = event.data.get("method")

            if not instance_name or not database_name or not table_name:
                return False, "Missing required parameters: instance_name, database_name, table_name"

            # Validate DataFrame
            if not isinstance(dataframe, pd.DataFrame):
                raise basefunctions.create_validation_error(
                    "Invalid dataframe parameter: expected pandas DataFrame",
                    error_code=basefunctions.DataFrameDbErrorCodes.TYPE_MISMATCH,
                )

            if dataframe.empty:
                raise basefunctions.create_validation_error(
                    "Cannot write empty DataFrame",
                    dataframe_shape=dataframe.shape,
                    error_code=basefunctions.DataFrameDbErrorCodes.EMPTY_DATAFRAME,
                )

            if len(dataframe.columns) == 0:
                raise basefunctions.create_validation_error(
                    "DataFrame has no columns",
                    dataframe_shape=dataframe.shape,
                    error_code=basefunctions.DataFrameDbErrorCodes.INVALID_COLUMNS,
                )

            # Get database connection
            db = basefunctions.Db(instance_name, database_name)

            try:
                # Convert DataFrame to SQL INSERT statements
                if if_exists == "replace":
                    # Drop table if exists
                    try:
                        db.execute(f"DROP TABLE IF EXISTS {table_name}")
                    except:
                        pass  # Table might not exist

                # Create table from DataFrame structure
                create_sql = _generate_create_table_sql(dataframe, table_name)
                if if_exists in ["replace"] or not db.check_if_table_exists(table_name):
                    db.execute(create_sql)

                # Generate INSERT statements
                insert_statements = _generate_insert_statements(dataframe, table_name, index)

                # Execute all inserts
                for insert_sql, values in insert_statements:
                    db.execute(insert_sql, values)

                return True, len(dataframe)

            except Exception as e:
                raise basefunctions.create_conversion_error(
                    f"Failed to write DataFrame to database table '{table_name}'",
                    conversion_direction="dataframe_to_sql",
                    original_error=e,
                )

        except basefunctions.DataFrameValidationError as e:
            return False, str(e)

        except basefunctions.DataFrameTableError as e:
            return False, str(e)

        except basefunctions.DataFrameConversionError as e:
            return False, str(e)

        except Exception as e:
            error_msg = f"Unexpected error in DataFrame write: {str(e)}"
            return False, error_msg


class DataFrameDeleteHandler(basefunctions.EventHandler):
    """
    Event handler for DataFrame delete operations in database.

    Executes delete operations on database tables.
    """

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self,
        event: basefunctions.Event,
        context: Optional[basefunctions.EventContext] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle DataFrame delete event.

        Expected event.data format:
        {
            "instance_name": "database_instance",
            "database_name": "target_database",
            "table_name": "target_table",
            "where": "column = 'value'",  # Optional WHERE clause
            "params": [...],  # Optional parameters for WHERE clause
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing delete request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        Tuple[bool, Any]
            (success, rows_deleted) where rows_deleted is int on success
        """
        try:
            # Validate event data
            if not event.data or not isinstance(event.data, dict):
                return False, "Invalid event data: expected dictionary with delete parameters"

            instance_name = event.data.get("instance_name")
            database_name = event.data.get("database_name")
            table_name = event.data.get("table_name")
            where_clause = event.data.get("where")
            params = event.data.get("params", [])

            if not instance_name or not database_name or not table_name:
                return False, "Missing required parameters: instance_name, database_name, table_name"

            # Get database connection
            db = basefunctions.Db(instance_name, database_name)

            # Check if table exists
            if not db.check_if_table_exists(table_name):
                raise basefunctions.create_table_error(
                    f"Table '{table_name}' does not exist",
                    table_name=table_name,
                    operation="delete",
                    error_code=basefunctions.DataFrameDbErrorCodes.TABLE_NOT_FOUND,
                )

            # Build delete query
            if where_clause:
                delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"
            else:
                # Delete all rows - be careful!
                delete_query = f"DELETE FROM {table_name}"

            try:
                # Execute delete operation
                db.execute(delete_query, params)

                # Note: Most databases don't return affected row count easily
                # For simplicity, we return success without exact count
                return True, "Delete operation completed"

            except Exception as e:
                raise basefunctions.create_table_error(
                    f"Failed to delete from table '{table_name}'",
                    table_name=table_name,
                    operation="delete",
                    original_error=e,
                )

        except basefunctions.DataFrameTableError as e:
            return False, str(e)

        except Exception as e:
            error_msg = f"Unexpected error in DataFrame delete: {str(e)}"
            return False, error_msg


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _generate_create_table_sql(dataframe, table_name):
    """Generate CREATE TABLE SQL from DataFrame structure."""
    columns = []

    for col_name, dtype in dataframe.dtypes.items():
        if dtype == "object":
            sql_type = "TEXT"
        elif "int" in str(dtype):
            sql_type = "INTEGER"
        elif "float" in str(dtype):
            sql_type = "REAL"
        elif "datetime" in str(dtype):
            sql_type = "TIMESTAMP"
        else:
            sql_type = "TEXT"

        columns.append(f'"{col_name}" {sql_type}')

    return f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"


def _generate_insert_statements(dataframe, table_name, include_index=False):
    """Generate INSERT statements from DataFrame."""
    columns = list(dataframe.columns)
    if include_index:
        columns = [dataframe.index.name or "index"] + columns

    # Use %s for PostgreSQL/MySQL, ? for SQLite
    placeholders = ", ".join(["%s" for _ in columns])
    column_names = ", ".join([f'"{col}"' for col in columns])

    insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    statements = []
    for _, row in dataframe.iterrows():
        values = []
        if include_index:
            values.append(row.name)
        values.extend([None if pd.isna(val) else val for val in row.values])
        statements.append((insert_sql, tuple(values)))

    return statements


# =============================================================================
# HANDLER REGISTRATION
# =============================================================================


def register_dataframe_handlers() -> None:
    """
    Register all DataFrame handlers with the EventFactory.

    Call this function to register DataFrame event handlers:
    - "dataframe_read": DataFrame read operations
    - "dataframe_write": DataFrame write operations
    - "dataframe_delete": DataFrame delete operations
    """
    factory = basefunctions.EventFactory()

    factory.register_event_type("dataframe_read", DataFrameReadHandler)
    factory.register_event_type("dataframe_write", DataFrameWriteHandler)
    factory.register_event_type("dataframe_delete", DataFrameDeleteHandler)
