"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  DataFrame Database exception hierarchy for pandas integration

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional
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


class DataFrameDbError(Exception):
    """
    Base class for all DataFrame database exceptions.

    Provides consistent error handling across the DataFrame database abstraction layer.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize DataFrame database error with enhanced context.

        Parameters
        ----------
        message : str
            Human-readable error message
        error_code : str, optional
            Machine-readable error code for programmatic handling
        original_error : Exception, optional
            Original exception that caused this error (for chaining)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error message with optional error code."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        class_name = self.__class__.__name__
        if self.error_code:
            return f"{class_name}(message='{self.message}', error_code='{self.error_code}')"
        return f"{class_name}(message='{self.message}')"


class DataFrameValidationError(DataFrameDbError):
    """
    Error in DataFrame validation.

    Raised when:
    - DataFrame is empty when data is required
    - DataFrame has no columns or invalid column structure
    - Data type mismatches that prevent database operations
    - Invalid DataFrame structure for the requested operation
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        dataframe_shape: Optional[tuple] = None,
        column_info: Optional[dict] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize validation error with DataFrame context.

        Parameters
        ----------
        message : str
            Error message
        error_code : str, optional
            Machine-readable error code
        dataframe_shape : tuple, optional
            Shape of the problematic DataFrame (rows, columns)
        column_info : dict, optional
            Information about DataFrame columns and types
        original_error : Exception, optional
            Original exception that caused this error
        """
        super().__init__(message, error_code, original_error)
        self.dataframe_shape = dataframe_shape
        self.column_info = column_info


class DataFrameTableError(DataFrameDbError):
    """
    Error in table operations.

    Raised when:
    - Target table does not exist for read operations
    - Schema conflicts during write operations
    - Table creation fails
    - Table access permissions are insufficient
    - Table structure incompatible with DataFrame
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        table_name: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize table error with table context.

        Parameters
        ----------
        message : str
            Error message
        error_code : str, optional
            Machine-readable error code
        table_name : str, optional
            Name of the table that caused the error
        operation : str, optional
            Operation that failed (read, write, create, delete)
        original_error : Exception, optional
            Original exception that caused this error
        """
        super().__init__(message, error_code, original_error)
        self.table_name = table_name
        self.operation = operation


class DataFrameCacheError(DataFrameDbError):
    """
    Error in DataFrame caching operations.

    Raised when:
    - Cache write operations fail
    - Cache corruption is detected
    - Cache flush operations fail
    - Memory limits exceeded during caching
    - Cache backend unavailable
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        cache_key: Optional[str] = None,
        cache_operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize cache error with cache context.

        Parameters
        ----------
        message : str
            Error message
        error_code : str, optional
            Machine-readable error code
        cache_key : str, optional
            Cache key that caused the error
        cache_operation : str, optional
            Cache operation that failed (get, set, flush, clear)
        original_error : Exception, optional
            Original exception that caused this error
        """
        super().__init__(message, error_code, original_error)
        self.cache_key = cache_key
        self.cache_operation = cache_operation


class DataFrameConversionError(DataFrameDbError):
    """
    Error in DataFrame conversion operations.

    Raised when:
    - SQL to DataFrame conversion fails
    - DataFrame to SQL conversion fails
    - Data type mapping between pandas and SQL fails
    - Encoding issues during conversion
    - Large dataset conversion exceeds memory limits
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        conversion_direction: Optional[str] = None,
        data_types: Optional[dict] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize conversion error with conversion context.

        Parameters
        ----------
        message : str
            Error message
        error_code : str, optional
            Machine-readable error code
        conversion_direction : str, optional
            Direction of conversion ('sql_to_dataframe' or 'dataframe_to_sql')
        data_types : dict, optional
            Information about data types involved in conversion
        original_error : Exception, optional
            Original exception that caused this error
        """
        super().__init__(message, error_code, original_error)
        self.conversion_direction = conversion_direction
        self.data_types = data_types


# =============================================================================
# ERROR CODE CONSTANTS
# =============================================================================


class DataFrameDbErrorCodes:
    """Constants for DataFrame database error codes to enable programmatic error handling."""

    # Validation errors
    EMPTY_DATAFRAME = "DF_EMPTY_DATAFRAME"
    INVALID_COLUMNS = "DF_INVALID_COLUMNS"
    TYPE_MISMATCH = "DF_TYPE_MISMATCH"
    INVALID_STRUCTURE = "DF_INVALID_STRUCTURE"

    # Table errors
    TABLE_NOT_FOUND = "DF_TABLE_NOT_FOUND"
    SCHEMA_CONFLICT = "DF_SCHEMA_CONFLICT"
    TABLE_CREATION_FAILED = "DF_TABLE_CREATION_FAILED"
    ACCESS_DENIED = "DF_ACCESS_DENIED"

    # Cache errors
    CACHE_WRITE_FAILED = "DF_CACHE_WRITE_FAILED"
    CACHE_CORRUPTION = "DF_CACHE_CORRUPTION"
    FLUSH_FAILED = "DF_FLUSH_FAILED"
    MEMORY_LIMIT_EXCEEDED = "DF_MEMORY_LIMIT_EXCEEDED"

    # Conversion errors
    SQL_TO_DATAFRAME_FAILED = "DF_SQL_TO_DATAFRAME_FAILED"
    DATAFRAME_TO_SQL_FAILED = "DF_DATAFRAME_TO_SQL_FAILED"
    TYPE_MAPPING_FAILED = "DF_TYPE_MAPPING_FAILED"
    ENCODING_ERROR = "DF_ENCODING_ERROR"
