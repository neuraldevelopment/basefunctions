"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Simple logging with Loguru - KISSS principle

 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import loguru

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_configured_modules = set()

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Set default console level to CRITICAL only
loguru.logger.remove()
loguru.logger.add(sys.stderr, level="CRITICAL")

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def setup_logger(name: str, level: str = "ERROR", file: str = None) -> None:
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
    if name not in _configured_modules:
        if file:
            loguru.logger.add(file, level=level, filter=lambda record: record["name"] == name)
        _configured_modules.add(name)


def get_logger(name: str):
    """
    Get logger instance for module.

    Parameters
    ----------
    name : str
        Module name (use __name__)

    Returns
    -------
    loguru.logger
        Logger instance bound to module name
    """
    return loguru.logger.bind(name=name)


def disable_console() -> None:
    """
    Disable all console output.
    """
    loguru.logger.remove()


def redirect_all_to_file(file: str, level: str = "DEBUG") -> None:
    """
    Redirect all logging to file.

    Parameters
    ----------
    file : str
        File path for all logging output
    level : str
        Minimum log level
    """
    loguru.logger.add(file, level=level)
