"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  DataFrame handlers for EventBus integration with proper database type support

  Log:
  v1.0 : Initial implementation
  v1.1 : Renamed _get_cached_db_connection to _get_cached_database
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def _get_cached_database(context: basefunctions.EventContext, instance_name: str, database_name: str):
    """
    Get cached database from context or create new one.

    Parameters
    ----------
    context : basefunctions.EventContext
        Event execution context
    instance_name : str
        Database instance name
    database_name : str
        Database name

    Returns
    -------
    basefunctions.Db
        Database connection object

    Raises
    ------
    basefunctions.DataFrameTableError
        If database connection fails
    """
    try:
        # Check cache in context first
        cache_key = f"{instance_name}.{database_name}"
        if hasattr(context.thread_local_data, "db_connections"):
            if cache_key in context.thread_local_data.db_connections:
                return context.thread_local_data.db_connections[cache_key]
        else:
            context.thread_local_data.db_connections = {}

        # Create new database connection
        manager = basefunctions.DbManager()
        instance = manager.get_instance(instance_name)
        db = instance.get_database(database_name)

        # Cache in context
        context.thread_local_data.db_connections[cache_key] = db

        return db
    except Exception as e:
        raise basefunctions.DataFrameTableError(
            f"Failed to get database connection for '{instance_name}.{database_name}'",
            error_code=basefunctions.DataFrameDbErrorCodes.TABLE_NOT_FOUND,
            original_error=e,
        )


def _check_table_exists(db, table_name: str) -> bool:
    """
    Check if table exists in database.

    Parameters
    ----------
    db : basefunctions.Db
        Database connection
    table_name : str
        Name of table to check

    Returns
    -------
    bool
        True if table exists, False otherwise
    """
    try:
        return db.table_exists(table_name)
    except Exception:
        return False


