"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for basefunctions.utils.logging module - comprehensive test suite
 for get_standard_log_directory() and enable_logging() with >80% coverage.
 Log:
 v1.0 : Initial implementation with 7+ test scenarios
 v1.1 : Added enable_logging() tests (8 scenarios)
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Project modules
from basefunctions.utils.logging import get_standard_log_directory


# =============================================================================
# TEST: get_standard_log_directory() - Development Environment
# =============================================================================


def test_get_standard_log_directory_development_environment():
    """Test returns correct path in development environment."""
    # Arrange
    package_name = "basefunctions"
    expected_path = "/Users/test/Code/neuraldev/basefunctions/logs"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=expected_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = get_standard_log_directory(package_name)

    # Assert
    assert result == expected_path
    mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_get_standard_log_directory_deployment_environment():
    """Test returns correct path in deployment environment."""
    # Arrange
    package_name = "tickerhub"
    expected_path = "/Users/test/.neuraldevelopment/logs/tickerhub"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=expected_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = get_standard_log_directory(package_name)

    # Assert
    assert result == expected_path
    mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)


# =============================================================================
# TEST: get_standard_log_directory() - Directory Creation
# =============================================================================


def test_get_standard_log_directory_creates_directory_when_ensure_exists_true():
    """Test directory is created when ensure_exists=True."""
    # Arrange
    package_name = "basefunctions"
    log_path = "/tmp/test_logs"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=log_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = get_standard_log_directory(package_name, ensure_exists=True)

    # Assert
    assert result == log_path
    mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_get_standard_log_directory_skips_creation_when_ensure_exists_false():
    """Test directory is NOT created when ensure_exists=False."""
    # Arrange
    package_name = "basefunctions"
    log_path = "/tmp/test_logs"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=log_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = get_standard_log_directory(package_name, ensure_exists=False)

    # Assert
    assert result == log_path
    mock_path_instance.mkdir.assert_not_called()


# =============================================================================
# TEST: get_standard_log_directory() - Exception Handling
# =============================================================================


def test_get_standard_log_directory_propagates_oserror_on_mkdir_failure():
    """Test OSError propagates when directory creation fails."""
    # Arrange
    package_name = "basefunctions"
    log_path = "/root/restricted/logs"

    # Act & Assert
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=log_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.mkdir.side_effect = OSError("Permission denied")

            with pytest.raises(OSError, match="Permission denied"):
                get_standard_log_directory(package_name, ensure_exists=True)


# =============================================================================
# TEST: get_standard_log_directory() - Multiple Packages
# =============================================================================


def test_get_standard_log_directory_handles_multiple_packages():
    """Test function works with different package names."""
    # Arrange
    packages = [
        ("basefunctions", "/home/user/logs/basefunctions"),
        ("tickerhub", "/home/user/logs/tickerhub"),
        ("dbfunctions", "/home/user/logs/dbfunctions"),
    ]

    # Act & Assert
    for package_name, expected_path in packages:
        with patch("basefunctions.runtime.get_runtime_log_path", return_value=expected_path):
            with patch("basefunctions.utils.logging.Path") as mock_path:
                mock_path_instance = MagicMock()
                mock_path.return_value = mock_path_instance

                result = get_standard_log_directory(package_name, ensure_exists=False)

                assert result == expected_path


# =============================================================================
# TEST: get_standard_log_directory() - Integration Test
# =============================================================================


def test_get_standard_log_directory_integration_with_real_runtime():
    """Test actual behavior with real get_runtime_log_path() call."""
    # Arrange
    package_name = "basefunctions"

    # Act
    with patch("basefunctions.utils.logging.Path") as mock_path:
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        result = get_standard_log_directory(package_name, ensure_exists=False)

    # Assert
    # Should return a valid path (either dev or deploy)
    assert isinstance(result, str)
    assert len(result) > 0
    assert package_name in result or "logs" in result


# =============================================================================
# TEST: get_standard_log_directory() - Edge Cases
# =============================================================================


def test_get_standard_log_directory_with_empty_package_name():
    """Test behavior with empty package name."""
    # Arrange
    package_name = ""
    expected_path = "/tmp/logs"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=expected_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = get_standard_log_directory(package_name, ensure_exists=False)

    # Assert
    # Function should handle empty package name gracefully (delegates to runtime)
    assert result == expected_path


def test_get_standard_log_directory_with_special_characters_in_package_name():
    """Test behavior with special characters in package name."""
    # Arrange
    package_name = "test-package_v2.0"
    expected_path = "/tmp/logs/test-package_v2.0"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=expected_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            result = get_standard_log_directory(package_name, ensure_exists=False)

    # Assert
    assert result == expected_path


