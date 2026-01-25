"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  A simple framework for base functionalities in Python,

  including thread and process-based task pools, configuration,

  I/O utilities, decorators, observer pattern, and secure storage.

=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# Decorators
# -------------------------------------------------------------
from basefunctions.utils.decorators import (
    function_timer,
    singleton,
    auto_property,
    assert_non_null_args,
    cache_results,
    catch_exceptions,
    profile_memory,
    retry_on_exception,
    suppress,
    thread_safe,
    warn_if_slow,
)

# -------------------------------------------------------------
# Logging
# -------------------------------------------------------------
from basefunctions.utils.logging import (
    setup_logger,
    get_logger,
    enable_console,
    disable_console,
    redirect_all_to_file,
    get_standard_log_directory,
    enable_logging,
)

# -------------------------------------------------------------
# Time utils
# -------------------------------------------------------------
from basefunctions.utils.time_utils import (
    now_utc,
    now_local,
    utc_timestamp,
    format_iso,
    parse_iso,
    to_timezone,
    datetime_to_str,
    str_to_datetime,
    timestamp_to_datetime,
    datetime_to_timestamp,
)

# -------------------------------------------------------------
# CLI Functions
# -------------------------------------------------------------
from basefunctions.cli.argument_parser import ArgumentParser
from basefunctions.cli.base_command import BaseCommand
from basefunctions.cli.cli_application import CLIApplication
from basefunctions.cli.command_metadata import ArgumentSpec, CommandMetadata
from basefunctions.cli.command_registry import CommandRegistry
from basefunctions.cli.completion_handler import (
    CompletionHandler,
    setup_completion,
    cleanup_completion,
)
from basefunctions.cli.context_manager import ContextManager
from basefunctions.cli.help_formatter import HelpFormatter
from basefunctions.cli.output_formatter import (
    OutputFormatter,
    show_header,
    show_progress,
    show_result,
)
from basefunctions.utils.progress_tracker import ProgressTracker, AliveProgressTracker


# -------------------------------------------------------------
# Runtime Functions
# -------------------------------------------------------------
from basefunctions.runtime import (
    get_runtime_path,
    get_runtime_component_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path,
    get_runtime_completion_path,
    create_bootstrap_package_structure,
    create_full_package_structure,
    ensure_bootstrap_package_structure,
    create_root_structure,
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories,
    get_deployment_path,
    find_development_path,
    DeploymentManager,
    DeploymentError,
    VenvUtils,
    VenvUtilsError,
    version,
    versions,
)

# -------------------------------------------------------------
# IO Functions
# -------------------------------------------------------------
from basefunctions.io.filefunctions import (
    check_if_exists,
    check_if_file_exists,
    check_if_dir_exists,
    is_file,
    is_directory,
    get_file_name,
    get_file_extension,
    get_extension,
    get_base_name,
    get_base_name_prefix,
    get_path_name,
    get_parent_path_name,
    get_home_path,
    get_path_without_extension,
    get_current_directory,
    set_current_directory,
    rename_file,
    remove_file,
    create_directory,
    remove_directory,
    create_file_list,
    norm_path,
)

from basefunctions.io.output_redirector import (
    OutputTarget,
    OutputRedirector,
    FileTarget,
    DatabaseTarget,
    MemoryTarget,
    ThreadSafeOutputRedirector,
    redirect_output,
)

# Serializer imports
from basefunctions.io.serializer import (
    SerializerFactory,
    Serializer,
    JSONSerializer,
    PickleSerializer,
    YAMLSerializer,
    MessagePackSerializer,
    SerializationError,
    UnsupportedFormatError,
    serialize,
    deserialize,
    to_file,
    from_file,
)

# -------------------------------------------------------------
# OHLCV Generator
# -------------------------------------------------------------
from basefunctions.utils.ohlcv_generator import OHLCVGenerator

# -------------------------------------------------------------
# Cache Manager imports
# -------------------------------------------------------------
from basefunctions.utils.cache_manager import (
    CacheManager,
    CacheFactory,
    CacheBackend,
    MemoryBackend,
    DatabaseBackend,
    FileBackend,
    MultiLevelBackend,
    CacheError,
    CacheBackendError,
    get_cache,
)

# -------------------------------------------------------------
# Demo runner
# -------------------------------------------------------------
from basefunctions.utils.demo_runner import DemoRunner, run, test

# -------------------------------------------------------------
# Observer & Observable
# -------------------------------------------------------------
from basefunctions.utils.observer import Observer, Observable

# -------------------------------------------------------------
# Protocols (all consolidated in centralized protocols/ directory)
# -------------------------------------------------------------
from basefunctions.protocols import KPIProvider, MetricsSource

