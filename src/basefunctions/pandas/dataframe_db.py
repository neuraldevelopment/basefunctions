"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  DataFrame database abstraction with EventBus integration for pandas operations
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List
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
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DataFrameDb:
    """
    High-level DataFrame database abstraction with EventBus integration.

    Provides pandas DataFrame operations (read/write/delete) through EventBus
    for asynchronous and thread-safe database operations.
    """

    def __init__(self, instance_name: str, database_name: str) -> None:
        """
        Initialize DataFrame database interface.

        Parameters
        ----------
        instance_name : str
            Name of the database instance
        database_name : str
            Name of the database

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        """
        if not instance_name:
            raise basefunctions.DataFrameValidationError(
                "instance_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )
        if not database_name:
            raise basefunctions.DataFrameValidationError(
                "database_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        self.instance_name = instance_name
        self.database_name = database_name
        self.logger = basefunctions.get_logger(__name__)

        # Initialize EventBus and register handlers
        self.event_bus = basefunctions.EventBus()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """
        Register DataFrame handlers with EventFactory.
        """
        try:
            # Direct registration instead of function call
            basefunctions.EventFactory.register_event_type("dataframe_read", basefunctions.DataFrameReadHandler)
            basefunctions.EventFactory.register_event_type("dataframe_write", basefunctions.DataFrameWriteHandler)
            basefunctions.EventFactory.register_event_type("dataframe_delete", basefunctions.DataFrameDeleteHandler)
            self.logger.debug("DataFrame handlers registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register DataFrame handlers: {str(e)}")
            raise basefunctions.DataFrameDbError(f"Handler registration failed: {str(e)}") from e

    def read(
        self,
        table_name: str,
        query: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> pd.DataFrame:
        """
        Read DataFrame from database table via EventBus.

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
        pd.DataFrame
            DataFrame containing query results

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
            # Create read event
            event_data = {
                "instance_name": self.instance_name,
                "database_name": self.database_name,
                "table_name": table_name,
                "query": query,
                "params": params or [],
            }

            event = basefunctions.Event(
                type="dataframe_read", data=event_data, timeout=timeout, max_retries=max_retries
            )

            # Publish event and wait for result
            event_id = self.event_bus.publish(event)
            self.event_bus.join()

            # Get results
            results, errors = self.event_bus.get_results()

            # Process results
            for result_event in results:
                if result_event.data.get("result_success"):
                    dataframe = result_event.data.get("result_data")
                    if isinstance(dataframe, pd.DataFrame):
                        self.logger.debug(f"Read {len(dataframe)} rows from table '{table_name}'")
                        return dataframe
                    else:
                        raise basefunctions.DataFrameDbError(
                            f"Invalid result type: expected DataFrame, got {type(dataframe)}"
                        )

            # Process errors
            for error_event in errors:
                error_msg = error_event.data.get("error", "Unknown error in read operation")
                raise basefunctions.DataFrameDbError(f"Read operation failed: {error_msg}")

            # No results received
            raise basefunctions.DataFrameDbError("No results received from read operation")

        except basefunctions.DataFrameDbError:
            raise
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
    ) -> bool:
        """
        Write DataFrame to database table via EventBus.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame to write to database
        table_name : str
            Name of the target table
        if_exists : str, optional
            What to do if table exists ('append', 'replace', 'fail'), by default "append"
        index : bool, optional
            Whether to write DataFrame index, by default False
        method : Optional[str], optional
            Insertion method for pandas.to_sql(), by default None
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3

        Returns
        -------
        bool
            True if write was successful

        Raises
        ------
        DataFrameValidationError
            If parameters are invalid
        DataFrameDbError
            If write operation fails
        """
        # Validate inputs
        if not isinstance(dataframe, pd.DataFrame):
            raise basefunctions.DataFrameValidationError(
                "dataframe parameter must be pandas DataFrame",
                error_code=basefunctions.DataFrameDbErrorCodes.TYPE_MISMATCH,
            )

        if not table_name:
            raise basefunctions.DataFrameValidationError(
                "table_name cannot be empty", error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE
            )

        if dataframe.empty:
            raise basefunctions.DataFrameValidationError(
                "Cannot write empty DataFrame",
                error_code=basefunctions.DataFrameDbErrorCodes.EMPTY_DATAFRAME,
                dataframe_shape=dataframe.shape,
            )

        if if_exists not in ["append", "replace", "fail"]:
            raise basefunctions.DataFrameValidationError(
                f"Invalid if_exists value: {if_exists}. Must be 'append', 'replace', or 'fail'",
                error_code=basefunctions.DataFrameDbErrorCodes.INVALID_STRUCTURE,
            )

        try:
            # Create write event
            event_data = {
                "instance_name": self.instance_name,
                "database_name": self.database_name,
                "table_name": table_name,
                "dataframe": dataframe,
                "if_exists": if_exists,
                "index": index,
                "method": method,
            }

            event = basefunctions.Event(
                type="dataframe_write", data=event_data, timeout=timeout, max_retries=max_retries
            )

            # Publish event and wait for result
            event_id = self.event_bus.publish(event)
            self.event_bus.join()

            # Get results
            results, errors = self.event_bus.get_results()

            # Process results
            for result_event in results:
                if result_event.data.get("result_success"):
                    rows_written = result_event.data.get("result_data", 0)
                    self.logger.debug(f"Wrote {rows_written} rows to table '{table_name}'")
                    return True

            # Process errors
            for error_event in errors:
                error_msg = error_event.data.get("error", "Unknown error in write operation")
                raise basefunctions.DataFrameDbError(f"Write operation failed: {error_msg}")

            # No results received
            raise basefunctions.DataFrameDbError("No results received from write operation")

        except basefunctions.DataFrameDbError:
            raise
        except Exception as e:
            raise basefunctions.DataFrameDbError(f"Unexpected error in write operation: {str(e)}") from e

    def delete(
        self,
        table_name: str,
        where: Optional[str] = None,
        params: Optional[List] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> bool:
        """
        Delete data from database table via EventBus.

        Parameters
        ----------
        table_name : str
            Name of the table to delete from
        where : Optional[str], optional
            WHERE clause for conditional delete. If None, deletes all rows
        params : Optional[List], optional
            Parameters for WHERE clause
        timeout : int, optional
            Timeout in seconds, by default 30
        max_retries : int, optional
            Maximum retry attempts, by default 3

        Returns
        -------
        bool
            True if delete was successful

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
            # Create delete event
            event_data = {
                "instance_name": self.instance_name,
                "database_name": self.database_name,
                "table_name": table_name,
                "where": where,
                "params": params or [],
            }

            event = basefunctions.Event(
                type="dataframe_delete", data=event_data, timeout=timeout, max_retries=max_retries
            )

            # Publish event and wait for result
            event_id = self.event_bus.publish(event)
            self.event_bus.join()

            # Get results
            results, errors = self.event_bus.get_results()

            # Process results
            for result_event in results:
                if result_event.data.get("result_success"):
                    self.logger.debug(f"Delete operation completed on table '{table_name}'")
                    return True

            # Process errors
            for error_event in errors:
                error_msg = error_event.data.get("error", "Unknown error in delete operation")
                raise basefunctions.DataFrameDbError(f"Delete operation failed: {error_msg}")

            # No results received
            raise basefunctions.DataFrameDbError("No results received from delete operation")

        except basefunctions.DataFrameDbError:
            raise
        except Exception as e:
            raise basefunctions.DataFrameDbError(f"Unexpected error in delete operation: {str(e)}") from e

    def get_connection_info(self) -> dict:
        """
        Get connection information for debugging.

        Returns
        -------
        dict
            Connection information
        """
        return {
            "instance_name": self.instance_name,
            "database_name": self.database_name,
            "event_bus_stats": self.event_bus.get_stats(),
        }

    def __str__(self) -> str:
        """
        String representation for debugging.

        Returns
        -------
        str
            String representation
        """
        return f"DataFrameDb[{self.instance_name}.{self.database_name}]"

    def __repr__(self) -> str:
        """
        Detailed representation for debugging.

        Returns
        -------
        str
            Detailed representation
        """
        return f"DataFrameDb(instance_name='{self.instance_name}', database_name='{self.database_name}')"
