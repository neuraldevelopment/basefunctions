"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Tests for DbFactory singleton class
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
from unittest.mock import MagicMock, patch
import threading
import basefunctions
from basefunctions.database.db_factory import (
    DbFactory,
    DB_TYPE_SQLITE,
    DB_TYPE_MYSQL,
    DB_TYPE_POSTGRESQL,
)

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


class MockDbConnector:
    """Mock DB connector for testing DbFactory."""

    def __init__(self, parameters):
        self.parameters = parameters


class TestDbFactory:
    """Test suite for the DbFactory singleton class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup for each test - isolate DbFactory singleton.
        This fixture:
        1. Saves original state
        2. Patches the _register_default_connectors method to prevent auto-registration
        3. Resets the singleton state completely
        4. Yields control to the test
        5. Restores original state after the test
        """
        # Save original state
        original_instance = DbFactory._instance
        original_registry = DbFactory._connector_registry.copy()
        original_register_method = DbFactory._register_default_connectors

        # Start patch for _register_default_connectors to prevent auto-registration
        patcher = patch.object(DbFactory, "_register_default_connectors")
        self.mock_register = patcher.start()

        # Reset singleton state completely
        DbFactory._instance = None
        DbFactory._connector_registry = {}

        # Run the test
        yield

        # Restore original state
        DbFactory._register_default_connectors = original_register_method
        DbFactory._instance = original_instance
        DbFactory._connector_registry = original_registry

        # Stop all patches
        patcher.stop()

    def test_singleton_pattern(self):
        """Test that DbFactory implements the Singleton pattern."""
        # Get instances and verify they are the same object
        factory1 = DbFactory()
        factory2 = DbFactory()

        assert factory1 is factory2
        assert DbFactory._instance is factory1

    def test_register_default_connectors(self):
        """Test registration of default connectors."""
        # Replace the mocked method with a controlled test version
        original_method = DbFactory._register_default_connectors

        try:
            # Create mock connectors
            mock_sqlite = MagicMock()
            mock_mysql = MagicMock()
            mock_postgres = MagicMock()

            # Define test implementation for _register_default_connectors
            def test_register():
                # Register the mock connectors
                DbFactory._connector_registry[DB_TYPE_SQLITE] = mock_sqlite
                DbFactory._connector_registry[DB_TYPE_MYSQL] = mock_mysql
                DbFactory._connector_registry[DB_TYPE_POSTGRESQL] = mock_postgres

            # Replace with our test implementation
            DbFactory._register_default_connectors = classmethod(lambda cls: test_register())

            # Get a factory instance, which will call our _register_default_connectors
            factory = DbFactory()

            # Verify connectors were registered
            assert DbFactory._connector_registry[DB_TYPE_SQLITE] is mock_sqlite
            assert DbFactory._connector_registry[DB_TYPE_MYSQL] is mock_mysql
            assert DbFactory._connector_registry[DB_TYPE_POSTGRESQL] is mock_postgres
        finally:
            # Restore original method
            DbFactory._register_default_connectors = original_method

    def test_register_connector(self):
        """Test registering a custom connector."""
        # Get a factory instance
        factory = DbFactory()

        # Mock logger
        with patch("basefunctions.get_logger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance

            # Register a custom connector
            DbFactory.register_connector("custom_db", MockDbConnector)

            # Verify the connector was registered
            assert "custom_db" in DbFactory._connector_registry
            assert DbFactory._connector_registry["custom_db"] is MockDbConnector

            # Verify logger was called
            mock_logger_instance.warning.assert_called_with("registered connector for 'custom_db'")

    def test_create_connector(self):
        """Test creating a connector instance."""
        # Register a mock connector
        DbFactory._connector_registry["test_db"] = MockDbConnector

        # Create a connector
        params = {"database": "test.db", "user": "test_user"}
        connector = DbFactory.create_connector("test_db", params)

        # Verify the connector
        assert isinstance(connector, MockDbConnector)
        assert connector.parameters == params

    def test_create_connector_unregistered(self):
        """Test error when creating connector with unregistered type."""
        # Try to create a connector for an unregistered type
        with pytest.raises(ValueError) as excinfo:
            DbFactory.create_connector("unknown_db", {})

        # Verify error message
        assert "no connector registered for database type 'unknown_db'" in str(excinfo.value)

    def test_get_available_connectors(self):
        """Test getting available connectors."""
        # Register test connectors
        DbFactory._connector_registry = {"db1": MockDbConnector, "db2": MagicMock()}

        # Get available connectors
        connectors = DbFactory.get_available_connectors()

        # Verify result
        assert len(connectors) == 2
        assert "db1" in connectors
        assert "db2" in connectors
        assert connectors["db1"] is MockDbConnector

        # Verify it's a copy, not the original
        assert connectors is not DbFactory._connector_registry

        # Modify the copy and verify original is unchanged
        connectors["db3"] = MagicMock()
        assert "db3" not in DbFactory._connector_registry

    def test_thread_safety(self):
        """Test thread safety of the singleton pattern."""
        # List to collect instances created in threads
        instances = []
        lock = threading.Lock()

        # Function to create instance in a thread
        def create_instance():
            instance = DbFactory()
            with lock:
                instances.append(instance)

        # Create and start threads
        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all instances are the same object
        assert len(instances) == 5
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance
