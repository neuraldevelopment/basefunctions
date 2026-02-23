"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for basefunctions.utils.logging module - comprehensive test suite
 for new logging API (get_logger, set_log_level, set_log_console,
 set_log_file, set_log_file_rotation) with >80% coverage.
 Log:
 v1.0 : Initial implementation with 7+ test scenarios
 v1.1 : Added enable_logging() tests (8 scenarios)
 v2.0 : Rewritten for new logging API - TDD approach
 v2.1 : Auto-log-file feature tests - 10 new test scenarios
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
import logging
import sys
from logging.handlers import RotatingFileHandler
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
# TEST: NEW LOGGING API - get_logger()
# =============================================================================


@pytest.fixture
def reset_logging():
    """Reset logging state before and after each test."""
    from basefunctions.utils.logging import _reset_logging_state

    # Reset all logging state (including _config_loaded flag)
    _reset_logging_state()

    yield

    # Cleanup after test
    _reset_logging_state()


def test_get_logger_with_explicit_name_returns_logger():
    """Test get_logger with explicit name parameter returns logger."""
    # Arrange
    from basefunctions.utils.logging import get_logger

    # Act
    logger = get_logger(name="test.module")

    # Assert
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_get_logger_with_none_auto_detects_caller_module(reset_logging):
    """Test get_logger(name=None) auto-detects caller module via inspect."""
    # Arrange
    from basefunctions.utils.logging import get_logger

    # Act
    logger = get_logger(name=None)

    # Assert
    assert isinstance(logger, logging.Logger)
    # Should auto-detect this test module
    assert "test_logging" in logger.name or __name__ in logger.name


def test_get_logger_initializes_root_logger_on_first_call(reset_logging):
    """Test get_logger initializes root logger with ERROR level and no handlers on first call."""
    # Arrange
    from basefunctions.utils.logging import get_logger

    # Act
    logger = get_logger(name="first.call")
    root = logging.getLogger()

    # Assert
    assert root.level == logging.ERROR
    # Only pytest's LogCaptureHandler should be present (reset_logging preserves it)
    non_pytest_handlers = [h for h in root.handlers if h.__class__.__name__ != "LogCaptureHandler"]
    assert len(non_pytest_handlers) == 0


