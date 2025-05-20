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

# Import messaging system - unified import of Observer/Observable
from basefunctions.messaging.observer import Observer, Observable
from basefunctions.messaging.event import Event, TypedEvent
from basefunctions.messaging.event_handler import (
    EventHandler,
    TypedEventHandler,
    PrioritizedEventHandler,
)
from basefunctions.messaging.subscription import Subscription, CompositeSubscription
from basefunctions.messaging.event_filter import (
    EventFilter,
    FunctionFilter,
    TypeFilter,
    PropertyFilter,
    DataFilter,
    AndFilter,
    OrFilter,
    NotFilter,
    type_filter,
    property_filter,
    data_filter,
    function_filter,
)
from basefunctions.messaging.event_bus import EventBus, get_event_bus

from basefunctions.utils.logging_utils import (
    setup_basic_logging,
    setup_file_logging,
    setup_rotating_file_logging,
    get_logger,
    set_log_level,
    disable_logger,
)
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

from basefunctions.config.config_handler import ConfigHandler
from basefunctions.config.secret_handler import SecretHandler

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

from basefunctions.threading.thread_pool import (
    ThreadPoolMessage,
    ThreadPoolResult,
    ThreadPoolRequestInterface,
    ThreadPoolContext,
    ThreadPool,
    TimerThread,
)
from basefunctions.threading.decorators import thread_handler, corelet_handler, debug_task
from basefunctions.threading.corelet_base import CoreletBase

# -------------------------------------------------------------
# DATABASE COMPONENTS
# -------------------------------------------------------------
# Core database components
from basefunctions.database.db_manager import DbManager
from basefunctions.database.db_instance import DbInstance
from basefunctions.database.db import Db
from basefunctions.database.db_factory import DbFactory
from basefunctions.database.transaction import TransactionContextManager, DbTransactionProxy

# Database exceptions
from basefunctions.database.exceptions import (
    DatabaseError,
    QueryError,
    TransactionError,
    DbConnectionError,
    ConfigurationError,
    DataFrameError,
    NoSuchDatabaseError,
    NoSuchTableError,
    AuthenticationError,
    ThreadPoolError,
)

# Database connectors
from basefunctions.database.connectors.db_connector import DbConnector
from basefunctions.database.connectors.sqlite_connector import SQLiteConnector
from basefunctions.database.connectors.mysql_connector import MySQLConnector
from basefunctions.database.connectors.postgresql_connector import PostgreSQLConnector

# Data models
from basefunctions.database.db_models import (
    DatabaseParameters,
    ConnectionConfig,
    PortsConfig,
    PoolConfig,
    DbConfig,
    validate_config,
    config_to_parameters,
)

# DataFrame handling
from basefunctions.database.dataframe.dataframe_handler import DataFrameHandler

# Thread pool for database operations
from basefunctions.database.threadpool.db_threadpool import DbThreadPool
from basefunctions.database.threadpool.task_handlers import DataFrameTaskHandler


# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------

__all__ = [
    # Database Core
    "DbManager",
    "DbInstance",
    "Db",
    "DbFactory",
    "TransactionContextManager",
    "DbTransactionProxy",
    # Database Connectors
    "DbConnector",
    "SQLiteConnector",
    "MySQLConnector",
    "PostgreSQLConnector",
    # Database Exceptions
    "DatabaseError",
    "QueryError",
    "TransactionError",
    "DbConnectionError",
    "ConfigurationError",
    "DataFrameError",
    "NoSuchDatabaseError",
    "NoSuchTableError",
    "AuthenticationError",
    "ThreadPoolError",
    # Database Models
    "DatabaseParameters",
    "ConnectionConfig",
    "PortsConfig",
    "PoolConfig",
    "DbConfig",
    "validate_config",
    "config_to_parameters",
    # DataFrame Handling
    "DataFrameHandler",
    # ThreadPool
    "DbThreadPool",
    "DataFrameTaskHandler",
    # Observer pattern and Event system
    "Observer",
    "Observable",  # Updated from "Subject" to "Observable"
    "Event",
    "TypedEvent",
    "EventBus",
    "get_event_bus",
    "EventHandler",
    "TypedEventHandler",
    "PrioritizedEventHandler",
    "Subscription",
    "CompositeSubscription",
    # Filters
    "EventFilter",
    "FunctionFilter",
    "TypeFilter",
    "PropertyFilter",
    "DataFilter",
    "AndFilter",
    "OrFilter",
    "NotFilter",
    "type_filter",
    "property_filter",
    "data_filter",
    "function_filter",
    # Threading
    "CoreletBase",
    "ThreadPoolMessage",
    "ThreadPoolResult",
    "ThreadPoolRequestInterface",
    "ThreadPool",
    "ThreadPoolContext",
    "TimerThread",
    "thread_handler",
    "corelet_handler",
    "debug_task",
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
]

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------

# load default config
ConfigHandler().load_default_config("basefunctions")

# init logging
setup_basic_logging()

_default_thread_task_pool = None


def get_default_thread_task_pool(force_recreate=False):
    """
    Returns the default ThreadTaskPool instance.

    Parameters
    ----------
    force_recreate : bool, optional
        If True, always creates a new instance.

    Returns
    -------
    ThreadTaskPool
        The default ThreadTaskPool.
    """
    # pylint W0603
    global _default_thread_task_pool

    if force_recreate or _default_thread_task_pool is None:
        _default_thread_task_pool = ThreadPool(
            num_of_threads=ConfigHandler().get_config_value(
                path="basefunctions/threadpool/num_of_threads", default_value=10
            )
        )
    return _default_thread_task_pool
