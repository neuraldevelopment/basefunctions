"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Bulletproof logging utilities - prevents duplicate handlers no matter what
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler
import threading

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
LOG_FORMAT = "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_logging_lock = threading.Lock()
_configured_handlers = set()  # Track what we've already set up

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def _clear_duplicate_handlers():
    """
    Nuclear option: clear ALL handlers to prevent any fucking duplicates.
    Called before every setup to ensure clean slate.
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    _configured_handlers.clear()


def _add_handler_safely(handler, handler_type):
    """
    Add handler only if we haven't seen this type before.

    Parameters
    ----------
    handler : logging.Handler
        The handler to add
    handler_type : str
        Type identifier to prevent duplicates
    """
    root_logger = logging.getLogger()

    # Always remove existing handlers of same type first
    for existing_handler in root_logger.handlers[:]:
        if type(existing_handler).__name__ == type(handler).__name__:
            root_logger.removeHandler(existing_handler)

    # Add the new handler
    root_logger.addHandler(handler)
    _configured_handlers.add(handler_type)


def setup_basic_logging(level: int = 20) -> None:
    """
    Initialize basic logging to the console.
    GUARANTEES: No duplicate console output, no matter how often called.

    Parameters
    ----------
    level : int
        Logging level (default INFO = 20)
    """
    with _logging_lock:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        # Add safely (removes any existing console handlers first)
        _add_handler_safely(console_handler, "console")


def setup_file_logging(filepath: str, level: int = 20) -> None:
    """
    Add file logging. Removes any existing file handlers first.
    GUARANTEES: Only ONE file handler, no duplicates.

    Parameters
    ----------
    filepath : str
        Path to the log file
    level : int
        Logging level (default INFO = 20)
    """
    with _logging_lock:
        root_logger = logging.getLogger()
        root_logger.setLevel(min(root_logger.level, level))

        # Create file handler
        file_handler = logging.FileHandler(filepath)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        # Add safely (removes any existing file handlers first)
        _add_handler_safely(file_handler, f"file_{filepath}")


def setup_rotating_file_logging(
    filepath: str, level: int = 20, max_bytes: int = 10_000_000, backup_count: int = 3
) -> None:
    """
    Add rotating file logging. Removes any existing rotating handlers first.
    GUARANTEES: Only ONE rotating handler, no duplicates.

    Parameters
    ----------
    filepath : str
        Path to the log file
    level : int
        Logging level (default INFO = 20)
    max_bytes : int
        Maximum size of a log file before rotation
    backup_count : int
        Number of backup files to keep
    """
    with _logging_lock:
        root_logger = logging.getLogger()
        root_logger.setLevel(min(root_logger.level, level))

        # Create rotating handler
        rotating_handler = RotatingFileHandler(filepath, maxBytes=max_bytes, backupCount=backup_count)
        rotating_handler.setLevel(level)
        rotating_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        # Add safely (removes any existing rotating handlers first)
        _add_handler_safely(rotating_handler, f"rotating_{filepath}")


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger by name. Safe to call multiple times.

    Parameters
    ----------
    name : str
        Name of the logger

    Returns
    -------
    logging.Logger
        The logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    """
    Set the global log level for root logger and all handlers.

    Parameters
    ----------
    level : int
        Logging level
    """
    with _logging_lock:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Also update all existing handlers
        for handler in root_logger.handlers:
            handler.setLevel(level)


def disable_logger(name: str) -> None:
    """
    Disable a specific logger by name.

    Parameters
    ----------
    name : str
        Name of the logger
    """
    logger = logging.getLogger(name)
    logger.disabled = True


def reset_logging() -> None:
    """
    Nuclear reset: clear everything and start fresh.
    Use this if you're really fucked and need to start over.
    """
    with _logging_lock:
        _clear_duplicate_handlers()
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)


def get_handler_info() -> dict:
    """
    Debug function: see what handlers are currently active.

    Returns
    -------
    dict
        Handler information for debugging
    """
    root_logger = logging.getLogger()
    return {
        "handler_count": len(root_logger.handlers),
        "handlers": [type(h).__name__ for h in root_logger.handlers],
        "configured_types": list(_configured_handlers),
        "root_level": root_logger.level,
    }
