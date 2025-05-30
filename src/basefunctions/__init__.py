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
# Observer & Observable
# -------------------------------------------------------------

from basefunctions.utils.observer import Observer, Observable

# -------------------------------------------------------------
# Config- & SecretHandler
# -------------------------------------------------------------

from basefunctions.config.config_handler import ConfigHandler
from basefunctions.config.secret_handler import SecretHandler

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

# -------------------------------------------------------------
# Pandas Accessors
# -------------------------------------------------------------

from basefunctions.pandas.accessors import BasefunctionsDataFrame, BasefunctionsSeries


# -------------------------------------------------------------
# Messaging Framework
# -------------------------------------------------------------
from basefunctions.messaging.event import Event
from basefunctions.messaging.event_handler import (
    EventHandler,
    EventContext,
    EXECUTION_MODE_SYNC,
    EXECUTION_MODE_THREAD,
    EXECUTION_MODE_CORELET,
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
    create_connection_error,
    create_query_error,
    create_validation_error,
    create_transaction_error,
    create_resource_error,
    is_retryable_error,
    get_error_category,
    format_error_context,
)

# -------------------------------------------------------------
# DATABASE CORE COMPONENTS
# -------------------------------------------------------------
from basefunctions.database.db_connector import DatabaseParameters, DbConnector
from basefunctions.database.db_factory import DbFactory
from basefunctions.database.db_instance import DbInstance
from basefunctions.database.db_manager import DbManager
from basefunctions.database.db_transaction import DbTransaction
from basefunctions.database.db import Db

# -------------------------------------------------------------
# DATABASE CONNECTORS
# -------------------------------------------------------------
from basefunctions.database.connectors.mysql_connector import MySQLConnector
from basefunctions.database.connectors.postgresql_connector import PostgreSQLConnector
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
    # Exceptions
    "EventError",
    "EventConnectError",
    "EventErrorCodes",
    "create_connection_error",
    "format_error_context",
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
    # Exception Factory Functions
    "create_connection_error",
    "create_query_error",
    "create_validation_error",
    "create_transaction_error",
    "create_resource_error",
    # Exception Utilities
    "is_retryable_error",
    "get_error_category",
    "format_error_context",
    # Database Core
    "DatabaseParameters",
    "DbConnector",
    "DbFactory",
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
    "Event",
    "EventHandler",
    "EventContext",
    "EventBus",
    "get_event_bus",
    "CoreletPool",
    "WorkerInfo",
    "CoreletWorker",
    "worker_main",
    # Event Bus
    "EventBus",
    "get_event_bus",
    # Corelet System
    "CoreletPool",
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


def get_logger(name: str):
    """
    Get logger instance for basefunctions modules.

    Parameters
    ----------
    name : str
        Logger name.

    Returns
    -------
    logging.Logger
        Logger instance.
    """
    import logging

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
