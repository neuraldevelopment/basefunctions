"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 DataFrame database abstraction layer with EventBus integration

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, List, Dict, Any, Union
import threading
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

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


class DataFrameDb:
    """
    DataFrame database abstraction layer using EventBus for async operations.

    Provides non-blocking DataFrame CRUD operations via EventBus.
    Client must call get_results() to retrieve operation results.
    """

    def __init__(self, instance_name: str, database_name: str) -> None:
        """
        Initialize DataFrame database interface.

        Parameters
        ----------
        instance_name : str
            Name of the database instance
        database_name : str
            Name of the target database
        """
        self.instance_name = instance_name
        self.database_name = database_name
        self.event_bus = basefunctions.EventBus()
        self.logger = basefunctions.get_logger(__name__)
        self.lock = threading.RLock()

    def read(
        self,
        queries: Dict[str, str],
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> str:
        """
        Execute multiple named SQL queries to read DataFrames.

        Parameters
        ----------
        queries : Dict[str, str]
            Named queries: {"dataframe_name": "SQL query"}
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3

        Returns
        -------
        List[str]
            List of event IDs for result tracking

        Result: Dict[str, pd.DataFrame]
        """
        if not queries or not isinstance(queries, dict):
            raise basefunctions.DbValidationError("queries must be a non-empty dictionary")

        if not all(isinstance(query, str) and query.strip() for query in queries.values()):
            raise basefunctions.DbValidationError("All queries must be non-empty strings")

        with self.lock:
            try:
                event_ids = []

                # Iteriere über alle Queries und erstelle separate Events
                for query_name, sql in queries.items():
                    event_data = {
                        "operation": "read",
                        "query_name": query_name,
                        "sql": sql,
                        "instance_name": self.instance_name,
                        "database_name": self.database_name,
                    }

                    event = basefunctions.Event(
                        event_type="dataframe", event_data=event_data, timeout=timeout, max_retries=max_retries
                    )

                    event_id = self.event_bus.publish(event)
                    event_ids.append(event_id)

                return event_ids

            except Exception as e:
                raise basefunctions.DbQueryError(f"Failed to publish read events: {str(e)}") from e

    def write(
        self,
        dataframes: Dict[str, pd.DataFrame],
        table_mapping: Optional[Dict[str, str]] = None,
        if_exists: str = "append",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> List[str]:
        """
        Write multiple DataFrames to database tables.

        Parameters
        ----------
        dataframes : Dict[str, pd.DataFrame]
            DataFrames to write: {"name": dataframe}
        table_mapping : Optional[Dict[str, str]], optional
            Map names to table names: {"name": "table_name"}
            If None, uses names as table names
        if_exists : str, optional
            How to behave if table exists, by default "append"
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3

        Returns
        -------
        List[str]
            List of event IDs for result tracking
        """
        if not dataframes or not isinstance(dataframes, dict):
            raise basefunctions.DbValidationError("dataframes must be a non-empty dictionary")

        if not all(isinstance(df, pd.DataFrame) and not df.empty for df in dataframes.values()):
            raise basefunctions.DbValidationError("All dataframes must be non-empty pandas DataFrames")

        if if_exists not in ["fail", "replace", "append"]:
            raise basefunctions.DbValidationError(
                f"if_exists must be 'fail', 'replace', or 'append', got '{if_exists}'"
            )

        with self.lock:
            try:
                event_ids = []

                # Iteriere über alle DataFrames und erstelle separate Events
                for df_name, dataframe in dataframes.items():
                    # Bestimme Tabellennamen
                    table_name = table_mapping.get(df_name, df_name) if table_mapping else df_name

                    event_data = {
                        "operation": "write",
                        "dataframe_name": df_name,
                        "dataframe": dataframe,
                        "table_name": table_name,
                        "if_exists": if_exists,
                        "index": False,
                        "method": None,
                        "instance_name": self.instance_name,
                        "database_name": self.database_name,
                    }

                    event = basefunctions.Event(
                        event_type="dataframe", event_data=event_data, timeout=timeout, max_retries=max_retries
                    )

                    event_id = self.event_bus.publish(event)
                    event_ids.append(event_id)

                return event_ids

            except Exception as e:
                raise basefunctions.DbQueryError(f"Failed to publish write events: {str(e)}") from e

    def get_results(
        self,
        event_ids: List[str] = None,
        join_before=True,
    ) -> Dict[str, basefunctions.EventResult]:
        """
        Get response(s) from processed DataFrame operations.

        Parameters
        ----------
        event_ids : List[str], optional
            List of specific event IDs to retrieve. If None, returns all results.
        join_before : bool, optional
            Whether to wait for events to complete before returning, by default True

        Returns
        -------
        Dict[str, basefunctions.EventResult]
            Dictionary mapping event IDs to their results
        """
        return self.event_bus.get_results(event_ids, join_before=join_before)
