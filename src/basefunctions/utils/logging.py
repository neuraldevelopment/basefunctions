"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  logging utilities for basic logging, file logging and rotating file logging

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
LOG_FORMAT = "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------
def setup_basic_logging(level: int = 20) -> None:
    """
    Initialize basic logging to the console.

    Parameters
    ----------
    level : int
        Logging level (default INFO = 20).
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
    )


def setup_file_logging(filepath: str, level: int = 20) -> None:
    """
    Redirect logging output to a file.

    Parameters
    ----------
    filepath : str
        Path to the log file.
    level : int
        Logging level (default INFO = 20).
    """
    file_handler = logging.FileHandler(filepath)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(file_handler)


def setup_rotating_file_logging(
    filepath: str, level: int = 20, max_bytes: int = 10_000_000, backup_count: int = 3
) -> None:
    """
    Redirect logging output to rotating log files.

    Parameters
    ----------
    filepath : str
        Path to the log file.
    level : int
        Logging level (default INFO = 20).
    max_bytes : int
        Maximum size of a log file before rotation.
    backup_count : int
        Number of backup files to keep.
    """
    rotating_handler = RotatingFileHandler(filepath, maxBytes=max_bytes, backupCount=backup_count)
    rotating_handler.setLevel(level)
    rotating_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(rotating_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger by name.

    Parameters
    ----------
    name : str
        Name of the logger.

    Returns
    -------
    logging.Logger
        The logger instance.
    """
    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    """
    Set the global log level.

    Parameters
    ----------
    level : int
        Logging level.
    """
    logging.getLogger().setLevel(level)


def disable_logger(name: str) -> None:
    """
    Disable a specific logger by name.

    Parameters
    ----------
    name : str
        Name of the logger.
    """
    logger = logging.getLogger(name)
    logger.disabled = True