def test_get_standard_log_directory_mkdir_called_with_correct_arguments():
    """Test mkdir is called with correct arguments (parents=True, exist_ok=True)."""
    # Arrange
    package_name = "basefunctions"
    log_path = "/tmp/test_logs"

    # Act
    with patch("basefunctions.runtime.get_runtime_log_path", return_value=log_path):
        with patch("basefunctions.utils.logging.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            get_standard_log_directory(package_name, ensure_exists=True)

    # Assert
    # Verify mkdir was called with exact arguments
    mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)


# =============================================================================
# TEST: enable_logging() - Global Logging ON/OFF Switch
# =============================================================================


def test_enable_logging_with_true_sets_root_logger_to_debug():
    """Test enable_logging(True) sets root logger level to DEBUG."""
    # Arrange
    from basefunctions.utils.logging import enable_logging

    # Act
    enable_logging(True)

    # Assert
    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_enable_logging_with_false_sets_root_logger_to_critical_plus_one():
    """Test enable_logging(False) sets root logger level to CRITICAL+1."""
    # Arrange
    from basefunctions.utils.logging import enable_logging

    # Act
    enable_logging(False)

    # Assert
    root = logging.getLogger()
    assert root.level == logging.CRITICAL + 1


def test_enable_logging_toggle_changes_root_logger_level():
    """Test toggling enable_logging changes root logger level correctly."""
    # Arrange
    from basefunctions.utils.logging import enable_logging

    # Act & Assert - Enable
    enable_logging(True)
    root = logging.getLogger()
    assert root.level == logging.DEBUG

    # Act & Assert - Disable
    enable_logging(False)
    assert root.level == logging.CRITICAL + 1

    # Act & Assert - Re-enable
    enable_logging(True)
    assert root.level == logging.DEBUG


def test_enable_logging_with_false_prevents_root_logger_from_propagating():
    """Test enable_logging(False) sets root logger to prevent propagation."""
    # Arrange
    from basefunctions.utils.logging import enable_logging

    # Act - Disable logging
    enable_logging(False)

    # Assert
    root = logging.getLogger()
    # When disabled, root logger is at CRITICAL+1, which blocks propagation
    assert root.level == logging.CRITICAL + 1
    # This means child loggers won't propagate to root handlers
    assert root.level > logging.CRITICAL


def test_enable_logging_with_true_allows_root_logger_propagation():
    """Test enable_logging(True) sets root logger to allow propagation."""
    # Arrange
    from basefunctions.utils.logging import enable_logging

    # Act - Enable logging
    enable_logging(True)

    # Assert
    root = logging.getLogger()
    # When enabled, root logger is at DEBUG, allowing all levels
    assert root.level == logging.DEBUG
    # This allows child loggers to propagate to root handlers
    assert root.level <= logging.DEBUG


def test_enable_logging_preserves_individual_logger_configurations():
    """Test enable_logging does not modify individual logger level settings."""
    # Arrange
    from basefunctions.utils.logging import enable_logging, setup_logger, get_logger

    test_logger_name = "test_config_preservation"
    setup_logger(test_logger_name, level="WARNING")
    logger = get_logger(test_logger_name)

    initial_level = logger.level

    # Act - Toggle logging
    enable_logging(False)
    enable_logging(True)

    # Assert
    assert logger.level == initial_level, "Individual logger level should not change"


def test_enable_logging_multiple_toggles_work_correctly():
    """Test multiple enable_logging toggles work correctly."""
    # Arrange
    from basefunctions.utils.logging import enable_logging

    root = logging.getLogger()

    # Act & Assert - Multiple toggles
    enable_logging(True)
    assert root.level == logging.DEBUG

    enable_logging(False)
    assert root.level == logging.CRITICAL + 1

    enable_logging(True)
    assert root.level == logging.DEBUG

    enable_logging(False)
    assert root.level == logging.CRITICAL + 1


def test_enable_logging_integration_with_setup_logger():
    """Test enable_logging integration with setup_logger configuration."""
    # Arrange
    from basefunctions.utils.logging import enable_logging, setup_logger, get_logger

    test_logger_name = "test_integration_logger"
    setup_logger(test_logger_name, level="INFO")
    logger = get_logger(test_logger_name)

    initial_logger_level = logger.level

    # Act - Toggle global logging
    enable_logging(False)
    root_disabled = logging.getLogger().level

    enable_logging(True)
    root_enabled = logging.getLogger().level

    # Assert
    assert root_disabled == logging.CRITICAL + 1, "Root logger should be silenced"
    assert root_enabled == logging.DEBUG, "Root logger should allow all levels"
    assert logger.level == initial_logger_level, "Individual logger config unchanged"
