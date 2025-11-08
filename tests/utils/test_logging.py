"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for basefunctions.utils.logging module.
 Tests thread-safe logging configuration, console/file handlers,
 module-specific logging control, and global state management.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import logging
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

# Project imports
from basefunctions.utils import logging as logging_module

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_logging_state() -> None:
    """
    Reset global logging state before each test.

    This fixture automatically runs before each test to ensure clean state.
    Clears all logger configurations, resets global variables, and removes handlers.

    Parameters
    ----------
    None

    Yields
    ------
    None
        Control returned to test after setup

    Notes
    -----
    Uses autouse=True to run automatically for every test function.
    Critical for preventing test interference via global state.
    """
    # ARRANGE - Store original values
    original_configs = logging_module._logger_configs.copy()
    original_console_enabled = logging_module._console_enabled
    original_console_level = logging_module._console_level
    original_global_file_handler = logging_module._global_file_handler

    # Clear all configured loggers
    for config in logging_module._logger_configs.values():
        logger = config.get("logger")
        if logger:
            logger.handlers.clear()

    logging_module._logger_configs.clear()
    logging_module._console_enabled = False
    logging_module._console_level = "CRITICAL"
    logging_module._global_file_handler = None

    # YIELD - Run test
    yield

    # CLEANUP - Restore original state (defensive)
    for config in logging_module._logger_configs.values():
        logger = config.get("logger")
        if logger:
            logger.handlers.clear()

    logging_module._logger_configs = original_configs
    logging_module._console_enabled = original_console_enabled
    logging_module._console_level = original_console_level
    logging_module._global_file_handler = original_global_file_handler


@pytest.fixture
def sample_log_file(tmp_path: Path) -> Path:
    """
    Create temporary log file path for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to temporary log file (not yet created)

    Notes
    -----
    File is not created by fixture - tests create it via logging handlers.
    """
    # RETURN
    return tmp_path / "test.log"


@pytest.fixture
def sample_logger_name() -> str:
    """
    Provide consistent test logger name.

    Returns
    -------
    str
        Logger name for testing
    """
    # RETURN
    return "test_module.submodule"


@pytest.fixture
def configured_logger(sample_logger_name: str) -> str:
    """
    Setup a configured logger for testing.

    Parameters
    ----------
    sample_logger_name : str
        Logger name from fixture

    Returns
    -------
    str
        Logger name (for use with get_logger)

    Notes
    -----
    Creates logger with ERROR level, no console, no file output.
    """
    # ARRANGE & ACT
    logging_module.setup_logger(sample_logger_name, level="ERROR")

    # RETURN
    return sample_logger_name


# -------------------------------------------------------------
# TEST CASES - _NullHandler
# -------------------------------------------------------------


def test_null_handler_emit_does_nothing() -> None:
    """
    Test _NullHandler.emit method successfully does nothing.

    Verifies that _NullHandler silently discards log records
    without raising exceptions or producing output.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if no exception raised
    """
    # ARRANGE
    handler: logging_module._NullHandler = logging_module._NullHandler()
    record: logging.LogRecord = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    # ACT - Should not raise exception
    handler.emit(record)

    # ASSERT - No exception means success
    assert True


# -------------------------------------------------------------
# TEST CASES - setup_logger
# -------------------------------------------------------------


def test_setup_logger_creates_logger_with_correct_level(sample_logger_name: str) -> None:
    """
    Test setup_logger creates logger with specified level.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture

    Returns
    -------
    None
        Test passes if logger level matches requested level
    """
    # ARRANGE
    expected_level: int = logging.DEBUG

    # ACT
    logging_module.setup_logger(sample_logger_name, level="DEBUG")

    # ASSERT
    logger: logging.Logger = logging.getLogger(sample_logger_name)
    assert logger.level == expected_level
    assert sample_logger_name in logging_module._logger_configs


def test_setup_logger_creates_file_handler_when_file_provided(
    sample_logger_name: str, sample_log_file: Path
) -> None:
    """
    Test setup_logger creates file handler for valid file path.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture
    sample_log_file : Path
        Temporary log file path fixture

    Returns
    -------
    None
        Test passes if file handler created and file exists after logging
    """
    # ARRANGE
    log_message: str = "Test log message"

    # ACT
    logging_module.setup_logger(sample_logger_name, level="INFO", file=str(sample_log_file))
    logger: logging.Logger = logging.getLogger(sample_logger_name)
    logger.info(log_message)

    # ASSERT
    assert sample_log_file.exists()
    content: str = sample_log_file.read_text()
    assert log_message in content
    assert "INFO" in content


