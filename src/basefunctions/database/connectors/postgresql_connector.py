"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  PostgreSQL connector implementation with explicit connection semantics
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
from typing import Optional, Any, List, Dict, Union
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
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


class PostgreSQLConnector(basefunctions.DbConnector):
    """
    PostgreSQL-specific connector implementing the base interface.

    Connection Behavior:
    - Connects to specific database (server_database required)
    - No cross-database queries possible
    - Supports schema switching with use_schema()
    - Database switching not supported (raises NotImplementedError)

    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: basefunctions.DatabaseParameters) -> None:
        """
        Initialize the PostgreSQL connector.

        parameters
        ----------
        parameters : basefunctions.DatabaseParameters
            connection parameters for the database
        """
        super().__init__(parameters)
        self.db_type = "postgresql"
        self.engine = None
        self.lock = threading.RLock()

    def connect(self) -> None:
        """
        Establish connection to PostgreSQL database.
        Requires server_database parameter for target database.

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            try:
                self._validate_parameters(["user", "password", "host", "server_database"])

                # Prepare connection arguments
                connect_args = {
                    "user": self.parameters["user"],
                    "password": self.parameters["password"],
                    "host": self.parameters["host"],
                    "database": self.parameters["server_database"],
                    "port": self.parameters.get("port", 5432),
                }

                # Set current database from connection
                self.current_database = self.parameters["server_database"]

                # Add SSL parameters if available
                if self.parameters.get("ssl_ca"):
                    connect_args["sslrootcert"] = self.parameters["ssl_ca"]
                if self.parameters.get("ssl_cert"):
                    connect_args["sslcert"] = self.parameters["ssl_cert"]
                if self.parameters.get("ssl_key"):
                    connect_args["sslkey"] = self.parameters["ssl_key"]
                if "ssl_verify" in self.parameters and not self.parameters["ssl_verify"]:
                    connect_args["sslmode"] = "require"
                elif any(key in self.parameters for key in ["ssl_ca", "ssl_cert", "ssl_key"]):
                    connect_args["sslmode"] = "verify-ca"

                # Add client encoding if specified
                if "charset" in self.parameters:
                    connect_args["client_encoding"] = self.parameters["charset"]

                # Establish connection
                self.connection = psycopg2.connect(**connect_args)
                self.connection.autocommit = True

                # Use RealDictCursor for dictionary results
                self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                # Set default schema if specified
                if self.parameters.get("default_schema"):
                    self.use_schema(self.parameters["default_schema"])

                # Create SQLAlchemy engine
                conn_url_parts = [
                    f"postgresql+psycopg2://{self.parameters['user']}",
                    f":{self.parameters['password']}@{self.parameters['host']}",
                    f":{self.parameters.get('port', 5432)}/{self.current_database}",
                ]
                connection_url = "".join(conn_url_parts)
                self.engine = create_engine(connection_url)

                self.logger.warning(
                    f"connected to postgresql database '{self.current_database}' "
                    f"at {self.parameters['host']}:{self.parameters.get('port', 5432)}"
                    f"{f' using schema {self.current_schema}' if self.current_schema else ''}"
                )
            except Exception as e:
                self.logger.critical(f"failed to connect to postgresql database: {str(e)}")
                raise basefunctions.DbConnectionError(
                    f"failed to connect to postgresql database: {str(e)}"
                ) from e

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
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)
                if not self.in_transaction:
                    self.connection.commit()
            except Exception as e:
                if not self.in_transaction:
                    self.connection.rollback()
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.QueryError(f"failed to execute query: {str(e)}") from e

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
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                if new_query or self.last_query_string != query:
                    self.cursor.execute(self.replace_sql_statement(query), parameters)
                    self.last_query_string = query

                return self.cursor.fetchone()
            except Exception as e:
                self.logger.critical(f"failed to fetch row: {str(e)}")
                raise basefunctions.QueryError(f"failed to fetch row: {str(e)}") from e

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
        basefunctions.QueryError
            if query execution fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)
                return list(self.cursor.fetchall())
            except Exception as e:
                self.logger.critical(f"failed to fetch rows: {str(e)}")
                raise basefunctions.QueryError(f"failed to fetch rows: {str(e)}") from e

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            SQLAlchemy engine or PostgreSQL connection object
        """
        return self.engine or self.connection

    def begin_transaction(self) -> None:
        """
        Begin a database transaction.

        raises
        ------
        basefunctions.TransactionError
            if transaction cannot be started
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                self.connection.autocommit = False
                self.in_transaction = True
            except Exception as e:
                self.logger.critical(f"failed to begin transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to begin transaction: {str(e)}"
                ) from e

    def commit(self) -> None:
        """
        Commit the current transaction.

        raises
        ------
        basefunctions.TransactionError
            if commit fails
        """
        with self.lock:
            if not self.is_connected():
                raise basefunctions.TransactionError("not connected to database")

            try:
                self.connection.commit()
                self.connection.autocommit = True
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to commit transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to commit transaction: {str(e)}"
                ) from e

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        raises
        ------
        basefunctions.TransactionError
            if rollback fails
        """
        with self.lock:
            if not self.is_connected():
                raise basefunctions.TransactionError("not connected to database")

            try:
                self.connection.rollback()
                self.connection.autocommit = True
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to rollback transaction: {str(e)}")
                raise basefunctions.TransactionError(
                    f"failed to rollback transaction: {str(e)}"
                ) from e

    def is_connected(self) -> bool:
        """
        Check if connection is established and valid.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            self.logger.debug(f"connection check failed: {str(e)}")
            return False

    def check_if_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the current database/schema.

        parameters
        ----------
        table_name : str
            name of the table to check

        returns
        -------
        bool
            True if table exists, False otherwise
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                query = (
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)"
                )
                self.cursor.execute(query, (table_name,))
                result = self.cursor.fetchone()
                return result and result.get("exists", False)
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def use_database(self, database_name: str) -> None:
        """
        Database switching not supported for PostgreSQL.

        parameters
        ----------
        database_name : str
            name of the database (not supported for PostgreSQL)

        raises
        ------
        NotImplementedError
            always, as PostgreSQL requires separate connections for different databases
        """
        raise NotImplementedError(
            "PostgreSQL requires separate connections for different databases. "
            "Create a new connector instance instead."
        )

    def use_schema(self, schema_name: str) -> None:
        """
        Switch to a different schema by modifying the search_path.

        parameters
        ----------
        schema_name : str
            name of the schema to switch to

        raises
        ------
        basefunctions.QueryError
            if schema switch fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                # Set search_path to prioritize the specified schema
                self.cursor.execute(f"SET search_path TO {schema_name}, public")
                self.current_schema = schema_name
                self.logger.info(f"switched to schema: {schema_name}")
            except Exception as e:
                self.logger.critical(f"failed to switch to schema {schema_name}: {str(e)}")
                raise basefunctions.QueryError(
                    f"failed to switch to schema {schema_name}: {str(e)}"
                ) from e

    def get_server_version(self) -> str:
        """
        Get the PostgreSQL server version.

        returns
        -------
        str
            PostgreSQL server version
        """
        if not self.is_connected():
            self.connect()

        try:
            self.cursor.execute("SHOW server_version")
            result = self.cursor.fetchone()
            return result.get("server_version", "Unknown")
        except Exception as e:
            self.logger.warning(f"error getting server version: {str(e)}")
            return "Unknown"

    def list_schemas(self) -> List[str]:
        """
        List all schemas in the current database.

        returns
        -------
        List[str]
            list of schema names
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            try:
                query = (
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')"
                )
                self.cursor.execute(query)
                return [row["schema_name"] for row in self.cursor.fetchall()]
            except Exception as e:
                self.logger.warning(f"error listing schemas: {str(e)}")
                return []

    def get_current_schema(self) -> str:
        """
        Get the current schema name.

        returns
        -------
        str
            current schema name
        """
        if not self.is_connected():
            self.connect()

        try:
            self.cursor.execute("SELECT current_schema()")
            result = self.cursor.fetchone()
            return result.get("current_schema", "public")
        except Exception as e:
            self.logger.warning(f"error getting current schema: {str(e)}")
            return "public"
