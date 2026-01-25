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
 v3.0 : Added module-specific logging control
 v3.1 : Added get_standard_log_directory() with runtime detection
 v3.2 : Added enable_logging() for global logging ON/OFF switch
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import logging
import threading
from pathlib import Path

# Project modules
# NOTE: No imports here - get_runtime_log_path imported locally in function
#       to prevent circular dependency (see get_standard_log_directory)

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_lock = threading.Lock()
_logger_configs: dict[str, dict] = {}
_console_enabled = False
_console_level = "CRITICAL"
_global_file_handler: logging.Handler | None = None

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


def setup_logger(name: str, level: str = "ERROR", file: str | None = None) -> None:
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
        # Close all file handlers before clearing
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
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
            "console_override": None,  # None|True|False - module-specific console control
            "console_level": None,  # None|str - module-specific console level
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
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to create file handler: {e}\n")

        # Add console handler based on global or module-specific settings
        if _should_enable_console_for_module(config):
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
            # Close all file handlers before clearing
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
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

        # Add console handler to all configured loggers (unless module overrides to False)
        for name, config in _logger_configs.items():
            if config.get("console_override") is not False:
                logger = config["logger"]
                _add_console_handler(logger, config)


def disable_console() -> None:
    """
    Disable console output for all modules.
    """
    global _console_enabled

    with _lock:
        _console_enabled = False

        # Remove console handlers from all loggers (unless module overrides to True)
        for name, config in _logger_configs.items():
            if config.get("console_override") is not True:
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
            # Close the old global file handler
            _global_file_handler.close()

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


def _add_console_handler(logger: logging.Logger, config: dict) -> None:
    """Add console handler to logger."""
    # Remove existing console handler
    _remove_console_handler(logger, config)

    # Determine console level (module override > global level > module level)
    module_console_level = config.get("console_level")
    if module_console_level:
        console_level = module_console_level
    elif _console_level:
        console_level = _console_level
    else:
        console_level = config["level"]

    # Add new console handler
    try:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, console_level, logging.CRITICAL))
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        config["console_handler"] = console_handler
    except Exception:
        config["console_handler"] = None


def _remove_console_handler(logger: logging.Logger, config: dict) -> None:
    """Remove console handler from logger."""
    console_handler = config.get("console_handler")
    if console_handler and console_handler in logger.handlers:
        logger.removeHandler(console_handler)
    config["console_handler"] = None


def _should_enable_console_for_module(config: dict) -> bool:
    """
    Check if console should be enabled for this module.

    Parameters
    ----------
    config : Dict
        Module configuration dict

    Returns
    -------
    bool
        True if console should be enabled
    """
    console_override = config.get("console_override")
    if console_override is True:
        return True
    if console_override is False:
        return False
    return _console_enabled


def configure_module_logging(
    name: str,
    level: str | None = None,
    console: bool | None = None,
    console_level: str | None = None,
    file: str | None = None,
) -> None:
    """
    Configure or update logging for specific module at runtime.

    This function allows fine-grained control over logging for individual modules,
    including the ability to override global console settings.

    Parameters
    ----------
    name : str
        Module name (e.g., "basefunctions.http", "basefunctions.events")
    level : str, optional
        Logger level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        If None, keeps existing level or uses ERROR as default.
    console : bool, optional
        Enable console output for this module specifically.
        - True: Force console ON (ignores global disable_console)
        - False: Force console OFF (ignores global enable_console)
        - None: Follow global _console_enabled setting (default)
    console_level : str, optional
        Console output level for this module only.
        If None, uses global _console_level or module level.
    file : str, optional
        File path for this module's output.
        If None, keeps existing file handler or has none.

    Raises
    ------
    ValueError
        If invalid log level provided

    Examples
    --------
    Enable DEBUG logging for http module with console output:

    >>> configure_module_logging("basefunctions.http", level="DEBUG", console=True)

    Enable INFO logging for events module, but only show WARNING+ on console:

    >>> configure_module_logging(
    ...     "basefunctions.events",
    ...     level="INFO",
    ...     console=True,
    ...     console_level="WARNING"
    ... )

    Disable console for specific module (even if globally enabled):

    >>> configure_module_logging("basefunctions.config", console=False)

    Update only console level, keep everything else:

    >>> configure_module_logging("basefunctions.http", console_level="ERROR")
    """
    with _lock:
        # If module not yet configured, set it up first
        if name not in _logger_configs:
            setup_logger(name, level or "ERROR", file)

        config = _logger_configs[name]
        logger = config["logger"]

        # Update logger level if provided
        if level is not None:
            level_upper = level.upper()
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level_upper not in valid_levels:
                raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")
            config["level"] = level_upper
            logger.setLevel(getattr(logging, level_upper))

        # Update console override
        if console is not None:
            config["console_override"] = console

        # Update console level override
        if console_level is not None:
            console_level_upper = console_level.upper()
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if console_level_upper not in valid_levels:
                raise ValueError(f"Invalid console_level: {console_level}. " f"Must be one of {valid_levels}")
            config["console_level"] = console_level_upper

        # Update file handler if provided
        if file is not None:
            # Remove old file handler if exists
            old_file_handler = config.get("file_handler")
            if old_file_handler and old_file_handler in logger.handlers:
                logger.removeHandler(old_file_handler)
                # Close the old file handler
                old_file_handler.close()

            # Add new file handler
            try:
                file_handler = logging.FileHandler(file)
                file_handler.setLevel(getattr(logging, config["level"], logging.ERROR))
                formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                config["file_handler"] = file_handler
                config["file"] = file
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to create file handler for {name}: {e}\n")

        # Re-apply console handler with new settings
        _remove_console_handler(logger, config)
        if _should_enable_console_for_module(config):
            _add_console_handler(logger, config)


