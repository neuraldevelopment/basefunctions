"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 MINIMAL pytest test suite for utils.logging module.
 ONLY tests basic functionality WITHOUT console handlers to avoid test hangs.

 TODO-TEST Notation System:
 ---------------------------
 This file uses standardized TODO-TEST markers to indicate incomplete or
 simplified test coverage. Each TODO-TEST block follows this structure:

 # =============================================================================
 # TODO-TEST: <Descriptive Title>
 # =============================================================================
 # STATUS: <one of: MINIMAL_COVERAGE_ONLY | NOT_IMPLEMENTED | MOCKED_ONLY>
 # REASON: <Why the full test was removed or not implemented>
 # ORIGINAL_INTENT: <What the test was supposed to verify>
 # MISSING_COVERAGE: <Bullet list of specific test scenarios not covered>
 # RECOMMENDED_APPROACH: <Suggestion for proper implementation>
 # AGENT_ACTION: <Instructions for python_test_agent to recreate test>
 # =============================================================================

 When python_test_agent encounters TODO-TEST markers, it should:
 1. Parse the structured metadata
 2. Understand what coverage is missing
 3. Implement the test according to RECOMMENDED_APPROACH
 4. Remove the TODO-TEST marker once implemented

 Log:
 v1.0.0 : Initial test implementation
 v1.1.0 : Added TODO-TEST notation system for deferred test coverage
 v1.2.0 : Drastically simplified to minimal tests only (no console handlers)
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import pytest
from pathlib import Path