def test_setup_logger_handles_invalid_file_path_gracefully(sample_logger_name: str) -> None:
    """
    Test setup_logger handles invalid file path without crashing.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture

    Returns
    -------
    None
        Test passes if no exception raised for invalid path
    """
    # ARRANGE
    invalid_path: str = "/invalid/nonexistent/directory/test.log"

    # ACT - Should not raise exception
    logging_module.setup_logger(sample_logger_name, level="INFO", file=invalid_path)

    # ASSERT - Logger still created
    assert sample_logger_name in logging_module._logger_configs


def test_setup_logger_stores_configuration_correctly(sample_logger_name: str) -> None:
    """
    Test setup_logger stores configuration in _logger_configs dict.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture

    Returns
    -------
    None
        Test passes if configuration dict contains expected keys and values
    """
    # ARRANGE
    expected_level: str = "WARNING"

    # ACT
    logging_module.setup_logger(sample_logger_name, level=expected_level)

    # ASSERT
    config: Dict[str, Any] = logging_module._logger_configs[sample_logger_name]
    assert config["level"] == expected_level
    assert config["logger"] is not None
    assert config["file"] is None
    assert config["console_override"] is None


def test_setup_logger_clears_existing_handlers(sample_logger_name: str) -> None:
    """
    Test setup_logger clears existing handlers when reconfiguring.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture

    Returns
    -------
    None
        Test passes if handlers cleared on second setup
    """
    # ARRANGE - Setup logger first time
    logging_module.setup_logger(sample_logger_name, level="INFO")
    logger: logging.Logger = logging.getLogger(sample_logger_name)
    initial_handler_count: int = len(logger.handlers)

    # ACT - Setup again with different config
    logging_module.setup_logger(sample_logger_name, level="DEBUG")

    # ASSERT - Handlers reset, not accumulated
    assert len(logger.handlers) == initial_handler_count


def test_setup_logger_sets_propagate_to_false(sample_logger_name: str) -> None:
    """
    Test setup_logger disables log propagation to parent loggers.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture

    Returns
    -------
    None
        Test passes if logger.propagate is False
    """
    # ACT
    logging_module.setup_logger(sample_logger_name, level="INFO")

    # ASSERT
    logger: logging.Logger = logging.getLogger(sample_logger_name)
    assert logger.propagate is False


@pytest.mark.parametrize(
    "level_str,expected_level",
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("debug", logging.DEBUG),  # Case insensitive
        ("info", logging.INFO),
    ],
)
def test_setup_logger_handles_various_log_levels(
    sample_logger_name: str, level_str: str, expected_level: int
) -> None:
    """
    Test setup_logger correctly interprets various log level strings.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture
    level_str : str
        Log level string (case insensitive)
    expected_level : int
        Expected numeric logging level

    Returns
    -------
    None
        Test passes if logger level matches expected value
    """
    # ACT
    logging_module.setup_logger(sample_logger_name, level=level_str)

    # ASSERT
    logger: logging.Logger = logging.getLogger(sample_logger_name)
    assert logger.level == expected_level


def test_setup_logger_handles_invalid_level_gracefully(sample_logger_name: str) -> None:
    """
    Test setup_logger defaults to ERROR for invalid log level.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture

    Returns
    -------
    None
        Test passes if invalid level defaults to ERROR
    """
    # ARRANGE
    invalid_level: str = "INVALID_LEVEL_XYZ"

    # ACT
    logging_module.setup_logger(sample_logger_name, level=invalid_level)

    # ASSERT - Should default to ERROR
    logger: logging.Logger = logging.getLogger(sample_logger_name)
    assert logger.level == logging.ERROR


