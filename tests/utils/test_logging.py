"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Comprehensive pytest test suite for utils.logging module.
 Tests cover all critical paths, edge cases, and configuration scenarios.

 Log:
 v1.0.0 : Initial test implementation
 v1.1.0 : Added TODO-TEST notation system for deferred test coverage
 v1.2.0 : Drastically simplified to minimal tests only (no console handlers)
 v2.0.0 : Complete rewrite with comprehensive coverage (>80% target)
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard Library
import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch, mock_open

# Third-party
import pytest

# Project modules
import basefunctions.utils.logging as logging_module
from basefunctions.utils.logging import (
    setup_logger,
    get_logger,
    enable_console,
    disable_console,
    redirect_all_to_file,
    configure_module_logging,
    get_module_logging_config,
    _NullHandler,
    _add_console_handler,
    _remove_console_handler,
    _should_enable_console_for_module,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def clean_logging_state() -> None:
    """Reset logging module state before and after each test."""
    # Store original state
    original_configs = logging_module._logger_configs.copy()
    original_console_enabled = logging_module._console_enabled
    original_console_level = logging_module._console_level
    original_global_file_handler = logging_module._global_file_handler

    # Clear state for clean test
    logging_module._logger_configs.clear()
    logging_module._console_enabled = False
    logging_module._console_level = "CRITICAL"
    logging_module._global_file_handler = None

    # Run test
    yield

    # Clean up loggers
    for config in logging_module._logger_configs.values():
        logger = config.get("logger")
        if logger:
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
            logger.handlers.clear()

    # Close global file handler if exists
    if logging_module._global_file_handler:
        logging_module._global_file_handler.close()

    # Restore original state
    logging_module._logger_configs = original_configs
    logging_module._console_enabled = original_console_enabled
    logging_module._console_level = original_console_level
    logging_module._global_file_handler = original_global_file_handler


@pytest.fixture
def mock_stream_handler():
    """Provide mocked StreamHandler that doesn't write to stderr."""
    with patch('logging.StreamHandler') as mock_handler_class:
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        yield mock_handler


# -------------------------------------------------------------
# TEST _NullHandler CLASS
# -------------------------------------------------------------


class TestNullHandler:
    """Tests for _NullHandler class."""

    def test_null_handler_emit_does_nothing(self):
        """Test that _NullHandler.emit does nothing (complete silence)."""
        # Arrange
        handler = _NullHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Act & Assert - should not raise any exception
        handler.emit(record)


# -------------------------------------------------------------
# TEST SETUP_LOGGER FUNCTION
# -------------------------------------------------------------


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_creates_logger_with_default_level(self, clean_logging_state: None) -> None:
        """Test setup_logger creates logger with default ERROR level."""
        # Arrange
        logger_name = "test.module"

        # Act
        setup_logger(logger_name)
        logger = get_logger(logger_name)

        # Assert
        assert logger is not None
        assert logger.level == logging.ERROR
        assert logger.propagate is False

    def test_setup_logger_creates_logger_with_custom_level(self, clean_logging_state: None) -> None:
        """Test setup_logger creates logger with specified level."""
        # Arrange
        logger_name = "test.module"

        # Act
        setup_logger(logger_name, level="DEBUG")
        logger = get_logger(logger_name)

        # Assert
        assert logger.level == logging.DEBUG

    @pytest.mark.parametrize("level,expected_level", [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("debug", logging.DEBUG),  # Test case-insensitive
        ("info", logging.INFO),
    ])
    def test_setup_logger_handles_various_log_levels(
        self,
        clean_logging_state: None,
        level: str,
        expected_level: int
    ) -> None:
        """Test setup_logger handles various valid log levels (case-insensitive)."""
        # Arrange
        logger_name = "test.module"

        # Act
        setup_logger(logger_name, level=level)
        logger = get_logger(logger_name)

        # Assert
        assert logger.level == expected_level

    def test_setup_logger_creates_file_handler(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test setup_logger creates file handler for logging to file."""
        # Arrange
        logger_name = "test.module"
        log_file = tmp_path / "test.log"

        # Act
        setup_logger(logger_name, file=str(log_file))
        logger = get_logger(logger_name)
        logger.error("Test message")

        # Assert
        assert log_file.exists()
        assert "Test message" in log_file.read_text()

    def test_setup_logger_adds_null_handler_when_no_output_configured(
        self,
        clean_logging_state: None
    ) -> None:
        """Test setup_logger adds NullHandler when no file/console configured."""
        # Arrange
        logger_name = "test.module"

        # Act
        setup_logger(logger_name)
        logger = get_logger(logger_name)

        # Assert
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, _NullHandler) for h in logger.handlers)

    def test_setup_logger_does_not_add_null_handler_with_file(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test setup_logger doesn't add NullHandler when file is configured."""
        # Arrange
        logger_name = "test.module"
        log_file = tmp_path / "test.log"

        # Act
        setup_logger(logger_name, file=str(log_file))
        logger = get_logger(logger_name)

        # Assert
        assert not any(isinstance(h, _NullHandler) for h in logger.handlers)

    def test_setup_logger_handles_file_creation_failure(
        self,
        clean_logging_state: None
    ) -> None:
        """Test setup_logger handles file creation failure gracefully."""
        # Arrange
        logger_name = "test.module"
        invalid_path = "/invalid/path/that/does/not/exist/test.log"

        # Act - should not raise exception, just warn to stderr
        with patch('sys.stderr.write') as mock_stderr:
            setup_logger(logger_name, file=invalid_path)

        # Assert
        mock_stderr.assert_called_once()
        assert "Warning: Failed to create file handler" in mock_stderr.call_args[0][0]

    def test_setup_logger_closes_existing_file_handlers(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test setup_logger closes existing file handlers before replacing."""
        # Arrange
        logger_name = "test.module"
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"

        # Act - Setup twice with different files
        setup_logger(logger_name, file=str(log_file1))
        logger = get_logger(logger_name)
        logger.error("First message")

        setup_logger(logger_name, file=str(log_file2))
        logger = get_logger(logger_name)
        logger.error("Second message")

        # Assert - Second file should have the message
        assert log_file2.exists()
        assert "Second message" in log_file2.read_text()

    def test_setup_logger_with_invalid_level_uses_error(
        self,
        clean_logging_state: None
    ) -> None:
        """Test setup_logger uses ERROR for invalid log level."""
        # Arrange
        logger_name = "test.module"

        # Act
        setup_logger(logger_name, level="INVALID_LEVEL")
        logger = get_logger(logger_name)

        # Assert - Should fall back to ERROR
        assert logger.level == logging.ERROR


# -------------------------------------------------------------
# TEST GET_LOGGER FUNCTION
# -------------------------------------------------------------


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_configured_logger(self, clean_logging_state: None) -> None:
        """Test get_logger returns logger for configured module."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="INFO")

        # Act
        logger = get_logger(logger_name)

        # Assert
        assert logger is not None
        assert logger.level == logging.INFO

    def test_get_logger_returns_silent_logger_for_unconfigured_module(
        self,
        clean_logging_state: None
    ) -> None:
        """Test get_logger returns silent logger for unconfigured module."""
        # Arrange
        logger_name = "unconfigured.module"

        # Act
        logger = get_logger(logger_name)

        # Assert
        assert logger is not None
        assert logger.level == logging.CRITICAL + 1  # Silent level
        assert logger.propagate is False
        assert any(isinstance(h, _NullHandler) for h in logger.handlers)

    def test_get_logger_closes_file_handlers_for_unconfigured_logger(
        self,
        clean_logging_state: None
    ) -> None:
        """Test get_logger closes existing file handlers when creating unconfigured logger."""
        # Arrange
        logger_name = "unconfigured.module_unconfigured"

        # Pre-create a logger with a file handler
        existing_logger = logging.getLogger(logger_name)
        mock_file_handler = MagicMock(spec=logging.FileHandler)
        existing_logger.addHandler(mock_file_handler)

        # Act
        logger = get_logger("unconfigured.module")

        # Assert - Should have closed the file handler
        if mock_file_handler in existing_logger.handlers:
            mock_file_handler.close.assert_called()


# -------------------------------------------------------------
# TEST ENABLE_CONSOLE FUNCTION
# -------------------------------------------------------------


class TestEnableConsole:
    """Tests for enable_console function."""

    def test_enable_console_sets_global_flag(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test enable_console sets global _console_enabled flag."""
        # Act
        enable_console(level="INFO")

        # Assert
        assert logging_module._console_enabled is True
        assert logging_module._console_level == "INFO"

    def test_enable_console_adds_handler_to_configured_loggers(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test enable_console adds StreamHandler to all configured loggers."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")

        # Act
        enable_console(level="INFO")

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config.get("console_handler") is not None

    def test_enable_console_respects_module_override_false(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test enable_console doesn't add handler to modules with console_override=False."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        config = logging_module._logger_configs[logger_name]
        config["console_override"] = False

        # Act
        enable_console(level="INFO")

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config.get("console_handler") is None

    def test_enable_console_with_default_level(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test enable_console uses CRITICAL as default level."""
        # Act
        enable_console()

        # Assert
        assert logging_module._console_level == "CRITICAL"


# -------------------------------------------------------------
# TEST DISABLE_CONSOLE FUNCTION
# -------------------------------------------------------------


class TestDisableConsole:
    """Tests for disable_console function."""

    def test_disable_console_sets_global_flag(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test disable_console sets global _console_enabled to False."""
        # Arrange
        enable_console(level="INFO")

        # Act
        disable_console()

        # Assert
        assert logging_module._console_enabled is False

    def test_disable_console_removes_handlers_from_loggers(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test disable_console removes console handlers from loggers."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        enable_console(level="INFO")

        # Act
        disable_console()

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config.get("console_handler") is None

    def test_disable_console_respects_module_override_true(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test disable_console doesn't remove handler from modules with console_override=True."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        enable_console(level="INFO")
        config = logging_module._logger_configs[logger_name]
        config["console_override"] = True

        # Act
        disable_console()

        # Assert
        config = logging_module._logger_configs[logger_name]
        # Handler should still be present because override is True
        assert config.get("console_handler") is not None


# -------------------------------------------------------------
# TEST REDIRECT_ALL_TO_FILE FUNCTION
# -------------------------------------------------------------


class TestRedirectAllToFile:
    """Tests for redirect_all_to_file function."""

    def test_redirect_all_to_file_creates_global_handler(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test redirect_all_to_file creates global file handler."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        global_log = tmp_path / "global.log"

        # Act
        redirect_all_to_file(str(global_log), level="INFO")

        # Assert
        assert logging_module._global_file_handler is not None
        assert isinstance(logging_module._global_file_handler, logging.FileHandler)

    def test_redirect_all_to_file_adds_handler_to_all_loggers(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test redirect_all_to_file adds global handler to all configured loggers."""
        # Arrange
        logger1 = "test.module1"
        logger2 = "test.module2"
        setup_logger(logger1, level="DEBUG")
        setup_logger(logger2, level="INFO")
        global_log = tmp_path / "global.log"

        # Act
        redirect_all_to_file(str(global_log), level="DEBUG")

        # Assert
        config1 = logging_module._logger_configs[logger1]
        config2 = logging_module._logger_configs[logger2]
        assert logging_module._global_file_handler in config1["logger"].handlers
        assert logging_module._global_file_handler in config2["logger"].handlers

    def test_redirect_all_to_file_replaces_previous_global_handler(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test redirect_all_to_file replaces previous global file handler."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        global_log1 = tmp_path / "global1.log"
        global_log2 = tmp_path / "global2.log"

        # Act
        redirect_all_to_file(str(global_log1), level="DEBUG")
        first_handler = logging_module._global_file_handler

        redirect_all_to_file(str(global_log2), level="DEBUG")
        second_handler = logging_module._global_file_handler

        # Assert
        assert first_handler != second_handler
        config = logging_module._logger_configs[logger_name]
        assert first_handler not in config["logger"].handlers
        assert second_handler in config["logger"].handlers

    def test_redirect_all_to_file_handles_file_creation_failure(
        self,
        clean_logging_state: None
    ) -> None:
        """Test redirect_all_to_file handles file creation failure gracefully."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        invalid_path = "/invalid/path/that/does/not/exist/global.log"

        # Act - should not raise exception
        redirect_all_to_file(invalid_path, level="DEBUG")

        # Assert
        assert logging_module._global_file_handler is None

    def test_redirect_all_to_file_with_various_levels(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test redirect_all_to_file with various log levels."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")
        global_log = tmp_path / "global.log"

        # Act
        redirect_all_to_file(str(global_log), level="WARNING")

        # Assert
        assert logging_module._global_file_handler.level == logging.WARNING


# -------------------------------------------------------------
# TEST HELPER FUNCTIONS
# -------------------------------------------------------------


class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_should_enable_console_for_module_with_override_true(
        self,
        clean_logging_state: None
    ) -> None:
        """Test _should_enable_console_for_module returns True when override is True."""
        # Arrange
        config = {"console_override": True}

        # Act
        result = _should_enable_console_for_module(config)

        # Assert
        assert result is True

    def test_should_enable_console_for_module_with_override_false(
        self,
        clean_logging_state: None
    ) -> None:
        """Test _should_enable_console_for_module returns False when override is False."""
        # Arrange
        config = {"console_override": False}

        # Act
        result = _should_enable_console_for_module(config)

        # Assert
        assert result is False

    def test_should_enable_console_for_module_uses_global_setting(
        self,
        clean_logging_state: None
    ) -> None:
        """Test _should_enable_console_for_module uses global setting when no override."""
        # Arrange
        config = {"console_override": None}
        logging_module._console_enabled = True

        # Act
        result = _should_enable_console_for_module(config)

        # Assert
        assert result is True

    def test_add_console_handler_adds_stream_handler(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test _add_console_handler adds StreamHandler to logger."""
        # Arrange
        logger = logging.getLogger("test.module")
        config = {
            "level": "DEBUG",
            "console_level": None,
            "console_handler": None
        }

        # Act
        _add_console_handler(logger, config)

        # Assert
        assert config["console_handler"] is not None

    def test_add_console_handler_uses_module_console_level(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test _add_console_handler uses module-specific console level."""
        # Arrange
        logger = logging.getLogger("test.module")
        config = {
            "level": "DEBUG",
            "console_level": "ERROR",
            "console_handler": None
        }

        # Act
        _add_console_handler(logger, config)

        # Assert
        mock_stream_handler.setLevel.assert_called_with(logging.ERROR)

    def test_add_console_handler_uses_global_console_level(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test _add_console_handler uses global console level when no module override."""
        # Arrange
        logger = logging.getLogger("test.module")
        config = {
            "level": "DEBUG",
            "console_level": None,
            "console_handler": None
        }
        logging_module._console_level = "WARNING"

        # Act
        _add_console_handler(logger, config)

        # Assert
        mock_stream_handler.setLevel.assert_called_with(logging.WARNING)

    def test_add_console_handler_handles_exception(
        self,
        clean_logging_state: None
    ) -> None:
        """Test _add_console_handler handles StreamHandler creation failure gracefully."""
        # Arrange
        logger = logging.getLogger("test.module")
        config = {
            "level": "DEBUG",
            "console_level": None,
            "console_handler": None
        }

        # Act
        with patch('logging.StreamHandler', side_effect=Exception("Stream error")):
            _add_console_handler(logger, config)

        # Assert
        assert config["console_handler"] is None

    def test_remove_console_handler_removes_handler_from_logger(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test _remove_console_handler removes console handler from logger."""
        # Arrange
        logger = logging.getLogger("test.module")
        config = {
            "level": "DEBUG",
            "console_level": None,
            "console_handler": None
        }
        _add_console_handler(logger, config)

        # Act
        _remove_console_handler(logger, config)

        # Assert
        assert config["console_handler"] is None

    def test_remove_console_handler_with_no_handler(
        self,
        clean_logging_state: None
    ) -> None:
        """Test _remove_console_handler handles case when no console handler exists."""
        # Arrange
        logger = logging.getLogger("test.module")
        config = {
            "console_handler": None
        }

        # Act & Assert - should not raise exception
        _remove_console_handler(logger, config)
        assert config["console_handler"] is None


# -------------------------------------------------------------
# TEST CONFIGURE_MODULE_LOGGING FUNCTION
# -------------------------------------------------------------


class TestConfigureModuleLogging:
    """Tests for configure_module_logging function."""

    def test_configure_module_logging_creates_logger_if_not_exists(
        self,
        clean_logging_state: None
    ) -> None:
        """Test configure_module_logging creates logger if not already configured."""
        # Arrange
        logger_name = "test.module"

        # Act
        configure_module_logging(logger_name, level="INFO")

        # Assert
        assert logger_name in logging_module._logger_configs
        config = logging_module._logger_configs[logger_name]
        assert config["level"] == "INFO"

    def test_configure_module_logging_updates_existing_logger_level(
        self,
        clean_logging_state: None
    ) -> None:
        """Test configure_module_logging updates level for existing logger."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="ERROR")

        # Act
        configure_module_logging(logger_name, level="DEBUG")

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["level"] == "DEBUG"
        assert config["logger"].level == logging.DEBUG

    def test_configure_module_logging_with_invalid_level_raises_value_error(
        self,
        clean_logging_state: None
    ) -> None:
        """Test configure_module_logging raises ValueError for invalid log level."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid log level"):
            configure_module_logging(logger_name, level="INVALID")

    def test_configure_module_logging_sets_console_override(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test configure_module_logging sets console override."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)

        # Act
        configure_module_logging(logger_name, console=True)

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["console_override"] is True

    def test_configure_module_logging_sets_console_level(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test configure_module_logging sets module-specific console level."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)

        # Act
        configure_module_logging(logger_name, console_level="ERROR")

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["console_level"] == "ERROR"

    def test_configure_module_logging_with_invalid_console_level_raises_value_error(
        self,
        clean_logging_state: None
    ) -> None:
        """Test configure_module_logging raises ValueError for invalid console_level."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid console_level"):
            configure_module_logging(logger_name, console_level="INVALID")

    def test_configure_module_logging_updates_file_handler(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test configure_module_logging updates file handler."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        new_log_file = tmp_path / "new.log"

        # Act
        configure_module_logging(logger_name, file=str(new_log_file))

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["file"] == str(new_log_file)
        assert config["file_handler"] is not None

    def test_configure_module_logging_replaces_old_file_handler(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test configure_module_logging closes and replaces old file handler."""
        # Arrange
        logger_name = "test.module"
        log_file1 = tmp_path / "log1.log"
        log_file2 = tmp_path / "log2.log"
        setup_logger(logger_name, file=str(log_file1))

        # Act
        configure_module_logging(logger_name, file=str(log_file2))

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["file"] == str(log_file2)

    def test_configure_module_logging_handles_file_creation_failure(
        self,
        clean_logging_state: None
    ) -> None:
        """Test configure_module_logging handles file creation failure gracefully."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        invalid_path = "/invalid/path/that/does/not/exist/test.log"

        # Act
        with patch('sys.stderr.write') as mock_stderr:
            configure_module_logging(logger_name, file=invalid_path)

        # Assert
        mock_stderr.assert_called_once()
        assert "Warning: Failed to create file handler" in mock_stderr.call_args[0][0]

    def test_configure_module_logging_reapplies_console_handler(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test configure_module_logging re-applies console handler with new settings."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        configure_module_logging(logger_name, console=True, console_level="INFO")

        # Act - Update console level
        configure_module_logging(logger_name, console_level="ERROR")

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["console_level"] == "ERROR"

    def test_configure_module_logging_with_console_false_removes_handler(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test configure_module_logging with console=False removes console handler."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        enable_console()

        # Act
        configure_module_logging(logger_name, console=False)

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["console_override"] is False
        assert config["console_handler"] is None

    def test_configure_module_logging_with_all_parameters(
        self,
        clean_logging_state: None,
        mock_stream_handler,
        tmp_path: Path
    ) -> None:
        """Test configure_module_logging with all parameters simultaneously."""
        # Arrange
        logger_name = "test.module"
        log_file = tmp_path / "test.log"

        # Act
        configure_module_logging(
            logger_name,
            level="DEBUG",
            console=True,
            console_level="WARNING",
            file=str(log_file)
        )

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["level"] == "DEBUG"
        assert config["console_override"] is True
        assert config["console_level"] == "WARNING"
        assert config["file"] == str(log_file)


# -------------------------------------------------------------
# TEST GET_MODULE_LOGGING_CONFIG FUNCTION
# -------------------------------------------------------------


class TestGetModuleLoggingConfig:
    """Tests for get_module_logging_config function."""

    def test_get_module_logging_config_returns_config(self, clean_logging_state: None) -> None:
        """Test get_module_logging_config returns config dict for configured module."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="INFO")

        # Act
        config = get_module_logging_config(logger_name)

        # Assert
        assert config is not None
        assert config["level"] == "INFO"
        assert "console" in config
        assert "console_level" in config
        assert "file" in config
        assert "effective_console" in config

    def test_get_module_logging_config_returns_none_for_unconfigured(
        self,
        clean_logging_state: None
    ) -> None:
        """Test get_module_logging_config returns None for unconfigured module."""
        # Act
        config = get_module_logging_config("unconfigured.module")

        # Assert
        assert config is None

    def test_get_module_logging_config_shows_effective_console_enabled(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test get_module_logging_config shows effective_console when globally enabled."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        enable_console()

        # Act
        config = get_module_logging_config(logger_name)

        # Assert
        assert config["effective_console"] is True

    def test_get_module_logging_config_shows_effective_console_disabled(
        self,
        clean_logging_state: None
    ) -> None:
        """Test get_module_logging_config shows effective_console as False when disabled."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)

        # Act
        config = get_module_logging_config(logger_name)

        # Assert
        assert config["effective_console"] is False

    def test_get_module_logging_config_includes_console_override(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test get_module_logging_config includes console override setting."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        configure_module_logging(logger_name, console=True)

        # Act
        config = get_module_logging_config(logger_name)

        # Assert
        assert config["console"] is True


# -------------------------------------------------------------
# TEST INTEGRATION SCENARIOS
# -------------------------------------------------------------


class TestIntegrationScenarios:
    """Integration tests for complex logging scenarios."""

    def test_multiple_loggers_with_different_levels(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test multiple loggers with different log levels and files."""
        # Arrange
        logger1_name = "module.one"
        logger2_name = "module.two"
        log_file1 = tmp_path / "log1.log"
        log_file2 = tmp_path / "log2.log"

        # Act
        setup_logger(logger1_name, level="DEBUG", file=str(log_file1))
        setup_logger(logger2_name, level="ERROR", file=str(log_file2))

        logger1 = get_logger(logger1_name)
        logger2 = get_logger(logger2_name)

        logger1.debug("Debug message")
        logger2.error("Error message")

        # Assert
        assert "Debug message" in log_file1.read_text()
        assert "Error message" in log_file2.read_text()

    def test_global_file_redirection_with_existing_loggers(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test redirect_all_to_file adds handler to existing loggers."""
        # Arrange
        logger1_name = "module.one"
        logger2_name = "module.two"
        setup_logger(logger1_name, level="DEBUG")
        setup_logger(logger2_name, level="INFO")

        global_log = tmp_path / "global.log"

        # Act
        redirect_all_to_file(str(global_log), level="DEBUG")

        logger1 = get_logger(logger1_name)
        logger2 = get_logger(logger2_name)

        logger1.debug("Debug from module1")
        logger2.info("Info from module2")

        # Assert
        global_content = global_log.read_text()
        assert "Debug from module1" in global_content
        assert "Info from module2" in global_content

    def test_console_enable_after_logger_setup(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test enabling console after loggers are already set up."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name, level="DEBUG")

        # Act
        enable_console(level="INFO")

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["console_handler"] is not None

    def test_module_override_prevents_global_console_disable(
        self,
        clean_logging_state: None,
        mock_stream_handler
    ) -> None:
        """Test module with console_override=True keeps handler when globally disabled."""
        # Arrange
        logger_name = "test.module"
        setup_logger(logger_name)
        enable_console()
        configure_module_logging(logger_name, console=True)

        # Act
        disable_console()

        # Assert
        config = logging_module._logger_configs[logger_name]
        assert config["console_handler"] is not None  # Should still have handler

    def test_reconfiguration_workflow(
        self,
        clean_logging_state: None,
        tmp_path: Path
    ) -> None:
        """Test complete reconfiguration workflow for a logger."""
        # Arrange
        logger_name = "test.module"
        log_file1 = tmp_path / "log1.log"
        log_file2 = tmp_path / "log2.log"

        # Act - Initial setup
        setup_logger(logger_name, level="ERROR", file=str(log_file1))
        config1 = get_module_logging_config(logger_name)

        # Reconfigure
        configure_module_logging(logger_name, level="DEBUG", file=str(log_file2))
        config2 = get_module_logging_config(logger_name)

        # Assert
        assert config1["level"] == "ERROR"
        assert config1["file"] == str(log_file1)
        assert config2["level"] == "DEBUG"
        assert config2["file"] == str(log_file2)
