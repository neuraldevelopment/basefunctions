"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : backtraderfunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  a simple database abstraction layer for SQLite, MySQL, and PostgreSQL

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sqlite3

import mysql.connector
import psycopg2
from sqlalchemy import create_engine

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------
class BaseDatabaseHandler:
    """
    Central database interface for managing multiple database connectors.

    Methods
    -------
    register_connector(connector_id: str, db_type: str, parameters: dict):
        Registers a new database connector under the given ID.

    connect(connector_id: str):
        Connects to the database identified by the given ID.

    close(connector_id: str):
        Closes the connection for the given connector.

    execute(connector_id: str, query: str, parameters: tuple = ()):
        Executes a non-returning query.

    fetch_one(connector_id: str, query: str, parameters: tuple = (), new_query: bool = False) -> dict:
        Fetches a single record.

    fetch_all(connector_id: str, query: str, parameters: tuple = ()) -> list:
        Fetches all records.

    begin_transaction(connector_id: str):
        Begins a transaction.

    commit(connector_id: str):
        Commits the current transaction.

    rollback(connector_id: str):
        Rolls back the current transaction.

    is_connected(connector_id: str) -> bool:
        Checks if the connection is active.

    check_if_table_exists(connector_id: str, table_name: str) -> bool:
        Checks if the specified table exists.

    get_connection(connector_id: str):
        Returns the raw connection/engine for pandas usage.
    """

    def __init__(self):
        self.connectors = {}

    def register_connector(
        self, connector_id: str, db_type: str, parameters: dict
    ) -> "BaseDatabaseConnector":
        """
        Register a new database connector with the given ID, type, and parameters.

        Parameters:
        -----------
            connector_id: str
                Unique identifier for the database connector.
            db_type: str
                Type of the database (e.g., "sqlite3", "mysql" or "postgresql").
            parameters: dict
                Connection parameters required for the database.

        Returns:
        --------
            BaseDatabaseConnector
                The connector instance corresponding to the ID.
        """
        connector_map = {
            "sqlite3": SQLiteConnector,
            "mysql": MySQLConnector,
            "postgresql": PostgreSQLConnector,
        }
        db_type = db_type.lower()
        if db_type not in connector_map:
            raise ValueError(f"Unsupported db_type '{db_type}'")
        self.connectors[connector_id] = connector_map[db_type](parameters)
        return self.connectors[connector_id]

    def get_connector(self, connector_id: str) -> "BaseDatabaseConnector":
        """
        Retrieve the database connector associated with the given ID.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to retrieve.

        Returns:
        --------
            BaseDatabaseConnector
                The connector instance corresponding to the ID.
        """
        if connector_id not in self.connectors:
            raise KeyError(f"Connector '{connector_id}' not registered.")
        return self.connectors[connector_id]

    def connect(self, connector_id: str):
        """
        Establish a connection using the specified connector ID.

        Parameters:
        -----------
            connector_id: str
                The ID of the registered connector to use for the connection.

        Returns:
        --------
            None
                This function does not return a value.
        """
        self.get_connector(connector_id).connect()

    def close(self, connector_id: str):
        """
        Close the connection associated with the specified connector ID.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector whose connection should be closed.

        Returns:
        --------
            None
                This function does not return a value.
        """
        self.get_connector(connector_id).close()

    def close_all(self):
        """
        Close all connections associated with the connectors

        Parameters:
        -----------
            None
                This function does not take a value.

        Returns:
        --------
            None
                This function does not return a value.
        """
        for connector_id in self.connectors.values():
            self.get_connector(connector_id).close()

    def execute(self, connector_id: str, query: str, parameters: tuple = ()):
        """
        Execute a SQL query using the specified connector and parameters.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to use for execution.
            query: str
                The SQL query to be executed.
            parameters: tuple, optional
                Parameters to safely inject into the SQL query. Default is an empty tuple.

        Returns:
        --------
            Any
                The result of the query execution, if any.
        """
        self.get_connector(connector_id).execute(query, parameters)

    def fetch_one(
        self, connector_id: str, query: str, parameters: tuple = (), new_query: bool = False
    ) -> dict:
        """
        Execute a query and fetch a single result as a dictionary.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to use for execution.
            query: str
                The SQL query to execute.
            parameters: tuple, optional
                Parameters to safely inject into the SQL query. Default is an empty tuple.
            new_query: bool, optional
                If True, forces execution of the query even if cached. Default is False.

        Returns:
        --------
            dict
                A dictionary representing the single result row.
        """
        return self.get_connector(connector_id).fetch_one(query, new_query, parameters)

    def fetch_all(self, connector_id: str, query: str, parameters: tuple = ()) -> list:
        """
        Execute a query and fetch all results as a list of dictionaries.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to use for execution.
            query: str
                The SQL query to execute.
            parameters: tuple, optional
                Parameters to safely inject into the SQL query. Default is an empty tuple.

        Returns:
        --------
            list
                A list of dictionaries representing the result rows.
        """
        return self.get_connector(connector_id).fetch_all(query, parameters)

    def begin_transaction(self, connector_id: str):
        """
        Begin a new transaction for the specified connector.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to begin the transaction on.

        Returns:
        --------
            None
                This function does not return a value.
        """
        self.get_connector(connector_id).begin_transaction()

    def commit(self, connector_id: str):
        """
        Commit the current transaction for the specified connector.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to commit the transaction on.

        Returns:
        --------
            None
                This function does not return a value.
        """
        self.get_connector(connector_id).commit()

    def rollback(self, connector_id: str):
        """
        Roll back the current transaction for the specified connector.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to roll back the transaction on.

        Returns:
        --------
            None
                This function does not return a value.
        """
        self.get_connector(connector_id).rollback()

    def is_connected(self, connector_id: str) -> bool:
        """
        Check if the connector with the given ID is currently connected.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to check.

        Returns:
        --------
            bool
                True if the connector is connected, False otherwise.
        """
        return self.get_connector(connector_id).is_connected()

    def check_if_table_exists(self, connector_id: str, table_name: str) -> bool:
        """
        Check whether a specific table exists in the database.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to use for the check.
            table_name: str
                The name of the table to check for existence.

        Returns:
        --------
            bool
                True if the table exists, False otherwise.
        """
        return self.get_connector(connector_id).check_if_table_exists(table_name)

    def get_connection(self, connector_id: str):
        """
        Retrieve the raw database connection for the specified connector ID.

        Parameters:
        -----------
            connector_id: str
                The ID of the connector to retrieve the connection from.

        Returns:
        --------
            Any
                The raw connection object associated with the connector.
        """
        return self.get_connector(connector_id).get_connection()