# -------------------------------------------------------------
# KPI System
# -------------------------------------------------------------
from basefunctions.kpi import KPIProvider, KPICollector, export_to_dataframe

# -------------------------------------------------------------
# Config- & SecretHandler
# -------------------------------------------------------------
from basefunctions.config.config_handler import ConfigHandler
from basefunctions.config.secret_handler import SecretHandler

# -------------------------------------------------------------
# EVENT DEFINITIONS
# -------------------------------------------------------------
from basefunctions.events.event_exceptions import (
    EventValidationError,
    EventConnectionError,
    EventExecutionError,
    EventShutdownError,
    InvalidEventError,
    NoHandlerAvailableError,
)
from basefunctions.events.event_context import EventContext
from basefunctions.events.event import (
    Event,
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET,
    EXECUTION_MODE_CMD,
)
from basefunctions.events.event_handler import (
    EventHandler,
    EventResult,
    DefaultCmdHandler,
    CoreletHandle,
    CoreletForwardingHandler,
    register_internal_handlers,
)

from basefunctions.events.timer_thread import TimerThread

# Event Management
from basefunctions.events.event_factory import EventFactory

# Worker System
from basefunctions.events.corelet_worker import CoreletWorker, worker_main

from basefunctions.events.event_bus import (
    EventBus,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_PRIORITY,
    INTERNAL_CMD_EXECUTION_EVENT,
    INTERNAL_CORELET_FORWARDING_EVENT,
    INTERNAL_SHUTDOWN_EVENT,
)

# -------------------------------------------------------------
# PANDAS DEFINITIONS
# -------------------------------------------------------------
# NOTE: Pandas accessors are registered lazily to avoid import-time dependencies
# Import manually: from basefunctions.pandas.accessors import PandasDataFrame, PandasSeries
from basefunctions.pandas.accessors import PandasDataFrame, PandasSeries

# -------------------------------------------------------------
# HTTP CLIENT DEFINITIONS
# -------------------------------------------------------------
from basefunctions.http.http_client import HttpClient
from basefunctions.http.http_client_handler import (
    HttpClientHandler,
    register_http_handlers,
)

# -------------------------------------------------------------
# Subpackage Imports (Framework-Style)
# -------------------------------------------------------------
# Import subpackages AFTER all other imports to avoid circular imports
from basefunctions import cli
from basefunctions import config
from basefunctions import events
from basefunctions import http
from basefunctions import io
from basefunctions import kpi
from basefunctions import pandas
from basefunctions import runtime
from basefunctions import utils

# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------
__all__ = [
    # Decorators
    "function_timer",
    "singleton",
    "auto_property",
    "assert_non_null_args",
    "cache_results",
    "catch_exceptions",
    "profile_memory",
    "retry_on_exception",
    "suppress",
    "thread_safe",
    "warn_if_slow",
    # Logging
    "setup_logger",
    "get_logger",
    "enable_console",
    "disable_console",
    "redirect_all_to_file",
    "get_standard_log_directory",
    "enable_logging",
    # Time utils
    "now_utc",
    "now_local",
    "utc_timestamp",
    "format_iso",
    "parse_iso",
    "to_timezone",
    "datetime_to_str",
    "str_to_datetime",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    # CLI Framework
    "ArgumentParser",
    "BaseCommand",
    "CLIApplication",
    "ArgumentSpec",
    "CommandMetadata",
    "CommandRegistry",
    "CompletionHandler",
    "setup_completion",
    "cleanup_completion",
    "ContextManager",
    "HelpFormatter",
    "OutputFormatter",
    "show_header",
    "show_progress",
    "show_result",
    # IO Functions
    "check_if_exists",
    "check_if_file_exists",
    "check_if_dir_exists",
    "is_file",
    "is_directory",
    "get_file_name",
    "get_file_extension",
    "get_extension",
    "get_base_name",
    "get_base_name_prefix",
    "get_path_name",
    "get_parent_path_name",
    "get_home_path",
    "get_path_without_extension",
    "get_current_directory",
    "set_current_directory",
    "rename_file",
    "remove_file",
    "create_directory",
    "remove_directory",
    "create_file_list",
    "norm_path",
    # Output Redirector
    "OutputTarget",
    "OutputRedirector",
    "FileTarget",
    "DatabaseTarget",
    "MemoryTarget",
    "ThreadSafeOutputRedirector",
    "redirect_output",
    # Serializer
    "SerializerFactory",
    "Serializer",
    "JSONSerializer",
    "PickleSerializer",
    "YAMLSerializer",
    "MessagePackSerializer",
    "SerializationError",
    "UnsupportedFormatError",
    "serialize",
    "deserialize",
    "to_file",
    "from_file",
    # OHLCV Generator
    "OHLCVGenerator",
    # Cache Manager
    "CacheManager",
    "CacheFactory",
    "CacheBackend",
    "MemoryBackend",
    "DatabaseBackend",
    "FileBackend",
    "MultiLevelBackend",
    "CacheError",
    "CacheBackendError",
    "get_cache",
    # Demo runner
    "DemoRunner",
    "run",
    "test",
    # Observer & Observable
    "Observer",
    "Observable",
    # Protocols
    "KPIProvider",
    "MetricsSource",
    # KPI System
    "KPICollector",
    "export_to_dataframe",
    # Config & Secrets
    "ConfigHandler",
    "SecretHandler",
    # Runtime Functions
    "get_runtime_path",
    "get_runtime_component_path",
    "get_runtime_config_path",
    "get_runtime_log_path",
    "get_runtime_template_path",
    "create_bootstrap_package_structure",
    "create_full_package_structure",
    "ensure_bootstrap_package_structure",
    "create_root_structure",
    "get_bootstrap_config_path",
    "get_bootstrap_deployment_directory",
    "get_bootstrap_development_directories",
    "get_deployment_path",
    "find_development_path",
    "DeploymentManager",
    "DeploymentError",
    "VenvUtils",
    "VenvUtilsError",
    "version",
    "versions",
    # Messaging Framework
    "Event",
    "EventHandler",
    "EventContext",
    "EventResult",
    "DefaultCmdHandler",
    "CoreletForwardingHandler",
    "register_internal_handlers",
    "TimerThread",
    "EventFactory",
    "EventBus",
    "CoreletHandle",
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRY_COUNT",
    "DEFAULT_PRIORITY",
    "INTERNAL_CMD_EXECUTION_EVENT",
    "INTERNAL_CORELET_FORWARDING_EVENT",
    "INTERNAL_SHUTDOWN_EVENT",
    "CoreletWorker",
    "worker_main",
    "EventValidationError",
    "EventExecutionError",
    "EventConnectionError",
    "InvalidEventError",
    "EventShutdownError",
    "NoHandlerAvailableError",
    "EXECUTION_MODE_SYNC",
    "EXECUTION_MODE_THREAD",
    "EXECUTION_MODE_CORELET",
    "EXECUTION_MODE_CMD",
    # Progress Tracking
    "ProgressTracker",
    "AliveProgressTracker",
    # Http Client
    "HttpClient",
    "HttpClientHandler",
    "register_http_handlers",
    # Pandas Accessors
    "PandasDataFrame",
    "PandasSeries",
    # Subpackages (Framework-Style)
    "cli",
    "config",
    "events",
    "http",
    "io",
    "kpi",
    "pandas",
    "runtime",
    "utils",
    # Initialization
    "initialize",
]

# -------------------------------------------------------------
# INITIALIZATION SYSTEM
# -------------------------------------------------------------
_INITIALIZED = False


def initialize() -> None:
    """Initialize basefunctions framework.

    This function is called automatically on import for backwards compatibility.
    It loads the configuration and registers all required handlers.

    Safe to call multiple times - initialization happens only once.

    Notes
    -----
    **Idempotent:** Multiple calls to initialize() are safe - initialization
    happens only once. Subsequent calls are no-ops.

    **Auto-initialization:** This function is called automatically when
    basefunctions is imported, ensuring the framework is ready to use.

    **External libraries:** External libraries can call initialize() before
    registering their own handlers to ensure basefunctions is ready.

    Examples
    --------
    Manual initialization (e.g., in tests):

    >>> import basefunctions
    >>> basefunctions.initialize()  # Safe to call explicitly

    Check if initialized:

    >>> import basefunctions
    >>> basefunctions._INITIALIZED
    True

    External library registering custom handlers:

    >>> import basefunctions
    >>> # basefunctions is already initialized (auto-import)
    >>> factory = basefunctions.EventFactory()
    >>> factory.register_event_type("my_event", MyCustomHandler)
    """
    global _INITIALIZED  # pylint: disable=global-statement
    if not _INITIALIZED:
        # Load basefunctions configuration
        ConfigHandler().load_config_for_package("basefunctions")

        # Register internal event handlers (CMD, Corelet, Shutdown)
        register_internal_handlers()

        # Register HTTP request handler
        register_http_handlers()

        _INITIALIZED = True


# -------------------------------------------------------------
# AUTO-INITIALIZATION ON IMPORT
# -------------------------------------------------------------
# Automatically initialize on import for backwards compatibility
initialize()
