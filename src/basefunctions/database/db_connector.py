"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Abstract base class for database connectors with Registry-based configuration

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict, TypedDict, Union
from abc import ABC, abstractmethod
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


class DatabaseParameters(TypedDict, total=False):
    """
    Type definition for database connection parameters with explicit semantics.

    Connection Target Semantics:
    - PostgreSQL: Connects to specific server_database (required)
    - MySQL: Connects to server instance, server_database optional
    - SQLite: server_database is file path (required)
    - Redis: server_database not applicable
    """

    host: Optional[str]  # Server hostname/IP (not needed for SQLite)
    port: Optional[int]  # Server port (not needed for SQLite)
    server_database: Optional[str]  # Target database name or file path
    default_schema: Optional[str]  # Default schema (PostgreSQL only)
    user: Optional[str]  # Database user
    password: Optional[str]  # Database password
    min_connections: Optional[int]  # Connection pool minimum
    max_connections: Optional[int]  # Connection pool maximum
    charset: Optional[str]  # Character encoding
    ssl_ca: Optional[str]  # SSL certificate authority
    ssl_cert: Optional[str]  # SSL client certificate
    ssl_key: Optional[str]  # SSL client key
    ssl_verify: Optional[bool]  # SSL verification mode
    pragmas: Optional[Dict[str, Any]]  # SQLite pragmas


