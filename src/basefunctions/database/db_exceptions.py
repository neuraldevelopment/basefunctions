"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Unified database exception hierarchy with Db prefix naming convention

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Any, Optional, cast
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


class DbError(Exception):
    """
    Base class for all database-related exceptions.

    All database operations should raise exceptions derived from this class
    to provide consistent error handling across the database abstraction layer.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize database error with enhanced context.

        parameters
        ----------
        message : str
            human-readable error message
        error_code : str, optional
            machine-readable error code for programmatic handling
        original_error : Exception, optional
            original exception that caused this error (for chaining)
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


class DbConnectionError(DbError):
    """
    Error establishing or maintaining database connections.

    Raised when:
    - Initial connection to database fails
    - Connection is lost during operation
    - Connection parameters are invalid
    - Network connectivity issues
    - SSL/TLS configuration problems
    """

    def __init__(
        self,
        message: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize connection error with server context.

        parameters
        ----------
        message : str
            error message
        host : str, optional
            database host that failed
        port : int, optional
            database port that failed
        database : str, optional
            database name that failed
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.host = host
        self.port = port
        self.database = database


class DbQueryError(DbError):
    """
    Error executing SQL queries or database operations.

    Raised when:
    - SQL syntax errors
    - Query execution failures
    - Data type conversion errors
    - Constraint violations
    - Permission denied for query execution
    - Table or column not found errors
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        parameters=None,
        table: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize query error with SQL context.

        parameters
        ----------
        message : str
            error message
        query : str, optional
            SQL query that failed
        parameters : any, optional
            query parameters that were used
        table : str, optional
            table name involved in error
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.query = query
        self.parameters = parameters
        self.table = table


class DbTransactionError(DbError):
    """
    Error handling database transactions.

    Raised when:
    - Transaction begin/commit/rollback fails
    - Deadlock detection
    - Transaction timeout
    - Nested transaction errors
    - Isolation level conflicts
    - Transaction state inconsistencies
    """

    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize transaction error with transaction context.

        parameters
        ----------
        message : str
            error message
        transaction_id : str, optional
            transaction identifier for debugging
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.transaction_id = transaction_id


class DbConfigurationError(DbError):
    """
    Error in database configuration or setup.

    Raised when:
    - Missing required configuration parameters
    - Invalid configuration values
    - Conflicting configuration settings
    - Environment setup errors
    - Secret/credential processing failures
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs,
    ):
        """
        Initialize configuration error with config context.

        parameters
        ----------
        message : str
            error message
        config_key : str, optional
            configuration key that caused the error
        config_value : any, optional
            configuration value that caused the error
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


class DbValidationError(DbError):
    """
    Error validating database parameters or inputs.

    Raised when:
    - Parameter validation fails
    - Input data format is invalid
    - Required parameters are missing
    - Data constraints are violated
    - Type conversion failures
    """

    def __init__(
        self,
        message: str,
        parameter_name: Optional[str] = None,
        parameter_value=None,
        expected_type: Optional[type] = None,
        **kwargs,
    ):
        """
        Initialize validation error with parameter context.

        parameters
        ----------
        message : str
            error message
        parameter_name : str, optional
            name of parameter that failed validation
        parameter_value : any, optional
            value that failed validation
        expected_type : type, optional
            expected type for the parameter
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.expected_type = expected_type


class DbResourceError(DbError):
    """
    Error managing database resources.

    Raised when:
    - Connection pool exhausted
    - Memory allocation failures
    - File system errors (SQLite)
    - Resource cleanup failures
    - Resource lock timeouts
    - Disk space issues
    """

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_limit: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize resource error with resource context.

        parameters
        ----------
        message : str
            error message
        resource_type : str, optional
            type of resource that failed (connection, memory, disk)
        resource_limit : int, optional
            resource limit that was exceeded
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_limit = resource_limit


class DbFactoryError(DbError):
    """
    Error in database factory operations.

    Raised when:
    - Connector registration fails
    - Unknown database type requested
    - Factory initialization errors
    - Connector instantiation failures
    - Dynamic loading errors
    """

    def __init__(
        self,
        message: str,
        db_type: Optional[str] = None,
        connector_class: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize factory error with factory context.

        parameters
        ----------
        message : str
            error message
        db_type : str, optional
            database type that caused the error
        connector_class : str, optional
            connector class name that failed
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.db_type = db_type
        self.connector_class = connector_class


class DbInstanceError(DbError):
    """
    Error in database instance management.

    Raised when:
    - Instance creation fails
    - Instance configuration errors
    - Multiple instances conflict
    - Instance state inconsistencies
    - Manager registration failures
    """

    def __init__(
        self,
        message: str,
        instance_name: Optional[str] = None,
        instance_type: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize instance error with instance context.

        parameters
        ----------
        message : str
            error message
        instance_name : str, optional
            name of instance that caused the error
        instance_type : str, optional
            type of instance that failed
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.instance_name = instance_name
        self.instance_type = instance_type


class DbDataFrameError(DbError):
    """
    Error in DataFrame operations.

    Raised when:
    - DataFrame to SQL conversion fails
    - SQL to DataFrame conversion fails
    - DataFrame caching errors
    - EventBus DataFrame operation failures
    - Pandas integration issues
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        row_count: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize DataFrame error with operation context.

        parameters
        ----------
        message : str
            error message
        operation : str, optional
            DataFrame operation that failed (read, write, cache)
        table_name : str, optional
            table name involved in the operation
        row_count : int, optional
            number of rows involved in the operation
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.operation = operation
        self.table_name = table_name
        self.row_count = row_count


