"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Central database type registry with metadata for unified DB management

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Any, Optional
import threading
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
SUPPORTED_DB_TYPES = {
    "postgres": {
        "connector_class": "PostgreSQLConnector",
        "connector_module": "basefunctions.database.connectors.postgres_connector",
        "system_db": "postgres",
        "supports_databases": True,
        "supports_schemas": True,
        "primary_key_syntax": "BIGSERIAL PRIMARY KEY",
        "default_port": 5432,
        "admin_port_offset": 1,
        "has_templates": True,
        "supports_docker_support": True,
        "connection_test_query": "SELECT 1",
        "table_exists_query": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
        "list_tables_query": "SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = current_schema()",
        "list_databases_query": "SELECT datname FROM pg_database WHERE datistemplate = false",
    },
    "mysql": {
        "connector_class": "MySQLConnector",
        "connector_module": "basefunctions.database.connectors.mysql_connector",
        "system_db": "mysql",
        "supports_databases": True,
        "supports_schemas": False,
        "primary_key_syntax": "SERIAL AUTO_INCREMENT PRIMARY KEY",
        "default_port": 3306,
        "admin_port_offset": 1,
        "has_templates": True,
        "supports_docker_support": True,
        "connection_test_query": "SELECT 1",
        "table_exists_query": "SHOW TABLES LIKE %s",
        "list_tables_query": "SHOW TABLES",
        "list_databases_query": "SHOW DATABASES",
    },
    "sqlite3": {
        "connector_class": "SQLiteConnector",
        "connector_module": "basefunctions.database.connectors.sqlite_connector",
        "system_db": None,
        "supports_databases": False,
        "supports_schemas": False,
        "primary_key_syntax": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "default_port": None,
        "admin_port_offset": 8080,
        "has_templates": True,
        "supports_docker_support": True,
        "connection_test_query": "SELECT 1",
        "table_exists_query": "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        "list_tables_query": "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        "list_databases_query": None,
    },
    "redis": {
        "connector_class": "RedisConnector",
        "connector_module": "basefunctions.database.connectors.redis_connector",
        "system_db": None,
        "supports_databases": False,
        "supports_schemas": False,
        "primary_key_syntax": None,
        "default_port": 6379,
        "admin_port_offset": 1,
        "has_templates": True,
        "supports_docker_support": True,
        "connection_test_query": "PING",
        "table_exists_query": None,
        "list_tables_query": None,
        "list_databases_query": None,
    },
}

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