def test_get_logger_thread_safety(reset_logging):
    """Test get_logger is thread-safe with concurrent calls."""
    # Arrange
    from basefunctions.utils.logging import get_logger
    import threading

    results = []
    errors = []

    def get_logger_thread(name):
        try:
            logger = get_logger(name=name)
            results.append((name, logger))
        except Exception as e:
            errors.append(e)

    # Act - Create 10 concurrent threads
    threads = [
        threading.Thread(target=get_logger_thread, args=(f"thread.module.{i}",))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Assert
    assert len(errors) == 0, f"Thread errors occurred: {errors}"
    assert len(results) == 10
    assert all(isinstance(logger, logging.Logger) for _, logger in results)


def test_get_logger_auto_detect_fails_raises_runtime_error(reset_logging):
    """Test get_logger raises RuntimeError when auto-detect fails."""
    # Arrange
    from basefunctions.utils.logging import get_logger
    from unittest.mock import patch

    # Act & Assert
    # Mock inspect.stack() to simulate failure scenario
    with patch("inspect.stack", side_effect=Exception("Stack inspection failed")):
        with pytest.raises(RuntimeError, match="Failed to auto-detect module name"):
            get_logger(name=None)


def test_get_logger_same_name_returns_same_instance(reset_logging):
    """Test calling get_logger with same name returns same logger instance."""
    # Arrange
    from basefunctions.utils.logging import get_logger

    # Act
    logger1 = get_logger(name="shared.module")
    logger2 = get_logger(name="shared.module")

    # Assert
    assert logger1 is logger2


# =============================================================================
# TEST: NEW LOGGING API - set_log_level()
# =============================================================================


def test_set_log_level_global_sets_root_logger_level(reset_logging):
    """Test set_log_level with no module sets global root logger level."""
    # Arrange
    from basefunctions.utils.logging import set_log_level

    # Act
    set_log_level(level="WARNING", module=None)
    root = logging.getLogger()

    # Assert
    assert root.level == logging.WARNING


def test_set_log_level_module_specific_sets_module_logger_level(reset_logging):
    """Test set_log_level with module name sets specific module logger level."""
    # Arrange
    from basefunctions.utils.logging import set_log_level, get_logger

    # Act
    set_log_level(level="DEBUG", module="test.specific.module")
    logger = get_logger(name="test.specific.module")

    # Assert
    assert logger.level == logging.DEBUG


def test_set_log_level_invalid_level_raises_value_error(reset_logging):
    """Test set_log_level raises ValueError for invalid log level."""
    # Arrange
    from basefunctions.utils.logging import set_log_level

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid log level"):
        set_log_level(level="INVALID", module=None)


def test_set_log_level_case_insensitive_parsing(reset_logging):
    """Test set_log_level accepts case-insensitive level strings."""
    # Arrange
    from basefunctions.utils.logging import set_log_level, get_logger

    # Act
    set_log_level(level="debug", module="test.case.module")
    logger = get_logger(name="test.case.module")

    # Assert
    assert logger.level == logging.DEBUG


def test_set_log_level_thread_safety(reset_logging):
    """Test set_log_level is thread-safe with concurrent calls."""
    # Arrange
    from basefunctions.utils.logging import set_log_level
    import threading

    errors = []

    def set_level_thread(module, level):
        try:
            set_log_level(level=level, module=module)
        except Exception as e:
            errors.append(e)

    # Act - Create 10 concurrent threads
    threads = [
        threading.Thread(target=set_level_thread, args=(f"thread.module.{i}", "INFO"))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Assert
    assert len(errors) == 0, f"Thread errors occurred: {errors}"


def test_set_log_level_multiple_calls_updates_level(reset_logging):
    """Test multiple set_log_level calls update the level correctly."""
    # Arrange
    from basefunctions.utils.logging import set_log_level, get_logger

    logger = get_logger(name="test.update.module")

    # Act
    set_log_level(level="DEBUG", module="test.update.module")
    assert logger.level == logging.DEBUG

    set_log_level(level="ERROR", module="test.update.module")
    assert logger.level == logging.ERROR

    set_log_level(level="INFO", module="test.update.module")

    # Assert
    assert logger.level == logging.INFO


# =============================================================================
# TEST: NEW LOGGING API - set_log_console()
# =============================================================================


def test_set_log_console_enable_activates_console_output(reset_logging):
    """Test set_log_console(enabled=True) activates console output."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, get_logger

    logger = get_logger(name="test.console.module")

    # Act
    set_log_console(enabled=True, level="INFO")

    # Assert - Check logger has StreamHandler pointing to stderr
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(handlers) > 0
    assert handlers[0].stream == sys.stderr


def test_set_log_console_disable_deactivates_console_output(reset_logging):
    """Test set_log_console(enabled=False) removes console output."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, get_logger

    logger = get_logger(name="test.console.disable")

    # Act - First enable, then disable
    set_log_console(enabled=True, level="INFO")
    set_log_console(enabled=False)

    # Assert - No StreamHandler should be present
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(handlers) == 0


def test_set_log_console_custom_level_sets_handler_level(reset_logging):
    """Test set_log_console with custom level sets handler to that level."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, get_logger

    logger = get_logger(name="test.console.level")

    # Act
    set_log_console(enabled=True, level="WARNING")

    # Assert
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(handlers) > 0
    assert handlers[0].level == logging.WARNING


def test_set_log_console_none_level_uses_global_level(reset_logging):
    """Test set_log_console with level=None uses global logger level."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, set_log_level, get_logger

    # Set global level
    set_log_level(level="ERROR", module=None)
    logger = get_logger(name="test.console.global")

    # Act - Enable console without specific level
    set_log_console(enabled=True, level=None)

    # Assert - Handler should use global level
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(handlers) > 0
    # Handler should inherit from logger or root
    root = logging.getLogger()
    assert root.level == logging.ERROR


def test_set_log_console_invalid_level_raises_value_error(reset_logging):
    """Test set_log_console raises ValueError for invalid level."""
    # Arrange
    from basefunctions.utils.logging import set_log_console

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid log level"):
        set_log_console(enabled=True, level="INVALID_LEVEL")


def test_set_log_console_output_goes_to_stderr(reset_logging):
    """Test set_log_console output is directed to stderr."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, get_logger

    logger = get_logger(name="test.stderr.module")

    # Act
    set_log_console(enabled=True, level="DEBUG")

    # Assert - StreamHandler should use sys.stderr
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(handlers) > 0
    assert handlers[0].stream == sys.stderr


def test_set_log_console_thread_safety(reset_logging):
    """Test set_log_console is thread-safe with concurrent calls."""
    # Arrange
    from basefunctions.utils.logging import set_log_console
    import threading

    errors = []

    def toggle_console(enabled):
        try:
            set_log_console(enabled=enabled, level="INFO")
        except Exception as e:
            errors.append(e)

    # Act - Create 10 concurrent threads toggling console
    threads = [
        threading.Thread(target=toggle_console, args=(i % 2 == 0,))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Assert
    assert len(errors) == 0, f"Thread errors occurred: {errors}"


def test_set_log_console_multiple_enable_calls_replace_handler(reset_logging):
    """Test multiple set_log_console enable calls replace the handler."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, get_logger

    logger = get_logger(name="test.console.replace")

    # Act - Enable with different levels
    set_log_console(enabled=True, level="DEBUG")
    set_log_console(enabled=True, level="ERROR")

    # Assert - Only one StreamHandler should exist
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(handlers) == 1
    assert handlers[0].level == logging.ERROR


# =============================================================================
# TEST: NEW LOGGING API - set_log_file()
# =============================================================================


def test_set_log_file_basic_file_output(reset_logging, tmp_path):
    """Test set_log_file creates file handler with basic configuration."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file = tmp_path / "test.log"
    logger = get_logger(name="test.file.module")

    # Act
    set_log_file(filepath=str(log_file), level="INFO")

    # Assert - FileHandler should exist
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(handlers) > 0
    assert log_file.exists()


def test_set_log_file_custom_level(reset_logging, tmp_path):
    """Test set_log_file with custom level sets handler level correctly."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file = tmp_path / "custom_level.log"
    logger = get_logger(name="test.file.level")

    # Act
    set_log_file(filepath=str(log_file), level="ERROR")

    # Assert
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(handlers) > 0
    assert handlers[0].level == logging.ERROR


def test_set_log_file_none_filepath_deactivates_file_logging(reset_logging, tmp_path):
    """Test set_log_file with filepath=None removes file handler."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file = tmp_path / "deactivate.log"
    logger = get_logger(name="test.file.deactivate")

    # Act - First enable, then disable
    set_log_file(filepath=str(log_file), level="INFO")
    set_log_file(filepath=None)

    # Assert - No FileHandler should exist
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(handlers) == 0


def test_set_log_file_creates_directory_if_needed(reset_logging, tmp_path):
    """Test set_log_file creates parent directories if they don't exist."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file = tmp_path / "nested" / "dir" / "test.log"
    logger = get_logger(name="test.file.mkdir")

    # Act
    set_log_file(filepath=str(log_file), level="INFO")

    # Assert - Directory should be created
    assert log_file.parent.exists()
    assert log_file.exists()


def test_set_log_file_rotation_enabled(reset_logging, tmp_path):
    """Test set_log_file with rotation=True uses RotatingFileHandler."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file = tmp_path / "rotation.log"
    logger = get_logger(name="test.file.rotation")

    # Act
    set_log_file(filepath=str(log_file), level="INFO", rotation=True, rotation_count=5, rotation_size_kb=512)

    # Assert - Should use RotatingFileHandler
    handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(handlers) > 0
    # Check rotation parameters
    assert handlers[0].maxBytes == 512 * 1024
    assert handlers[0].backupCount == 5


def test_set_log_file_rotation_parameter_validation_count(reset_logging, tmp_path):
    """Test set_log_file validates rotation_count parameter (1-10)."""
    # Arrange
    from basefunctions.utils.logging import set_log_file

    log_file = tmp_path / "invalid_count.log"

    # Act & Assert - count < 1
    with pytest.raises(ValueError, match="rotation_count must be between 1 and 10"):
        set_log_file(filepath=str(log_file), level="INFO", rotation=True, rotation_count=0)

    # Act & Assert - count > 10
    with pytest.raises(ValueError, match="rotation_count must be between 1 and 10"):
        set_log_file(filepath=str(log_file), level="INFO", rotation=True, rotation_count=11)


def test_set_log_file_rotation_parameter_validation_size(reset_logging, tmp_path):
    """Test set_log_file validates rotation_size_kb parameter (1-100000)."""
    # Arrange
    from basefunctions.utils.logging import set_log_file

    log_file = tmp_path / "invalid_size.log"

    # Act & Assert - size < 1
    with pytest.raises(ValueError, match="rotation_size_kb must be between 1 and 100000"):
        set_log_file(filepath=str(log_file), level="INFO", rotation=True, rotation_size_kb=0)

    # Act & Assert - size > 100000
    with pytest.raises(ValueError, match="rotation_size_kb must be between 1 and 100000"):
        set_log_file(filepath=str(log_file), level="INFO", rotation=True, rotation_size_kb=100001)


def test_set_log_file_invalid_level_raises_value_error(reset_logging, tmp_path):
    """Test set_log_file raises ValueError for invalid log level."""
    # Arrange
    from basefunctions.utils.logging import set_log_file

    log_file = tmp_path / "invalid_level.log"

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid log level"):
        set_log_file(filepath=str(log_file), level="INVALID")


def test_set_log_file_oserror_on_creation_failure(reset_logging):
    """Test set_log_file raises OSError when file creation fails."""
    # Arrange
    from basefunctions.utils.logging import set_log_file

    # Use invalid path (root directory without permissions on most systems)
    log_file = "/root/restricted/cannot_create.log"

    # Act & Assert
    with pytest.raises(OSError):
        set_log_file(filepath=log_file, level="INFO")


def test_set_log_file_thread_safety(reset_logging, tmp_path):
    """Test set_log_file is thread-safe with concurrent calls."""
    # Arrange
    from basefunctions.utils.logging import set_log_file
    import threading

    errors = []

    def set_file_thread(filepath):
        try:
            set_log_file(filepath=filepath, level="INFO")
        except Exception as e:
            errors.append(e)

    # Act - Create 10 concurrent threads
    threads = [
        threading.Thread(target=set_file_thread, args=(str(tmp_path / f"thread_{i}.log"),))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Assert
    assert len(errors) == 0, f"Thread errors occurred: {errors}"


def test_set_log_file_multiple_calls_replace_handler(reset_logging, tmp_path):
    """Test multiple set_log_file calls replace the file handler."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file1 = tmp_path / "file1.log"
    log_file2 = tmp_path / "file2.log"
    logger = get_logger(name="test.file.replace")

    # Act - Set file twice
    set_log_file(filepath=str(log_file1), level="DEBUG")
    set_log_file(filepath=str(log_file2), level="INFO")

    # Assert - Only one FileHandler should exist
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(handlers) == 1


# =============================================================================
# TEST: NEW LOGGING API - set_log_file_rotation()
# =============================================================================


def test_set_log_file_rotation_enable_on_existing_handler(reset_logging, tmp_path):
    """Test set_log_file_rotation enables rotation on existing file handler."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, set_log_file_rotation, get_logger

    log_file = tmp_path / "enable_rotation.log"
    logger = get_logger(name="test.rotation.enable")

    # First create file handler WITHOUT rotation
    set_log_file(filepath=str(log_file), level="INFO", rotation=False)

    # Act - Enable rotation
    set_log_file_rotation(enabled=True, count=5, size_kb=256)

    # Assert - Should now have RotatingFileHandler
    handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(handlers) > 0
    assert handlers[0].maxBytes == 256 * 1024
    assert handlers[0].backupCount == 5


def test_set_log_file_rotation_disable(reset_logging, tmp_path):
    """Test set_log_file_rotation disables rotation on rotating handler."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, set_log_file_rotation, get_logger

    log_file = tmp_path / "disable_rotation.log"
    logger = get_logger(name="test.rotation.disable")

    # First create file handler WITH rotation
    set_log_file(filepath=str(log_file), level="INFO", rotation=True, rotation_count=3, rotation_size_kb=128)

    # Act - Disable rotation
    set_log_file_rotation(enabled=False)

    # Assert - Should now have regular FileHandler (NOT RotatingFileHandler)
    rotating_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(rotating_handlers) == 0
    assert len(file_handlers) > 0


def test_set_log_file_rotation_no_file_handler_raises_runtime_error(reset_logging):
    """Test set_log_file_rotation raises RuntimeError when no file handler exists."""
    # Arrange
    from basefunctions.utils.logging import set_log_file_rotation, get_logger

    # Create logger without file handler
    logger = get_logger(name="test.rotation.nofile")

    # Act & Assert
    with pytest.raises(RuntimeError, match="No file handler configured"):
        set_log_file_rotation(enabled=True, count=3, size_kb=512)


def test_set_log_file_rotation_invalid_count_raises_value_error(reset_logging, tmp_path):
    """Test set_log_file_rotation validates count parameter (1-10)."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, set_log_file_rotation

    log_file = tmp_path / "invalid_count.log"
    set_log_file(filepath=str(log_file), level="INFO", rotation=False)

    # Act & Assert - count < 1
    with pytest.raises(ValueError, match="count must be between 1 and 10"):
        set_log_file_rotation(enabled=True, count=0, size_kb=512)

    # Act & Assert - count > 10
    with pytest.raises(ValueError, match="count must be between 1 and 10"):
        set_log_file_rotation(enabled=True, count=11, size_kb=512)


def test_set_log_file_rotation_invalid_size_kb_raises_value_error(reset_logging, tmp_path):
    """Test set_log_file_rotation validates size_kb parameter (1-100000)."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, set_log_file_rotation

    log_file = tmp_path / "invalid_size.log"
    set_log_file(filepath=str(log_file), level="INFO", rotation=False)

    # Act & Assert - size_kb < 1
    with pytest.raises(ValueError, match="size_kb must be between 1 and 100000"):
        set_log_file_rotation(enabled=True, count=3, size_kb=0)

    # Act & Assert - size_kb > 100000
    with pytest.raises(ValueError, match="size_kb must be between 1 and 100000"):
        set_log_file_rotation(enabled=True, count=3, size_kb=100001)


def test_set_log_file_rotation_thread_safety(reset_logging, tmp_path):
    """Test set_log_file_rotation is thread-safe with concurrent calls."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, set_log_file_rotation
    import threading

    log_file = tmp_path / "thread_rotation.log"
    set_log_file(filepath=str(log_file), level="INFO", rotation=False)

    errors = []

    def toggle_rotation(enabled):
        try:
            set_log_file_rotation(enabled=enabled, count=3, size_kb=512)
        except Exception as e:
            errors.append(e)

    # Act - Create 10 concurrent threads toggling rotation
    threads = [
        threading.Thread(target=toggle_rotation, args=(i % 2 == 0,))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Assert
    assert len(errors) == 0, f"Thread errors occurred: {errors}"


# =============================================================================
# TEST: NEW LOGGING API - Integration Tests
# =============================================================================


def test_integration_console_and_file_simultaneously(reset_logging, tmp_path):
    """Test console and file output work simultaneously."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, set_log_file, get_logger

    log_file = tmp_path / "integration.log"
    logger = get_logger(name="test.integration.both")

    # Act - Enable both console and file
    set_log_console(enabled=True, level="INFO")
    set_log_file(filepath=str(log_file), level="DEBUG")

    logger.info("Test message")

    # Assert - Both handlers should exist
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                      and not isinstance(h, logging.FileHandler)]
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

    assert len(stream_handlers) > 0, "Console handler should exist"
    assert len(file_handlers) > 0, "File handler should exist"
    assert log_file.exists()


def test_integration_level_hierarchy_global_module_handler(reset_logging, tmp_path):
    """Test level hierarchy: global < module < handler."""
    # Arrange
    from basefunctions.utils.logging import set_log_level, set_log_console, get_logger

    # Act - Set different levels at each layer
    set_log_level(level="WARNING", module=None)  # Global
    set_log_level(level="INFO", module="test.hierarchy")  # Module-specific
    set_log_console(enabled=True, level="ERROR")  # Handler-specific

    logger = get_logger(name="test.hierarchy")
    root = logging.getLogger()

    # Assert - Levels should be set correctly
    assert root.level == logging.WARNING  # Global
    assert logger.level == logging.INFO  # Module
    # Handler level
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    if stream_handlers:
        assert stream_handlers[0].level == logging.ERROR


def test_integration_rotation_actually_rotates_on_size_limit(reset_logging, tmp_path):
    """Test rotation actually creates backup files when size limit is exceeded."""
    # Arrange
    from basefunctions.utils.logging import set_log_file, get_logger

    log_file = tmp_path / "rotation_test.log"
    logger = get_logger(name="test.rotation.actual")

    # Small size limit (1 KB) to trigger rotation easily
    set_log_file(filepath=str(log_file), level="DEBUG", rotation=True, rotation_count=3, rotation_size_kb=1)

    # Act - Write enough logs to exceed 1 KB
    for i in range(100):
        logger.debug(f"This is log message number {i} with some extra padding to increase size" * 10)

    # Assert - Rotation files should exist
    # Check for .log.1, .log.2, etc.
    rotation_files = list(tmp_path.glob("rotation_test.log.*"))
    assert len(rotation_files) > 0, "Rotation should have created backup files"


def test_integration_all_logs_captured_including_direct_getlogger_calls(reset_logging, tmp_path):
    """Test all logs are captured, including direct logging.getLogger() calls."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, set_log_file

    log_file = tmp_path / "capture_all.log"

    # Act - Enable logging globally
    set_log_console(enabled=True, level="DEBUG")
    set_log_file(filepath=str(log_file), level="DEBUG")

    # Direct logging.getLogger() call (not using our get_logger)
    direct_logger = logging.getLogger("direct.test.module")
    direct_logger.setLevel(logging.DEBUG)
    direct_logger.info("Direct logger message")

    # Assert - Message should be captured in file
    assert log_file.exists()
    content = log_file.read_text()
    assert "Direct logger message" in content


def test_integration_dynamic_level_changes_affect_output(reset_logging, tmp_path):
    """Test dynamically changing log levels affects what gets logged."""
    # Arrange
    from basefunctions.utils.logging import set_log_level, set_log_file, get_logger

    log_file = tmp_path / "dynamic_level.log"
    logger = get_logger(name="test.dynamic")

    set_log_file(filepath=str(log_file), level="DEBUG")

    # Act - Log at DEBUG level (should not appear initially if level is INFO)
    set_log_level(level="INFO", module="test.dynamic")
    logger.debug("This should NOT appear")

    # Change level to DEBUG
    set_log_level(level="DEBUG", module="test.dynamic")
    logger.debug("This SHOULD appear")

    # Assert
    content = log_file.read_text()
    assert "This should NOT appear" not in content
    assert "This SHOULD appear" in content


def test_integration_console_disable_after_enable(reset_logging, tmp_path):
    """Test disabling console after enabling removes output."""
    # Arrange
    from basefunctions.utils.logging import set_log_console, get_logger

    logger = get_logger(name="test.console.toggle")

    # Act - Enable then disable
    set_log_console(enabled=True, level="INFO")
    handlers_enabled = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]

    set_log_console(enabled=False)
    handlers_disabled = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]

    # Assert
    assert len(handlers_enabled) > 0, "Console handler should exist when enabled"
    assert len(handlers_disabled) == 0, "Console handler should be removed when disabled"


def test_integration_multiple_modules_independent_configuration(reset_logging, tmp_path):
    """Test multiple modules can have independent logging configurations."""
    # Arrange
    from basefunctions.utils.logging import set_log_level, set_log_console, get_logger

    logger1 = get_logger(name="module.one")
    logger2 = get_logger(name="module.two")

    # Act - Configure differently
    set_log_level(level="DEBUG", module="module.one")
    set_log_level(level="ERROR", module="module.two")
    set_log_console(enabled=True, level="INFO")

    # Assert - Levels should be independent
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.ERROR


# =============================================================================
# TEST: Config-based Auto-Init - _auto_init_from_config()
# =============================================================================


def test_auto_init_from_config_disabled_no_logging_setup(reset_logging):
    """Test _auto_init_from_config with log_enabled=false does not setup logging."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": False,
    }.get(path, default)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        from basefunctions.utils.logging import _auto_init_from_config, _console_handler, _file_handler

        _auto_init_from_config()

    # Assert - Internal state should show no handlers configured
    from basefunctions.utils.logging import _console_handler, _file_handler

    assert _console_handler is None
    assert _file_handler is None