class DbSchemaError(DbError):
    """
    Error in database schema operations.

    Raised when:
    - Table creation/modification fails
    - Schema migration errors
    - Index creation failures
    - Constraint definition errors
    - Column type mismatches
    """

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        table_name: Optional[str] = None,
        column_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize schema error with schema context.

        parameters
        ----------
        message : str
            error message
        schema_name : str, optional
            schema name that caused the error
        table_name : str, optional
            table name that caused the error
        column_name : str, optional
            column name that caused the error
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.schema_name = schema_name
        self.table_name = table_name
        self.column_name = column_name


class DbAuthenticationError(DbError):
    """
    Error in database authentication.

    Raised when:
    - Invalid credentials provided
    - Authentication method not supported
    - Permission denied for database access
    - SSL certificate validation fails
    - Token/session expiration
    """

    def __init__(
        self,
        message: str,
        username: Optional[str] = None,
        auth_method: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize authentication error with auth context.

        parameters
        ----------
        message : str
            error message
        username : str, optional
            username that failed authentication
        auth_method : str, optional
            authentication method that failed
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.username = username
        self.auth_method = auth_method


class DbTimeoutError(DbError):
    """
    Error due to operation timeouts.

    Raised when:
    - Query execution timeout
    - Connection establishment timeout
    - Transaction timeout
    - Lock acquisition timeout
    - Resource wait timeout
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize timeout error with timing context.

        parameters
        ----------
        message : str
            error message
        timeout_seconds : float, optional
            timeout value that was exceeded
        operation : str, optional
            operation that timed out
        **kwargs
            additional context passed to parent
        """
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


# =============================================================================
# ERROR CODE CONSTANTS
# =============================================================================


class DbErrorCodes:
    """Constants for database error codes to enable programmatic error handling."""

    # Connection errors
    CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    CONNECTION_LOST = "DB_CONNECTION_LOST"
    CONNECTION_TIMEOUT = "DB_CONNECTION_TIMEOUT"
    CONNECTION_REFUSED = "DB_CONNECTION_REFUSED"
    SSL_ERROR = "DB_SSL_ERROR"

    # Query errors
    QUERY_FAILED = "DB_QUERY_FAILED"
    QUERY_SYNTAX_ERROR = "DB_QUERY_SYNTAX_ERROR"
    QUERY_TIMEOUT = "DB_QUERY_TIMEOUT"
    TABLE_NOT_FOUND = "DB_TABLE_NOT_FOUND"
    COLUMN_NOT_FOUND = "DB_COLUMN_NOT_FOUND"
    CONSTRAINT_VIOLATION = "DB_CONSTRAINT_VIOLATION"

    # Transaction errors
    TRANSACTION_FAILED = "DB_TRANSACTION_FAILED"
    TRANSACTION_DEADLOCK = "DB_TRANSACTION_DEADLOCK"
    TRANSACTION_ROLLBACK = "DB_TRANSACTION_ROLLBACK"
    TRANSACTION_TIMEOUT = "DB_TRANSACTION_TIMEOUT"
    TRANSACTION_ALREADY_ACTIVE = "DB_TRANSACTION_ALREADY_ACTIVE"

    # Configuration errors
    CONFIG_MISSING = "DB_CONFIG_MISSING"
    CONFIG_INVALID = "DB_CONFIG_INVALID"
    CONFIG_CONFLICT = "DB_CONFIG_CONFLICT"
    SECRET_NOT_FOUND = "DB_SECRET_NOT_FOUND"

    # Validation errors
    VALIDATION_FAILED = "DB_VALIDATION_FAILED"
    PARAMETER_MISSING = "DB_PARAMETER_MISSING"
    PARAMETER_INVALID = "DB_PARAMETER_INVALID"
    TYPE_MISMATCH = "DB_TYPE_MISMATCH"

    # Resource errors
    RESOURCE_EXHAUSTED = "DB_RESOURCE_EXHAUSTED"
    POOL_EXHAUSTED = "DB_POOL_EXHAUSTED"
    MEMORY_LIMIT = "DB_MEMORY_LIMIT"
    DISK_FULL = "DB_DISK_FULL"

    # Authentication errors
    AUTH_FAILED = "DB_AUTH_FAILED"
    PERMISSION_DENIED = "DB_PERMISSION_DENIED"
    TOKEN_EXPIRED = "DB_TOKEN_EXPIRED"

    # Factory errors
    FACTORY_ERROR = "DB_FACTORY_ERROR"
    CONNECTOR_NOT_FOUND = "DB_CONNECTOR_NOT_FOUND"
    CONNECTOR_REGISTRATION_FAILED = "DB_CONNECTOR_REGISTRATION_FAILED"

    # Instance errors
    INSTANCE_ERROR = "DB_INSTANCE_ERROR"
    INSTANCE_NOT_FOUND = "DB_INSTANCE_NOT_FOUND"
    INSTANCE_CONFLICT = "DB_INSTANCE_CONFLICT"

    # DataFrame errors
    DATAFRAME_READ_ERROR = "DB_DATAFRAME_READ_ERROR"
    DATAFRAME_WRITE_ERROR = "DB_DATAFRAME_WRITE_ERROR"
    DATAFRAME_CACHE_ERROR = "DB_DATAFRAME_CACHE_ERROR"

    # Schema errors
    SCHEMA_ERROR = "DB_SCHEMA_ERROR"
    MIGRATION_ERROR = "DB_MIGRATION_ERROR"
    INDEX_ERROR = "DB_INDEX_ERROR"


# =============================================================================
# EXCEPTION FACTORY FUNCTIONS
# =============================================================================


def create_connection_error(
    message: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    original_error: Optional[Exception] = None,
) -> DbConnectionError:
    """
    Factory function for creating connection errors with context.

    parameters
    ----------
    message : str
        base error message
    host : str, optional
        database host that failed
    port : int, optional
        database port that failed
    database : str, optional
        database name that failed
    original_error : Exception, optional
        underlying exception

    returns
    -------
    DbConnectionError
        configured connection error
    """
    context_parts = []
    if host:
        context_parts.append(f"host={host}")
    if port:
        context_parts.append(f"port={port}")
    if database:
        context_parts.append(f"database={database}")

    if context_parts:
        enhanced_message = f"{message} ({', '.join(context_parts)})"
    else:
        enhanced_message = message

    return DbConnectionError(
        enhanced_message,
        host=host,
        port=port,
        database=database,
        error_code=DbErrorCodes.CONNECTION_FAILED,
        original_error=original_error,
    )


def create_query_error(
    message: str,
    query: Optional[str] = None,
    parameters: Optional[Any] = None,
    table: Optional[str] = None,
    original_error: Optional[Exception] = None,
) -> DbQueryError:
    """
    Factory function for creating query errors with SQL context.

    parameters
    ----------
    message : str
        base error message
    query : str, optional
        SQL query that failed
    parameters : any, optional
        query parameters
    table : str, optional
        table name involved in error
    original_error : Exception, optional
        underlying exception

    returns
    -------
    DbQueryError
        configured query error
    """
    enhanced_message = message
    if table:
        enhanced_message = f"{message} (table: {table})"

    return DbQueryError(
        enhanced_message,
        query=query,
        parameters=parameters,
        table=table,
        error_code=DbErrorCodes.QUERY_FAILED,
        original_error=original_error,
    )


def create_validation_error(
    message: str,
    parameter_name: Optional[str] = None,
    parameter_value: Optional[Any] = None,
    expected_type: Optional[type] = None,
    original_error: Optional[Exception] = None,
) -> DbValidationError:
    """
    Factory function for creating validation errors with parameter context.

    parameters
    ----------
    message : str
        base error message
    parameter_name : str, optional
        name of parameter that failed validation
    parameter_value : any, optional
        value that failed validation
    expected_type : type, optional
        expected type for the parameter
    original_error : Exception, optional
        underlying exception

    returns
    -------
    DbValidationError
        configured validation error
    """
    enhanced_message = message
    if parameter_name:
        enhanced_message = f"{message} (parameter: {parameter_name}"
        if parameter_value is not None:
            enhanced_message += f", value: {parameter_value}"
        if expected_type:
            enhanced_message += f", expected: {expected_type.__name__}"
        enhanced_message += ")"

    return DbValidationError(
        enhanced_message,
        parameter_name=parameter_name,
        parameter_value=parameter_value,
        expected_type=expected_type,
        error_code=DbErrorCodes.VALIDATION_FAILED,
        original_error=original_error,
    )


def create_transaction_error(
    message: str,
    transaction_id: Optional[str] = None,
    original_error: Optional[Exception] = None,
) -> DbTransactionError:
    """
    Factory function for creating transaction errors with context.

    parameters
    ----------
    message : str
        base error message
    transaction_id : str, optional
        transaction identifier
    original_error : Exception, optional
        underlying exception

    returns
    -------
    DbTransactionError
        configured transaction error
    """
    enhanced_message = message
    if transaction_id:
        enhanced_message = f"{message} (transaction: {transaction_id})"

    return DbTransactionError(
        enhanced_message,
        transaction_id=transaction_id,
        error_code=DbErrorCodes.TRANSACTION_FAILED,
        original_error=original_error,
    )


def create_resource_error(
    message: str,
    resource_type: Optional[str] = None,
    resource_limit: Optional[int] = None,
    original_error: Optional[Exception] = None,
) -> DbResourceError:
    """
    Factory function for creating resource errors with context.

    parameters
    ----------
    message : str
        base error message
    resource_type : str, optional
        type of resource that failed
    resource_limit : int, optional
        resource limit that was exceeded
    original_error : Exception, optional
        underlying exception

    returns
    -------
    DbResourceError
        configured resource error
    """
    enhanced_message = message
    if resource_type:
        enhanced_message = f"{message} (resource: {resource_type}"
        if resource_limit:
            enhanced_message += f", limit: {resource_limit}"
        enhanced_message += ")"

    return DbResourceError(
        enhanced_message,
        resource_type=resource_type,
        resource_limit=resource_limit,
        error_code=DbErrorCodes.RESOURCE_EXHAUSTED,
        original_error=original_error,
    )


# =============================================================================
# EXCEPTION UTILITY FUNCTIONS
# =============================================================================


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is potentially retryable.

    parameters
    ----------
    error : Exception
        exception to check

    returns
    -------
    bool
        True if error might be retryable, False otherwise
    """
    if isinstance(error, DbTimeoutError):
        return True
    elif isinstance(error, DbConnectionError):
        return True  # Connection issues might be temporary
    elif isinstance(error, DbResourceError):
        return True  # Resource exhaustion might be temporary
    elif isinstance(error, (DbValidationError, DbConfigurationError, DbAuthenticationError)):
        return False  # These are permanent errors
    return False  # Conservative default


def get_error_category(error: Exception) -> str:
    """
    Get the category of a database error for logging/monitoring.

    parameters
    ----------
    error : Exception
        exception to categorize

    returns
    -------
    str
        error category
    """
    if isinstance(error, DbConnectionError):
        return "connection"
    elif isinstance(error, DbQueryError):
        return "query"
    elif isinstance(error, DbTransactionError):
        return "transaction"
    elif isinstance(error, DbConfigurationError):
        return "configuration"
    elif isinstance(error, DbValidationError):
        return "validation"
    elif isinstance(error, DbResourceError):
        return "resource"
    elif isinstance(error, DbFactoryError):
        return "factory"
    elif isinstance(error, DbInstanceError):
        return "instance"
    elif isinstance(error, DbDataFrameError):
        return "dataframe"
    elif isinstance(error, DbSchemaError):
        return "schema"
    elif isinstance(error, DbAuthenticationError):
        return "authentication"
    elif isinstance(error, DbTimeoutError):
        return "timeout"
    elif isinstance(error, DbError):
        return "database"
    else:
        return "unknown"


def format_error_context(error: Exception) -> Dict[str, Any]:
    """
    Extract context information from a database error for logging.

    parameters
    ----------
    error : Exception
        exception to extract context from

    returns
    -------
    Dict[str, Any]
        context information
    """
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_category": get_error_category(error),
        "retryable": is_retryable_error(error),
    }

    if isinstance(error, DbError) and error.error_code:
        context["error_code"] = error.error_code

    if isinstance(error, DbConnectionError):
        if error.host:
            context["host"] = error.host
        if error.port:
            context["port"] = error.port
        if error.database:
            context["database"] = error.database

    elif isinstance(error, DbQueryError):
        if error.query:
            context["query"] = error.query[:200] + "..." if len(error.query) > 200 else error.query
        if error.table:
            context["table"] = error.table

    elif isinstance(error, DbTransactionError):
        if error.transaction_id:
            context["transaction_id"] = error.transaction_id

    elif isinstance(error, DbValidationError):
        if error.parameter_name:
            context["parameter_name"] = error.parameter_name
        if error.expected_type:
            context["expected_type"] = error.expected_type.__name__

    elif isinstance(error, DbResourceError):
        if error.resource_type:
            context["resource_type"] = error.resource_type
        if error.resource_limit:
            context["resource_limit"] = error.resource_limit

    elif isinstance(error, DbTimeoutError):
        if error.timeout_seconds:
            context["timeout_seconds"] = error.timeout_seconds
        if error.operation:
            context["operation"] = error.operation

    return context