@basefunctions.singleton
class DbRegistry:
    """
    Central registry for database type metadata and configuration.
    Implements singleton pattern for global access to DB type information.
    """

    def __init__(self) -> None:
        """
        Initialize database registry with supported types.
        """
        self._registry = SUPPORTED_DB_TYPES.copy()
        self._lock = threading.RLock()
        self.logger = basefunctions.get_logger(__name__)

    def validate_db_type(self, db_type: str) -> None:
        """
        Validate if database type is supported.

        parameters
        ----------
        db_type : str
            database type to validate

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")

        with self._lock:
            if db_type not in self._registry:
                supported = ", ".join(self.get_supported_types())
                raise basefunctions.DbValidationError(
                    f"unsupported database type: {db_type}. Supported types: {supported}"
                )

    def get_db_config(self, db_type: str) -> Dict[str, Any]:
        """
        Get complete configuration for database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        Dict[str, Any]
            database configuration dictionary

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        self.validate_db_type(db_type)

        with self._lock:
            return self._registry[db_type].copy()

    def get_supported_types(self) -> List[str]:
        """
        Get list of all supported database types.

        returns
        -------
        List[str]
            list of supported database type identifiers
        """
        with self._lock:
            return list(self._registry.keys())

    def get_connector_info(self, db_type: str) -> tuple[str, str]:
        """
        Get connector class name and module for database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        tuple[str, str]
            (connector_class_name, connector_module_path)

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        return config["connector_class"], config["connector_module"]

    def get_primary_key_syntax(self, db_type: str) -> Optional[str]:
        """
        Get primary key syntax for database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        Optional[str]
            primary key syntax or None if not applicable

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        return config.get("primary_key_syntax")

    def get_system_database(self, db_type: str) -> Optional[str]:
        """
        Get system database name for database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        Optional[str]
            system database name or None if not applicable

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        return config.get("system_db")

    def get_default_ports(self, db_type: str) -> tuple[Optional[int], Optional[int]]:
        """
        Get default database and admin ports for database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        tuple[Optional[int], Optional[int]]
            (database_port, admin_port) or (None, None) if not applicable

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        db_port = config.get("default_port")
        admin_port_offset = config.get("admin_port_offset", 1)

        if db_port is not None:
            admin_port = db_port + admin_port_offset
            return db_port, admin_port
        else:
            return None, None

    def supports_feature(self, db_type: str, feature: str) -> bool:
        """
        Check if database type supports specific feature.

        parameters
        ----------
        db_type : str
            database type
        feature : str
            feature to check (databases, schemas, docker_support, etc.)

        returns
        -------
        bool
            True if feature is supported, False otherwise

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        feature_key = f"supports_{feature}" if not feature.startswith("supports_") else feature
        return config.get(feature_key, False)

    def has_templates(self, db_type: str) -> bool:
        """
        Check if database type has Docker templates available.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        bool
            True if templates are available, False otherwise

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        return config.get("has_templates", False)

    def get_query_template(self, db_type: str, query_type: str) -> Optional[str]:
        """
        Get SQL query template for database type and operation.

        parameters
        ----------
        db_type : str
            database type
        query_type : str
            type of query (connection_test, table_exists, list_tables, list_databases)

        returns
        -------
        Optional[str]
            SQL query template or None if not available

        raises
        ------
        basefunctions.DbValidationError
            if database type is not supported
        """
        config = self.get_db_config(db_type)
        query_key = f"{query_type}_query"
        return config.get(query_key)

    def register_db_type(self, db_type: str, config: Dict[str, Any]) -> None:
        """
        Register new database type with configuration.

        parameters
        ----------
        db_type : str
            database type identifier
        config : Dict[str, Any]
            database configuration dictionary

        raises
        ------
        basefunctions.DbValidationError
            if configuration is invalid
        """
        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")

        if not isinstance(config, dict):
            raise basefunctions.DbValidationError("config must be a dictionary")

        required_keys = ["connector_class", "connector_module"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise basefunctions.DbValidationError(f"missing required config keys: {missing_keys}")

        with self._lock:
            self._registry[db_type] = config.copy()
            self.logger.info(f"registered new database type: {db_type}")

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics for debugging.

        returns
        -------
        Dict[str, Any]
            registry statistics
        """
        with self._lock:
            return {
                "supported_types_count": len(self._registry),
                "supported_types": list(self._registry.keys()),
                "docker_supported": [
                    db_type for db_type, config in self._registry.items() if config.get("docker_support", False)
                ],
                "template_available": [
                    db_type for db_type, config in self._registry.items() if config.get("has_templates", False)
                ],
            }


# -------------------------------------------------------------
# GLOBAL REGISTRY INSTANCE
# -------------------------------------------------------------
_registry_instance = None
_registry_lock = threading.Lock()


def get_registry() -> DbRegistry:
    """
    Get global database registry instance.

    returns
    -------
    DbRegistry
        singleton registry instance
    """
    global _registry_instance

    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = DbRegistry()

    return _registry_instance


# -------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------------------------------------


def validate_db_type(db_type: str) -> None:
    """
    Convenience function for database type validation.

    parameters
    ----------
    db_type : str
        database type to validate

    raises
    ------
    basefunctions.DbValidationError
        if database type is not supported
    """
    get_registry().validate_db_type(db_type)


def get_db_config(db_type: str) -> Dict[str, Any]:
    """
    Convenience function to get database configuration.

    parameters
    ----------
    db_type : str
        database type

    returns
    -------
    Dict[str, Any]
        database configuration dictionary

    raises
    ------
    basefunctions.DbValidationError
        if database type is not supported
    """
    return get_registry().get_db_config(db_type)


def get_supported_types() -> List[str]:
    """
    Convenience function to get supported database types.

    returns
    -------
    List[str]
        list of supported database type identifiers
    """
    return get_registry().get_supported_types()


def get_connector_info(db_type: str) -> tuple[str, str]:
    """
    Convenience function to get connector information.

    parameters
    ----------
    db_type : str
        database type

    returns
    -------
    tuple[str, str]
        (connector_class_name, connector_module_path)

    raises
    ------
    basefunctions.DbValidationError
        if database type is not supported
    """
    return get_registry().get_connector_info(db_type)
