"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Tests for DbInstance class

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch, call
import basefunctions
from basefunctions.database.db_instance import DbInstance
from basefunctions.database.exceptions import DbConnectionError

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


class TestDbInstance:
    """Test suite for the DbInstance class."""

    def test_init_minimal_config(self):
        """Test initialization with minimal config."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_secret_handler = MagicMock()

        # Create a minimal config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.SecretHandler", return_value=mock_secret_handler):
                # Create instance
                instance = DbInstance("test_instance", config)

                # Verify instance attributes
                assert instance.instance_name == "test_instance"
                assert instance.config == config
                assert instance.logger == mock_logger
                assert instance.databases == {}
                assert instance.connection is None
                assert instance.db_type == "sqlite3"
                assert instance.manager is None

    def test_init_missing_type(self):
        """Test initialization with missing type."""
        # Setup mock objects
        mock_logger = MagicMock()

        # Create a config with missing type
        config = {"connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Attempt to create instance should raise ValueError
            with pytest.raises(ValueError) as excinfo:
                DbInstance("test_instance", config)

            # Verify error message
            assert "database type not specified" in str(excinfo.value)

            # Verify logger was called
            mock_logger.critical.assert_called_once()
            assert "database type not specified" in mock_logger.critical.call_args[0][0]

    def test_process_credentials_no_secret(self):
        """Test process_credentials with no secrets to process."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_secret_handler = MagicMock()

        # Create config with no secrets
        config = {
            "type": "sqlite3",
            "connection": {
                "database": "test.db",
                "user": "test_user",
                "password": "direct_password",  # Not a secret reference
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.SecretHandler", return_value=mock_secret_handler):
                # Create instance
                instance = DbInstance("test_instance", config)

                # Verify password was not changed
                assert instance.config["connection"]["password"] == "direct_password"

                # Verify secret handler was not called to get secret
                mock_secret_handler.get_secret_value.assert_not_called()

    def test_process_credentials_with_secret(self):
        """Test process_credentials with a secret to process."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_secret_handler = MagicMock()
        mock_secret_handler.get_secret_value.return_value = "resolved_password"

        # Create config with a secret reference
        config = {
            "type": "sqlite3",
            "connection": {
                "database": "test.db",
                "user": "test_user",
                "password": "${DB_PASSWORD}",  # Secret reference
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.SecretHandler", return_value=mock_secret_handler):
                # Create instance
                instance = DbInstance("test_instance", config)

                # Verify secret was resolved
                assert instance.config["connection"]["password"] == "resolved_password"

                # Verify secret handler was called correctly
                mock_secret_handler.get_secret_value.assert_called_once_with("DB_PASSWORD")

    def test_process_credentials_secret_not_found(self):
        """Test process_credentials with a secret that doesn't exist."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_secret_handler = MagicMock()
        mock_secret_handler.get_secret_value.return_value = None  # Secret not found

        # Create config with a secret reference
        config = {
            "type": "sqlite3",
            "connection": {
                "database": "test.db",
                "user": "test_user",
                "password": "${MISSING_SECRET}",  # Secret reference that doesn't exist
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.SecretHandler", return_value=mock_secret_handler):
                # Create instance
                instance = DbInstance("test_instance", config)

                # Verify password still contains the reference
                assert instance.config["connection"]["password"] == "${MISSING_SECRET}"

                # Verify logger warning was called
                mock_logger.warning.assert_called_once()
                assert "secret 'MISSING_SECRET' not found" in mock_logger.warning.call_args[0][0]

    def test_connect_success(self):
        """Test successful connection to database."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_connector.return_value = mock_connector

        # Create config
        config = {
            "type": "mysql",
            "connection": {
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
                "host": "localhost",
            },
            "ports": {"db": 3306},
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.DbFactory") as mock_factory_class:
                mock_factory_class.create_connector.return_value = mock_connector

                # Create instance
                instance = DbInstance("test_instance", config)

                # Call connect
                instance.connect()

                # Verify connector was created with correct parameters
                expected_params = {
                    "host": "localhost",
                    "port": 3306,
                    "user": "test_user",
                    "password": "test_pass",
                    "database": "test_db",  # Korrigiert von "test_instance" zu "test_db"
                }
                mock_factory_class.create_connector.assert_called_once_with(
                    "mysql", expected_params
                )

                # Verify connector's connect method was called
                mock_connector.connect.assert_called_once()

                # Verify logger was called
                mock_logger.warning.assert_called_with(
                    "connected to instance 'test_instance' (mysql)"
                )

    def test_connect_already_connected(self):
        """Test connect when already connected."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()
        mock_connector.is_connected.return_value = True

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.DbFactory") as mock_factory_class:
                # Create instance and set connection
                instance = DbInstance("test_instance", config)
                instance.connection = mock_connector

                # Call connect
                instance.connect()

                # Verify factory was not called (no new connection created)
                mock_factory_class.create_connector.assert_not_called()

                # Verify logger debug was called
                mock_logger.debug.assert_called_with(
                    "already connected to instance 'test_instance'"
                )

    def test_connect_failure(self):
        """Test connection failure."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_connector.side_effect = Exception("Connection error")

        # Create config
        config = {
            "type": "mysql",
            "connection": {
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
                "host": "localhost",
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.DbFactory") as mock_factory_class:
                mock_factory_class.create_connector.side_effect = Exception("Connection error")

                # Create instance
                instance = DbInstance("test_instance", config)

                # Call connect should raise DbConnectionError
                with pytest.raises(DbConnectionError) as excinfo:
                    instance.connect()

                # Verify error message
                assert "failed to connect to instance" in str(excinfo.value)
                assert "Connection error" in str(excinfo.value)

                # Verify logger critical was called
                mock_logger.critical.assert_called_with(
                    "failed to connect to instance 'test_instance': Connection error"
                )

    def test_close(self):
        """Test closing database connection."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()
        mock_db = MagicMock()

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance and setup databases and connection
            instance = DbInstance("test_instance", config)
            instance.connection = mock_connector
            instance.databases = {"db1": mock_db, "db2": mock_db}

            # Call close
            instance.close()

            # Verify all databases were closed
            assert mock_db.close.call_count == 2

            # Verify connection was closed
            mock_connector.close.assert_called_once()

            # Verify databases were cleared
            assert instance.databases == {}

            # Verify connection was set to None
            assert instance.connection is None

            # Verify logger was called
            mock_logger.warning.assert_called_with("closed connection to instance 'test_instance'")

    def test_get_database_exists(self):
        """Test getting an existing database."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_db = MagicMock()

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance and setup database
            instance = DbInstance("test_instance", config)
            instance.databases = {"test_db": mock_db}

            # Mock is_connected and connect
            instance.is_connected = MagicMock(return_value=True)
            instance.connect = MagicMock()  # Mocken der connect-Methode

            # Get database
            db = instance.get_database("test_db")

            # Verify correct database was returned
            assert db is mock_db

            # Verify is_connected was called
            instance.is_connected.assert_called_once()

            # Verify connect was not called
            instance.connect.assert_not_called()  # Verwenden der assert_not_called Methode

    def test_get_database_new(self):
        """Test getting a new database."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_db_class = MagicMock()
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.Db", mock_db_class):
                # Create instance
                instance = DbInstance("test_instance", config)

                # Mock is_connected and connect
                instance.is_connected = MagicMock(return_value=True)
                instance.connect = MagicMock()

                # Get database
                db = instance.get_database("new_db")

                # Verify is_connected was called
                instance.is_connected.assert_called_once()

                # Verify connect was not called (already connected)
                instance.connect.assert_not_called()

                # Verify Db constructor was called
                mock_db_class.assert_called_once_with(instance, "new_db")

                # Verify database was added to databases dict
                assert instance.databases["new_db"] is mock_db

                # Verify correct database was returned
                assert db is mock_db

    def test_get_database_not_connected(self):
        """Test getting database when not connected."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_db_class = MagicMock()
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.Db", mock_db_class):
                # Create instance
                instance = DbInstance("test_instance", config)

                # Mock is_connected to return False and connect
                instance.is_connected = MagicMock(return_value=False)
                instance.connect = MagicMock()

                # Get database
                db = instance.get_database("new_db")

                # Verify is_connected was called
                instance.is_connected.assert_called_once()

                # Verify connect was called
                instance.connect.assert_called_once()

                # Verify Db constructor was called
                mock_db_class.assert_called_once_with(instance, "new_db")

                # Verify database was added to databases dict
                assert instance.databases["new_db"] is mock_db

                # Verify correct database was returned
                assert db is mock_db

    def test_list_databases(self):
        """Test listing available databases."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()
        mock_connector.fetch_all.return_value = [{"Database": "db1"}, {"Database": "db2"}]

        # Create config
        config = {
            "type": "mysql",  # Using MySQL for this test
            "connection": {
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
                "host": "localhost",
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)

            # Setup connection
            instance.connection = mock_connector

            # Mock is_connected to return True
            instance.is_connected = MagicMock(return_value=True)
            instance.connect = MagicMock()

            # List databases
            dbs = instance.list_databases()

            # Verify is_connected was called
            instance.is_connected.assert_called_once()

            # Verify connect was not called
            instance.connect.assert_not_called()

            # Verify fetch_all was called with correct query for MySQL
            mock_connector.fetch_all.assert_called_once_with("SHOW DATABASES")

            # Verify correct databases were returned
            assert dbs == ["db1", "db2"]

    def test_create_database_mysql(self):
        """Test creating a database with MySQL."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()

        # Create config
        config = {
            "type": "mysql",
            "connection": {
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
                "host": "localhost",
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)

            # Setup connection
            instance.connection = mock_connector

            # Mock is_connected to return True
            instance.is_connected = MagicMock(return_value=True)
            instance.connect = MagicMock()

            # Create database
            result = instance.create_database("new_db")

            # Verify is_connected was called
            instance.is_connected.assert_called_once()

            # Verify connect was not called
            instance.connect.assert_not_called()

            # Verify execute was called with correct SQL
            mock_connector.execute.assert_called_once_with("CREATE DATABASE `new_db`")

            # Verify result is True
            assert result is True

            # Verify logger was called
            mock_logger.warning.assert_called_with("created database 'new_db'")

    def test_create_database_sqlite(self):
        """Test creating a database with SQLite (not supported)."""
        # Setup mock objects
        mock_logger = MagicMock()

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)
            instance.db_type = "sqlite3"

            # Mock is_connected to return True
            instance.is_connected = MagicMock(return_value=True)

            # Create database (should fail for SQLite)
            result = instance.create_database("new_db")

            # Verify logger warning was called
            mock_logger.warning.assert_called_with("SQLite does not support CREATE DATABASE")

            # Verify result is False
            assert result is False

    def test_drop_database_postgres(self):
        """Test dropping a database with PostgreSQL."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()
        mock_db = MagicMock()

        # Create config
        config = {
            "type": "postgres",
            "connection": {
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
                "host": "localhost",
            },
        }

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)
            instance.db_type = "postgres"

            # Setup connection and database
            instance.connection = mock_connector
            instance.databases = {"db_to_drop": mock_db}

            # Mock is_connected to return True
            instance.is_connected = MagicMock(return_value=True)

            # Drop database
            result = instance.drop_database("db_to_drop")

            # Verify database was closed
            mock_db.close.assert_called_once()

            # Verify database was removed from databases dict
            assert "db_to_drop" not in instance.databases

            # Verify execute was called with correct SQL
            mock_connector.execute.assert_called_once_with('DROP DATABASE "db_to_drop"')

            # Verify result is True
            assert result is True

            # Verify logger was called
            mock_logger.warning.assert_called_with("dropped database 'db_to_drop'")

    def test_is_connected(self):
        """Test checking connection status."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)

            # Case 1: No connection
            assert instance.is_connected() is False

            # Case 2: Connection exists but is_connected not implemented or returns non-boolean
            mock_without_is_connected = MagicMock()
            # Entfernen oder überschreiben des standardmäßigen is_connected-Verhaltens
            delattr(mock_without_is_connected, "is_connected")

            instance.connection = mock_without_is_connected
            assert instance.is_connected() is False

            # Case 3: Connection exists with is_connected that returns False
            mock_connector_false = MagicMock()
            mock_connector_false.is_connected.return_value = False
            instance.connection = mock_connector_false
            assert instance.is_connected() is False

            # Case 4: Connection exists and is connected
            mock_connector_true = MagicMock()
            mock_connector_true.is_connected.return_value = True
            instance.connection = mock_connector_true
            assert instance.is_connected() is True
            mock_connector_true.is_connected.assert_called_once()

    def test_get_type(self):
        """Test getting database type."""
        # Setup mock objects
        mock_logger = MagicMock()

        # Create config
        config = {"type": "mysql", "connection": {"database": "test_db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)
            instance.db_type = "mysql"

            # Get type
            db_type = instance.get_type()

            # Verify type is correct
            assert db_type == "mysql"

    def test_get_connection(self):
        """Test getting database connection."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_connector = MagicMock()

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)
            instance.connection = mock_connector

            # Get connection
            connection = instance.get_connection()

            # Verify connection is correct
            assert connection is mock_connector

    def test_manager_methods(self):
        """Test manager getter and setter."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_manager = MagicMock()

        # Create config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            # Create instance
            instance = DbInstance("test_instance", config)

            # Initially manager should be None
            assert instance.get_manager() is None

            # Set manager
            instance.set_manager(mock_manager)

            # Verify manager was set
            assert instance.get_manager() is mock_manager