class DbConnector(ABC):
    """
    Abstract base class for database connectors with Registry-based configuration.

    Connection Behavior:
    - PostgreSQL: Connects to specific database, no cross-database queries
    - MySQL: Connects to server, can switch databases with USE statement
    - SQLite: Connects to single file database
    - Redis: Connects to Redis server, database selection via SELECT
    """

    def __init__(self, parameters: DatabaseParameters) -> None:
        """
        Initialize connector with connection parameters.

        parameters
        ----------
        parameters : DatabaseParameters
            connection parameters for the database
        """
        self.parameters = parameters
        self.connection: Optional[Any] = None
        self.cursor: Optional[Any] = None
        self.last_query_string: Optional[str] = None
        self.db_type: Optional[str] = None
        self.in_transaction: bool = False
        self.current_database: Optional[str] = None
        self.current_schema: Optional[str] = None
        self.logger = basefunctions.get_logger(__name__)
        self.registry = basefunctions.get_registry()

    def __enter__(self) -> "DbConnector":
        """
        Context manager entry point.

        returns
        -------
        DbConnector
            self for use in with statement
        """
        if not self.is_connected():
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context manager exit point.

        parameters
        ----------
        exc_type : Type[Exception]
            exception type if an exception was raised
        exc_val : Exception
            exception value if an exception was raised
        exc_tb : traceback
            traceback if an exception was raised

        returns
        -------
        bool
            False to propagate exceptions
        """
        self.disconnect()
        return False

    def _validate_parameters(self, required_keys: List[str]) -> None:
        """
        Validate that all required parameters are present.

        parameters
        ----------
        required_keys : List[str]
            list of required parameter keys

        raises
        ------
        basefunctions.DbValidationError
            if any required key is missing
        """
        missing_keys = [key for key in required_keys if key not in self.parameters]
        if missing_keys:
            raise basefunctions.DbValidationError(f"missing required parameters: {', '.join(missing_keys)}")

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the database.

        Connection semantics depend on database type:
        - PostgreSQL: Connects to specific server_database
        - MySQL: Connects to server, optionally selects server_database
        - SQLite: Opens database file specified in server_database
        - Redis: Connects to Redis server

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        pass

    def disconnect(self) -> None:
        """
        Close database connection and cursor.
        """
        try:
            if self.cursor:
                self.cursor.close()
        except Exception as e:
            self.logger.warning(f"error closing cursor: {str(e)}")

        try:
            if self.connection:
                self.connection.close()
        except Exception as e:
            self.logger.warning(f"error closing connection: {str(e)}")

        self.cursor = self.connection = None
        self.current_database = self.current_schema = None
        self.in_transaction = False
        self.logger.debug(f"connection closed ({self.db_type})")

    @abstractmethod
    def execute(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Execute a SQL query.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        raises
        ------
        basefunctions.DbQueryError
            if query execution fails
        """
        pass

    @abstractmethod
    def query_one(
        self, query: str, parameters: Union[tuple, dict] = (), new_query: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()
        new_query : bool, optional
            whether to execute a new query or use the last one, by default True

        returns
        -------
        Optional[Dict[str, Any]]
            row as dictionary or None if no row found

        raises
        ------
        basefunctions.DbQueryError
            if query execution fails
        """
        pass

    @abstractmethod
    def query_all(self, query: str, parameters: Union[tuple, dict] = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database.

        parameters
        ----------
        query : str
            SQL query to execute
        parameters : Union[tuple, dict], optional
            query parameters, by default ()

        returns
        -------
        List[Dict[str, Any]]
            rows as list of dictionaries

        raises
        ------
        basefunctions.DbQueryError
            if query execution fails
        """
        pass

    @abstractmethod
    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            database connection object
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """
        Begin a database transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if transaction cannot be started
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """
        Commit the current transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if commit fails
        """
        pass

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback the current transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if rollback fails
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connection is established.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def check_if_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the current database/schema context.

        parameters
        ----------
        table_name : str
            name of the table to check

        returns
        -------
        bool
            True if table exists, False otherwise
        """
        pass

    @abstractmethod
    def use_database(self, database_name: str) -> None:
        """
        Switch to a different database context.

        Behavior by database type:
        - MySQL: Changes current database with USE statement
        - PostgreSQL: Not supported, raises NotImplementedError
        - SQLite: Not supported, raises NotImplementedError
        - Redis: Uses SELECT command to switch database

        parameters
        ----------
        database_name : str
            name of the database to switch to

        raises
        ------
        NotImplementedError
            if database switching is not supported
        basefunctions.DbQueryError
            if database switch fails
        """
        pass

    @abstractmethod
    def use_schema(self, schema_name: str) -> None:
        """
        Switch to a different schema context.

        Behavior by database type:
        - PostgreSQL: Changes search_path to prioritize schema
        - MySQL: Not applicable, raises NotImplementedError
        - SQLite: Not applicable, raises NotImplementedError
        - Redis: Not applicable, raises NotImplementedError

        parameters
        ----------
        schema_name : str
            name of the schema to switch to

        raises
        ------
        NotImplementedError
            if schema switching is not supported
        basefunctions.DbQueryError
            if schema switch fails
        """
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        List all tables in the current database/schema context.

        returns
        -------
        List[str]
            list of table names
        """
        pass

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information.

        returns
        -------
        Dict[str, Any]
            connection details including current database and schema
        """
        return {
            "db_type": self.db_type,
            "connected": self.is_connected(),
            "current_database": self.current_database,
            "current_schema": self.current_schema,
            "in_transaction": self.in_transaction,
            "host": self.parameters.get("host"),
            "port": self.parameters.get("port"),
        }

    def replace_sql_statement(self, sql_statement: str) -> str:
        """
        Safe replacement of SQL placeholders using Registry-based configuration.

        parameters
        ----------
        sql_statement : str
            SQL statement with placeholders

        returns
        -------
        str
            SQL statement with placeholders replaced
        """
        if not self.db_type:
            return sql_statement

        try:
            # Get primary key syntax from Registry
            primary_key_syntax = self.registry.get_primary_key_syntax(self.db_type)
            if primary_key_syntax:
                return sql_statement.replace("<PRIMARYKEY>", primary_key_syntax)
            else:
                # For database types without primary key syntax (like Redis), return as-is
                return sql_statement
        except Exception as e:
            self.logger.warning(f"error replacing SQL placeholders: {str(e)}")
            return sql_statement

    def _get_primary_key_syntax(self) -> str:
        """
        Get database-specific primary key syntax using Registry.

        returns
        -------
        str
            primary key syntax from Registry or fallback

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        if not self.db_type:
            return "BIGSERIAL PRIMARY KEY"  # fallback

        try:
            primary_key_syntax = self.registry.get_primary_key_syntax(self.db_type)
            return primary_key_syntax or "BIGSERIAL PRIMARY KEY"  # fallback if None
        except Exception as e:
            self.logger.warning(f"error getting primary key syntax for {self.db_type}: {str(e)}")
            return "BIGSERIAL PRIMARY KEY"  # fallback

    def supports_feature(self, feature: str) -> bool:
        """
        Check if the current database type supports a specific feature using Registry.

        parameters
        ----------
        feature : str
            feature to check (databases, schemas, etc.)

        returns
        -------
        bool
            True if feature is supported, False otherwise
        """
        if not self.db_type:
            return False

        try:
            return self.registry.supports_feature(self.db_type, feature)
        except Exception as e:
            self.logger.warning(f"error checking feature support for {self.db_type}.{feature}: {str(e)}")
            return False

    def get_query_template(self, query_type: str) -> Optional[str]:
        """
        Get SQL query template for current database type using Registry.

        parameters
        ----------
        query_type : str
            type of query (connection_test, table_exists, list_tables, list_databases)

        returns
        -------
        Optional[str]
            SQL query template or None if not available
        """
        if not self.db_type:
            return None

        try:
            return self.registry.get_query_template(self.db_type, query_type)
        except Exception as e:
            self.logger.warning(f"error getting query template for {self.db_type}.{query_type}: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """
        Test database connection using Registry-based connection test query.

        returns
        -------
        bool
            True if connection test successful, False otherwise
        """
        try:
            if not self.is_connected():
                return False

            # Get connection test query from Registry
            test_query = self.get_query_template("connection_test")
            if not test_query:
                return True  # assume connected if no test query available

            # Execute test query
            try:
                self.query_one(test_query)
                return True
            except Exception as e:
                self.logger.debug(f"connection test failed: {str(e)}")
                return False

        except Exception as e:
            self.logger.warning(f"error testing connection: {str(e)}")
            return False

    def get_default_port(self) -> Optional[int]:
        """
        Get default port for current database type using Registry.

        returns
        -------
        Optional[int]
            default port or None if not applicable
        """
        if not self.db_type:
            return None

        try:
            db_port, _ = self.registry.get_default_ports(self.db_type)
            return db_port
        except Exception as e:
            self.logger.warning(f"error getting default port for {self.db_type}: {str(e)}")
            return None
