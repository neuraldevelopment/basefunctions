"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions - tests

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  unit tests for basefunctions logging interface

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import pytest
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
def test_basic_logging_console_handler():
    basefunctions.setup_basic_logging()
    root_logger = logging.getLogger()
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)


def test_file_logging_creates_logfile(tmp_path):
    logfile = tmp_path / "logfile.log"
    basefunctions.setup_file_logging(str(logfile))

    logger = basefunctions.get_logger("test_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = True
    logger.info("File logging test.")

    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    assert logfile.exists()
    with open(logfile, "r") as f:
        content = f.read()
    assert "File logging test." in content


def test_rotating_file_logging_creates_backups(tmp_path):
    logfile = tmp_path / "rotate.log"
    basefunctions.setup_rotating_file_logging(str(logfile), max_bytes=200, backup_count=1)

    logger = basefunctions.get_logger("test_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = True

    for _ in range(20):
        logger.info("X" * 100)

    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.flush()

    backup_file = tmp_path / "rotate.log.1"
    assert logfile.exists()
    assert backup_file.exists()


def test_get_logger_returns_named_logger():
    logger = basefunctions.get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_set_log_level_sets_global_level():
    basefunctions.set_log_level(logging.DEBUG)
    assert logging.getLogger().level == logging.DEBUG


def test_disable_logger_prevents_output(tmp_path):
    logfile = tmp_path / "disabled.log"
    basefunctions.setup_file_logging(str(logfile))
    logger = basefunctions.get_logger("mute.me")
    logger.info("This should be written")
    basefunctions.disable_logger("mute.me")
    logger.info("This should NOT be written")
    for handler in logger.handlers:
        handler.flush()
    with open(logfile, "r") as f:
        content = f.read()
    assert "This should be written" in content
    assert "This should NOT be written" not in content
