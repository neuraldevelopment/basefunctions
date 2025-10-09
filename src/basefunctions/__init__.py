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
from basefunctions.cli.completion_handler import CompletionHandler, setup_completion, cleanup_completion
from basefunctions.cli.context_manager import ContextManager
from basefunctions.cli.help_formatter import HelpFormatter
from basefunctions.cli.output_formatter import OutputFormatter, show_header, show_progress, show_result
from basefunctions.cli.progress_tracker import ProgressTracker, TqdmProgressTracker


# -------------------------------------------------------------
# Runtime Functions
# -------------------------------------------------------------
from basefunctions.runtime import (
    get_runtime_path,
    get_runtime_component_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path,
    create_bootstrap_package_structure,
    create_full_package_structure,
    ensure_bootstrap_package_structure,
    create_root_structure,
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories,
    get_deployment_path,
    find_development_path,
)

from basefunctions.runtime import DeploymentManager, DeploymentError
from basefunctions.runtime import VenvUtils, VenvUtilsError

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
)

from basefunctions.events.timer_thread import TimerThread

# -------------------------------------------------------------
# PROGRESS TRACKING
# -------------------------------------------------------------
from basefunctions.utils.progress_tracker import (
    ProgressTracker,
    TqdmProgressTracker,
)

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
from basefunctions.pandas.accessors import PandasDataFrame, PandasSeries

# -------------------------------------------------------------
# HTTP CLIENT DEFINITIONS
# -------------------------------------------------------------
from basefunctions.http.http_client import HttpClient
from basefunctions.http.http_client_handler import HttpClientHandler, register_http_handlers

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
    # Messaging Framework
    "Event",
    "EventHandler",
    "EventContext",
    "EventResult",
    "DefaultCmdHandler",
    "CoreletForwardingHandler",
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
    "TqdmProgressTracker",
    # Http Client
    "HttpClient",
    "HttpClientHandler",
    "register_http_handlers",
    # Pandas Accessors
    "PandasDataFrame",
    "PandasSeries",
]

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------

# load default config
ConfigHandler().load_config_for_package("basefunctions")
# register basefunctions handlers
register_http_handlers()
