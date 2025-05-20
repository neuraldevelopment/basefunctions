"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Data models for database configuration and parameters
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Union, TypedDict

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


class DatabaseParameters(TypedDict, total=False):
    """
    Type definition for database connection parameters.
    Used for all database connector types.
    """

    database: str
    user: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[int]
    min_connections: Optional[int]
    max_connections: Optional[int]
    ssl_ca: Optional[str]
    ssl_cert: Optional[str]
    ssl_key: Optional[str]
    ssl_verify: Optional[bool]
    connection_timeout: Optional[int]
    command_timeout: Optional[int]
    charset: Optional[str]
    timezone: Optional[str]


class ConnectionConfig(TypedDict, total=False):
    """
    Type definition for the connection section in a database configuration.
    """

    database: str
    user: str
    password: str
    host: str
    encrypt: bool
    charset: str
    use_ssl: bool


class PortsConfig(TypedDict, total=False):
    """
    Type definition for the ports section in a database configuration.
    """

    db: int
    admin: Optional[int]


class PoolConfig(TypedDict, total=False):
    """
    Type definition for the connection pool section in a database configuration.
    """

    min_connections: int
    max_connections: int
    connection_timeout: int
    idle_timeout: int


class DbConfig(TypedDict):
    """
    Type definition for a complete database configuration.
    Represents the structure of a database instance config.
    """

    type: str
    connection: ConnectionConfig
    ports: PortsConfig
    pool: Optional[PoolConfig]
    options: Optional[Dict[str, Any]]


def validate_config(config: DbConfig) -> bool:
    """
    Validate a database configuration for required fields.

    parameters
    ----------
    config : DbConfig
        configuration to validate

    returns
    -------
    bool
        True if configuration is valid, False otherwise

    raises
    ------
    ValueError
        if configuration is missing required fields
    """
    # Check required top-level fields
    if "type" not in config:
        raise ValueError("missing required field 'type' in database configuration")

    if "connection" not in config:
        raise ValueError("missing required field 'connection' in database configuration")

    # Check required connection fields based on database type
    connection = config["connection"]
    db_type = config["type"]

    # Common required fields for all database types
    required_fields = ["database"]

    # Additional fields required for MySQL and PostgreSQL
    if db_type in ["mysql", "postgres"]:
        required_fields.extend(["user", "host"])

    # Validate required connection fields
    missing_fields = [field for field in required_fields if field not in connection]
    if missing_fields:
        raise ValueError(f"missing required connection fields: {', '.join(missing_fields)}")

    return True


def config_to_parameters(config: DbConfig) -> DatabaseParameters:
    """
    Convert a database configuration to connection parameters.

    parameters
    ----------
    config : DbConfig
        database configuration

    returns
    -------
    DatabaseParameters
        connection parameters for a connector
    """
    parameters: DatabaseParameters = {"database": config["connection"]["database"]}

    # Copy common fields
    for field in ["user", "password", "host", "charset"]:
        if field in config["connection"]:
            parameters[field] = config["connection"][field]

    # Add port if available
    if "ports" in config and "db" in config["ports"]:
        parameters["port"] = config["ports"]["db"]

    # Add pool configuration if available
    if "pool" in config:
        pool = config["pool"]
        if "min_connections" in pool:
            parameters["min_connections"] = pool["min_connections"]
        if "max_connections" in pool:
            parameters["max_connections"] = pool["max_connections"]

    return parameters