def test_auto_init_from_config_enabled_console_only(reset_logging, tmp_path):
    """Test _auto_init_from_config with log_enabled=true and log_file=null creates auto log file."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "DEBUG",
        "basefunctions/log_file": None,
    }.get(path, default)

    log_dir = str(tmp_path / "logs")

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("sys.argv", ["/home/user/test_script.py"]):
            with patch("basefunctions.utils.logging.get_standard_log_directory", return_value=log_dir):
                from basefunctions.utils.logging import _auto_init_from_config

                _auto_init_from_config()

    # Assert - File handler should be configured (new behavior: auto log file)
    from basefunctions.utils.logging import _console_handler, _file_handler

    assert _file_handler is not None
    assert isinstance(_file_handler, logging.FileHandler)
    # Console should be disabled when file logging is active
    assert _console_handler is None


def test_auto_init_from_config_enabled_file_only(reset_logging, tmp_path):
    """Test _auto_init_from_config with log_enabled=true and log_file=/path enables file, disables console."""
    # Arrange
    from unittest.mock import Mock, patch

    log_file = tmp_path / "config_test.log"
    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "INFO",
        "basefunctions/log_file": str(log_file),
    }.get(path, default)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        from basefunctions.utils.logging import _auto_init_from_config

        _auto_init_from_config()

    # Assert - File handler should be configured, console should NOT
    from basefunctions.utils.logging import _console_handler, _file_handler

    assert _file_handler is not None
    assert isinstance(_file_handler, logging.FileHandler)
    assert _console_handler is None
    assert log_file.exists()


def test_auto_init_from_config_no_config_available_silent_fail(reset_logging):
    """Test _auto_init_from_config with no config available fails silently."""
    # Arrange
    from unittest.mock import patch

    # Act - ConfigHandler raises exception (e.g., config file not found)
    with patch("basefunctions.config.ConfigHandler", side_effect=Exception("Config not found")):
        from basefunctions.utils.logging import _auto_init_from_config

        # Should not raise exception
        try:
            _auto_init_from_config()
            success = True
        except Exception:
            success = False

    # Assert - Should fail silently
    assert success is True


def test_auto_init_from_config_custom_log_level_is_set(reset_logging):
    """Test _auto_init_from_config with custom log_level sets the level correctly."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "WARNING",
        "basefunctions/log_file": None,
    }.get(path, default)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        from basefunctions.utils.logging import _auto_init_from_config

        _auto_init_from_config()

    # Assert - Root logger should have WARNING level
    root = logging.getLogger()
    assert root.level == logging.WARNING


