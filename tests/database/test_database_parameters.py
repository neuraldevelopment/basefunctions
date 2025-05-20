"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Tests for DatabaseParameters typed dictionary
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import typing
from typing import TypedDict, Optional
import basefunctions
from basefunctions.database.db_models import DatabaseParameters

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


class TestDatabaseParameters:
    """Test suite for the DatabaseParameters TypedDict."""

    def test_instance_minimal(self):
        """Test creating a minimal DatabaseParameters instance."""
        params: DatabaseParameters = {"database": "test_db"}
        assert isinstance(params, dict)
        assert params["database"] == "test_db"

    def test_instance_complete(self):
        """Test creating a complete DatabaseParameters instance with all fields."""
        params: DatabaseParameters = {
            "database": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "localhost",
            "port": 5432,
            "min_connections": 1,
            "max_connections": 10,
            "ssl_ca": "/path/to/ca.pem",
            "ssl_cert": "/path/to/cert.pem",
            "ssl_key": "/path/to/key.pem",
            "ssl_verify": True,
            "connection_timeout": 30,
            "command_timeout": 60,
            "charset": "utf8mb4",
            "timezone": "UTC",
        }

        assert params["database"] == "test_db"
        assert params["user"] == "test_user"
        assert params["password"] == "test_password"
        assert params["host"] == "localhost"
        assert params["port"] == 5432
        assert params["min_connections"] == 1
        assert params["max_connections"] == 10
        assert params["ssl_ca"] == "/path/to/ca.pem"
        assert params["ssl_cert"] == "/path/to/cert.pem"
        assert params["ssl_key"] == "/path/to/key.pem"
        assert params["ssl_verify"] is True
        assert params["connection_timeout"] == 30
        assert params["command_timeout"] == 60
        assert params["charset"] == "utf8mb4"
        assert params["timezone"] == "UTC"

    def test_type_safety(self):
        """Test that TypedDict provides some type safety at runtime."""
        # This will fail type checking but should work at runtime
        params: DatabaseParameters = {"database": "test_db", "port": "not_an_int"}
        assert params["port"] == "not_an_int"  # Runtime allows incorrect types

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        params: DatabaseParameters = {"database": "test_db"}
        assert "user" not in params
        assert "password" not in params

        # Add optional fields later
        params["user"] = "added_user"
        params["password"] = "added_password"
        assert params["user"] == "added_user"
        assert params["password"] == "added_password"

    def test_required_field(self):
        """Test handling of the required 'database' field."""
        # Not setting 'database' would fail mypy type check
        # but we can test behavior at runtime
        params = {}  # type: ignore

        # Check that we can add the required field later
        params["database"] = "added_db"
        valid_params: DatabaseParameters = params  # type: ignore
        assert valid_params["database"] == "added_db"

    def test_conversion_to_connector_parameters(self):
        """Test using DatabaseParameters with config_to_parameters function."""
        from basefunctions.database.db_models import config_to_parameters, DbConfig

        # Create a minimal DbConfig
        config: DbConfig = {
            "type": "postgres",
            "connection": {
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
                "host": "localhost",
                "charset": "utf8",
            },
            "ports": {"db": 5432},
        }

        # Convert to DatabaseParameters
        params = config_to_parameters(config)

        # Check conversion results
        assert isinstance(params, dict)
        assert params["database"] == "test_db"
        assert params["user"] == "test_user"
        assert params["password"] == "test_pass"
        assert params["host"] == "localhost"
        assert params["port"] == 5432
        assert params["charset"] == "utf8"
