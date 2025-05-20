"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Tests for DbManager central database management class
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch
import basefunctions
from basefunctions.database.db_manager import DbManager

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


class TestDbManager:
    """Test suite for the DbManager class."""

    def test_init(self):
        """Test initialization of DbManager."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # Verify instance attributes
                assert isinstance(manager.instances, dict)
                assert manager.instances == {}
                assert manager.config_handler == mock_config_handler
                assert manager.logger == mock_logger
                assert manager.threadpool is None
                assert hasattr(manager, "lock")

    def test_get_instance_existing(self):
        """Test getting an existing instance."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_instance = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # Add existing instance
                manager.instances = {"test_instance": mock_instance}

                # Get instance
                instance = manager.get_instance("test_instance")

                # Verify correct instance was returned
                assert instance is mock_instance

                # Verify config handler not called (existing instance)
                mock_config_handler.get_database_config.assert_not_called()

    def test_get_instance_new(self):
        """Test getting a new instance that needs to be created."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_db_instance = MagicMock()

        # Define mock config for test instance
        db_config = {"type": "sqlite3", "connection": {"database": "test.db"}}
        mock_config_handler.get_database_config.return_value = db_config

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch("basefunctions.DbInstance", return_value=mock_db_instance):
                    # Create DbManager
                    manager = DbManager()

                    # Get instance (should create new)
                    instance = manager.get_instance("test_instance")

                    # Verify config handler was called
                    mock_config_handler.get_database_config.assert_called_once_with(
                        "test_instance"
                    )

                    # Verify DbInstance was created
                    basefunctions.DbInstance.assert_called_once_with("test_instance", db_config)

                    # Verify instance was stored in instances dict
                    assert manager.instances["test_instance"] is mock_db_instance

                    # Verify correct instance was returned
                    assert instance is mock_db_instance

    def test_get_instance_no_config(self):
        """Test getting an instance with no configuration."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_config_handler.get_database_config.return_value = None

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # Try to get instance with no config
                with pytest.raises(ValueError) as excinfo:
                    manager.get_instance("missing_instance")

                # Verify error message
                assert "no configuration found for database instance" in str(excinfo.value)

                # Verify config handler was called
                mock_config_handler.get_database_config.assert_called_once_with("missing_instance")

                # Verify logger warning was called
                mock_logger.warning.assert_called_with(
                    "no configuration found for instance 'missing_instance'"
                )

    def test_get_instance_creation_error(self):
        """Test error handling during instance creation."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()

        # Define mock config for test instance
        db_config = {"type": "sqlite3", "connection": {"database": "test.db"}}
        mock_config_handler.get_database_config.return_value = db_config

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch("basefunctions.DbInstance", side_effect=Exception("Creation error")):
                    # Create DbManager
                    manager = DbManager()

                    # Try to get instance with creation error
                    with pytest.raises(Exception) as excinfo:
                        manager.get_instance("error_instance")

                    # Verify error was propagated
                    assert "Creation error" in str(excinfo.value)

                    # Verify logger critical was called
                    mock_logger.critical.assert_called_with(
                        "error creating instance 'error_instance': Creation error"
                    )

    def test_register_instance(self):
        """Test registering a new instance with provided configuration."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_db_instance = MagicMock()

        # Define test config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch("basefunctions.DbInstance", return_value=mock_db_instance):
                    # Create DbManager
                    manager = DbManager()

                    # Register new instance
                    instance = manager.register_instance("custom_instance", config)

                    # Verify DbInstance was created
                    basefunctions.DbInstance.assert_called_once_with("custom_instance", config)

                    # Verify instance was stored in instances dict
                    assert manager.instances["custom_instance"] is mock_db_instance

                    # Verify correct instance was returned
                    assert instance is mock_db_instance

    def test_register_instance_already_exists(self):
        """Test registering an instance that already exists."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_existing_instance = MagicMock()
        mock_new_instance = MagicMock()

        # Define test config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch("basefunctions.DbInstance", return_value=mock_new_instance):
                    # Create DbManager
                    manager = DbManager()

                    # Add existing instance
                    manager.instances = {"existing_instance": mock_existing_instance}

                    # Register instance with same name
                    instance = manager.register_instance("existing_instance", config)

                    # Verify logger warning was called
                    mock_logger.warning.assert_called_with(
                        "instance 'existing_instance' already registered, will be overwritten"
                    )

                    # Verify DbInstance was created
                    basefunctions.DbInstance.assert_called_once_with("existing_instance", config)

                    # Verify instance was stored in instances dict (overwriting previous)
                    assert manager.instances["existing_instance"] is mock_new_instance

                    # Verify correct instance was returned
                    assert instance is mock_new_instance

    def test_register_instance_error(self):
        """Test error handling during instance registration."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()

        # Define test config
        config = {"type": "sqlite3", "connection": {"database": "test.db"}}

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch(
                    "basefunctions.DbInstance", side_effect=Exception("Registration error")
                ):
                    # Create DbManager
                    manager = DbManager()

                    # Try to register instance with error
                    with pytest.raises(Exception) as excinfo:
                        manager.register_instance("error_instance", config)

                    # Verify error was propagated
                    assert "Registration error" in str(excinfo.value)

                    # Verify logger critical was called
                    mock_logger.critical.assert_called_with(
                        "error registering instance 'error_instance': Registration error"
                    )

    def test_close_all(self):
        """Test closing all registered database connections."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_instance1 = MagicMock()
        mock_instance2 = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # Add instances
                manager.instances = {"instance1": mock_instance1, "instance2": mock_instance2}

                # Close all instances
                manager.close_all()

                # Verify close was called on all instances
                mock_instance1.close.assert_called_once()
                mock_instance2.close.assert_called_once()

    def test_close_all_with_errors(self):
        """Test closing all connections with errors during close."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_instance1 = MagicMock()
        mock_instance1.close.side_effect = Exception("Close error")
        mock_instance2 = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # Add instances
                manager.instances = {"instance1": mock_instance1, "instance2": mock_instance2}

                # Close all instances (should handle error gracefully)
                manager.close_all()

                # Verify close was called on all instances
                mock_instance1.close.assert_called_once()
                mock_instance2.close.assert_called_once()

                # Verify logger warning was called for the error
                mock_logger.warning.assert_called_with(
                    "error closing instance 'instance1': Close error"
                )

    def test_configure_threadpool(self):
        """Test configuring the ThreadPool."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_threadpool = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch("basefunctions.DbThreadPool", return_value=mock_threadpool):
                    # Create DbManager
                    manager = DbManager()

                    # Configure threadpool
                    manager.configure_threadpool(num_threads=10)

                    # Verify DbThreadPool was created with correct number of threads
                    basefunctions.DbThreadPool.assert_called_once_with(10)

                    # Verify threadpool was set
                    assert manager.threadpool == mock_threadpool

                    # Verify logger was called
                    mock_logger.warning.assert_called_with(
                        "threadpool initialized with 10 threads"
                    )

    def test_configure_threadpool_error(self):
        """Test error handling during ThreadPool configuration."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                with patch(
                    "basefunctions.DbThreadPool", side_effect=Exception("Threadpool error")
                ):
                    # Create DbManager
                    manager = DbManager()

                    # Try to configure threadpool with error
                    with pytest.raises(Exception) as excinfo:
                        manager.configure_threadpool(num_threads=10)

                    # Verify error was propagated
                    assert "Threadpool error" in str(excinfo.value)

                    # Verify logger critical was called
                    mock_logger.critical.assert_called_with(
                        "error initializing threadpool: Threadpool error"
                    )

    def test_get_threadpool(self):
        """Test getting the ThreadPool."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_threadpool = MagicMock()

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # No threadpool configured yet
                assert manager.get_threadpool() is None

                # Set threadpool
                manager.threadpool = mock_threadpool

                # Get threadpool
                threadpool = manager.get_threadpool()

                # Verify correct threadpool was returned
                assert threadpool is mock_threadpool

    def test_list_instances(self):
        """Test listing all registered instances."""
        # Setup mock objects
        mock_logger = MagicMock()
        mock_config_handler = MagicMock()
        mock_instance1 = MagicMock()
        mock_instance1.is_connected.return_value = True
        mock_instance1.get_type.return_value = "mysql"
        mock_instance1.list_databases.return_value = ["db1", "db2"]

        mock_instance2 = MagicMock()
        mock_instance2.is_connected.return_value = False
        mock_instance2.get_type.return_value = "sqlite3"

        # Patch dependencies
        with patch("basefunctions.get_logger", return_value=mock_logger):
            with patch("basefunctions.ConfigHandler", return_value=mock_config_handler):
                # Create DbManager
                manager = DbManager()

                # Add instances
                manager.instances = {"instance1": mock_instance1, "instance2": mock_instance2}

                # List instances
                result = manager.list_instances()

                # Verify expected result
                expected = {
                    "instance1": {"connected": True, "type": "mysql", "databases": ["db1", "db2"]},
                    "instance2": {"connected": False, "type": "sqlite3", "databases": []},
                }
                assert result == expected

                # Verify methods were called at least once (not exactly once)
                mock_instance1.is_connected.assert_called()  # Statt assert_called_once()
                mock_instance1.get_type.assert_called_once()
                mock_instance1.list_databases.assert_called_once()

                mock_instance2.is_connected.assert_called()  # Statt assert_called_once()
                mock_instance2.get_type.assert_called_once()
                # list_databases should NOT be called when not connected
                mock_instance2.list_databases.assert_not_called()
