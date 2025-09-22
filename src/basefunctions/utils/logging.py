"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Simple logging with Python stdlib - KISSS principle

 Log:
 v1.0 : Initial implementation
 v1.1 : Default logging OFF
 v2.0 : Rewritten with stdlib, thread-safe, bulletproof
 v2.1 : Fixed the fucking broken shit
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import logging
import threading
from typing import Optional, Dict, Set

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_lock = threading.Lock()
_logger_configs: Dict[str, Dict] = {}
_console_enabled = False
_console_level = "CRITICAL"
_global_file_handler: Optional[logging.Handler] = None

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# DEFAULT: NO OUTPUT - completely silent
logging.getLogger().setLevel(logging.CRITICAL + 1)
logging.getLogger().handlers.clear()

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class _NullHandler(logging.Handler):
    """Silent handler that does nothing."""

    def emit(self, record):
        pass


def setup_logger(name: str, level: str = "ERROR", file: Optional[str] = None) -> None:
    """
    Enable logging for specific module.

    Parameters
    ----------
    name : str
        Module name (use __name__)
    level : str
        Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    file : str, optional
        File path for logging output
    """
    with _lock:
        # Get or create logger
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(getattr(logging, level.upper(), logging.ERROR))
        logger.propagate = False

        # Only add null handler if NO other handlers will be added
        has_any_handler = bool(file) or _console_enabled or _global_file_handler
        if not has_any_handler:
            logger.addHandler(_NullHandler())

        # Store configuration
        config = {
            "logger": logger,
            "level": level.upper(),
            "file": file,
            "file_handler": None,
            "console_handler": None,
        }

        # Add file handler if specified
        if file:
            try:
                file_handler = logging.FileHandler(file)
                file_handler.setLevel(getattr(logging, level.upper(), logging.ERROR))
                formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                config["file_handler"] = file_handler
            except Exception:
                pass

        # Add console handler if globally enabled
        if _console_enabled:
            _add_console_handler(logger, config)

        # Add global file handler if exists
        if _global_file_handler:
            logger.addHandler(_global_file_handler)

        _logger_configs[name] = config


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for module.

    Parameters
    ----------
    name : str
        Module name (use __name__)

    Returns
    -------
    logging.Logger
        Logger instance for module
    """
    with _lock:
        if name not in _logger_configs:
            # Create silent logger for unconfigured modules
            logger = logging.getLogger(name + "_unconfigured")
            logger.handlers.clear()
            logger.addHandler(_NullHandler())
            logger.propagate = False
            logger.setLevel(logging.CRITICAL + 1)
            return logger

        return _logger_configs[name]["logger"]


def enable_console(level: str = "CRITICAL") -> None:
    """
    Enable console output for all configured modules.

    Parameters
    ----------
    level : str
        Minimum log level for console
    """
    global _console_enabled, _console_level

    with _lock:
        _console_enabled = True
        _console_level = level.upper()

        # Add console handler to all configured loggers
        for name, config in _logger_configs.items():
            logger = config["logger"]
            _add_console_handler(logger, config)


def disable_console() -> None:
    """
    Disable console output for all modules.
    """
    global _console_enabled

    with _lock:
        _console_enabled = False

        # Remove console handlers from all loggers
        for name, config in _logger_configs.items():
            logger = config["logger"]
            _remove_console_handler(logger, config)


def redirect_all_to_file(file: str, level: str = "DEBUG") -> None:
    """
    Redirect all configured modules to single file.

    Parameters
    ----------
    file : str
        File path for all logging output
    level : str
        Minimum log level
    """
    global _global_file_handler

    with _lock:
        # Remove old global file handler
        if _global_file_handler:
            for config in _logger_configs.values():
                logger = config["logger"]
                if _global_file_handler in logger.handlers:
                    logger.removeHandler(_global_file_handler)

        # Create new global file handler
        try:
            _global_file_handler = logging.FileHandler(file)
            _global_file_handler.setLevel(getattr(logging, level.upper(), logging.DEBUG))
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            _global_file_handler.setFormatter(formatter)

            # Add to all configured loggers
            for config in _logger_configs.values():
                logger = config["logger"]
                logger.addHandler(_global_file_handler)
        except Exception:
            _global_file_handler = None


def _add_console_handler(logger: logging.Logger, config: Dict) -> None:
    """Add console handler to logger."""
    # Remove existing console handler
    _remove_console_handler(logger, config)

    # Add new console handler
    try:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, _console_level, logging.CRITICAL))
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        config["console_handler"] = console_handler
    except Exception:
        config["console_handler"] = None


def _remove_console_handler(logger: logging.Logger, config: Dict) -> None:
    """Remove console handler from logger."""
    console_handler = config.get("console_handler")
    if console_handler and console_handler in logger.handlers:
        logger.removeHandler(console_handler)
    config["console_handler"] = None
