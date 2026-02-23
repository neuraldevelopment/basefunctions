"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Simple logging with Python stdlib - KISSS principle
 New API: get_logger, set_log_level, set_log_console, set_log_file, set_log_file_rotation

 Log:
 v1.0 : Initial implementation
 v1.1 : Default logging OFF
 v2.0 : Rewritten with stdlib, thread-safe, bulletproof
 v2.1 : Fixed the fucking broken shit
 v3.0 : Added module-specific logging control
 v3.1 : Added get_standard_log_directory() with runtime detection
 v3.2 : Added enable_logging() for global logging ON/OFF switch
 v4.0 : New API - Breaking change, removed old functions
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
import inspect
import logging
import logging.handlers
import sys
import threading
from pathlib import Path

# =============================================================================
# CONSTANTS
# =============================================================================
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# =============================================================================
# GLOBAL STATE
# =============================================================================
_lock = threading.RLock()  # Reentrant lock to prevent deadlock when ConfigHandler calls get_logger()
_root_initialized = False
_config_loaded = False
_console_handler: logging.Handler | None = None
_file_handler: logging.Handler | None = None
_current_log_file: str | None = None
_registered_loggers: set[logging.Logger] = set()

# =============================================================================
# LOGGING
# =============================================================================
logger = logging.getLogger(__name__)

# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get or create a logger with auto-detection of module name.

    This is the primary way to get a logger instance in the new API.
    If name is None, automatically detects the caller's module using inspect.

    Parameters
    ----------
    name : str or None, default None
        Logger name. If None, auto-detects caller module via inspect.currentframe()

    Returns
    -------
    logging.Logger
        Logger instance for the specified or detected module

    Raises
    ------
    RuntimeError
        If auto-detect fails when name=None

    Examples
    --------
    Explicit name:

    >>> logger = get_logger(name="myapp.module")
    >>> logger.info("Hello")

    Auto-detect caller module:

    >>> logger = get_logger()  # Automatically uses __name__ of caller
    >>> logger.debug("Auto-detected module")
    """
    global _root_initialized, _config_loaded, _registered_loggers

    with _lock:
        # Initialize root logger on first call
        if not _root_initialized:
            root = logging.getLogger()
            # Only set ERROR if root level not already configured
            if root.level == logging.NOTSET:
                root.setLevel(logging.ERROR)
            # Clear all handlers (except pytest's LogCaptureHandler)
            for handler in root.handlers[:]:
                if handler.__class__.__name__ not in ["LogCaptureHandler"]:
                    handler.close()
                    root.removeHandler(handler)
            _root_initialized = True

        # Auto-init from config on first call
        if not _config_loaded:
            _config_loaded = True  # Set BEFORE import to prevent re-entry if ConfigHandler calls get_logger()
            _auto_init_from_config()

        # Auto-detect module name if not provided
        if name is None:
            try:
                # Use inspect.stack() for better compatibility with mocking/testing
                stack = inspect.stack()
                if len(stack) < 2:
                    raise RuntimeError("Failed to get caller from stack")
                caller_frame = stack[1].frame
                name = caller_frame.f_globals.get("__name__", "unknown")
                if name == "unknown":
                    raise RuntimeError("Failed to detect module name from caller frame")
            except Exception as e:
                raise RuntimeError(f"Failed to auto-detect module name: {e}") from e

        # Get or create logger
        target_logger = logging.getLogger(name)

        # Register logger for handler management (only add once)
        if target_logger not in _registered_loggers:
            _registered_loggers.add(target_logger)

            # Set logger to DEBUG level ONLY if not explicitly set before
            # (handlers control actual filtering)
            # This ensures logger doesn't block messages before handlers see them
            if target_logger.level == logging.NOTSET:
                target_logger.setLevel(logging.DEBUG)

            # Apply current global handlers to this logger
            if _console_handler is not None and _console_handler not in target_logger.handlers:
                target_logger.addHandler(_console_handler)
            if _file_handler is not None and _file_handler not in target_logger.handlers:
                target_logger.addHandler(_file_handler)

        return target_logger


def set_log_level(level: str, module: str | None = None) -> None:
    """
    Set log level globally or for specific module.

    Parameters
    ----------
    level : str
        Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - case insensitive
    module : str or None, default None
        Module name for module-specific level, or None for global root logger level

    Raises
    ------
    ValueError
        If level is not a valid log level

    Examples
    --------
    Set global log level:

    >>> set_log_level("WARNING")

    Set module-specific level:

    >>> set_log_level("DEBUG", module="myapp.http")
    """
    with _lock:
        # Validate and normalize level
        level_upper = level.upper()
        if level_upper not in VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {level}. Must be one of {VALID_LOG_LEVELS}")

        level_value = getattr(logging, level_upper)

        if module is None:
            # Set global root logger level
            root = logging.getLogger()
            root.setLevel(level_value)
        else:
            # Set module-specific logger level
            target_logger = logging.getLogger(module)
            target_logger.setLevel(level_value)


def set_log_console(enabled: bool, level: str | None = None) -> None:
    """
    Enable or disable console output on all registered loggers and root logger.

    Parameters
    ----------
    enabled : bool
        True to enable console output, False to disable
    level : str or None, default None
        Log level for console handler (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        If None, uses global root logger level.

    Raises
    ------
    ValueError
        If level is provided but not valid

    Examples
    --------
    Enable console with INFO level:

    >>> set_log_console(enabled=True, level="INFO")

    Disable console output:

    >>> set_log_console(enabled=False)

    Enable console with global level:

    >>> set_log_console(enabled=True, level=None)
    """
    global _console_handler, _registered_loggers

    with _lock:
        root = logging.getLogger()

        # Remove existing console handler from all loggers (registered + root)
        if _console_handler is not None:
            for reg_logger in _registered_loggers:
                if _console_handler in reg_logger.handlers:
                    reg_logger.removeHandler(_console_handler)
            if _console_handler in root.handlers:
                root.removeHandler(_console_handler)
            _console_handler.close()
            _console_handler = None

        if enabled:
            # Validate level if provided
            if level is not None:
                level_upper = level.upper()
                if level_upper not in VALID_LOG_LEVELS:
                    raise ValueError(f"Invalid log level: {level}. Must be one of {VALID_LOG_LEVELS}")
                level_value = getattr(logging, level_upper)
            else:
                # Use root logger level
                level_value = root.level

            # Create new console handler
            _console_handler = logging.StreamHandler(sys.stderr)
            _console_handler.setLevel(level_value)
            formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            _console_handler.setFormatter(formatter)

            # Add to root logger (for propagation to all loggers)
            if _console_handler not in root.handlers:
                root.addHandler(_console_handler)

            # Add to all registered loggers (for direct handler access)
            for reg_logger in _registered_loggers:
                if _console_handler not in reg_logger.handlers:
                    reg_logger.addHandler(_console_handler)


def set_log_file(
    filepath: str | Path | None = None,
    level: str = "DEBUG",
    rotation: bool = False,
    rotation_count: int = 3,
    rotation_size_kb: int = 1024,
) -> None:
    """
    Configure file logging with optional rotation.

    Parameters
    ----------
    filepath : str, Path, or None
        Log file path. If None, disables file logging.
    level : str, default "DEBUG"
        Log level for file handler (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    rotation : bool, default False
        Enable log rotation using RotatingFileHandler
    rotation_count : int, default 3
        Number of backup files to keep (1-10)
    rotation_size_kb : int, default 1024
        Max file size in KB before rotation (1-100000)

    Raises
    ------
    ValueError
        If level invalid, or rotation parameters out of range
    OSError
        If file creation or directory creation fails

    Examples
    --------
    Basic file logging:

    >>> set_log_file("app.log", level="INFO")

    With rotation:

    >>> set_log_file("app.log", level="DEBUG", rotation=True, rotation_count=5, rotation_size_kb=2048)

    Disable file logging:

    >>> set_log_file(None)
    """
    global _file_handler, _current_log_file, _registered_loggers

    with _lock:
        root = logging.getLogger()

        # Remove existing file handler from all loggers (registered + root)
        if _file_handler is not None:
            for reg_logger in _registered_loggers:
                if _file_handler in reg_logger.handlers:
                    reg_logger.removeHandler(_file_handler)
            if _file_handler in root.handlers:
                root.removeHandler(_file_handler)
            _file_handler.close()
            _file_handler = None
            _current_log_file = None

        # If filepath is None, just disable file logging
        if filepath is None:
            return

        # Validate level
        level_upper = level.upper()
        if level_upper not in VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {level}. Must be one of {VALID_LOG_LEVELS}")
        level_value = getattr(logging, level_upper)

        # Validate rotation parameters if rotation enabled
        if rotation:
            if not (1 <= rotation_count <= 10):
                raise ValueError(f"rotation_count must be between 1 and 10, got {rotation_count}")
            if not (1 <= rotation_size_kb <= 100000):
                raise ValueError(f"rotation_size_kb must be between 1 and 100000, got {rotation_size_kb}")

        # Create directory if needed
        file_path = Path(filepath)
        if file_path.parent != Path("."):
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file handler (with or without rotation)
        try:
            if rotation:
                max_bytes = rotation_size_kb * 1024
                _file_handler = logging.handlers.RotatingFileHandler(
                    filepath, maxBytes=max_bytes, backupCount=rotation_count
                )
            else:
                _file_handler = logging.FileHandler(filepath)

            _file_handler.setLevel(level_value)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            _file_handler.setFormatter(formatter)

            # Add to root logger (for propagation to all loggers)
            if _file_handler not in root.handlers:
                root.addHandler(_file_handler)

            # Add to all registered loggers (for direct handler access)
            for reg_logger in _registered_loggers:
                if _file_handler not in reg_logger.handlers:
                    reg_logger.addHandler(_file_handler)

            _current_log_file = str(filepath)

        except OSError as e:
            _file_handler = None
            _current_log_file = None
            raise


def set_log_file_rotation(enabled: bool, count: int = 3, size_kb: int = 1024) -> None:
    """
    Toggle rotation on existing file handler.

    This function allows enabling/disabling rotation on an already configured
    file handler without changing the file path.

    Parameters
    ----------
    enabled : bool
        True to enable rotation, False to disable
    count : int, default 3
        Number of backup files to keep (1-10)
    size_kb : int, default 1024
        Max file size in KB before rotation (1-100000)

    Raises
    ------
    RuntimeError
        If no file handler is currently configured
    ValueError
        If count or size_kb parameters are out of valid range

    Examples
    --------
    Enable rotation on existing file handler:

    >>> set_log_file("app.log")
    >>> set_log_file_rotation(enabled=True, count=5, size_kb=2048)

    Disable rotation:

    >>> set_log_file_rotation(enabled=False)
    """
    global _file_handler, _current_log_file, _registered_loggers

    with _lock:
        # Check if file handler exists
        if _file_handler is None or _current_log_file is None:
            raise RuntimeError("No file handler configured. Use set_log_file() first.")

        # Validate parameters if enabling rotation
        if enabled:
            if not (1 <= count <= 10):
                raise ValueError(f"count must be between 1 and 10, got {count}")
            if not (1 <= size_kb <= 100000):
                raise ValueError(f"size_kb must be between 1 and 100000, got {size_kb}")

        root = logging.getLogger()
        current_level = _file_handler.level
        current_formatter = _file_handler.formatter
        filepath = _current_log_file

        # Remove old handler from all loggers (registered + root)
        for reg_logger in _registered_loggers:
            if _file_handler in reg_logger.handlers:
                reg_logger.removeHandler(_file_handler)
        if _file_handler in root.handlers:
            root.removeHandler(_file_handler)
        _file_handler.close()

        # Create new handler based on enabled flag
        try:
            if enabled:
                max_bytes = size_kb * 1024
                _file_handler = logging.handlers.RotatingFileHandler(
                    filepath, maxBytes=max_bytes, backupCount=count
                )
            else:
                _file_handler = logging.FileHandler(filepath)

            _file_handler.setLevel(current_level)
            if current_formatter:
                _file_handler.setFormatter(current_formatter)

            # Add to root logger
            if _file_handler not in root.handlers:
                root.addHandler(_file_handler)

            # Add to all registered loggers
            for reg_logger in _registered_loggers:
                if _file_handler not in reg_logger.handlers:
                    reg_logger.addHandler(_file_handler)

        except OSError as e:
            _file_handler = None
            _current_log_file = None
            raise


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
    >>> set_log_file(f"{log_dir}/app.log")

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


# =============================================================================
# INTERNAL FUNCTIONS - State Management
# =============================================================================


def _auto_init_from_config() -> None:
    """
    Auto-initialize logging from ConfigHandler.

    Reads configuration from basefunctions/log_* parameters and sets up logging:
    - Console output (if log_enabled=True and log_file=None)
    - File output (if log_enabled=True and log_file is set)
    - Log level (global)

    Config Parameters
    -----------------
    basefunctions/log_enabled : bool, default False
        Master switch for logging system

    basefunctions/log_level : str, default "INFO"
        Global log level: DEBUG, INFO, WARNING, ERROR, CRITICAL

    basefunctions/log_file : str | None, default None
        Log file path. If None, uses console output. If set, uses file output only.

    Behavior
    --------
    - Silent operation: No exceptions raised if config unavailable
    - If log_enabled=False: Returns immediately (no logging setup)
    - If log_enabled=True + log_file=None: Console logging
    - If log_enabled=True + log_file="/path": File logging (console disabled)
    - Uses existing set_log_level(), set_log_console(), set_log_file() functions

    Notes
    -----
    - Thread-safe via existing _lock mechanism in called functions
    - Called automatically by get_logger() on first invocation
    """
    try:
        from basefunctions.config import ConfigHandler

        config = ConfigHandler()

        # Read config parameters with defaults
        log_enabled = config.get_config_parameter("basefunctions/log_enabled", False)
        log_level = config.get_config_parameter("basefunctions/log_level", "INFO")
        log_file = config.get_config_parameter("basefunctions/log_file", None)

        # If logging disabled, return immediately
        if not log_enabled:
            return

        # Set global log level
        set_log_level(level=log_level, module=None)

        # Configure output based on log_file
        if log_file is None:
            # Console logging
            set_log_console(enabled=True, level=log_level)
        else:
            # File logging (console disabled)
            set_log_console(enabled=False)
            set_log_file(filepath=log_file, level=log_level)

    except Exception:
        # Silent fail - no exceptions raised if config unavailable
        pass


def _reset_logging_state() -> None:
    """
    Reset all global logging state (for testing).

    This is an internal function used by tests to reset the logging state
    between test runs. Should not be used in production code.
    """
    global _root_initialized, _config_loaded, _console_handler, _file_handler, _current_log_file, _registered_loggers

    with _lock:
        # Close and remove handlers
        root = logging.getLogger()

        if _console_handler is not None:
            if _console_handler in root.handlers:
                root.removeHandler(_console_handler)
            for logger in _registered_loggers:
                if _console_handler in logger.handlers:
                    logger.removeHandler(_console_handler)
            _console_handler.close()

        if _file_handler is not None:
            if _file_handler in root.handlers:
                root.removeHandler(_file_handler)
            for logger in _registered_loggers:
                if _file_handler in logger.handlers:
                    logger.removeHandler(_file_handler)
            _file_handler.close()

        # Reset global state
        _root_initialized = False
        _config_loaded = False
        _console_handler = None
        _file_handler = None
        _current_log_file = None
        _registered_loggers.clear()

        # Reset root logger level
        root.setLevel(logging.ERROR)


# =============================================================================
# DEPRECATED FUNCTIONS - Legacy API (v3.x)
# =============================================================================


def setup_logger(name: str, level: str = "ERROR", file: str | None = None) -> None:
    """
    DEPRECATED: Use get_logger() + set_log_level() + set_log_file() instead.

    This function is kept for backward compatibility only.
    """
    import warnings

    warnings.warn(
        "setup_logger() is deprecated. Use get_logger() + set_log_level() + set_log_file() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Backward compatibility: call new API
    set_log_level(level=level, module=name)

    if file is not None:
        set_log_file(filepath=file, level=level)


def enable_console(level: str = "CRITICAL") -> None:
    """
    DEPRECATED: Use set_log_console(enabled=True, level=...) instead.
    """
    import warnings

    warnings.warn(
        "enable_console() is deprecated. Use set_log_console(enabled=True, level=...) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    set_log_console(enabled=True, level=level)


def disable_console() -> None:
    """
    DEPRECATED: Use set_log_console(enabled=False) instead.
    """
    import warnings

    warnings.warn(
        "disable_console() is deprecated. Use set_log_console(enabled=False) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    set_log_console(enabled=False)


def redirect_all_to_file(file: str, level: str = "DEBUG") -> None:
    """
    DEPRECATED: Use set_log_file(filepath=..., level=...) instead.
    """
    import warnings

    warnings.warn(
        "redirect_all_to_file() is deprecated. Use set_log_file(filepath=..., level=...) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    set_log_file(filepath=file, level=level)


def configure_module_logging(
    name: str,
    level: str | None = None,
    console: bool | None = None,
    console_level: str | None = None,
    file: str | None = None,
) -> None:
    """
    DEPRECATED: Use set_log_level() + set_log_console() + set_log_file() instead.
    """
    import warnings

    warnings.warn(
        "configure_module_logging() is deprecated. Use set_log_level() + set_log_console() + set_log_file() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Legacy behavior: just return without doing anything
    pass


def get_module_logging_config(name: str) -> dict | None:
    """
    DEPRECATED: No replacement in new API.
    """
    import warnings

    warnings.warn(
        "get_module_logging_config() is deprecated. No replacement in new API.",
        DeprecationWarning,
        stacklevel=2,
    )
    return None


def enable_logging(enabled: bool) -> None:
    """
    DEPRECATED: Use set_log_level() to control logging levels instead.
    """
    import warnings

    warnings.warn(
        "enable_logging() is deprecated. Use set_log_level() to control logging levels instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if enabled:
        set_log_level("DEBUG", module=None)
    else:
        set_log_level("CRITICAL", module=None)
