"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Pytest test suite for ConfigHandler class

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class TestConfigHandler:
    """Test suite for ConfigHandler class."""

    def setup_method(self):
        """Setup for each test method."""
        # Reset singleton instance for each test
        if hasattr(basefunctions.ConfigHandler, "_instances"):
            basefunctions.ConfigHandler._instances.clear()
        self.config_handler = basefunctions.ConfigHandler()

    def teardown_method(self):
        """Cleanup after each test method."""
        # Reset singleton instance
        if hasattr(basefunctions.ConfigHandler, "_instances"):
            basefunctions.ConfigHandler._instances.clear()

    # =================================================================
    # SINGLETON TESTS
    # =================================================================

    def test_singleton_behavior(self):
        """Test that ConfigHandler implements singleton pattern correctly."""
        handler1 = basefunctions.ConfigHandler()
        handler2 = basefunctions.ConfigHandler()

        assert handler1 is handler2
        assert id(handler1) == id(handler2)

    # =================================================================
    # LOAD CONFIG TESTS
    # =================================================================

    def test_load_config_valid_json(self):
        """Test loading a valid JSON configuration file."""
        test_config = {
            "app": {"name": "test_app", "version": "1.0.0"},
            "database": {"host": "localhost", "port": 5432},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_config, f)
            temp_file = f.name

        try:
            self.config_handler.load_config(temp_file)

            assert self.config_handler.config["app"]["name"] == "test_app"
            assert self.config_handler.config["database"]["port"] == 5432
        finally:
            os.unlink(temp_file)

    def test_load_config_non_json_file(self):
        """Test error handling when file is not a JSON file."""
        with pytest.raises(ValueError, match="not a valid JSON file"):
            self.config_handler.load_config("test.txt")

    def test_load_config_file_not_found(self):
        """Test error handling when file does not exist."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            self.config_handler.load_config("nonexistent.json")

    def test_load_config_invalid_json(self):
        """Test error handling for malformed JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json content}')
            temp_file = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                self.config_handler.load_config(temp_file)
        finally:
            os.unlink(temp_file)

    def test_load_config_invalid_format(self):
        """Test error handling when JSON is not a dictionary."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            temp_file = f.name

        try:
            with pytest.raises(RuntimeError, match="Unexpected error"):
                self.config_handler.load_config(temp_file)
        finally:
            os.unlink(temp_file)

    # =================================================================
    # GET CONFIG VALUE TESTS
    # =================================================================

    def test_get_config_value_existing_path(self):
        """Test retrieving existing configuration values."""
        self.config_handler.config = {"app": {"name": "test_app", "settings": {"debug": True}}}

        assert self.config_handler.get_config_value("app/name") == "test_app"
        assert self.config_handler.get_config_value("app/settings/debug") is True

    def test_get_config_value_nested_path(self):
        """Test retrieving values from deeply nested paths."""
        self.config_handler.config = {"level1": {"level2": {"level3": {"level4": "deep_value"}}}}

        result = self.config_handler.get_config_value("level1/level2/level3/level4")
        assert result == "deep_value"

    def test_get_config_value_nonexistent_path(self):
        """Test default value return for nonexistent paths."""
        self.config_handler.config = {"app": {"name": "test"}}

        result = self.config_handler.get_config_value("nonexistent/path", "default")
        assert result == "default"

        result = self.config_handler.get_config_value("app/nonexistent", "fallback")
        assert result == "fallback"

    def test_get_config_value_invalid_path_type(self):
        """Test handling when path leads to non-dict intermediate value."""
        self.config_handler.config = {"app": {"name": "test_app"}}

        result = self.config_handler.get_config_value("app/name/invalid", "default")
        assert result == "default"

    # =================================================================
    # GET CONFIG TESTS
    # =================================================================

    def test_get_config_with_package(self):
        """Test retrieving configuration for specific package."""
        self.config_handler.config = {"package1": {"setting1": "value1"}, "package2": {"setting2": "value2"}}

        result = self.config_handler.get_config("package1")
        assert result == {"setting1": "value1"}

    def test_get_config_without_package(self):
        """Test retrieving all configurations when no package specified."""
        test_config = {"package1": {"setting1": "value1"}, "package2": {"setting2": "value2"}}
        self.config_handler.config = test_config

        result = self.config_handler.get_config()
        assert result == test_config

    def test_get_config_nonexistent_package(self):
        """Test retrieving config for nonexistent package."""
        self.config_handler.config = {"existing": {"value": "test"}}

        result = self.config_handler.get_config("nonexistent")
        assert result == {}

    # =================================================================
    # DEFAULT CONFIG TESTS
    # =================================================================

    @patch("basefunctions.create_directory")
    @patch("basefunctions.get_home_path")
    def test_create_default_config(self, mock_home_path, mock_create_dir):
        """Test creating default configuration file."""
        mock_home_path.return_value = "/mock/home"

        with patch("builtins.open", mock_open()) as mock_file:
            self.config_handler.create_default_config("test_package")

            mock_create_dir.assert_called_once()
            mock_file.assert_called_once()

            # Check that JSON was written
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            expected_content = json.dumps({"test_package": {}}, indent=2)
            assert written_content == expected_content

    def test_create_default_config_empty_package_name(self):
        """Test error handling for empty package name."""
        with pytest.raises(ValueError, match="Package name must be provided"):
            self.config_handler.create_default_config("")

    @patch("basefunctions.check_if_file_exists")
    @patch("basefunctions.get_home_path")
    def test_load_default_config_file_exists(self, mock_home_path, mock_file_exists):
        """Test loading default config when file exists."""
        mock_home_path.return_value = "/mock/home"
        mock_file_exists.return_value = True

        with (
            patch.object(self.config_handler, "create_default_config") as mock_create,
            patch.object(self.config_handler, "load_config") as mock_load_config,
            patch.object(self.config_handler, "load_database_configs") as mock_load_db,
        ):

            self.config_handler.load_default_config("test_package")

            mock_create.assert_not_called()
            mock_load_config.assert_called_once()
            mock_load_db.assert_called_once()

    @patch("basefunctions.check_if_file_exists")
    @patch("basefunctions.get_home_path")
    def test_load_default_config_file_not_exists(self, mock_home_path, mock_file_exists):
        """Test loading default config when file does not exist."""
        mock_home_path.return_value = "/mock/home"
        mock_file_exists.return_value = False

        with (
            patch.object(self.config_handler, "create_default_config") as mock_create,
            patch.object(self.config_handler, "load_config") as mock_load_config,
            patch.object(self.config_handler, "load_database_configs") as mock_load_db,
        ):

            self.config_handler.load_default_config("test_package")

            mock_create.assert_called_once_with("test_package")
            mock_load_config.assert_called_once()
            mock_load_db.assert_called_once()

    # =================================================================
    # DATABASE INTEGRATION TESTS
    # =================================================================

    @patch("os.path.expanduser")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.iterdir")
    def test_scan_database_instances_no_directory(self, mock_iterdir, mock_exists, mock_expanduser):
        """Test scanning when database instances directory does not exist."""
        mock_expanduser.return_value = "/mock/databases"
        mock_exists.return_value = False

        self.config_handler.scan_database_instances()

        assert "databases" not in self.config_handler.config
        mock_iterdir.assert_not_called()

    @patch("os.path.expanduser")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.iterdir")
    def test_scan_database_instances_with_configs(self, mock_iterdir, mock_exists, mock_expanduser):
        """Test scanning database instances with valid configs."""
        mock_expanduser.return_value = "/mock/databases"
        mock_exists.return_value = True

        # Mock directory structure
        mock_instance_dir = MagicMock()
        mock_instance_dir.name = "test_instance"
        mock_instance_dir.is_dir.return_value = True

        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_instance_dir.__truediv__.return_value.__truediv__.return_value = mock_config_file

        mock_iterdir.return_value = [mock_instance_dir]

        test_config = {"host": "localhost", "port": 5432}

        with patch("builtins.open", mock_open(read_data=json.dumps(test_config))):
            self.config_handler.scan_database_instances()

        assert "databases" in self.config_handler.config
        assert "test_instance" in self.config_handler.config["databases"]
        assert self.config_handler.config["databases"]["test_instance"] == test_config

    def test_get_database_config_existing(self):
        """Test retrieving existing database configuration."""
        self.config_handler.config = {"databases": {"test_db": {"host": "localhost", "port": 5432}}}

        result = self.config_handler.get_database_config("test_db")
        assert result == {"host": "localhost", "port": 5432}

    def test_get_database_config_nonexistent(self):
        """Test retrieving nonexistent database configuration."""
        self.config_handler.config = {"databases": {}}

        result = self.config_handler.get_database_config("nonexistent_db")
        assert result == {}

    def test_get_database_config_no_databases(self):
        """Test retrieving database config when no databases are configured."""
        self.config_handler.config = {}

        result = self.config_handler.get_database_config("any_db")
        assert result == {}

    # =================================================================
    # UTILITY TESTS
    # =================================================================

    def test_list_available_paths_empty_config(self):
        """Test listing paths with empty configuration."""
        self.config_handler.config = {}

        result = self.config_handler.list_available_paths()
        assert result == []

    def test_list_available_paths_nested_config(self):
        """Test listing all available configuration paths."""
        self.config_handler.config = {
            "app": {"name": "test", "settings": {"debug": True, "logging": {"level": "INFO"}}},
            "database": {"host": "localhost"},
        }

        result = self.config_handler.list_available_paths()

        expected_paths = [
            "app",
            "app/name",
            "app/settings",
            "app/settings/debug",
            "app/settings/logging",
            "app/settings/logging/level",
            "database",
            "database/host",
        ]

        assert set(result) == set(expected_paths)

    def test_list_available_paths_with_non_dict_values(self):
        """Test listing paths when config contains non-dict values."""
        self.config_handler.config = {"simple": "value", "list": [1, 2, 3], "nested": {"key": "value"}}

        result = self.config_handler.list_available_paths()

        expected_paths = ["simple", "list", "nested", "nested/key"]
        assert set(result) == set(expected_paths)

    # =================================================================
    # LOAD DATABASE CONFIGS TEST
    # =================================================================

    def test_load_database_configs(self):
        """Test load_database_configs calls scan_database_instances."""
        with patch.object(self.config_handler, "scan_database_instances") as mock_scan:
            self.config_handler.load_database_configs()

            mock_scan.assert_called_once()