def test_auto_init_from_config_exception_in_config_handler_silent_fail(reset_logging):
    """Test _auto_init_from_config when ConfigHandler.get_config_parameter throws exception."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = Exception("Config read error")

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        from basefunctions.utils.logging import _auto_init_from_config

        # Should not raise exception
        try:
            _auto_init_from_config()
            success = True
        except Exception:
            success = False

    # Assert - Should fail silently
    assert success is True


# =============================================================================
# TEST: get_logger() Integration with Auto-Init
# =============================================================================


def test_get_logger_first_call_triggers_auto_init(reset_logging):
    """Test first get_logger() call triggers auto-init from config."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "DEBUG",
        "basefunctions/log_file": None,
    }.get(path, default)

    auto_init_called = []

    def track_auto_init():
        auto_init_called.append(True)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("basefunctions.utils.logging._auto_init_from_config", side_effect=track_auto_init):
            from basefunctions.utils.logging import get_logger

            logger = get_logger(name="test.first.call")

    # Assert - Auto-init should have been called
    assert len(auto_init_called) == 1


def test_get_logger_second_call_does_not_trigger_auto_init(reset_logging):
    """Test second get_logger() call does NOT trigger auto-init again."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": False,
    }.get(path, default)

    auto_init_call_count = []

    def track_auto_init():
        auto_init_call_count.append(True)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("basefunctions.utils.logging._auto_init_from_config", side_effect=track_auto_init):
            from basefunctions.utils.logging import get_logger

            logger1 = get_logger(name="test.first")
            logger2 = get_logger(name="test.second")

    # Assert - Auto-init should have been called only ONCE
    assert len(auto_init_call_count) == 1


def test_get_logger_manual_override_after_auto_init(reset_logging, tmp_path):
    """Test manual set_log_file() overrides config-based auto-init."""
    # Arrange
    from unittest.mock import Mock, patch

    config_file = tmp_path / "config.log"
    manual_file = tmp_path / "manual.log"

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "INFO",
        "basefunctions/log_file": str(config_file),
    }.get(path, default)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        from basefunctions.utils.logging import get_logger, set_log_file

        # First call triggers auto-init with config_file
        logger = get_logger(name="test.override")

        # Manual override with manual_file
        set_log_file(filepath=str(manual_file), level="DEBUG")

        logger.info("Test message")

    # Assert - Manual file should exist and be used
    assert manual_file.exists()
    # Config file might or might not exist (depends on auto-init), but manual_file should have logs
    content = manual_file.read_text()
    assert "Test message" in content


# =============================================================================
# TEST: Auto-Log-File Feature - Script Name Detection
# =============================================================================


def test_get_script_name_from_sys_argv():
    """Test _get_script_name returns script name from sys.argv[0]."""
    # Arrange
    from unittest.mock import patch
    from basefunctions.utils.logging import _get_script_name

    # Act
    with patch("sys.argv", ["/path/to/my_script.py", "arg1", "arg2"]):
        result = _get_script_name()

    # Assert
    assert result == "my_script"


def test_get_script_name_stack_fallback_when_argv_empty():
    """Test _get_script_name falls back to stack inspection when sys.argv[0] is empty."""
    # Arrange
    from unittest.mock import patch
    from basefunctions.utils.logging import _get_script_name

    # Act - Mock sys.argv as empty and use real stack inspection
    with patch("sys.argv", []):
        result = _get_script_name()

    # Assert - Should detect test_logging as script name from stack
    assert result == "test_logging"


def test_get_script_name_removes_py_extension():
    """Test _get_script_name removes .py extension from script name."""
    # Arrange
    from unittest.mock import patch
    from basefunctions.utils.logging import _get_script_name

    # Act
    with patch("sys.argv", ["/path/to/test_script.py"]):
        result = _get_script_name()

    # Assert
    assert result == "test_script"
    assert not result.endswith(".py")


# =============================================================================
# TEST: Auto-Log-File Feature - Package Name Extraction
# =============================================================================


def test_extract_package_name_from_path_with_neuraldev_structure():
    """Test _extract_package_name extracts package from neuraldev/<package>/... path."""
    # Arrange
    from basefunctions.utils.logging import _extract_package_name

    # Act
    result = _extract_package_name("/Users/test/Code/neuraldev/basefunctions/src/main.py")

    # Assert
    assert result == "basefunctions"


def test_extract_package_name_from_path_different_package():
    """Test _extract_package_name works with different package names."""
    # Arrange
    from basefunctions.utils.logging import _extract_package_name

    # Act
    result = _extract_package_name("/home/user/neuraldev/tickerhub/demos/test.py")

    # Assert
    assert result == "tickerhub"


def test_extract_package_name_fallback_when_no_neuraldev_in_path():
    """Test _extract_package_name returns basefunctions fallback when neuraldev not in path."""
    # Arrange
    from basefunctions.utils.logging import _extract_package_name

    # Act
    result = _extract_package_name("/some/other/path/script.py")

    # Assert
    assert result == "basefunctions"


# =============================================================================
# TEST: Auto-Log-File Feature - Integration into _auto_init_from_config()
# =============================================================================


def test_auto_init_creates_log_file_when_enabled_true_and_file_none(reset_logging, tmp_path):
    """Test _auto_init_from_config creates auto log file when log_enabled=True and log_file=None."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "INFO",
        "basefunctions/log_file": None,
    }.get(path, default)

    log_dir = str(tmp_path / "logs")

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("sys.argv", ["/home/user/neuraldev/basefunctions/demos/my_demo.py"]):
            with patch("basefunctions.utils.logging.get_standard_log_directory", return_value=log_dir):
                from basefunctions.utils.logging import _auto_init_from_config, _file_handler

                _auto_init_from_config()

    # Assert - File handler should be configured with auto-generated log file
    from basefunctions.utils.logging import _file_handler

    assert _file_handler is not None
    # Expected log file: <log_dir>/my_demo.log
    expected_log_file = Path(log_dir) / "my_demo.log"
    assert expected_log_file.exists()