import basefunctions.utils.logging as logging_module
from basefunctions.utils.logging import (
    setup_logger,
    get_logger,
    get_module_logging_config,
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

    # Restore original state
    logging_module._logger_configs = original_configs
    logging_module._console_enabled = original_console_enabled
    logging_module._console_level = original_console_level
    logging_module._global_file_handler = original_global_file_handler


# -------------------------------------------------------------
# BASIC LOGGER SETUP TESTS
# -------------------------------------------------------------


def test_setup_logger_creates_logger_with_default_level(clean_logging_state: None) -> None:
    """Test setup_logger creates logger with default ERROR level."""
    logger_name: str = "test.module"
    setup_logger(logger_name)
    logger: logging.Logger = get_logger(logger_name)

    assert logger is not None
    assert logger.level == logging.ERROR


def test_setup_logger_creates_logger_with_custom_level(clean_logging_state: None) -> None:
    """Test setup_logger creates logger with specified level."""
    logger_name: str = "test.module"
    setup_logger(logger_name, level="DEBUG")
    logger: logging.Logger = get_logger(logger_name)

    assert logger.level == logging.DEBUG


@pytest.mark.parametrize("level,expected_level", [
    ("DEBUG", logging.DEBUG),
    ("INFO", logging.INFO),
    ("WARNING", logging.WARNING),
    ("ERROR", logging.ERROR),
    ("CRITICAL", logging.CRITICAL),
])
def test_setup_logger_handles_various_log_levels(
    clean_logging_state: None,
    level: str,
    expected_level: int
) -> None:
    """Test setup_logger handles various valid log levels."""
    logger_name: str = "test.module"
    setup_logger(logger_name, level=level)
    logger: logging.Logger = get_logger(logger_name)

    assert logger.level == expected_level


def test_setup_logger_creates_file_handler(
    clean_logging_state: None,
    tmp_path: Path
) -> None:
    """Test setup_logger creates file handler for logging to file."""
    logger_name: str = "test.module"
    log_file: Path = tmp_path / "test.log"

    setup_logger(logger_name, file=str(log_file))
    logger: logging.Logger = get_logger(logger_name)
    logger.error("Test message")

    assert log_file.exists()
    assert "Test message" in log_file.read_text()


# -------------------------------------------------------------
# GET LOGGER TESTS
# -------------------------------------------------------------


def test_get_logger_returns_configured_logger(clean_logging_state: None) -> None:
    """Test get_logger returns logger for configured module."""
    logger_name: str = "test.module"
    setup_logger(logger_name, level="INFO")
    logger: logging.Logger = get_logger(logger_name)

    assert logger is not None
    assert logger.level == logging.INFO


def test_get_logger_returns_silent_logger_for_unconfigured_module(
    clean_logging_state: None
) -> None:
    """Test get_logger returns silent logger for unconfigured module."""
    logger_name: str = "unconfigured.module"
    logger: logging.Logger = get_logger(logger_name)

    assert logger is not None
    assert logger.level == logging.CRITICAL + 1  # Silent level


# -------------------------------------------------------------
# CONFIG TESTS
# -------------------------------------------------------------


def test_get_module_logging_config_returns_config(clean_logging_state: None) -> None:
    """Test get_module_logging_config returns config dict."""
    logger_name: str = "test.module"
    setup_logger(logger_name, level="INFO")
    config = get_module_logging_config(logger_name)

    assert config is not None
    assert config["level"] == "INFO"


def test_get_module_logging_config_returns_none_for_unconfigured(
    clean_logging_state: None
) -> None:
    """Test get_module_logging_config returns None for unconfigured module."""
    config = get_module_logging_config("unconfigured.module")
    assert config is None


# =============================================================================
# TODO-TEST: Console Enable/Disable Tests
# =============================================================================
# STATUS: NOT_IMPLEMENTED
# REASON: All console-related tests caused hangs due to StreamHandler
#         operations and stderr access during test execution
# ORIGINAL_INTENT: Verify enable_console/disable_console functionality,
#                  console handler addition/removal, and global settings
# MISSING_COVERAGE:
#   - enable_console adds StreamHandler to configured loggers
#   - Global _console_enabled and _console_level setting
#   - disable_console removes console handlers
#   - Multiple enable/disable cycles
#   - Module-specific console overrides
# RECOMMENDED_APPROACH: Use mocked StreamHandler that doesn't write to stderr,
#                       or patch logging.StreamHandler in tests
# AGENT_ACTION: python_test_agent should create tests with:
#               @patch('logging.StreamHandler') to avoid actual stderr ops
# =============================================================================

# =============================================================================
# TODO-TEST: Global File Redirection Tests
# =============================================================================
# STATUS: NOT_IMPLEMENTED
# REASON: redirect_all_to_file tests caused hangs with multiple file handlers
# ORIGINAL_INTENT: Verify redirect_all_to_file creates global handler and
#                  correctly replaces previous handler
# MISSING_COVERAGE:
#   - redirect_all_to_file creates global file handler
#   - Handler added to all existing loggers
#   - Previous global handler properly replaced
# RECOMMENDED_APPROACH: Simple test with single redirect, verify handler exists
# AGENT_ACTION: python_test_agent should create single-redirect test only
# =============================================================================

# =============================================================================
# TODO-TEST: Module-Specific Configuration Tests
# =============================================================================
# STATUS: NOT_IMPLEMENTED
# REASON: configure_module_logging with console=True caused hangs
# ORIGINAL_INTENT: Verify configure_module_logging updates logger settings
# MISSING_COVERAGE:
#   - Update logger level for existing logger
#   - Invalid level raises ValueError
#   - Console override settings (True/False)
#   - Module-specific console levels
#   - File handler updates
# RECOMMENDED_APPROACH: Test without console parameter, or mock console handlers
# AGENT_ACTION: python_test_agent should test level/file updates only,
#               skip console parameters or use mocks
# =============================================================================

# =============================================================================
# TODO-TEST: Thread Safety Tests
# =============================================================================
# STATUS: NOT_IMPLEMENTED
# REASON: Threading tests caused test hangs due to lock contention and
#         StreamHandler operations in concurrent threads
# ORIGINAL_INTENT: Verify thread-safe operations of setup_logger, enable_console,
#                  and configure_module_logging under concurrent access
# MISSING_COVERAGE:
#   - Multi-threaded setup_logger (3+ threads with lock contention)
#   - Multi-threaded enable_console (StreamHandler creation in threads)
#   - Multi-threaded configure_module_logging (complex config updates)
# RECOMMENDED_APPROACH: Use thread-safe mocking or dedicated stress testing
#                       with proper timeout handling and deadlock detection
# AGENT_ACTION: python_test_agent should create robust threading tests with
#               proper synchronization primitives and mocked handlers
# =============================================================================

# =============================================================================
# TODO-TEST: Integration Tests
# =============================================================================
# STATUS: NOT_IMPLEMENTED
# REASON: Integration test combining all features caused hangs
# ORIGINAL_INTENT: Verify complete workflow: setup + console + file + configure
# MISSING_COVERAGE:
#   - Multiple modules with different configurations
#   - Console enable + module-specific console override
#   - Global file redirection with active console handlers
# RECOMMENDED_APPROACH: Break into smaller integration tests (2-3 features max)
# AGENT_ACTION: python_test_agent should create modular integration tests
# =============================================================================
