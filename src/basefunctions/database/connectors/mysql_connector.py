"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  MySQL connector implementation with Registry-based configuration

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict, Union
import threading
import mysql.connector
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
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class MySQLConnector(basefunctions.DbConnector):
    """
    MySQL-specific connector implementing the base interface with Registry integration.

    Connection Behavior:
    - Connects to MySQL server instance
    - server_database parameter is optional (can be set later with USE)
    - Supports database switching with use_database()
    - Schema concept not applicable (raises NotImplementedError)

    Thread-safe implementation for concurrent access.
    """

    def __init__(self, parameters: basefunctions.DatabaseParameters) -> None:
        """
        Initialize the MySQL connector with Registry integration.

        parameters
        ----------
        parameters : basefunctions.DatabaseParameters
            connection parameters for the database
        """
        super().__init__(parameters)
        self.db_type = "mysql"
        self.engine = None
        self.lock = threading.RLock()

    def connect(self) -> None:
        """
        Establish connection to MySQL server.
        Optionally selects initial database if server_database is provided.

        raises
        ------
        basefunctions.DbConnectionError
            if connection cannot be established
        """
        with self.lock:
            try:
                self._validate_parameters(["user", "password", "host"])

                # Get default port from Registry if not specified
                default_port = self.get_default_port() or 3306

                # Prepare connection arguments
                connect_args = {
                    "user": self.parameters["user"],
                    "password": self.parameters["password"],
                    "host": self.parameters["host"],
                    "port": self.parameters.get("port", default_port),
                    "charset": self.parameters.get("charset", "utf8mb4"),
                    "use_pure": True,
                    "autocommit": True,
                }

                # Add optional database selection
                if self.parameters.get("server_database"):
                    connect_args["database"] = self.parameters["server_database"]
                    self.current_database = self.parameters["server_database"]

                # Add SSL parameters if available
                if self.parameters.get("ssl_ca"):
                    connect_args["ssl_ca"] = self.parameters["ssl_ca"]
                if self.parameters.get("ssl_cert"):
                    connect_args["ssl_cert"] = self.parameters["ssl_cert"]
                if self.parameters.get("ssl_key"):
                    connect_args["ssl_key"] = self.parameters["ssl_key"]
                if "ssl_verify" in self.parameters:
                    connect_args["ssl_verify_cert"] = self.parameters["ssl_verify"]

                # Establish connection
                self.connection = mysql.connector.connect(**connect_args)
                if not self.connection:
                    raise basefunctions.DbConnectionError("Failed to establish MySQL connection")

                self.cursor = self.connection.cursor(dictionary=True)
                if not self.cursor:
                    raise basefunctions.DbConnectionError("Failed to create MySQL cursor")

                # Create SQLAlchemy engine
                if self.current_database:
                    conn_url_parts = [
                        f"mysql+pymysql://{self.parameters['user']}",
                        f":{self.parameters['password']}@{self.parameters['host']}",
                        f":{self.parameters.get('port', default_port)}/{self.current_database}",
                    ]
                    connection_url = "".join(conn_url_parts)
                    self.engine = create_engine(connection_url)

                self.logger.debug(
                    f"connected to mysql server at {self.parameters['host']}:{self.parameters.get('port', default_port)}"
                    f"{f' using database {self.current_database}' if self.current_database else ''}"
                )
            except Exception as e:
                self.logger.critical(f"failed to connect to mysql server: {str(e)}")
                raise basefunctions.DbConnectionError(f"failed to connect to mysql server: {str(e)}") from e

    def execute(self, query: str, parameters: Union[tuple, dict] = ()) -> None:
        """
        Execute a SQL query with Registry-based placeholder replacement.

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
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for query execution")
            if not self.connection:
                raise basefunctions.DbQueryError("No connection available for query execution")

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)
                if not self.in_transaction:
                    self.connection.commit()
            except Exception as e:
                if not self.in_transaction:
                    self.connection.rollback()
                self.logger.critical(f"failed to execute query: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute query: {str(e)}") from e

    def query_one(
        self, query: str, parameters: Union[tuple, dict] = (), new_query: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database with Registry-based query handling.

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
        with self.lock:
            if not self.connection or not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for fetch operation")

            try:
                if new_query or self.last_query_string != query:
                    self.cursor.execute(self.replace_sql_statement(query), parameters)
                    self.last_query_string = query

                return self.cursor.fetchone()
            except Exception as e:
                self.logger.critical(f"failed to fetch row: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to fetch row: {str(e)}") from e

    def query_all(self, query: str, parameters: Union[tuple, dict] = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database with Registry-based query handling.

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
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for fetch operation")

            try:
                self.cursor.execute(self.replace_sql_statement(query), parameters)
                return list(self.cursor.fetchall())
            except Exception as e:
                self.logger.critical(f"failed to fetch rows: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to fetch rows: {str(e)}") from e

    def get_connection(self) -> Any:
        """
        Get the underlying database connection.

        returns
        -------
        Any
            SQLAlchemy engine or MySQL connection object

        raises
        ------
        basefunctions.DbConnectionError
            if no connection is available
        """
        if self.engine:
            return self.engine
        if self.connection:
            return self.connection
        raise basefunctions.DbConnectionError("No connection available")

    def begin_transaction(self) -> None:
        """
        Begin a database transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if transaction cannot be started
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.connection:
                raise basefunctions.DbTransactionError("No connection available for transaction")

            try:
                self.connection.autocommit = False
                self.connection.start_transaction()
                self.in_transaction = True
            except Exception as e:
                self.logger.critical(f"failed to begin transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to begin transaction: {str(e)}") from e

    def commit(self) -> None:
        """
        Commit the current transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if commit fails
        """
        with self.lock:
            if not self.connection:
                raise basefunctions.DbTransactionError("No connection available for commit")

            if not self.is_connected():
                raise basefunctions.DbTransactionError("not connected to database")

            try:
                self.connection.commit()
                self.connection.autocommit = True
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to commit transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to commit transaction: {str(e)}") from e

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        raises
        ------
        basefunctions.DbTransactionError
            if rollback fails
        """
        with self.lock:
            if not self.connection:
                raise basefunctions.DbTransactionError("No connection available for rollback")

            if not self.is_connected():
                raise basefunctions.DbTransactionError("not connected to database")

            try:
                self.connection.rollback()
                self.connection.autocommit = True
                self.in_transaction = False
            except Exception as e:
                self.logger.critical(f"failed to rollback transaction: {str(e)}")
                raise basefunctions.DbTransactionError(f"failed to rollback transaction: {str(e)}") from e

    def is_connected(self) -> bool:
        """
        Check if connection is established and valid using Registry-based connection test.

        returns
        -------
        bool
            True if connected, False otherwise
        """
        if self.connection is None:
            return False

        try:
            # Use Registry-based connection test if available
            test_query = self.get_query_template("connection_test")
            if test_query:
                cursor = self.connection.cursor()
                cursor.execute(test_query)
                cursor.close()
            else:
                # Fallback to ping method
                self.connection.ping(reconnect=False)
            return True
        except Exception as e:
            self.logger.debug(f"connection check failed: {str(e)}")
            return False

    def check_if_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists using Registry-based query template.

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

            if not self.cursor:
                self.logger.warning("No cursor available for table existence check")
                return False

            try:
                # Use Registry-based table exists query
                table_exists_query = self.get_query_template("table_exists")
                if table_exists_query:
                    self.cursor.execute(table_exists_query, (table_name,))
                else:
                    # Fallback query
                    query = "SHOW TABLES LIKE %s"
                    self.cursor.execute(query, (table_name,))

                return self.cursor.fetchone() is not None
            except Exception as e:
                self.logger.warning(f"error checking if table exists: {str(e)}")
                return False

    def use_database(self, database_name: str) -> None:
        """
        Switch to a different database.

        parameters
        ----------
        database_name : str
            name of the database to switch to

        raises
        ------
        basefunctions.DbQueryError
            if database switch fails
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for database switch")

            try:
                self.cursor.execute(f"USE `{database_name}`")
                self.current_database = database_name
                self.logger.info(f"switched to database: {database_name}")
            except Exception as e:
                self.logger.critical(f"failed to switch to database {database_name}: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to switch to database {database_name}: {str(e)}") from e

    def use_schema(self, schema_name: str) -> None:
        """
        Schema switching not applicable for MySQL.

        parameters
        ----------
        schema_name : str
            name of the schema (not applicable for MySQL)

        raises
        ------
        NotImplementedError
            always, as MySQL uses database concept instead of schemas
        """
        raise NotImplementedError("MySQL uses databases instead of schemas. Use use_database() instead.")

    def list_tables(self) -> List[str]:
        """
        List all tables using Registry-based query template.

        returns
        -------
        List[str]
            list of table names
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                self.logger.warning("No cursor available for listing tables")
                return []

            try:
                # Use Registry-based list tables query
                list_tables_query = self.get_query_template("list_tables")
                if list_tables_query:
                    self.cursor.execute(list_tables_query)
                else:
                    # Fallback query
                    self.cursor.execute("SHOW TABLES")

                results = self.cursor.fetchall()
                # MySQL SHOW TABLES returns different column names, get first value from each row
                return [list(row.values())[0] for row in results if row]
            except Exception as e:
                self.logger.warning(f"error listing tables: {str(e)}")
                return []

    def execute_many(self, query: str, param_list: List[List]) -> None:
        """
        Execute a SQL query with multiple parameter sets for bulk operations.

        Uses mysql.connector's executemany() for optimal bulk performance with MySQL.
        Automatically handles Registry-based placeholder replacement and transaction
        management consistent with single execute() behavior.

        parameters
        ----------
        query : str
            SQL query to execute (typically INSERT, UPDATE, or DELETE)
        param_list : List[List]
            List of parameter lists, where each inner list contains parameters
            for one execution of the query

        raises
        ------
        basefunctions.DbQueryError
            if query execution fails for any parameter set

        Examples
        --------
        >>> # Bulk insert price data
        >>> connector.execute_many(
        ...     "INSERT INTO price_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ...     [["BMW.XETRA", "2024-01-01", 85.5, 86.2, 85.1, 3.35, 86.0, 150000],
        ...      ["BMW.XETRA", "2024-01-02", 86.0, 86.8, 85.9, 3.36, 86.5, 120000]]
        ... )
        """
        with self.lock:
            if not self.is_connected():
                self.connect()

            if not self.cursor:
                raise basefunctions.DbQueryError("No cursor available for bulk query execution")
            if not self.connection:
                raise basefunctions.DbQueryError("No connection available for bulk query execution")

            if not param_list:
                self.logger.warning("Empty parameter list provided to execute_many, skipping")
                return

            try:
                # Apply Registry-based SQL transformations
                transformed_query = self.replace_sql_statement(query)

                # Execute bulk operation using mysql.connector's executemany
                self.cursor.executemany(transformed_query, param_list)

                # Handle transaction state (consistent with execute() behavior)
                if not self.in_transaction:
                    self.connection.commit()

                self.logger.debug(f"executed bulk query with {len(param_list)} parameter sets")

            except Exception as e:
                # Rollback on error if not in explicit transaction
                if not self.in_transaction:
                    try:
                        self.connection.rollback()
                    except Exception as rollback_error:
                        self.logger.warning(f"rollback failed after bulk query error: {str(rollback_error)}")

                self.logger.critical(f"failed to execute bulk query: {str(e)}")
                raise basefunctions.DbQueryError(f"failed to execute bulk query: {str(e)}") from e
