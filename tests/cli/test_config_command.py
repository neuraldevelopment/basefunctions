"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for ConfigCommand — CLI command that outputs the current system configuration
 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import json
from unittest.mock import patch

import basefunctions
import pytest

from basefunctions.cli.config_command import ConfigCommand

# =============================================================================
# TESTS
# =============================================================================


def test_register_commands_returns_config_in_available_commands(mock_context_manager):
    """config command is registered and appears in available commands."""
    # Arrange / Act
    cmd = ConfigCommand(mock_context_manager)
    # Assert
    assert "config" in cmd.get_available_commands()


def test_register_commands_metadata_has_correct_name(mock_context_manager):
    """config command metadata has correct name."""
    # Arrange
    cmd = ConfigCommand(mock_context_manager)
    # Act
    metadata = cmd.get_command_metadata("config")
    # Assert
    assert metadata.name == "config"


def test_register_commands_metadata_has_usage_and_examples(mock_context_manager):
    """config command metadata has usage string and at least two examples."""
    # Arrange
    cmd = ConfigCommand(mock_context_manager)
    # Act
    metadata = cmd.get_command_metadata("config")
    # Assert
    assert metadata.usage == "config [package]"
    assert len(metadata.examples) >= 2


def test_execute_config_no_args_outputs_full_config_as_json(mock_context_manager, capsys):
    """execute with no args calls get_config_for_package(None) and prints JSON."""
    # Arrange
    expected = {"basefunctions": {"logging": {"level": "INFO"}}}
    cmd = ConfigCommand(mock_context_manager)
    # Act
    with patch.object(basefunctions.ConfigHandler(), "get_config_for_package", return_value=expected):
        cmd.execute("config", [])
    # Assert
    captured = capsys.readouterr()
    assert captured.out.strip() == json.dumps(expected, indent=2)


def test_execute_config_with_package_arg_calls_get_config_for_package_with_name(mock_context_manager):
    """execute with package arg passes package name to get_config_for_package."""
    # Arrange
    cmd = ConfigCommand(mock_context_manager)
    # Act
    with patch.object(
        basefunctions.ConfigHandler(), "get_config_for_package", return_value={}
    ) as mock_fn:
        cmd.execute("config", ["basefunctions"])
    # Assert — package name forwarded correctly
    mock_fn.assert_called_once_with("basefunctions")


def test_execute_config_with_unknown_package_outputs_empty_dict(mock_context_manager, capsys):
    """execute with unknown package prints {} without raising."""
    # Arrange
    cmd = ConfigCommand(mock_context_manager)
    # Act
    with patch.object(basefunctions.ConfigHandler(), "get_config_for_package", return_value={}):
        cmd.execute("config", ["unknown_package"])
    # Assert
    captured = capsys.readouterr()
    assert captured.out.strip() == "{}"


def test_execute_unknown_command_raises_value_error(mock_context_manager):
    """execute with unregistered command name raises ValueError."""
    # Arrange
    cmd = ConfigCommand(mock_context_manager)
    # Act / Assert
    with pytest.raises(ValueError, match="Unknown command: badcmd"):
        cmd.execute("badcmd", [])
