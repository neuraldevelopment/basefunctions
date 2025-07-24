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
        table_name: str = None,
        query: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> str:
        """
        Read DataFrame from database table via EventBus (non-blocking).

        Parameters
        ----------
        table_name : str, optional
            Name of the table to read from (used if query is None)
        query : Optional[str], optional
            Custom SQL query. If None, reads entire table
        params : Optional[List], optional
            Parameters for SQL query
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3

        Returns
        -------
        str
            Event ID for result tracking

        Raises
        ------
        basefunctions.DbValidationError
            If parameters are invalid
        """
        if not query and not table_name:
            raise basefunctions.DbValidationError("Either query or table_name must be provided")

        if not query:
            query = f"SELECT * FROM {table_name}"

        with self.lock:
            try:
                event_data = {
                    "operation": "read",
                    "sql": query,
                    "params": params or [],
                    "instance_name": self.instance_name,
                    "database_name": self.database_name,
                }

                event = basefunctions.Event(
                    event_type="dataframe", event_data=event_data, timeout=timeout, max_retries=max_retries
                )

                event_id = self.event_bus.publish(event)
                return event_id

            except Exception as e:
                raise basefunctions.DbQueryError(f"Failed to publish read event: {str(e)}") from e

    def write(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
        index: bool = False,
        method: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> str:
        """
        Write DataFrame to database table via EventBus (non-blocking).

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame to write to database
        table_name : str
            Name of the target table
        if_exists : str, optional
            How to behave if table exists, by default "append"
            Options: 'fail', 'replace', 'append'
        index : bool, optional
            Whether to write DataFrame index as column, by default False
        method : Optional[str], optional
            Method to use for SQL insertion, by default None
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3

        Returns
        -------
        str
            Event ID for result tracking

        Raises
        ------
        basefunctions.DbValidationError
            If parameters are invalid
        """
        if not table_name:
            raise basefunctions.DbValidationError("table_name cannot be empty")

        if dataframe.empty:
            raise basefunctions.DbValidationError("dataframe cannot be empty")

        if if_exists not in ["fail", "replace", "append"]:
            raise basefunctions.DbValidationError(
                f"if_exists must be 'fail', 'replace', or 'append', got '{if_exists}'"
            )

        with self.lock:
            try:
                event_data = {
                    "operation": "write",
                    "dataframe": dataframe,
                    "table_name": table_name,
                    "if_exists": if_exists,
                    "index": index,
                    "method": method,
                    "instance_name": self.instance_name,
                    "database_name": self.database_name,
                }

                event = basefunctions.Event(
                    event_type="dataframe", event_data=event_data, timeout=timeout, max_retries=max_retries
                )

                event_id = self.event_bus.publish(event)
                return event_id

            except Exception as e:
                raise basefunctions.DbQueryError(f"Failed to publish write event: {str(e)}") from e

    def get_results(
        self, event_ids: Optional[List[str]] = None
    ) -> Union[Dict[str, basefunctions.EventResult], List[basefunctions.EventResult]]:
        """
        Get response(s) from processed DataFrame operations.

        Parameters
        ----------
        event_ids : Optional[List[str]], optional
            List of specific event IDs to retrieve. If None, returns all results.

        Returns
        -------
        Union[Dict[str, EventResult], List[EventResult]]
            Dict when event_ids=None (all results), List when specific event_ids given
        """
        return self.event_bus.get_results(event_ids, join_before=True)