class BaseDatabaseConnector:
    """
    Abstract base class for database connectors.
    """

    def __init__(self, parameters: dict):
        self.parameters = parameters
        self.connection = None
        self.cursor = None
        self.last_query_string = None
        self.db_type = None

    def connect(self):
        """
        Establish a connection using the default or configured connector.

        Parameters:
        -----------
            None

        Returns:
        --------
            None
                This function does not return a value.
        """
        raise NotImplementedError

    def close(self):
        """
        Close the active connection of the default or configured connector.

        Parameters:
        -----------
            None

        Returns:
        --------
            None
                This function does not return a value.
        """
        raise NotImplementedError

    def execute(self, query: str, parameters: tuple = ()):
        """
        Execute a SQL query on the default or configured connector.

        Parameters:
        -----------
            query: str
                The SQL query to execute.
            parameters: tuple, optional
                Parameters to safely inject into the SQL query. Default is an empty tuple.

        Returns:
        --------
            Any
                The result of the query execution, if any.
        """
        raise NotImplementedError

    def fetch_one(self, query: str, new_query: bool = False, parameters: tuple = ()) -> dict:
        """
        Execute a query and fetch a single result as a dictionary using the default connector.

        Parameters:
        -----------
            query: str
                The SQL query to execute.
            new_query: bool, optional
                If True, forces execution of the query even if cached. Default is False.
            parameters: tuple, optional
                Parameters to safely inject into the SQL query. Default is an empty tuple.

        Returns:
        --------
            dict
                A dictionary representing the single result row.
        """
        raise NotImplementedError

    def fetch_all(self, query: str, parameters: tuple = ()) -> list:
        """
        Execute a query and fetch all results as a list of dictionaries using the default connector.

        Parameters:
        -----------
            query: str
                The SQL query to execute.
            parameters: tuple, optional
                Parameters to safely inject into the SQL query. Default is an empty tuple.

        Returns:
        --------
            list
                A list of dictionaries representing the result rows.
        """
        raise NotImplementedError

    def get_connection(self):
        """
        Retrieve the raw database connection from the default connector.

        Parameters:
        -----------
            None

        Returns:
        --------
            Any
                The raw connection object of the default connector.
        """
        raise NotImplementedError

    def begin_transaction(self):
        """
        Begin a new transaction using the default connector.

        Parameters:
        -----------
            None

        Returns:
        --------
            None
                This function does not return a value.
        """
        raise NotImplementedError

    def commit(self):
        """
        Commit the current transaction using the default connector.

        Parameters:
        -----------
            None

        Returns:
        --------
            None
                This function does not return a value.
        """
        raise NotImplementedError

    def rollback(self):
        """
        Roll back the current transaction using the default connector.

        Parameters:
        -----------
            None

        Returns:
        --------
            None
                This function does not return a value.
        """
        raise NotImplementedError

    def is_connected(self) -> bool:
        """
        Check if the default connector is currently connected.

        Parameters:
        -----------
            None

        Returns:
        --------
            bool
                True if the default connector is connected, False otherwise.
        """
        raise NotImplementedError

    def check_if_table_exists(self, table_name: str) -> bool:
        """
        Check whether a specific table exists in the database using the default connector.

        Parameters:
        -----------
            table_name: str
                The name of the table to check for existence.

        Returns:
        --------
            bool
                True if the table exists, False otherwise.
        """
        raise NotImplementedError

    def replace_sql_statement(self, sql_statement: str) -> str:
        """
        Replace placeholders or variables in the SQL statement as needed before execution.

        Parameters:
        -----------
            sql_statement: str
                The raw SQL statement to process.

        Returns:
        --------
            str
                The processed SQL statement with replacements applied.
        """
        # Replace DDL-specific placeholders.
        primary_key_map = {
            "sqlite3": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "mysql": "SERIAL AUTO_INCREMENT PRIMARY KEY",
            "postgresql": "BIGSERIAL PRIMARY KEY",
        }
        return sql_statement.replace(
            "<PRIMARYKEY>", primary_key_map.get(self.db_type, "BIGSERIAL PRIMARY KEY")
        )


