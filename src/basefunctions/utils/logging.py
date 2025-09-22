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
_configured_modules: Set[str] = set()
_loggers: Dict[str, logging.Logger] = {}
_console_handler: Optional[logging.Handler] = None

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# DEFAULT: NO OUTPUT - completely silent
logging.getLogger().setLevel(logging.CRITICAL + 1)

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class _NullHandler(logging.Handler):
    """Silent handler that does nothing."""

    def emit(self, record):
        pass


class _ModuleFilter(logging.Filter):
    """Filter for module-specific logging."""

    def __init__(self, module_name: str):
        super().__init__()
        self.module_name = module_name

    def filter(self, record):
        return record.name.startswith(self.module_name)


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
        if name in _configured_modules:
            return

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper(), logging.ERROR))

        # Always add null handler for fail-safe
        null_handler = _NullHandler()
        logger.addHandler(null_handler)

        # Add file handler if specified
        if file:
            try:
                file_handler = logging.FileHandler(file)
                file_handler.setLevel(getattr(logging, level.upper(), logging.ERROR))
                file_handler.addFilter(_ModuleFilter(name))
                formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception:
                # Fail silently - null handler ensures no crashes
                pass

        # Prevent propagation to root logger
        logger.propagate = False

        _configured_modules.add(name)
        _loggers[name] = logger


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
        if name not in _configured_modules:
            # Return silent logger for unconfigured modules
            silent_logger = logging.getLogger(name + "_silent")
            silent_logger.addHandler(_NullHandler())
            silent_logger.propagate = False
            return silent_logger

        return _loggers.get(name, logging.getLogger(name))


def enable_console(level: str = "CRITICAL") -> None:
    """
    Enable console output for all configured modules.

    Parameters
    ----------
    level : str
        Minimum log level for console
    """
    global _console_handler

    with _lock:
        # Remove existing console handler
        if _console_handler:
            for logger in _loggers.values():
                logger.removeHandler(_console_handler)

        # Add new console handler to all configured loggers
        _console_handler = logging.StreamHandler(sys.stderr)
        _console_handler.setLevel(getattr(logging, level.upper(), logging.CRITICAL))
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        _console_handler.setFormatter(formatter)

        for logger in _loggers.values():
            logger.addHandler(_console_handler)


def disable_console() -> None:
    """
    Disable console output for all modules.
    """
    global _console_handler

    with _lock:
        if _console_handler:
            for logger in _loggers.values():
                logger.removeHandler(_console_handler)
            _console_handler = None


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
    with _lock:
        try:
            global_handler = logging.FileHandler(file)
            global_handler.setLevel(getattr(logging, level.upper(), logging.DEBUG))
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            global_handler.setFormatter(formatter)

            for logger in _loggers.values():
                logger.addHandler(global_handler)
        except Exception:
            # Fail silently
            pass
