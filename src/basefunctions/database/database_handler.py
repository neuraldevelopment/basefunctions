"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : backtraderfunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  A simple database abstraction layer for SQLite, MySQL, and PostgreSQL

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sqlite3
from typing import Optional, Any, List, Dict
import mysql.connector
import psycopg2
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
# CLASS DEFINITIONS
# -------------------------------------------------------------
class BaseDatabaseHandler:
    """
    Central database interface for managing multiple database connectors.
    """

    def __init__(self):
        self.connectors: Dict[str, BaseDatabaseConnector] = {}

    def register_connector(
        self, connector_id: str, db_type: str, parameters: dict
    ) -> "BaseDatabaseConnector":
        connector_map = {
            "sqlite3": SQLiteConnector,
            "mysql": MySQLConnector,
            "postgresql": PostgreSQLConnector,
        }
        db_type = db_type.lower()
        if db_type not in connector_map:
            raise ValueError(f"Unsupported db_type '{db_type}'")
        self.connectors[connector_id] = connector_map[db_type](parameters)
        basefunctions.get_logger(__name__).info(
            f"Registered DB connector '{connector_id}' ({db_type})"
        )
        return self.connectors[connector_id]

    def get_connector(self, connector_id: str) -> "BaseDatabaseConnector":
        if connector_id not in self.connectors:
            raise KeyError(f"Connector '{connector_id}' not registered.")
        return self.connectors[connector_id]

    def connect(self, connector_id: str):
        self.get_connector(connector_id).connect()

    def close(self, connector_id: str):
        self.get_connector(connector_id).close()

    def close_all(self):
        for connector in self.connectors.values():
            connector.close()

    def execute(self, connector_id: str, query: str, parameters: tuple = ()):
        self.get_connector(connector_id).execute(query, parameters)

    def fetch_one(
        self, connector_id: str, query: str, parameters: tuple = (), new_query: bool = False
    ) -> Optional[Dict[str, Any]]:
        return self.get_connector(connector_id).fetch_one(query, new_query, parameters)

    def fetch_all(
        self, connector_id: str, query: str, parameters: tuple = ()
    ) -> List[Dict[str, Any]]:
        return self.get_connector(connector_id).fetch_all(query, parameters)

    def begin_transaction(self, connector_id: str):
        self.get_connector(connector_id).begin_transaction()

    def commit(self, connector_id: str):
        self.get_connector(connector_id).commit()

    def rollback(self, connector_id: str):
        self.get_connector(connector_id).rollback()

    def is_connected(self, connector_id: str) -> bool:
        return self.get_connector(connector_id).is_connected()

    def check_if_table_exists(self, connector_id: str, table_name: str) -> bool:
        return self.get_connector(connector_id).check_if_table_exists(table_name)

    def get_connection(self, connector_id: str) -> Any:
        return self.get_connector(connector_id).get_connection()


