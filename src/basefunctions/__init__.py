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
from multiprocessing import Pipe, Process


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
from basefunctions.messaging.event_context import EventContext
from basefunctions.messaging.event import (
    Event,
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET,
    EXECUTION_MODE_CMD,
)
from basefunctions.messaging.event_handler import (
    EventHandler,
    EventResult,
    ExceptionResult,
    DefaultCmdHandler,
    CoreletHandle,
    CoreletForwardingHandler,
)

from basefunctions.messaging.timer_thread import TimerThread

# Event Management
from basefunctions.messaging.event_factory import EventFactory

# Worker System
from basefunctions.messaging.corelet_worker import CoreletWorker, worker_main

# Exception Handling
from basefunctions.messaging.event_exceptions import (
    EventError,
    EventErrorCode,
    EventValidationError,
    EventExecutionError,
    EventConnectionError,
    EventBusError,
    EventBusShutdownError,
    NoHandlerAvailableError,
    InvalidEventError,
    EventBusInitializationError,
)

from basefunctions.messaging.event_bus import (
    EventBus,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_PRIORITY,
    INTERNAL_CMD_EXECUTION_EVENT,
    INTERNAL_CORELET_FORWARDING_EVENT,
    INTERNAL_SHUTDOWN_EVENT,
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
    # Multiprocessing
    "Pipe",
    "Process",
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
    # Messaging Framework
    "Event",
    "EventHandler",
    "EventContext",
    "EventResult",
    "ExceptionResult",
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
    "EventError",
    "EventErrorCode",
    "EventValidationError",
    "EventExecutionError",
    "EventConnectionError",
    "EventBusError",
    "EventBusShutdownError",
    "NoHandlerAvailableError",
    "InvalidEventError",
    "EventBusInitializationError",
    "EXECUTION_MODE_SYNC",
    "EXECUTION_MODE_THREAD",
    "EXECUTION_MODE_CORELET",
    "EXECUTION_MODE_CMD",
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
    # HTTP Client
    "HttpClient",
    "HttpClientHandler",
    "register_http_handlers",
    # Pandas Accessors
    "BasefunctionsDataFrame",
    "BasefunctionsSeries",
    # DataFrame Database
    "DataFrameDb",
    "CachedDataFrameDb",
    "DataFrameDbError",
    "DataFrameValidationError",
    "DataFrameTableError",
    "DataFrameCacheError",
    "DataFrameConversionError",
    "DataFrameDbErrorCodes",
    "DataFrameReadHandler",
    "DataFrameWriteHandler",
    "DataFrameDeleteHandler",
    "register_dataframe_handlers",
    # Database Exceptions
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
    # Database Core Components
    "DatabaseParameters",
    "DbConnector",
    "DbDockerManager",
    "DbInstance",
    "DbManager",
    "DbTransaction",
    "Db",
    "DbRegistry",
    "get_registry",
    "validate_db_type",
    "get_db_config",
    "get_supported_types",
    "get_connector_info",
    # Database Connectors
    "MySQLConnector",
    "PostgreSQLConnector",
    "SQLiteConnector",
]

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------

# load default config
ConfigHandler().load_default_config("basefunctions")


# register basefunctions handlers
register_dataframe_handlers()
register_http_handlers()
