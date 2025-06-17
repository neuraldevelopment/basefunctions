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
# IMPORTS
# -------------------------------------------------------------
import logging


# -------------------------------------------------------------
# Decorators
# -------------------------------------------------------------
from basefunctions.utils.decorators import (
    function_timer,
    singleton,
    auto_property,
    assert_non_null_args,
    assert_output,
    cache_results,
    catch_exceptions,
    count_calls,
    debug_all,
    enable_logging,
    freeze_args,
    inspect_signature,
    log,
    log_class_methods,
    log_instances,
    log_stack,
    log_types,
    profile_memory,
    recursion_limit,
    retry_on_exception,
    sanitize_args,
    suppress,
    thread_safe,
    trace,
    warn_if_slow,
    track_variable_changes,
)

# -------------------------------------------------------------
# Logging
# -------------------------------------------------------------

from basefunctions.utils.logging import (
    setup_basic_logging,
    setup_file_logging,
    setup_rotating_file_logging,
    get_logger,
    set_log_level,
    disable_logger,
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
# Messaging Framework
# -------------------------------------------------------------
from basefunctions.messaging.event import Event
from basefunctions.messaging.event_handler import (
    EventHandler,
    EventContext,
    DefaultExecHandler,
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET,
    EXECUTION_MODE_CMD,
)

# Event Management
from basefunctions.messaging.event_factory import EventFactory
from basefunctions.messaging.event_bus import EventBus

# Worker System
from basefunctions.messaging.corelet_worker import CoreletWorker, worker_main

# Exception Handling
from basefunctions.messaging.event_exceptions import (
    EventError,
    EventConnectError,
    EventErrorCodes,
    create_connection_error,
    format_error_context,
)

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
from basefunctions.utils.demo_runner import DemoRunner

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
# HTTP Functions
# -------------------------------------------------------------

from basefunctions.http.http_client import (
    HttpClient,
)

from basefunctions.http.http_client_handler import (
    HttpClientHandler,
    register_http_handlers,
)


# -------------------------------------------------------------
# Pandas Accessors
# -------------------------------------------------------------

from basefunctions.pandas.accessors import BasefunctionsDataFrame, BasefunctionsSeries

# -------------------------------------------------------------
# DataFrame Database imports
# -------------------------------------------------------------
from basefunctions.pandas.dataframe_exceptions import (
    DataFrameDbError,
    DataFrameValidationError,
    DataFrameTableError,
    DataFrameCacheError,
    DataFrameConversionError,
    DataFrameDbErrorCodes,
)

from basefunctions.pandas.dataframe_handlers import (
    DataFrameReadHandler,
    DataFrameWriteHandler,
    DataFrameDeleteHandler,
    register_dataframe_handlers,
)

from basefunctions.pandas.dataframe_db import DataFrameDb
from basefunctions.pandas.cached_dataframe_db import CachedDataFrameDb

# -------------------------------------------------------------
# DATABASE EXCEPTIONS
# -------------------------------------------------------------
from basefunctions.database.db_exceptions import (
    DbError,
    DbConnectionError,
    DbQueryError,
    DbTransactionError,
    DbConfigurationError,
    DbValidationError,
    DbResourceError,
    DbFactoryError,
    DbInstanceError,
    DbDataFrameError,
    DbSchemaError,
    DbAuthenticationError,
    DbTimeoutError,
    DbErrorCodes,
)

# -------------------------------------------------------------
# DATABASE CORE COMPONENTS
# -------------------------------------------------------------
from basefunctions.database.db_connector import DatabaseParameters, DbConnector
from basefunctions.database.db_docker_manager import DbDockerManager
from basefunctions.database.db_instance import DbInstance
from basefunctions.database.db_manager import DbManager
from basefunctions.database.db_transaction import DbTransaction
from basefunctions.database.db import Db
from basefunctions.database.db_registry import (
    DbRegistry,
    get_registry,
    validate_db_type,
    get_db_config,
    get_supported_types,
    get_connector_info,
)

# -------------------------------------------------------------
# DATABASE CONNECTORS
# -------------------------------------------------------------
from basefunctions.database.connectors.mysql_connector import MySQLConnector
from basefunctions.database.connectors.postgres_connector import PostgreSQLConnector
from basefunctions.database.connectors.sqlite_connector import SQLiteConnector

# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------

__all__ = [
    # Core Classes
    "Event",
    "EventHandler",
    "EventContext",
    "EventBus",
    "EventFactory",
    # Worker System
    "CoreletWorker",
    "worker_main",
    # Execution Modes
    "EXECUTION_MODE_SYNC",
    "EXECUTION_MODE_THREAD",
    "EXECUTION_MODE_CORELET",
    "EXECUTION_MODE_CMD",
    # Exceptions
    "EventError",
    "EventConnectError",
    "EventErrorCodes",
    "create_connection_error",
    "format_error_context",
    # DataFrame Database Core
    "DataFrameDb",
    "CachedDataFrameDb",
    # DataFrame Database Exceptions
    "DataFrameDbError",
    "DataFrameValidationError",
    "DataFrameTableError",
    "DataFrameCacheError",
    "DataFrameConversionError",
    "DataFrameDbErrorCodes",
    # DataFrame Database Handlers
    "DataFrameReadHandler",
    "DataFrameWriteHandler",
    "DataFrameDeleteHandler",
    "register_dataframe_handlers",
    # Database Exceptions
    "DbRegistry",
    "get_registry",
    "validate_db_type",
    "get_db_config",
    "get_supported_types",
    "get_connector_info",
    "DbError",
    "DbConnectionError",
    "DbQueryError",
    "DbTransactionError",
    "DbConfigurationError",
    "DbValidationError",
    "DbResourceError",
    "DbFactoryError",
    "DbInstanceError",
    "DbDataFrameError",
    "DbSchemaError",
    "DbAuthenticationError",
    "DbTimeoutError",
    "DbErrorCodes",
    "format_error_context",
    # Database Core
    "DatabaseParameters",
    "DbConnector",
    "DbDockerManager",
    "DbInstance",
    "DbManager",
    "DbTransaction",
    "Db",
    # Database Connectors
    "MySQLConnector",
    "PostgreSQLConnector",
    "SQLiteConnector",
    # Observer pattern and Event system
    "Observer",
    "Observable",  # Updated from "Subject" to "Observable"
    "EventHandler",
    "DefaultExecHandler",
    "Event",
    "EventContext",
    "EventBus",
    "CoreletWorker",
    "worker_main",
    # Event Bus
    "EventBus",
    # Corelet System
    "CoreletWorker",
    "worker_main",
    # IO
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
    "OutputTarget",
    "OutputRedirector",
    "FileTarget",
    "DatabaseTarget",
    "MemoryTarget",
    "ThreadSafeOutputRedirector",
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
    # Decorators
    "function_timer",
    "singleton",
    "auto_property",
    "assert_non_null_args",
    "assert_output",
    "cache_results",
    "catch_exceptions",
    "count_calls",
    "debug_all",
    "enable_logging",
    "freeze_args",
    "inspect_signature",
    "log",
    "log_class_methods",
    "log_instances",
    "log_stack",
    "log_types",
    "profile_memory",
    "recursion_limit",
    "retry_on_exception",
    "sanitize_args",
    "suppress",
    "thread_safe",
    "trace",
    "warn_if_slow",
    "track_variable_changes",
    "redirect_output",
    # Config / Secrets
    "ConfigHandler",
    "SecretHandler",
    # Pandas
    "BasefunctionsDataFrame",
    "BasefunctionsSeries",
    # utils
    "DemoRunner",
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
    "setup_basic_logging",
    "setup_file_logging",
    "setup_rotating_file_logging",
    "get_logger",
    "set_log_level",
    "disable_logger",
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
    # HTTP Client
    "HttpClient",
    # HTTP Handlers
    "HttpClientHandler",
    "register_http_handlers",
    # OHLCV Generator
    "OHLCVGenerator",
]

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------

# load default config
ConfigHandler().load_default_config("basefunctions")

# init demo runner logging
DemoRunner.disable_global_logging()

# init logging
setup_basic_logging()


def get_basic_logger(name: str):
    """Use the bulletproof setup instead of creating own handlers"""
    return logging.getLogger(name)


# register basefunctions handlers
register_dataframe_handlers()
register_http_handlers()