class BaseDatabaseConnector:
    """
    Abstract base class for database connectors.
    """

    def __init__(self, parameters: dict):
        self.parameters = parameters
        self.connection: Optional[Any] = None
        self.cursor: Optional[Any] = None
        self.last_query_string: Optional[str] = None
        self.db_type: Optional[str] = None

    def connect(self):
        raise NotImplementedError

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
        except Exception:
            pass
        try:
            if self.connection:
                self.connection.close()
        except Exception:
            pass
        self.cursor = self.connection = None
        basefunctions.get_logger(__name__).info(f"Connection closed ({self.db_type})")

    def execute(self, query: str, parameters: tuple = ()):
        raise NotImplementedError

    def fetch_one(
        self, query: str, new_query: bool = False, parameters: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def fetch_all(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_connection(self) -> Any:
        raise NotImplementedError

    def begin_transaction(self):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def rollback(self):
        raise NotImplementedError

    def is_connected(self) -> bool:
        raise NotImplementedError

    def check_if_table_exists(self, table_name: str) -> bool:
        raise NotImplementedError

    def replace_sql_statement(self, sql_statement: str) -> str:
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
        self.in_transaction = False

    def connect(self):
        if "database" not in self.parameters:
            raise ValueError("parameters must contain 'database'.")
        self.connection = sqlite3.connect(self.parameters["database"], isolation_level=None)
        self.cursor = self.connection.cursor()
        basefunctions.get_logger(__name__).info(
            "Connected to sqlite3 database at %s", self.parameters["database"]
        )

    def execute(self, query: str, parameters: tuple = ()):
        self.cursor.execute(self.replace_sql_statement(query), parameters)
        if not self.in_transaction:
            self.connection.commit()

    def fetch_one(
        self, query: str, new_query: bool = False, parameters: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        self.cursor.execute(query, parameters)
        self.last_query_string = query
        row = self.cursor.fetchone()
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row)) if row else None

    def fetch_all(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        self.cursor.execute(query, parameters)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_connection(self) -> Any:
        return self.connection

    def begin_transaction(self):
        self.connection.execute("BEGIN")
        self.in_transaction = True

    def commit(self):
        self.connection.commit()
        self.in_transaction = False

    def rollback(self):
        self.connection.rollback()
        self.in_transaction = False

    def is_connected(self) -> bool:
        return self.connection is not None

    def check_if_table_exists(self, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone() is not None


class MySQLConnector(BaseDatabaseConnector):
    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.db_type = "mysql"

    def connect(self):
        mandatory_keys = ["user", "password", "host", "database"]
        for key in mandatory_keys:
            if key not in self.parameters:
                raise ValueError(f"parameters must contain '{key}'.")
        self.connection = mysql.connector.connect(
            user=self.parameters["user"],
            password=self.parameters["password"],
            host=self.parameters["host"],
            port=self.parameters.get("port", 3306),
            database=self.parameters["database"],
        )
        self.cursor = self.connection.cursor()
        basefunctions.get_logger(__name__).info(
            "Connected to mysql database '%s' at %s:%s",
            self.parameters["database"],
            self.parameters["host"],
            self.parameters.get("port", 3306),
        )

    def execute(self, query: str, parameters: tuple = ()):
        self.cursor.execute(self.replace_sql_statement(query), parameters)
        self.connection.commit()

    def fetch_one(
        self, query: str, new_query: bool = False, parameters: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        self.cursor.execute(query, parameters)
        self.last_query_string = query
        row = self.cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def fetch_all(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        self.cursor.execute(query, parameters)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_connection(self) -> Any:
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
    def __init__(self, parameters: dict):
        super().__init__(parameters)
        self.db_type = "postgresql"
        self.engine: Optional[Any] = None

    def connect(self):
        mandatory_keys = ["user", "password", "host", "database"]
        for key in mandatory_keys:
            if key not in self.parameters:
                raise ValueError(f"parameters must contain '{key}'.")
        self.connection = psycopg2.connect(
            user=self.parameters["user"],
            password=self.parameters["password"],
            host=self.parameters["host"],
            port=self.parameters.get("port", 5432),
            database=self.parameters["database"],
        )
        self.cursor = self.connection.cursor()
        connection_url = (
            f"postgresql+psycopg2://{self.parameters['user']}:"
            f"{self.parameters['password']}@{self.parameters['host']}:"
            f"{self.parameters.get('port', 5432)}/{self.parameters['database']}"
        )
        self.engine = create_engine(connection_url)
        basefunctions.get_logger(__name__).info(
            "Connected to postgresql database '%s' at %s:%s",
            self.parameters["database"],
            self.parameters["host"],
            self.parameters.get("port", 5432),
        )

    def execute(self, query: str, parameters: tuple = ()):
        self.cursor.execute(self.replace_sql_statement(query), parameters)
        self.connection.commit()

    def fetch_one(
        self, query: str, new_query: bool = False, parameters: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        self.cursor.execute(query, parameters)
        self.last_query_string = query
        row = self.cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def fetch_all(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        self.cursor.execute(query, parameters)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_connection(self) -> Any:
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