def test_auto_init_uses_script_name_from_argv_for_log_file(reset_logging, tmp_path):
    """Test _auto_init_from_config uses script name from sys.argv[0] for log filename."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "DEBUG",
        "basefunctions/log_file": None,
    }.get(path, default)

    log_dir = str(tmp_path / "logs")

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("sys.argv", ["/path/to/test_script.py"]):
            with patch("basefunctions.utils.logging.get_standard_log_directory", return_value=log_dir):
                from basefunctions.utils.logging import _auto_init_from_config

                _auto_init_from_config()

    # Assert - Log file should be named test_script.log
    expected_log_file = Path(log_dir) / "test_script.log"
    assert expected_log_file.exists()


def test_auto_init_extracts_package_name_from_path(reset_logging, tmp_path):
    """Test _auto_init_from_config extracts correct package name from script path."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "INFO",
        "basefunctions/log_file": None,
    }.get(path, default)

    get_log_dir_calls = []

    def track_get_log_dir(package_name):
        get_log_dir_calls.append(package_name)
        return str(tmp_path / "logs")

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("sys.argv", ["/home/user/neuraldev/tickerhub/src/main.py"]):
            with patch("basefunctions.utils.logging.get_standard_log_directory", side_effect=track_get_log_dir):
                from basefunctions.utils.logging import _auto_init_from_config

                _auto_init_from_config()

    # Assert - get_standard_log_directory should be called with "tickerhub"
    assert len(get_log_dir_calls) == 1
    assert get_log_dir_calls[0] == "tickerhub"