def _generate_create_table_sql(dataframe: pd.DataFrame, table_name: str) -> str:
    """
    Generate CREATE TABLE SQL from DataFrame structure.

    Parameters
    ----------
    dataframe : pd.DataFrame
        DataFrame to analyze for table structure
    table_name : str
        Name of the table to create

    Returns
    -------
    str
        CREATE TABLE SQL statement
    """
    column_definitions = []

    # Add index column if it has a name
    if dataframe.index.name:
        column_definitions.append(f'"{dataframe.index.name}" TEXT')

    # Add DataFrame columns with generic types
    for col in dataframe.columns:
        dtype = dataframe[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            sql_type = "BIGINT"
        elif pd.api.types.is_float_dtype(dtype):
            sql_type = "DOUBLE PRECISION"
        elif pd.api.types.is_bool_dtype(dtype):
            sql_type = "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            sql_type = "TIMESTAMP"
        else:
            sql_type = "TEXT"

        column_definitions.append(f'"{col}" {sql_type}')

    columns_sql = ", ".join(column_definitions)
    return f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"


def _get_parameter_placeholder(db_type: str) -> str:
    """
    Get database-specific parameter placeholder.

    Parameters
    ----------
    db_type : str
        Database type (postgresql, postgres, sqlite, mysql)

    Returns
    -------
    str
        Parameter placeholder for the database type
    """
    # Handle both "postgresql" and "postgres"
    if db_type in ["postgresql", "postgres"]:
        return "%s"
    else:  # sqlite, mysql
        return "?"


def _generate_insert_statements(
    dataframe: pd.DataFrame, table_name: str, include_index: bool = False, db_type: str = "sqlite"
):
    """
    Generate INSERT statements with proper parameter placeholders for database type.

    Parameters
    ----------
    dataframe : pd.DataFrame
        DataFrame to generate INSERT statements for
    table_name : str
        Name of target table
    include_index : bool
        Whether to include DataFrame index as column
    db_type : str
        Database type for parameter placeholder selection

    Returns
    -------
    List[Tuple[str, tuple]]
        List of (SQL, values) tuples for execution
    """
    if dataframe.empty:
        return []

    columns = list(dataframe.columns)
    if include_index:
        columns = [dataframe.index.name or "index"] + columns

    # Use db_type specific parameter placeholders
    placeholder = _get_parameter_placeholder(db_type)
    placeholders = ", ".join([placeholder for _ in columns])
    column_names = ", ".join([f'"{col}"' for col in columns])

    insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    statements = []
    for _, row in dataframe.iterrows():
        values = []
        if include_index:
            values.append(row.name)

        # Convert pandas values to Python types
        for val in row.values:
            if pd.isna(val):
                values.append(None)
            elif hasattr(val, "item"):  # numpy scalar
                values.append(val.item())
            else:
                values.append(val)

        statements.append((insert_sql, tuple(values)))

    return statements


class DataFrameReadHandler(basefunctions.EventHandler):
    """
    Event handler for DataFrame read operations from database.

    Converts SQL query results to pandas DataFrames with proper error handling.
    """

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Handle DataFrame read event.

        Expected event.data format:
        {
            "instance_name": "database_instance",
            "database_name": "target_database",
            "table_name": "target_table",
            "query": "SELECT * FROM table WHERE ...",  # Optional
            "params": [...],  # Optional query parameters
            "db_type": "postgresql"  # Database type
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing read request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        basefunctions.EventResult
            Success flag and DataFrame data
        """
        try:
            # Validate event data
            if not event.event_data or not isinstance(event.event_data, dict):
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Invalid event data: expected dictionary with read parameters"
                )

            instance_name = event.event_data.get("instance_name")
            database_name = event.event_data.get("database_name")
            table_name = event.event_data.get("table_name")
            query = event.event_data.get("query")
            params = event.event_data.get("params", [])
            db_type = event.event_data.get("db_type", "sqlite")

            if not instance_name or not database_name or not table_name:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Missing required parameters: instance_name, database_name, table_name"
                )

            # Get cached database connection
            db = _get_cached_database(context, instance_name, database_name)

            # Build query with proper parameter placeholders
            if query is None:
                # Read entire table
                final_query = f"SELECT * FROM {table_name}"
            else:
                # Replace parameter placeholders if needed
                if db_type == "postgresql" and "?" in query:
                    # Convert ? placeholders to %s for PostgreSQL
                    final_query = query.replace("?", "%s")
                else:
                    final_query = query

            # Execute query and convert to DataFrame
            try:
                rows = db.query_all(final_query, params)

                if not rows:
                    # Return empty DataFrame with proper structure
                    return basefunctions.EventResult.business_result(event.event_id, True, pd.DataFrame())

                # Convert to DataFrame
                dataframe = pd.DataFrame(rows)

                # Validate result
                if dataframe.empty:
                    return basefunctions.EventResult.business_result(event.event_id, True, dataframe)

                return basefunctions.EventResult.business_result(event.event_id, True, dataframe)

            except Exception as e:
                raise basefunctions.DataFrameConversionError(
                    f"Failed to convert query result to DataFrame",
                    error_code=basefunctions.DataFrameDbErrorCodes.SQL_TO_DATAFRAME_FAILED,
                    conversion_direction="sql_to_dataframe",
                    original_error=e,
                )

        except basefunctions.DataFrameValidationError as e:
            return basefunctions.EventResult.business_result(event.event_id, False, str(e))

        except basefunctions.DataFrameTableError as e:
            return basefunctions.EventResult.business_result(event.event_id, False, str(e))

        except basefunctions.DataFrameConversionError as e:
            return basefunctions.EventResult.business_result(event.event_id, False, str(e))

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)


class DataFrameWriteHandler(basefunctions.EventHandler):
    """
    Event handler for DataFrame write operations to database.

    Converts pandas DataFrames to SQL and executes insert/update operations.
    """

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
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
            "db_type": "postgresql"  # Database type
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing write request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        basefunctions.EventResult
            Success flag and rows written count
        """
        try:
            # Validate event data
            if not event.event_data or not isinstance(event.event_data, dict):
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Invalid event data: expected dictionary with write parameters"
                )

            instance_name = event.event_data.get("instance_name")
            database_name = event.event_data.get("database_name")
            table_name = event.event_data.get("table_name")
            dataframe = event.event_data.get("dataframe")
            if_exists = event.event_data.get("if_exists", "append")
            index = event.event_data.get("index", False)
            method = event.event_data.get("method")
            db_type = event.event_data.get("db_type", "sqlite")

            if not instance_name or not database_name or not table_name:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Missing required parameters: instance_name, database_name, table_name"
                )

            # Validate DataFrame
            if not isinstance(dataframe, pd.DataFrame):
                raise basefunctions.DataFrameValidationError(
                    "Invalid dataframe parameter: expected pandas DataFrame",
                    error_code=basefunctions.DataFrameDbErrorCodes.TYPE_MISMATCH,
                )

            if dataframe.empty:
                raise basefunctions.DataFrameValidationError(
                    "Cannot write empty DataFrame",
                    error_code=basefunctions.DataFrameDbErrorCodes.EMPTY_DATAFRAME,
                    dataframe_shape=dataframe.shape,
                )

            if len(dataframe.columns) == 0:
                raise basefunctions.DataFrameValidationError(
                    "DataFrame has no columns",
                    error_code=basefunctions.DataFrameDbErrorCodes.INVALID_COLUMNS,
                    dataframe_shape=dataframe.shape,
                )

            # Get cached database connection
            db = _get_cached_database(context, instance_name, database_name)

            try:
                # Handle table replacement
                if if_exists == "replace":
                    try:
                        db.execute(f"DROP TABLE IF EXISTS {table_name}")
                    except:
                        pass  # Table might not exist

                # Create table from DataFrame structure if needed
                create_sql = _generate_create_table_sql(dataframe, table_name)
                if if_exists in ["replace"] or not _check_table_exists(db, table_name):
                    db.execute(create_sql)

                # Generate INSERT statements with correct db_type
                insert_statements = _generate_insert_statements(dataframe, table_name, index, db_type)

                # Execute all inserts in batch
                for insert_sql, values in insert_statements:
                    db.execute(insert_sql, values)

                return basefunctions.EventResult.business_result(event.event_id, True, len(dataframe))

            except Exception as e:
                raise basefunctions.DataFrameConversionError(
                    f"Failed to write DataFrame to database table '{table_name}'",
                    error_code=basefunctions.DataFrameDbErrorCodes.DATAFRAME_TO_SQL_FAILED,
                    conversion_direction="dataframe_to_sql",
                    original_error=e,
                )

        except basefunctions.DataFrameValidationError as e:
            return basefunctions.EventResult.business_result(event.event_id, False, str(e))

        except basefunctions.DataFrameTableError as e:
            return basefunctions.EventResult.business_result(event.event_id, False, str(e))

        except basefunctions.DataFrameConversionError as e:
            return basefunctions.EventResult.business_result(event.event_id, False, str(e))

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)


