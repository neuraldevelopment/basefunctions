"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Abstract base class for database connectors with explicit connection semantics
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict, TypedDict, Tuple, Union
from abc import ABC, abstractmethod
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


class DatabaseError(Exception):
    """Base class for database exceptions"""

    pass


class QueryError(DatabaseError):
    """Error executing query"""

    pass


class TransactionError(DatabaseError):
    """Error handling transactions"""

    pass


class DbConnectionError(DatabaseError):
    """Error establishing database connection"""

    pass


class DatabaseParameters(TypedDict, total=False):
    """
    Type definition for database connection parameters with explicit semantics.

    Connection Target Semantics:
    - PostgreSQL: Connects to specific server_database (required)
    - MySQL: Connects to server instance, server_database optional
    - SQLite: server_database is file path (required)
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
    Abstract base class for database connectors with explicit connection semantics.

    Connection Behavior:
    - PostgreSQL: Connects to specific database, no cross-database queries
    - MySQL: Connects to server, can switch databases with USE statement
    - SQLite: Connects to single file database
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
        self.close()
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
        ValueError
            if any required key is missing
        """
        missing_keys = [key for key in required_keys if key not in self.parameters]
        if missing_keys:
            raise ValueError(f"missing required parameters: {', '.join(missing_keys)}")

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the database.

        Connection semantics depend on database type:
        - PostgreSQL: Connects to specific server_database
        - MySQL: Connects to server, optionally selects server_database
        - SQLite: Opens database file specified in server_database

        raises
        ------
        DbConnectionError
            if connection cannot be established
        """
        pass

    def close(self) -> None:
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
        self.logger.warning(f"connection closed ({self.db_type})")

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
        QueryError
            if query execution fails
        """
        pass

    @abstractmethod
    def fetch_one(
        self, query: str, parameters: Union[tuple, dict] = (), new_query: bool = False
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
            whether to execute a new query or use the last one, by default False

        returns
        -------
        Optional[Dict[str, Any]]
            row as dictionary or None if no row found

        raises
        ------
        QueryError
            if query execution fails
        """
        pass

    @abstractmethod
    def fetch_all(self, query: str, parameters: Union[tuple, dict] = ()) -> List[Dict[str, Any]]:
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
        QueryError
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
        TransactionError
            if transaction cannot be started
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """
        Commit the current transaction.

        raises
        ------
        TransactionError
            if commit fails
        """
        pass

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback the current transaction.

        raises
        ------
        TransactionError
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

        parameters
        ----------
        database_name : str
            name of the database to switch to

        raises
        ------
        NotImplementedError
            if database switching is not supported
        QueryError
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

        parameters
        ----------
        schema_name : str
            name of the schema to switch to

        raises
        ------
        NotImplementedError
            if schema switching is not supported
        QueryError
            if schema switch fails
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
        Safe replacement of SQL placeholders.

        parameters
        ----------
        sql_statement : str
            SQL statement with placeholders

        returns
        -------
        str
            SQL statement with placeholders replaced
        """
        return sql_statement.replace("<PRIMARYKEY>", self._get_primary_key_syntax())

    def _get_primary_key_syntax(self) -> str:
        """
        Get database-specific primary key syntax.

        returns
        -------
        str
            primary key syntax
        """
        primary_key_map = {
            "sqlite3": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "mysql": "SERIAL AUTO_INCREMENT PRIMARY KEY",
            "postgresql": "BIGSERIAL PRIMARY KEY",
        }
        return primary_key_map.get(self.db_type, "BIGSERIAL PRIMARY KEY")

    def transaction(self) -> "basefunctions.TransactionContextManager":
        """
        Return a transaction context manager.

        returns
        -------
        basefunctions.TransactionContextManager
            transaction context manager

        example
        -------
        with connector.transaction():
            connector.execute("INSERT INTO users (name) VALUES (?)", ("John",))
            connector.execute("INSERT INTO logs (action) VALUES (?)", ("User created",))
        """
        return basefunctions.TransactionContextManager(self)
