"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  DataFrame database abstraction layer with EventBus integration
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, List, Dict, Any
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

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

    def __init__(self, instance_name: str, database_name: str):
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

        # Register DataFrame handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register DataFrame event handlers with EventFactory."""
        try:
            # Direct registration instead of function call
            basefunctions.EventFactory.register_event_type("dataframe_read", basefunctions.DataFrameReadHandler)
            basefunctions.EventFactory.register_event_type("dataframe_write", basefunctions.DataFrameWriteHandler)
            basefunctions.EventFactory.register_event_type("dataframe_delete", basefunctions.DataFrameDeleteHandler)
            self.logger.debug("DataFrame handlers registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register DataFrame handlers: {str(e)}")
            raise basefunctions.DataFrameDbError(f"Handler registration failed: {str(e)}") from e

    def _get_db_type(self) -> str:
        """
        Get database type for current instance.

        Returns
        -------
        str
            Database type (postgresql, sqlite, mysql, etc.)
        """
        try:
            manager = basefunctions.DbManager()
            instance = manager.get_instance(self.instance_name)
            return instance.get_type()
        except Exception as e:
            self.logger.warning(f"Could not determine db_type: {str(e)}")
            return "sqlite"  # Fallback

    def read(
        self,
        table_name: str,
        query: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> str:
        """
        Read DataFrame from database table via EventBus (non-blocking).

        Parameters
        ----------
        table_name : str
            Name of the table to read from
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
        DataFrameValidationError
            If parameters are invalid
        DataFrameDbError
            If read operation fails
        """
        if not table_name:
            raise basefunctions.DataFrameValidationError(
                "table_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        try:
            # Get db_type and add to event data
            db_type = self._get_db_type()

            # Create read event with db_type
            event_data = {
                "instance_name": self.instance_name,
                "database_name": self.database_name,
                "table_name": table_name,
                "query": query,
                "params": params or [],
                "db_type": db_type,
            }

            event = basefunctions.Event(
                type="dataframe_read", data=event_data, timeout=timeout, max_retries=max_retries
            )

            # Publish event and return event ID (non-blocking)
            event_id = self.event_bus.publish(event)
            return event_id

        except Exception as e:
            raise basefunctions.DataFrameDbError(f"Unexpected error in read operation: {str(e)}") from e

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
        DataFrameValidationError
            If parameters are invalid
        DataFrameDbError
            If write operation fails
        """
        if not table_name:
            raise basefunctions.DataFrameValidationError(
                "table_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        if dataframe.empty:
            raise basefunctions.DataFrameValidationError(
                "dataframe cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        if if_exists not in ["fail", "replace", "append"]:
            raise basefunctions.DataFrameValidationError(
                f"if_exists must be 'fail', 'replace', or 'append', got '{if_exists}'. "
                "Must be 'append', 'replace', or 'fail'",
                error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE,
            )

        try:
            # Get db_type and add to event data
            db_type = self._get_db_type()

            # Create write event with db_type
            event_data = {
                "instance_name": self.instance_name,
                "database_name": self.database_name,
                "table_name": table_name,
                "dataframe": dataframe,
                "if_exists": if_exists,
                "index": index,
                "method": method,
                "db_type": db_type,
            }

            event = basefunctions.Event(
                type="dataframe_write", data=event_data, timeout=timeout, max_retries=max_retries
            )

            # Publish event and return event ID (non-blocking)
            event_id = self.event_bus.publish(event)
            return event_id

        except Exception as e:
            raise basefunctions.DataFrameDbError(f"Unexpected error in write operation: {str(e)}") from e

    def delete(
        self,
        table_name: str,
        where: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> str:
        """
        Delete data from database table via EventBus (non-blocking).

        Parameters
        ----------
        table_name : str
            Name of the table to delete from
        where : Optional[str], optional
            WHERE clause for conditional delete.
            If None, deletes all rows from table, by default None
        params : Optional[List], optional
            Parameters for WHERE clause, by default None
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
        DataFrameValidationError
            If parameters are invalid
        DataFrameDbError
            If delete operation fails
        """
        if not table_name:
            raise basefunctions.DataFrameValidationError(
                "table_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        try:
            # Get db_type and add to event data
            db_type = self._get_db_type()

            # Create delete event with db_type
            event_data = {
                "instance_name": self.instance_name,
                "database_name": self.database_name,
                "table_name": table_name,
                "where": where,
                "params": params or [],
                "db_type": db_type,
            }

            event = basefunctions.Event(
                type="dataframe_delete", data=event_data, timeout=timeout, max_retries=max_retries
            )

            # Publish event and return event ID (non-blocking)
            event_id = self.event_bus.publish(event)
            return event_id

        except Exception as e:
            raise basefunctions.DataFrameDbError(f"Unexpected error in delete operation: {str(e)}") from e

    def get_results(self) -> Dict[str, Any]:
        """
        Get all available results from EventBus operations.

        Returns
        -------
        Dict[str, Any]
            Dictionary with event_id as key and result data as value.
            Format: {
                "event_id": {
                    "success": bool,
                    "data": Any,
                    "error": Optional[str]
                }
            }
        """
        # Wait for all operations to complete
        self.event_bus.join()

        results, errors = self.event_bus.get_results()
        result_dict = {}

        # Process successful results
        for result_event in results:
            if result_event.data.get("result_success"):
                result_dict[result_event.event_id] = {
                    "success": True,
                    "data": result_event.data.get("result_data"),
                    "error": None,
                }

        # Process errors
        for error_event in errors:
            result_dict[error_event.event_id] = {
                "success": False,
                "data": None,
                "error": error_event.data.get("error", "Unknown error"),
            }

        return result_dict
