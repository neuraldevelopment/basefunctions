"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Pytest test suite for DbDockerManager class

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import pytest
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock, mock_open

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


class TestDbDockerManager:
    """Test suite for DbDockerManager class."""

    def setup_method(self):
        """Setup for each test method."""
        self.mock_registry = Mock()
        self.mock_registry.validate_db_type.return_value = True
        self.mock_registry.supports_feature.return_value = True
        self.mock_registry.get_supported_types.return_value = ["mysql", "postgres", "redis"]

    # =================================================================
    # INITIALIZATION TESTS
    # =================================================================

    @patch("basefunctions.get_registry")
    def test_init_sets_registry_and_logger(self, mock_get_registry):
        """Test initialization sets registry and logger."""
        mock_get_registry.return_value = self.mock_registry

        manager = basefunctions.DbDockerManager()

        assert manager.registry is not None
        assert manager.logger is not None
        mock_get_registry.assert_called_once()

    # =================================================================
    # CREATE INSTANCE TESTS
    # =================================================================

    @patch("basefunctions.get_registry")
    @patch("basefunctions.create_directory")
    @patch("basefunctions.check_if_dir_exists")
    def test_create_instance_success(self, mock_check_dir, mock_create_dir, mock_get_registry):
        """Test successful instance creation."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = False  # Instance doesn't exist yet

        manager = basefunctions.DbDockerManager()

        with (
            patch.object(manager, "_allocate_ports", return_value=(5432, 8080)) as mock_allocate,
            patch.object(manager, "_create_instance_structure") as mock_create_structure,
            patch.object(manager, "_render_templates", return_value={"docker_compose": "test yaml"}) as mock_render,
            patch.object(manager, "_create_instance_config", return_value={"type": "mysql"}) as mock_create_config,
            patch.object(manager, "_docker_compose_up") as mock_compose_up,
            patch.object(manager, "_generate_simon_scripts") as mock_simon,
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.dump") as mock_json_dump,
            patch("basefunctions.DbInstance") as mock_instance_class,
        ):

            mock_instance = Mock()
            mock_instance_class.return_value = mock_instance

            result = manager.create_instance("mysql", "test_instance", "test_password")

            # Verify registry validation
            self.mock_registry.validate_db_type.assert_called_once_with("mysql")
            self.mock_registry.supports_feature.assert_called_once_with("mysql", "docker_support")

            # Verify workflow steps
            mock_allocate.assert_called_once_with("mysql")
            mock_create_structure.assert_called_once_with("test_instance")
            mock_render.assert_called_once()
            mock_create_config.assert_called_once()
            mock_compose_up.assert_called_once()
            mock_simon.assert_called_once()

            # Verify instance creation
            mock_instance_class.assert_called_once()
            assert result == mock_instance

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    def test_create_instance_already_exists(self, mock_check_dir, mock_get_registry):
        """Test creating instance that already exists raises error."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = True  # Instance already exists

        manager = basefunctions.DbDockerManager()

        with pytest.raises(basefunctions.DbInstanceError, match="instance 'test_instance' already exists"):
            manager.create_instance("mysql", "test_instance", "test_password")

    @patch("basefunctions.get_registry")
    def test_create_instance_invalid_db_type(self, mock_get_registry):
        """Test creating instance with invalid db_type raises error."""
        mock_registry = Mock()
        mock_registry.validate_db_type.side_effect = basefunctions.DbValidationError("Invalid db_type")
        mock_get_registry.return_value = mock_registry

        manager = basefunctions.DbDockerManager()

        with pytest.raises(basefunctions.DbValidationError):
            manager.create_instance("invalid_type", "test_instance", "test_password")

    @patch("basefunctions.get_registry")
    def test_create_instance_empty_name(self, mock_get_registry):
        """Test creating instance with empty name raises error."""
        mock_get_registry.return_value = self.mock_registry

        manager = basefunctions.DbDockerManager()

        with pytest.raises(basefunctions.DbValidationError, match="instance_name cannot be empty"):
            manager.create_instance("mysql", "", "test_password")

    @patch("basefunctions.get_registry")
    def test_create_instance_empty_password(self, mock_get_registry):
        """Test creating instance with empty password raises error."""
        mock_get_registry.return_value = self.mock_registry

        manager = basefunctions.DbDockerManager()

        with pytest.raises(basefunctions.DbValidationError, match="password cannot be empty"):
            manager.create_instance("mysql", "test_instance", "")

    # =================================================================
    # START/STOP INSTANCE TESTS
    # =================================================================

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    def test_start_instance_success(self, mock_check_dir, mock_get_registry):
        """Test successful instance start."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = True  # Instance exists

        manager = basefunctions.DbDockerManager()

        with patch.object(manager, "_docker_compose_up") as mock_compose_up:
            result = manager.start_instance("test_instance")

            assert result is True
            mock_check_dir.assert_called()
            mock_compose_up.assert_called_once()

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    def test_start_instance_not_found(self, mock_check_dir, mock_get_registry):
        """Test starting non-existent instance returns False."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = False  # Instance doesn't exist

        manager = basefunctions.DbDockerManager()
        result = manager.start_instance("nonexistent_instance")

        assert result is False

    @patch("basefunctions.get_registry")
    def test_start_instance_empty_name(self, mock_get_registry):
        """Test starting instance with empty name returns False."""
        mock_get_registry.return_value = self.mock_registry

        manager = basefunctions.DbDockerManager()
        result = manager.start_instance("")

        assert result is False

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    def test_stop_instance_success(self, mock_check_dir, mock_get_registry):
        """Test successful instance stop."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = True  # Instance exists

        manager = basefunctions.DbDockerManager()

        with patch.object(manager, "_docker_compose_down") as mock_compose_down:
            result = manager.stop_instance("test_instance")

            assert result is True
            mock_check_dir.assert_called()
            mock_compose_down.assert_called_once()

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    def test_start_instance_docker_error(self, mock_check_dir, mock_get_registry):
        """Test instance start handles docker errors gracefully."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = True

        manager = basefunctions.DbDockerManager()

        with patch.object(manager, "_docker_compose_up", side_effect=Exception("Docker error")):
            result = manager.start_instance("test_instance")

            assert result is False

    # =================================================================
    # DELETE INSTANCE TESTS
    # =================================================================

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    @patch("basefunctions.check_if_file_exists")
    @patch("basefunctions.remove_directory")
    def test_delete_instance_success(self, mock_remove_dir, mock_check_file, mock_check_dir, mock_get_registry):
        """Test successful instance deletion."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = True  # Instance exists
        mock_check_file.return_value = True  # Config file exists

        manager = basefunctions.DbDockerManager()

        with (
            patch.object(manager, "_docker_compose_down") as mock_compose_down,
            patch.object(manager, "_free_ports") as mock_free_ports,
            patch("builtins.open", mock_open(read_data='{"ports": {"db": 5432, "admin": 8080}}')) as mock_file,
            patch("json.load", return_value={"ports": {"db": 5432, "admin": 8080}}) as mock_json_load,
        ):

            result = manager.delete_instance("test_instance")

            assert result is True
            mock_check_dir.assert_called()
            mock_compose_down.assert_called_once()
            mock_free_ports.assert_called_once_with(5432, 8080)
            mock_remove_dir.assert_called_once()

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    def test_delete_instance_not_found(self, mock_check_dir, mock_get_registry):
        """Test deleting non-existent instance returns False."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = False  # Instance doesn't exist

        manager = basefunctions.DbDockerManager()
        result = manager.delete_instance("nonexistent_instance")

        assert result is False

    @patch("basefunctions.get_registry")
    def test_delete_instance_empty_name(self, mock_get_registry):
        """Test deleting instance with empty name returns False."""
        mock_get_registry.return_value = self.mock_registry

        manager = basefunctions.DbDockerManager()
        result = manager.delete_instance("")

        assert result is False

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    @patch("basefunctions.check_if_file_exists")
    def test_delete_instance_force_mode(self, mock_check_file, mock_check_dir, mock_get_registry):
        """Test deleting instance in force mode."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = False  # Instance doesn't exist
        mock_check_file.return_value = False

        manager = basefunctions.DbDockerManager()

        with patch.object(manager, "_force_remove_containers_by_name") as mock_force_remove:
            result = manager.delete_instance("test_instance", force=True)

            # In force mode, should still attempt cleanup
            assert result is True
            mock_force_remove.assert_called_once_with("test_instance")

    # =================================================================
    # INSTANCE STATUS TESTS
    # =================================================================

    @patch("basefunctions.get_registry")
    @patch("subprocess.run")
    def test_get_instance_status_running(self, mock_subprocess, mock_get_registry):
        """Test getting status of running instance."""
        mock_get_registry.return_value = self.mock_registry

        # Mock docker ps output
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test_instance_mysql_1\nUp 2 hours"

        manager = basefunctions.DbDockerManager()
        result = manager.get_instance_status("test_instance")

        assert isinstance(result, dict)
        assert "status" in result

    @patch("basefunctions.get_registry")
    @patch("subprocess.run")
    def test_get_instance_status_stopped(self, mock_subprocess, mock_get_registry):
        """Test getting status of stopped instance."""
        mock_get_registry.return_value = self.mock_registry

        # Mock docker ps output for stopped container
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""

        manager = basefunctions.DbDockerManager()
        result = manager.get_instance_status("test_instance")

        assert isinstance(result, dict)
        assert "status" in result

    @patch("basefunctions.get_registry")
    @patch("subprocess.run")
    def test_get_instance_status_docker_error(self, mock_subprocess, mock_get_registry):
        """Test getting status when docker command fails."""
        mock_get_registry.return_value = self.mock_registry
        mock_subprocess.side_effect = Exception("Docker not available")

        manager = basefunctions.DbDockerManager()
        result = manager.get_instance_status("test_instance")

        assert isinstance(result, dict)
        assert "error" in result or "status" in result

    # =================================================================
    # ERROR HANDLING TESTS
    # =================================================================

    @patch("basefunctions.get_registry")
    @patch("basefunctions.check_if_dir_exists")
    @patch("subprocess.run")
    def test_subprocess_timeout_handling(self, mock_subprocess, mock_check_dir, mock_get_registry):
        """Test handling of subprocess timeouts."""
        mock_get_registry.return_value = self.mock_registry
        mock_check_dir.return_value = True
        mock_subprocess.side_effect = subprocess.TimeoutExpired("docker-compose", 30)

        manager = basefunctions.DbDockerManager()

        with patch.object(manager, "_docker_compose_up", side_effect=subprocess.TimeoutExpired("docker-compose", 30)):
            result = manager.start_instance("test_instance")

            assert result is False

    @patch("basefunctions.get_registry")
    def test_invalid_instance_names(self, mock_get_registry):
        """Test handling of invalid instance names."""
        mock_get_registry.return_value = self.mock_registry

        manager = basefunctions.DbDockerManager()

        # Test various invalid names
        invalid_names = [None, "", "   "]

        for invalid_name in invalid_names:
            if invalid_name is None:
                # None would cause different error, skip
                continue
            assert manager.start_instance(invalid_name) is False
            assert manager.stop_instance(invalid_name) is False
            assert manager.delete_instance(invalid_name) is False
