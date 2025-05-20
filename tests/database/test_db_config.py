"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for DbConfig TypedDict and related functions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import basefunctions
from basefunctions.database.db_models import DbConfig, validate_config, config_to_parameters

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


class TestDbConfig:
    """Test suite for the DbConfig TypedDict and related functions."""

    def test_valid_minimal_config(self):
        """Test a minimal valid configuration."""
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # This should not raise an exception
        assert validate_config(config) is True

    def test_valid_mysql_config(self):
        """Test a valid MySQL configuration."""
        config = {
            "type": "mysql",
            "connection": {
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
                "host": "localhost",
                "charset": "utf8mb4",
            },
            "ports": {"db": 3306, "admin": 8080},
            "pool": {
                "min_connections": 1,
                "max_connections": 10,
                "connection_timeout": 30,
                "idle_timeout": 300,
            },
            "options": {"compress": True, "autocommit": True},
        }

        # This should not raise an exception
        assert validate_config(config) is True

        # Test converting to parameters
        params = config_to_parameters(config)
        assert params["database"] == "testdb"
        assert params["user"] == "testuser"
        assert params["password"] == "testpass"
        assert params["host"] == "localhost"
        assert params["charset"] == "utf8mb4"
        assert params["port"] == 3306
        assert params["min_connections"] == 1
        assert params["max_connections"] == 10

    def test_valid_postgres_config(self):
        """Test a valid PostgreSQL configuration."""
        config = {
            "type": "postgres",
            "connection": {
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
                "host": "localhost",
            },
            "ports": {"db": 5432},
        }

        # This should not raise an exception
        assert validate_config(config) is True

    def test_missing_type(self):
        """Test configuration with missing type."""
        config = {"connection": {"database": "test.db"}}

        with pytest.raises(ValueError) as excinfo:
            validate_config(config)

        assert "missing required field 'type'" in str(excinfo.value)

    def test_missing_connection(self):
        """Test configuration with missing connection section."""
        config = {"type": "sqlite3"}

        with pytest.raises(ValueError) as excinfo:
            validate_config(config)

        assert "missing required field 'connection'" in str(excinfo.value)

    def test_missing_database(self):
        """Test configuration with missing database in connection."""
        config = {"type": "sqlite3", "connection": {}}

        with pytest.raises(ValueError) as excinfo:
            validate_config(config)

        assert "missing required connection fields: database" in str(excinfo.value)

    def test_mysql_missing_required_fields(self):
        """Test MySQL configuration with missing required fields."""
        config = {
            "type": "mysql",
            "connection": {
                "database": "testdb"
                # Missing user and host
            },
        }

        with pytest.raises(ValueError) as excinfo:
            validate_config(config)

        # Both user and host are required for MySQL
        assert "missing required connection fields" in str(excinfo.value)
        assert "user" in str(excinfo.value)
        assert "host" in str(excinfo.value)

    def test_postgres_missing_required_fields(self):
        """Test PostgreSQL configuration with missing required fields."""
        config = {
            "type": "postgres",
            "connection": {
                "database": "testdb"
                # Missing user and host
            },
        }

        with pytest.raises(ValueError) as excinfo:
            validate_config(config)

        # Both user and host are required for PostgreSQL
        assert "missing required connection fields" in str(excinfo.value)
        assert "user" in str(excinfo.value)
        assert "host" in str(excinfo.value)

    def test_config_to_parameters_minimal(self):
        """Test conversion of minimal config to parameters."""
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        params = config_to_parameters(config)

        assert params["database"] == "test.db"
        assert "user" not in params
        assert "password" not in params
        assert "host" not in params
        assert "port" not in params

    def test_config_to_parameters_with_pool(self):
        """Test conversion of config with pool settings to parameters."""
        config = {
            "type": "postgres",
            "connection": {
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
                "host": "localhost",
            },
            "ports": {"db": 5432},
            "pool": {"min_connections": 2, "max_connections": 20},
        }

        params = config_to_parameters(config)

        assert params["database"] == "testdb"
        assert params["user"] == "testuser"
        assert params["password"] == "testpass"
        assert params["host"] == "localhost"
        assert params["port"] == 5432
        assert params["min_connections"] == 2
        assert params["max_connections"] == 20
