"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Unified DataFrame handler for EventBus integration using pandas native operations

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
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


class DataFrameHandler(basefunctions.EventHandler):
    """
    Unified DataFrame handler for all database operations using pandas native methods.

    Handles read and write operations through pandas.read_sql and DataFrame.to_sql
    with proper connection management and error handling.
    """

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Handle DataFrame database operations.

        Expected event.event_data format:
        {
            "operation": "read|write",
            "instance_name": "database_instance",
            "database_name": "target_database",

            # For read operations:
            "sql": "SELECT * FROM table WHERE ...",
            "params": [...],  # Optional query parameters

            # For write operations:
            "dataframe": pandas.DataFrame,
            "table_name": "target_table",
            "if_exists": "append",  # append, replace, fail
            "index": False,  # Whether to write DataFrame index
            "method": None  # Insertion method
        }

        Parameters
        ----------
        event : basefunctions.Event
            Event containing operation request data
        context : basefunctions.EventContext
            Event execution context with thread-local data

        Returns
        -------
        basefunctions.EventResult
            Success flag and operation result data
        """
        try:
            # Validate event data
            if not event.event_data or not isinstance(event.event_data, dict):
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Invalid event data: expected dictionary"
                )

            operation = event.event_data.get("operation")
            if not operation:
                return basefunctions.EventResult.business_result(event.event_id, False, "Missing operation type")

            # Route to operation handler
            if operation == "read":
                return self._handle_read(event, context)
            elif operation == "write":
                return self._handle_write(event, context)
            else:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, f"Unknown operation: {operation}"
                )

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)

    def _handle_read(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Handle DataFrame read operation using pandas.read_sql.

        Parameters
        ----------
        event : basefunctions.Event
            Event with read parameters
        context : basefunctions.EventContext
            Execution context

        Returns
        -------
        basefunctions.EventResult
            Result with DataFrame data
        """
        try:
            sql = event.event_data.get("sql")
            params = event.event_data.get("params")

            if not sql:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Missing sql parameter for read operation"
                )

            # Get database connection
            engine = self._get_engine(event.event_data, context)

            # Use pandas.read_sql for optimal performance
            dataframe = pd.read_sql(sql=sql, con=engine, params=params)

            return basefunctions.EventResult.business_result(event.event_id, True, dataframe)

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)

    def _handle_write(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> basefunctions.EventResult:
        """
        Handle DataFrame write operation using DataFrame.to_sql.

        Parameters
        ----------
        event : basefunctions.Event
            Event with write parameters
        context : basefunctions.EventContext
            Execution context

        Returns
        -------
        basefunctions.EventResult
            Result with rows written count
        """
        try:
            dataframe = event.event_data.get("dataframe")
            table_name = event.event_data.get("table_name")
            if_exists = event.event_data.get("if_exists", "append")
            index = event.event_data.get("index", False)
            method = event.event_data.get("method")

            if not isinstance(dataframe, pd.DataFrame):
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Invalid dataframe parameter: expected pandas DataFrame"
                )

            if not table_name:
                return basefunctions.EventResult.business_result(
                    event.event_id, False, "Missing table_name parameter for write operation"
                )

            if dataframe.empty:
                return basefunctions.EventResult.business_result(event.event_id, False, "Cannot write empty DataFrame")

            # Get database connection
            engine = self._get_engine(event.event_data, context)

            # Use pandas.to_sql for optimal performance
            dataframe.to_sql(name=table_name, con=engine, if_exists=if_exists, index=index, method=method)

            return basefunctions.EventResult.business_result(event.event_id, True, len(dataframe))

        except Exception as e:
            return basefunctions.EventResult.exception_result(event.event_id, e)

    def _get_engine(
        self,
        event_data: dict,
        context: basefunctions.EventContext,
    ):
        """
        Get database engine with thread-local caching.

        Parameters
        ----------
        event_data : dict
            Event data containing connection parameters
        context : basefunctions.EventContext
            Event execution context

        Returns
        -------
        Any
            Database connection object for pandas operations

        Raises
        ------
        basefunctions.DataFrameTableError
            If connection creation fails
        """
        try:
            instance_name = event_data.get("instance_name")
            database_name = event_data.get("database_name")

            if not instance_name or not database_name:
                raise ValueError("Missing instance_name or database_name")

            # Check thread-local cache
            cache_key = f"{instance_name}.{database_name}"
            if not hasattr(context.thread_local_data, "db_connections"):
                context.thread_local_data.db_engines = {}

            if cache_key in context.thread_local_data.db_engines:
                return context.thread_local_data.db_engines[cache_key]

            # Create new connection
            manager = basefunctions.DbManager()
            db = manager.get_database(instance_name, database_name)

            # Get raw connection for pandas
            engine = db.get_engine()

            # Cache connection
            context.thread_local_data.db_engines[cache_key] = engine

            return engine

        except Exception as e:
            raise basefunctions.DataFrameTableError(
                f"Failed to get database connection for '{instance_name}.{database_name}'",
                original_error=e,
            ) from e


# =============================================================================
# HANDLER REGISTRATION
# =============================================================================


def register_dataframe_handlers() -> None:
    """
    Register DataFrame handler with the EventFactory.

    Registers single "dataframe" event type that handles both read and write operations.
    """
    factory = basefunctions.EventFactory()
    factory.register_event_type("dataframe", DataFrameHandler)