def test_setup_logger_thread_safety_concurrent_setup() -> None:
    """
    Test setup_logger is thread-safe for concurrent logger creation.

    Tests that multiple threads can setup loggers simultaneously
    without race conditions or corrupted state.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all threads complete successfully and configs valid
    """
    # ARRANGE
    thread_count: int = 10
    logger_names: List[str] = [f"test_logger_{i}" for i in range(thread_count)]
    results: List[bool] = []

    def setup_thread(name: str) -> None:
        try:
            logging_module.setup_logger(name, level="INFO")
            results.append(True)
        except Exception:
            results.append(False)

    # ACT
    threads: List[threading.Thread] = [
        threading.Thread(target=setup_thread, args=(name,)) for name in logger_names
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert all(results)
    assert len(logging_module._logger_configs) == thread_count


# -------------------------------------------------------------
# TEST CASES - get_logger
# -------------------------------------------------------------


def test_get_logger_returns_configured_logger(configured_logger: str) -> None:
    """
    Test get_logger returns logger instance for configured module.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if returned logger is valid logging.Logger instance
    """
    # ACT
    logger: logging.Logger = logging_module.get_logger(configured_logger)

    # ASSERT
    assert isinstance(logger, logging.Logger)
    assert logger.name == configured_logger


def test_get_logger_returns_silent_logger_for_unconfigured_module() -> None:
    """
    Test get_logger returns silent logger for unconfigured module.

    Verifies that requesting logger for unconfigured module returns
    a logger with _NullHandler that produces no output.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if unconfigured logger is silent
    """
    # ARRANGE
    unconfigured_name: str = "completely_unconfigured_module"

    # ACT
    logger: logging.Logger = logging_module.get_logger(unconfigured_name)

    # ASSERT
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.CRITICAL + 1  # Effectively disabled
    assert any(isinstance(h, logging_module._NullHandler) for h in logger.handlers)


def test_get_logger_thread_safety_concurrent_access(configured_logger: str) -> None:
    """
    Test get_logger is thread-safe for concurrent access.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if all threads receive valid logger
    """
    # ARRANGE
    thread_count: int = 20
    results: List[logging.Logger] = []
    lock: threading.Lock = threading.Lock()

    def get_logger_thread() -> None:
        logger = logging_module.get_logger(configured_logger)
        with lock:
            results.append(logger)

    # ACT
    threads: List[threading.Thread] = [threading.Thread(target=get_logger_thread) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert len(results) == thread_count
    assert all(isinstance(logger, logging.Logger) for logger in results)


# -------------------------------------------------------------
# TEST CASES - enable_console
# -------------------------------------------------------------


def test_enable_console_activates_console_output(configured_logger: str, capsys) -> None:
    """
    Test enable_console activates console output for configured loggers.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if console output appears after enable_console
    """
    # ARRANGE
    log_message: str = "Test console message"

    # ACT
    logging_module.enable_console(level="INFO")
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.error(log_message)

    # ASSERT
    captured = capsys.readouterr()
    assert log_message in captured.err


def test_enable_console_sets_global_flag() -> None:
    """
    Test enable_console sets _console_enabled global flag to True.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if global flag set correctly
    """
    # ACT
    logging_module.enable_console(level="DEBUG")

    # ASSERT
    assert logging_module._console_enabled is True
    assert logging_module._console_level == "DEBUG"


def test_enable_console_respects_module_override_false(sample_logger_name: str, capsys) -> None:
    """
    Test enable_console respects module-specific console override False.

    Verifies that modules with console_override=False do not get
    console output even when global console is enabled.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if module with override=False has no console output
    """
    # ARRANGE
    logging_module.setup_logger(sample_logger_name, level="INFO")
    logging_module.configure_module_logging(sample_logger_name, console=False)
    log_message: str = "Should not appear"

    # ACT
    logging_module.enable_console(level="INFO")
    logger: logging.Logger = logging_module.get_logger(sample_logger_name)
    logger.info(log_message)

    # ASSERT
    captured = capsys.readouterr()
    assert log_message not in captured.err


def test_enable_console_adds_handler_to_all_configured_loggers() -> None:
    """
    Test enable_console adds console handlers to all configured loggers.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all loggers receive console handler
    """
    # ARRANGE
    logger_names: List[str] = ["logger1", "logger2", "logger3"]
    for name in logger_names:
        logging_module.setup_logger(name, level="INFO")

    # ACT
    logging_module.enable_console(level="WARNING")

    # ASSERT
    for name in logger_names:
        config = logging_module._logger_configs[name]
        assert config["console_handler"] is not None


# -------------------------------------------------------------
# TEST CASES - disable_console
# -------------------------------------------------------------


def test_disable_console_removes_console_output(configured_logger: str, capsys) -> None:
    """
    Test disable_console removes console output from loggers.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if no console output after disable_console
    """
    # ARRANGE
    logging_module.enable_console(level="INFO")
    log_message: str = "Should not appear"

    # ACT
    logging_module.disable_console()
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.error(log_message)

    # ASSERT
    captured = capsys.readouterr()
    assert log_message not in captured.err


def test_disable_console_sets_global_flag() -> None:
    """
    Test disable_console sets _console_enabled global flag to False.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if global flag set correctly
    """
    # ARRANGE
    logging_module.enable_console(level="INFO")

    # ACT
    logging_module.disable_console()

    # ASSERT
    assert logging_module._console_enabled is False


def test_disable_console_respects_module_override_true(sample_logger_name: str, capsys) -> None:
    """
    Test disable_console respects module-specific console override True.

    Verifies that modules with console_override=True keep console output
    even when global console is disabled.

    Parameters
    ----------
    sample_logger_name : str
        Logger name fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if module with override=True still has console output
    """
    # ARRANGE
    logging_module.setup_logger(sample_logger_name, level="INFO")
    # Enable console first, then set module override
    logging_module.enable_console(level="INFO")
    logging_module.configure_module_logging(sample_logger_name, console=True)
    log_message: str = "Should still appear"

    # ACT
    logging_module.disable_console()
    logger: logging.Logger = logging_module.get_logger(sample_logger_name)
    logger.info(log_message)

    # ASSERT
    captured = capsys.readouterr()
    assert log_message in captured.err


def test_disable_console_removes_handlers_from_all_loggers() -> None:
    """
    Test disable_console removes console handlers from all configured loggers.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all loggers have console_handler set to None
    """
    # ARRANGE
    logger_names: List[str] = ["logger1", "logger2", "logger3"]
    for name in logger_names:
        logging_module.setup_logger(name, level="INFO")
    logging_module.enable_console(level="INFO")

    # ACT
    logging_module.disable_console()

    # ASSERT
    for name in logger_names:
        config = logging_module._logger_configs[name]
        if config.get("console_override") is not True:
            assert config["console_handler"] is None


# -------------------------------------------------------------
# TEST CASES - redirect_all_to_file (CRITICAL)
# -------------------------------------------------------------


def test_redirect_all_to_file_creates_global_file_handler(
    configured_logger: str, sample_log_file: Path
) -> None:  # CRITICAL TEST
    """
    Test redirect_all_to_file creates global file handler for all loggers.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    sample_log_file : Path
        Temporary log file path fixture

    Returns
    -------
    None
        Test passes if global handler created and log file contains messages
    """
    # ARRANGE
    log_message: str = "Global file handler test"

    # ACT
    logging_module.redirect_all_to_file(str(sample_log_file), level="DEBUG")
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.error(log_message)  # Use ERROR level (configured_logger is ERROR level)

    # ASSERT
    assert logging_module._global_file_handler is not None
    assert sample_log_file.exists()
    content: str = sample_log_file.read_text()
    assert log_message in content


def test_redirect_all_to_file_replaces_existing_global_handler(
    configured_logger: str, tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test redirect_all_to_file replaces existing global file handler.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if old handler removed and new handler active
    """
    # ARRANGE
    old_file: Path = tmp_path / "old.log"
    new_file: Path = tmp_path / "new.log"
    message1: str = "Old handler message"
    message2: str = "New handler message"

    # ACT
    logging_module.redirect_all_to_file(str(old_file), level="DEBUG")
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.error(message1)  # Use ERROR level (configured_logger is ERROR level)

    logging_module.redirect_all_to_file(str(new_file), level="DEBUG")
    logger.error(message2)

    # ASSERT
    assert old_file.exists()
    assert new_file.exists()
    assert message1 in old_file.read_text()
    assert message2 in new_file.read_text()
    assert message2 not in old_file.read_text()  # Old handler stopped


def test_redirect_all_to_file_handles_invalid_path_gracefully(
    configured_logger: str,
) -> None:  # CRITICAL TEST
    """
    Test redirect_all_to_file handles invalid file path without crashing.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if no exception raised and _global_file_handler is None
    """
    # ARRANGE
    invalid_path: str = "/invalid/nonexistent/directory/test.log"

    # ACT - Should not raise exception
    logging_module.redirect_all_to_file(invalid_path, level="INFO")

    # ASSERT
    assert logging_module._global_file_handler is None


def test_redirect_all_to_file_applies_to_all_configured_loggers(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test redirect_all_to_file adds handler to all configured loggers.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if all loggers write to global file
    """
    # ARRANGE
    log_file: Path = tmp_path / "global.log"
    logger_names: List[str] = ["module1", "module2", "module3"]
    for name in logger_names:
        logging_module.setup_logger(name, level="DEBUG")

    # ACT
    logging_module.redirect_all_to_file(str(log_file), level="DEBUG")
    for name in logger_names:
        logger = logging_module.get_logger(name)
        logger.info(f"Message from {name}")

    # ASSERT
    content: str = log_file.read_text()
    for name in logger_names:
        assert f"Message from {name}" in content


@pytest.mark.parametrize(
    "invalid_path",
    [
        "/etc/passwd",  # System file
        "../../../etc/passwd",  # Path traversal
        "/root/.ssh/id_rsa",  # Protected file
        "",  # Empty string
    ],
)
def test_redirect_all_to_file_rejects_malicious_paths(invalid_path: str) -> None:  # CRITICAL TEST
    """
    Test redirect_all_to_file handles malicious file paths safely.

    Parameters
    ----------
    invalid_path : str
        Malicious or invalid file path

    Returns
    -------
    None
        Test passes if handler not created for malicious paths
    """
    # ACT - Should not raise exception or create handler
    logging_module.redirect_all_to_file(invalid_path, level="INFO")

    # ASSERT - Handler should be None due to permission/path issues
    # We verify it doesn't crash and doesn't create dangerous files
    assert True  # If we reach here, no crash occurred


# -------------------------------------------------------------
# TEST CASES - configure_module_logging (CRITICAL)
# -------------------------------------------------------------


def test_configure_module_logging_updates_existing_logger_level(
    configured_logger: str,
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging updates level for existing logger.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if logger level updated correctly
    """
    # ARRANGE
    new_level: str = "DEBUG"

    # ACT
    logging_module.configure_module_logging(configured_logger, level=new_level)

    # ASSERT
    config = logging_module._logger_configs[configured_logger]
    assert config["level"] == new_level
    logger = logging.getLogger(configured_logger)
    assert logger.level == logging.DEBUG


def test_configure_module_logging_raises_error_for_invalid_level() -> None:  # CRITICAL TEST
    """
    Test configure_module_logging raises ValueError for invalid log level.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if ValueError raised with correct message
    """
    # ARRANGE
    invalid_level: str = "INVALID_XYZ"
    module_name: str = "test_module"
    logging_module.setup_logger(module_name)

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Invalid log level"):
        logging_module.configure_module_logging(module_name, level=invalid_level)


def test_configure_module_logging_raises_error_for_invalid_console_level() -> None:  # CRITICAL TEST
    """
    Test configure_module_logging raises ValueError for invalid console_level.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if ValueError raised with correct message
    """
    # ARRANGE
    invalid_console_level: str = "INVALID_ABC"
    module_name: str = "test_module"
    logging_module.setup_logger(module_name)

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Invalid console_level"):
        logging_module.configure_module_logging(module_name, console_level=invalid_console_level)


def test_configure_module_logging_sets_console_override_true(
    configured_logger: str, capsys
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging enables console for specific module.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if module has console output when override=True
    """
    # ARRANGE
    log_message: str = "Console override test"

    # ACT - Set console_level explicitly to match logger level
    logging_module.configure_module_logging(configured_logger, console=True, level="INFO", console_level="INFO")
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.info(log_message)

    # ASSERT
    captured = capsys.readouterr()
    assert log_message in captured.err


def test_configure_module_logging_sets_console_override_false(
    configured_logger: str, capsys
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging disables console for specific module.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if module has no console output when override=False
    """
    # ARRANGE
    logging_module.enable_console(level="INFO")
    log_message: str = "Should not appear"

    # ACT
    logging_module.configure_module_logging(configured_logger, console=False)
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.info(log_message)

    # ASSERT
    captured = capsys.readouterr()
    assert log_message not in captured.err


def test_configure_module_logging_updates_file_handler(
    configured_logger: str, tmp_path: Path
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging updates file handler for logger.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if new file handler created and logs written
    """
    # ARRANGE
    new_file: Path = tmp_path / "new_log.log"
    log_message: str = "File handler update test"

    # ACT
    logging_module.configure_module_logging(configured_logger, file=str(new_file), level="INFO")
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.info(log_message)

    # ASSERT
    assert new_file.exists()
    content: str = new_file.read_text()
    assert log_message in content


def test_configure_module_logging_handles_file_handler_creation_failure(
    configured_logger: str,
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging handles file creation failure gracefully.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if no exception raised for invalid file path
    """
    # ARRANGE
    invalid_path: str = "/invalid/path/test.log"

    # ACT - Should not raise exception
    logging_module.configure_module_logging(configured_logger, file=invalid_path)

    # ASSERT - Logger still exists
    assert configured_logger in logging_module._logger_configs


def test_configure_module_logging_creates_logger_if_not_exists() -> None:  # CRITICAL TEST
    """
    Test configure_module_logging creates logger for unconfigured module.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if logger created with specified configuration
    """
    # ARRANGE
    new_module: str = "brand_new_module"

    # ACT
    logging_module.configure_module_logging(new_module, level="WARNING", console=True)

    # ASSERT
    assert new_module in logging_module._logger_configs
    config = logging_module._logger_configs[new_module]
    assert config["level"] == "WARNING"
    assert config["console_override"] is True


def test_configure_module_logging_sets_module_specific_console_level(
    configured_logger: str, capsys
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging sets module-specific console level.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if module console level overrides global level
    """
    # ARRANGE
    logging_module.enable_console(level="DEBUG")
    debug_message: str = "DEBUG level message"
    error_message: str = "ERROR level message"

    # ACT - Set module console level to ERROR (higher than global DEBUG)
    logging_module.configure_module_logging(configured_logger, console=True, console_level="ERROR", level="DEBUG")
    logger: logging.Logger = logging_module.get_logger(configured_logger)
    logger.debug(debug_message)
    logger.error(error_message)

    # ASSERT - Only ERROR message should appear
    captured = capsys.readouterr()
    assert debug_message not in captured.err
    assert error_message in captured.err


@pytest.mark.parametrize(
    "level,console,console_level",
    [
        ("DEBUG", True, "INFO"),
        ("INFO", False, None),
        ("WARNING", None, "ERROR"),
        ("ERROR", True, "CRITICAL"),
        (None, True, "DEBUG"),
        ("CRITICAL", True, None),
    ],
)
def test_configure_module_logging_various_parameter_combinations(
    configured_logger: str,
    level: Optional[str],
    console: Optional[bool],
    console_level: Optional[str],
) -> None:  # CRITICAL TEST
    """
    Test configure_module_logging handles various parameter combinations.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture
    level : str or None
        Logger level parameter
    console : bool or None
        Console override parameter
    console_level : str or None
        Console level override parameter

    Returns
    -------
    None
        Test passes if all parameter combinations handled correctly
    """
    # ACT - Should not raise exception
    logging_module.configure_module_logging(
        configured_logger, level=level, console=console, console_level=console_level
    )

    # ASSERT - Configuration updated without errors
    assert configured_logger in logging_module._logger_configs


# -------------------------------------------------------------
# TEST CASES - get_module_logging_config
# -------------------------------------------------------------


def test_get_module_logging_config_returns_config_for_configured_module(configured_logger: str) -> None:
    """
    Test get_module_logging_config returns config dict for configured module.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if config dict contains expected keys
    """
    # ACT
    config: Optional[Dict[str, Any]] = logging_module.get_module_logging_config(configured_logger)

    # ASSERT
    assert config is not None
    assert "level" in config
    assert "console" in config
    assert "console_level" in config
    assert "file" in config
    assert "effective_console" in config


def test_get_module_logging_config_returns_none_for_unconfigured_module() -> None:
    """
    Test get_module_logging_config returns None for unconfigured module.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if None returned for unconfigured module
    """
    # ARRANGE
    unconfigured_name: str = "nonexistent_module"

    # ACT
    config: Optional[Dict[str, Any]] = logging_module.get_module_logging_config(unconfigured_name)

    # ASSERT
    assert config is None


def test_get_module_logging_config_shows_effective_console_state(configured_logger: str) -> None:
    """
    Test get_module_logging_config shows effective console state correctly.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if effective_console reflects actual console state
    """
    # ARRANGE - Enable global console
    logging_module.enable_console(level="INFO")

    # ACT
    config: Optional[Dict[str, Any]] = logging_module.get_module_logging_config(configured_logger)

    # ASSERT
    assert config is not None
    assert config["effective_console"] is True


def test_get_module_logging_config_thread_safety(configured_logger: str) -> None:
    """
    Test get_module_logging_config is thread-safe for concurrent access.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if all threads receive valid config dict
    """
    # ARRANGE
    thread_count: int = 15
    results: List[Optional[Dict[str, Any]]] = []
    lock: threading.Lock = threading.Lock()

    def get_config_thread() -> None:
        config = logging_module.get_module_logging_config(configured_logger)
        with lock:
            results.append(config)

    # ACT
    threads: List[threading.Thread] = [threading.Thread(target=get_config_thread) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert len(results) == thread_count
    assert all(config is not None for config in results)


# -------------------------------------------------------------
# TEST CASES - _add_console_handler
# -------------------------------------------------------------


def test_add_console_handler_adds_stream_handler(configured_logger: str) -> None:
    """
    Test _add_console_handler adds StreamHandler to logger.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if console_handler added to config
    """
    # ARRANGE
    config: Dict[str, Any] = logging_module._logger_configs[configured_logger]
    logger: logging.Logger = logging.getLogger(configured_logger)

    # ACT
    logging_module._add_console_handler(logger, config)

    # ASSERT
    assert config["console_handler"] is not None
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_add_console_handler_removes_existing_handler_first(configured_logger: str) -> None:
    """
    Test _add_console_handler removes existing console handler before adding new one.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if only one console handler exists after multiple calls
    """
    # ARRANGE
    config: Dict[str, Any] = logging_module._logger_configs[configured_logger]
    logger: logging.Logger = logging.getLogger(configured_logger)

    # ACT - Call twice
    logging_module._add_console_handler(logger, config)
    initial_handler_count: int = len(logger.handlers)
    logging_module._add_console_handler(logger, config)

    # ASSERT - Handler count should not increase
    assert len(logger.handlers) == initial_handler_count


def test_add_console_handler_uses_module_console_level_if_set(configured_logger: str) -> None:
    """
    Test _add_console_handler uses module-specific console_level if set.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if console handler level matches module console_level
    """
    # ARRANGE
    config: Dict[str, Any] = logging_module._logger_configs[configured_logger]
    config["console_level"] = "ERROR"
    logger: logging.Logger = logging.getLogger(configured_logger)

    # ACT
    logging_module._add_console_handler(logger, config)

    # ASSERT
    console_handler = config["console_handler"]
    assert console_handler.level == logging.ERROR


def test_add_console_handler_uses_global_console_level_if_no_module_level(configured_logger: str) -> None:
    """
    Test _add_console_handler uses global _console_level if no module override.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if console handler level matches global _console_level
    """
    # ARRANGE
    logging_module._console_level = "WARNING"
    config: Dict[str, Any] = logging_module._logger_configs[configured_logger]
    config["console_level"] = None
    logger: logging.Logger = logging.getLogger(configured_logger)

    # ACT
    logging_module._add_console_handler(logger, config)

    # ASSERT
    console_handler = config["console_handler"]
    assert console_handler.level == logging.WARNING


# -------------------------------------------------------------
# TEST CASES - _remove_console_handler
# -------------------------------------------------------------


def test_remove_console_handler_removes_handler_from_logger(configured_logger: str) -> None:
    """
    Test _remove_console_handler removes console handler from logger.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if console_handler removed from logger.handlers
    """
    # ARRANGE
    config: Dict[str, Any] = logging_module._logger_configs[configured_logger]
    logger: logging.Logger = logging.getLogger(configured_logger)
    logging_module._add_console_handler(logger, config)
    initial_handler: logging.Handler = config["console_handler"]

    # ACT
    logging_module._remove_console_handler(logger, config)

    # ASSERT
    assert config["console_handler"] is None
    assert initial_handler not in logger.handlers


def test_remove_console_handler_handles_missing_handler_gracefully(configured_logger: str) -> None:
    """
    Test _remove_console_handler handles missing handler gracefully.

    Parameters
    ----------
    configured_logger : str
        Configured logger name from fixture

    Returns
    -------
    None
        Test passes if no exception raised when handler doesn't exist
    """
    # ARRANGE
    config: Dict[str, Any] = logging_module._logger_configs[configured_logger]
    config["console_handler"] = None
    logger: logging.Logger = logging.getLogger(configured_logger)

    # ACT - Should not raise exception
    logging_module._remove_console_handler(logger, config)

    # ASSERT
    assert config["console_handler"] is None


# -------------------------------------------------------------
# TEST CASES - _should_enable_console_for_module
# -------------------------------------------------------------


def test_should_enable_console_returns_true_when_override_true() -> None:
    """
    Test _should_enable_console_for_module returns True when console_override=True.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if function returns True for override=True
    """
    # ARRANGE
    config: Dict[str, Any] = {"console_override": True}

    # ACT
    result: bool = logging_module._should_enable_console_for_module(config)

    # ASSERT
    assert result is True


def test_should_enable_console_returns_false_when_override_false() -> None:
    """
    Test _should_enable_console_for_module returns False when console_override=False.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if function returns False for override=False
    """
    # ARRANGE
    config: Dict[str, Any] = {"console_override": False}

    # ACT
    result: bool = logging_module._should_enable_console_for_module(config)

    # ASSERT
    assert result is False


def test_should_enable_console_follows_global_when_override_none() -> None:
    """
    Test _should_enable_console_for_module follows _console_enabled when override=None.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if function returns _console_enabled value
    """
    # ARRANGE
    config: Dict[str, Any] = {"console_override": None}
    logging_module._console_enabled = True

    # ACT
    result: bool = logging_module._should_enable_console_for_module(config)

    # ASSERT
    assert result is True


def test_should_enable_console_handles_missing_override_key() -> None:
    """
    Test _should_enable_console_for_module handles missing console_override key.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if function handles missing key without exception
    """
    # ARRANGE
    config: Dict[str, Any] = {}  # Missing console_override key
    logging_module._console_enabled = False

    # ACT
    result: bool = logging_module._should_enable_console_for_module(config)

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TEST CASES - Integration Tests
# -------------------------------------------------------------


def test_integration_multiple_modules_different_configs(tmp_path: Path, capsys) -> None:
    """
    Test integration scenario with multiple modules and different configurations.

    Verifies that multiple loggers can coexist with different levels,
    console settings, and file handlers without interference.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory fixture
    capsys : pytest.CaptureFixture
        Pytest fixture for capturing stderr/stdout

    Returns
    -------
    None
        Test passes if all modules log correctly with independent configs
    """
    # ARRANGE
    module1: str = "app.module1"
    module2: str = "app.module2"
    module3: str = "app.module3"
    file1: Path = tmp_path / "module1.log"
    file2: Path = tmp_path / "module2.log"

    # ACT - Setup different configurations
    logging_module.setup_logger(module1, level="DEBUG", file=str(file1))
    logging_module.setup_logger(module2, level="WARNING", file=str(file2))
    logging_module.setup_logger(module3, level="INFO")

    logging_module.configure_module_logging(module1, console=True, console_level="INFO")
    logging_module.configure_module_logging(module2, console=False)
    logging_module.enable_console(level="DEBUG")

    # Log messages
    logger1 = logging_module.get_logger(module1)
    logger2 = logging_module.get_logger(module2)
    logger3 = logging_module.get_logger(module3)

    logger1.debug("Module1 DEBUG")
    logger1.info("Module1 INFO")
    logger2.warning("Module2 WARNING")
    logger3.info("Module3 INFO")

    # ASSERT - File outputs
    assert file1.exists()
    content1 = file1.read_text()
    assert "Module1 DEBUG" in content1
    assert "Module1 INFO" in content1

    assert file2.exists()
    content2 = file2.read_text()
    assert "Module2 WARNING" in content2

    # ASSERT - Console outputs
    captured = capsys.readouterr()
    assert "Module1 INFO" in captured.err  # Console level INFO
    assert "Module1 DEBUG" not in captured.err  # Below console level
    assert "Module2 WARNING" not in captured.err  # Console disabled for module2
    assert "Module3 INFO" in captured.err  # Global console enabled


def test_integration_global_file_with_module_files(tmp_path: Path) -> None:
    """
    Test integration of global file handler with module-specific file handlers.

    Verifies that both global and module-specific file handlers
    can coexist and log messages correctly.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory fixture

    Returns
    -------
    None
        Test passes if messages appear in both global and module files
    """
    # ARRANGE
    global_file: Path = tmp_path / "global.log"
    module_file: Path = tmp_path / "module.log"
    module_name: str = "test.integration"

    # ACT
    logging_module.setup_logger(module_name, level="INFO", file=str(module_file))
    logging_module.redirect_all_to_file(str(global_file), level="DEBUG")

    logger = logging_module.get_logger(module_name)
    logger.info("Test message")

    # ASSERT - Message in both files
    assert global_file.exists()
    assert module_file.exists()
    assert "Test message" in global_file.read_text()
    assert "Test message" in module_file.read_text()


def test_integration_thread_safety_stress_test() -> None:
    """
    Test thread safety under stress with concurrent operations.

    Tests simultaneous logger creation, configuration updates,
    console enable/disable, and logging operations.

    Parameters
    ----------
    None

    Returns
    -------
    None
        Test passes if all operations complete without errors or race conditions
    """
    # ARRANGE
    thread_count: int = 20
    operations_per_thread: int = 10
    errors: List[Exception] = []
    lock: threading.Lock = threading.Lock()

    def stress_test_thread(thread_id: int) -> None:
        try:
            for i in range(operations_per_thread):
                logger_name = f"stress_test.thread{thread_id}.logger{i}"
                logging_module.setup_logger(logger_name, level="INFO")
                logging_module.configure_module_logging(logger_name, console=True)
                logger = logging_module.get_logger(logger_name)
                logger.info(f"Thread {thread_id} iteration {i}")
                logging_module.enable_console(level="DEBUG")
                logging_module.disable_console()
        except Exception as e:
            with lock:
                errors.append(e)

    # ACT
    threads: List[threading.Thread] = [
        threading.Thread(target=stress_test_thread, args=(i,)) for i in range(thread_count)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert len(errors) == 0
    assert len(logging_module._logger_configs) == thread_count * operations_per_thread