def get_module_logging_config(name: str) -> dict | None:
    """
    Get current logging configuration for module.

    Parameters
    ----------
    name : str
        Module name

    Returns
    -------
    dict or None
        Configuration dict with keys: level, console, console_level, file, effective_console
        Returns None if module not configured

    Examples
    --------
    >>> config = get_module_logging_config("basefunctions.http")
    >>> if config:
    ...     print(f"Level: {config['level']}")
    ...     print(f"Console override: {config['console']}")
    ...     print(f"Effectively enabled: {config['effective_console']}")
    """
    with _lock:
        if name not in _logger_configs:
            return None

        config = _logger_configs[name]
        return {
            "level": config["level"],
            "console": config.get("console_override"),
            "console_level": config.get("console_level"),
            "file": config.get("file"),
            "effective_console": _should_enable_console_for_module(config),
        }


def get_standard_log_directory(package_name: str, ensure_exists: bool = True) -> str:
    """
    Get standard log directory for package with optional creation.

    This function automatically detects the runtime environment (development vs deployment)
    and returns the appropriate log directory path. In development, logs are stored in
    <cwd>/logs. In deployment, logs are stored in ~/.neuraldevelopment/logs/<package>/.

    Parameters
    ----------
    package_name : str
        Package name (e.g., "basefunctions", "tickerhub")
    ensure_exists : bool, default True
        Create directory if it doesn't exist

    Returns
    -------
    str
        Full path to package log directory

    Raises
    ------
    OSError
        If directory creation fails when ensure_exists=True

    Examples
    --------
    Get log directory for basefunctions package:

    >>> log_dir = get_standard_log_directory("basefunctions")
    >>> setup_logger(__name__, file=f"{log_dir}/app.log")

    Get log directory without creating it:

    >>> log_dir = get_standard_log_directory("tickerhub", ensure_exists=False)
    """
    # Local import to prevent circular dependency:
    # basefunctions.utils.logging <- basefunctions.runtime.deployment_manager
    # <- basefunctions.utils.logging
    from basefunctions.runtime import get_runtime_log_path

    log_path = get_runtime_log_path(package_name)

    if ensure_exists:
        Path(log_path).mkdir(parents=True, exist_ok=True)

    return log_path


def enable_logging(enabled: bool) -> None:
    """
    Enable or disable logging globally.

    When disabled, the root logger is set to CRITICAL+1 level, effectively
    silencing all logging output across all configured modules. When enabled,
    the root logger is set to DEBUG level, allowing all configured loggers
    to work normally with their individual level settings.

    This function provides a simple global ON/OFF switch for all logging
    without affecting individual logger configurations.

    Parameters
    ----------
    enabled : bool
        True to enable logging globally, False to disable all logging

    Examples
    --------
    Disable all logging output:

    >>> enable_logging(False)

    Re-enable logging with configured levels:

    >>> enable_logging(True)

    Temporarily disable logging for performance-critical sections:

    >>> enable_logging(False)
    >>> # ... performance-critical code ...
    >>> enable_logging(True)
    """
    root = logging.getLogger()
    if enabled:
        # Allow all loggers to work with their configured levels
        root.setLevel(logging.DEBUG)
    else:
        # Silence everything (CRITICAL+1 = effectively silent)
        root.setLevel(logging.CRITICAL + 1)