class DataFrameDeleteHandler(basefunctions.EventHandler):
    """
    Event handler for DataFrame delete operations in database.

    Executes DELETE SQL operations with proper parameter handling.
    """

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Handle DataFrame delete event.

        Expected event.data format:
        {
            "instance_name": "database_instance",
            "database_name": "target_database",
            "table_name": "target_table",
            "where": "WHERE clause",
            "params": [...],
            "db_type": "postgresql"
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing delete request data
        context : Optional[basefunctions.EventContext], optional
            Event execution context

        Returns
        -------
        basefunctions.EventResult
            Success flag and rows deleted count
        """
        try:
            # Validate event data
            if not event.event_data or not isinstance(event.event_data, dict):
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Invalid event data: expected dictionary with delete parameters"
                )

            instance_name = event.event_data.get("instance_name")
            database_name = event.event_data.get("database_name")
            table_name = event.event_data.get("table_name")
            where_clause = event.event_data.get("where")
            params = event.event_data.get("params", [])
            db_type = event.event_data.get("db_type", "sqlite")

            if not instance_name or not database_name or not table_name:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Missing required parameters: instance_name, database_name, table_name"
                )

            # Get cached database connection
            db = _get_cached_database(context, instance_name, database_name)

            try:
                # Build DELETE SQL
                if where_clause:
                    # Adjust parameter placeholders for db_type
                    if db_type == "postgresql" and "?" in where_clause:
                        adjusted_where = where_clause.replace("?", "%s")
                    else:
                        adjusted_where = where_clause

                    delete_sql = f"DELETE FROM {table_name} WHERE {adjusted_where}"
                    result = db.execute(delete_sql, params)
                else:
                    # Delete all rows
                    delete_sql = f"DELETE FROM {table_name}"
                    result = db.execute(delete_sql)

                # Return success with affected row count if available
                return basefunctions.EventResult.business_result(event.event_id, True, getattr(result, "rowcount", 0))

            except Exception as e:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, f"Failed to delete from table '{table_name}': {str(e)}"
                )

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)


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