class SQLiteConnector(BaseDatabaseConnector):
    """
    SQLite-specific connector implementing the base interface.
    """

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.db_type = "sqlite3"

    def connect(self):
        mandatory_keys = ["database"]
        for key in mandatory_keys:
            if key not in self.parameters:
                raise ValueError(f"parameters must contain '{mandatory_keys}'.")
        self.connection = sqlite3.connect(self.parameters["database"])
        self.cursor = self.connection.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = self.connection = None

    def execute(self, query: str, parameters: tuple = ()):
        self.cursor.execute(self.replace_sql_statement(query), parameters)
        self.connection.commit()

    def fetch_one(self, query: str, new_query: bool = False, parameters: tuple = ()) -> dict:
        if new_query or (query != self.last_query_string):
            self.cursor.execute(query, parameters)
            self.last_query_string = query
        row = self.cursor.fetchone()
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row)) if row else None

    def fetch_all(self, query: str, parameters: tuple = ()) -> list:
        self.cursor.execute(query, parameters)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_connection(self):
        return self.connection

    def begin_transaction(self):
        self.connection.execute("BEGIN")

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def is_connected(self) -> bool:
        return self.connection is not None

    def check_if_table_exists(self, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone() is not None


class MySQLConnector(BaseDatabaseConnector):
    """
    MySQL-specific connector implementing the base interface.
    """

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.db_type = "mysql"

    def connect(self):
        mandatory_keys = ["user", "password", "host", "database"]
        for key in mandatory_keys:
            if key not in self.parameters:
                raise ValueError(f"parameters must contain '{mandatory_keys}'.")
        self.connection = mysql.connector.connect(
            user=self.parameters["user"],
            password=self.parameters["password"],
            host=self.parameters["host"],
            port=self.parameters.get("port", 3306),
            database=self.parameters["database"],
        )
        self.cursor = self.connection.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = self.connection = None

    def execute(self, query: str, parameters: tuple = ()):
        self.cursor.execute(self.replace_sql_statement(query), parameters)
        self.connection.commit()

    def fetch_one(self, query: str, new_query: bool = False, parameters: tuple = ()) -> dict:
        if new_query or (query != self.last_query_string):
            self.cursor.execute(query, parameters)
            self.last_query_string = query
        row = self.cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def fetch_all(self, query: str, parameters: tuple = ()) -> list:
        self.cursor.execute(query, parameters)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_connection(self):
        return self.connection

    def begin_transaction(self):
        self.connection.start_transaction()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def is_connected(self) -> bool:
        return self.connection.is_connected() if self.connection else False

    def check_if_table_exists(self, table_name: str) -> bool:
        query = "SHOW TABLES LIKE %s;"
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone() is not None


class PostgreSQLConnector(BaseDatabaseConnector):
    """
    PostgreSQL-specific connector implementing the base interface.
    """

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.db_type = "postgresql"
        self.engine = None

    def connect(self):
        mandatory_keys = ["user", "password", "host", "database"]
        for key in mandatory_keys:
            if key not in self.parameters:
                raise ValueError(f"parameters must contain '{mandatory_keys}'.")
        self.connection = psycopg2.connect(
            user=self.parameters["user"],
            password=self.parameters["password"],
            host=self.parameters["host"],
            port=self.parameters.get("port", 5432),
            database=self.parameters["database"],
        )
        self.cursor = self.connection.cursor()
        # Optional: Create SQLAlchemy engine
        connection_url = (
            f"postgresql+psycopg2://{self.parameters['user']}:"
            f"{self.parameters['password']}@"
            f"{self.parameters['host']}:{self.parameters.get('port', 5432)}/"
            f"{self.parameters['database']}"
        )
        self.engine = create_engine(connection_url)

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = self.connection = self.engine = None

    def execute(self, query: str, parameters: tuple = ()):
        self.cursor.execute(self.replace_sql_statement(query), parameters)
        self.connection.commit()

    def fetch_one(self, query: str, new_query: bool = False, parameters: tuple = ()) -> dict:
        if new_query or (query != self.last_query_string):
            self.cursor.execute(query, parameters)
            self.last_query_string = query
        row = self.cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def fetch_all(self, query: str, parameters: tuple = ()) -> list:
        self.cursor.execute(query, parameters)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_connection(self):
        return self.engine or self.connection

    def begin_transaction(self):
        self.connection.autocommit = False

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def is_connected(self) -> bool:
        return self.connection is not None and self.cursor is not None

    def check_if_table_exists(self, table_name: str) -> bool:
        query = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s);"
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone()[0]