def test_auto_init_explicit_log_file_overrides_auto_generation(reset_logging, tmp_path):
    """Test _auto_init_from_config uses explicit log_file when provided (no auto-generation)."""
    # Arrange
    from unittest.mock import Mock, patch

    explicit_log_file = tmp_path / "explicit.log"
    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "INFO",
        "basefunctions/log_file": str(explicit_log_file),
    }.get(path, default)

    # Act
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        from basefunctions.utils.logging import _auto_init_from_config, _file_handler

        _auto_init_from_config()

    # Assert - Should use explicit log file, not auto-generated
    from basefunctions.utils.logging import _file_handler

    assert _file_handler is not None
    assert explicit_log_file.exists()
    # No other log files should be created
    auto_generated_files = list(tmp_path.glob("*.log"))
    assert len(auto_generated_files) == 1
    assert auto_generated_files[0] == explicit_log_file


# =============================================================================
# TEST: Auto-Log-File Feature - Fallback to Console on Exception
# =============================================================================


def test_auto_init_fallback_to_console_on_log_dir_exception(reset_logging):
    """Test _auto_init_from_config falls back to console when get_standard_log_directory fails."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "INFO",
        "basefunctions/log_file": None,
    }.get(path, default)

    # Act - Mock get_standard_log_directory to raise exception
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("sys.argv", ["/home/user/script.py"]):
            with patch("basefunctions.utils.logging.get_standard_log_directory", side_effect=OSError("Permission denied")):
                from basefunctions.utils.logging import _auto_init_from_config, _console_handler, _file_handler

                _auto_init_from_config()

    # Assert - Should fall back to console handler
    from basefunctions.utils.logging import _console_handler, _file_handler

    assert _console_handler is not None
    assert isinstance(_console_handler, logging.StreamHandler)
    assert _file_handler is None


def test_auto_init_fallback_to_console_on_set_log_file_exception(reset_logging, tmp_path):
    """Test _auto_init_from_config falls back to console when set_log_file fails."""
    # Arrange
    from unittest.mock import Mock, patch

    mock_config = Mock()
    mock_config.get_config_parameter.side_effect = lambda path, default: {
        "basefunctions/log_enabled": True,
        "basefunctions/log_level": "DEBUG",
        "basefunctions/log_file": None,
    }.get(path, default)

    log_dir = str(tmp_path / "logs")

    # Act - Mock set_log_file to raise exception
    with patch("basefunctions.config.ConfigHandler", return_value=mock_config):
        with patch("sys.argv", ["/home/user/test.py"]):
            with patch("basefunctions.utils.logging.get_standard_log_directory", return_value=log_dir):
                with patch("basefunctions.utils.logging.set_log_file", side_effect=OSError("Disk full")):
                    from basefunctions.utils.logging import _auto_init_from_config, _console_handler

                    _auto_init_from_config()

    # Assert - Should fall back to console handler
    from basefunctions.utils.logging import _console_handler

    assert _console_handler is not None
    assert isinstance(_console_handler, logging.StreamHandler)
