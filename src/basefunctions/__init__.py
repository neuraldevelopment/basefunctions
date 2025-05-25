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

from basefunctions.utils.observer import Observer, Observable

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

from basefunctions.pandas.accessors import BasefunctionsDataFrame, BasefunctionsSeries

# -------------------------------------------------------------
# Messaging Imports
# -------------------------------------------------------------

from basefunctions.messaging.event import Event
from basefunctions.messaging.event_handler import EventHandler, EventContext
from basefunctions.messaging.event_bus import EventBus, get_event_bus
from basefunctions.messaging.corelet_pool import CoreletPool, WorkerInfo
from basefunctions.messaging.corelet_worker import CoreletWorker, worker_main

# Database System
from .database.db_factory import DbFactory
from .database.db_instance import DbInstance
from .database.db_manager import DbManager
from .database.db import Db
from .database.exceptions import (
    DatabaseError,
    QueryError,
    TransactionError,
    DbConnectionError,
    ConfigurationError,
    DataFrameError,
    NoSuchDatabaseError,
    NoSuchTableError,
    AuthenticationError,
)
from .database.transaction import TransactionContextManager, DbTransactionProxy
from .database.eventbus.db_eventbus import DbEventBus
from .database.eventbus.db_event_handlers import (
    DbQueryHandler,
    DataFrameHandler,
    DbTransactionHandler,
    DbBulkOperationHandler,
)


# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------

__all__ = [
    # Database System
    "DbFactory",
    "DbInstance",
    "DbManager",
    "Db",
    "DatabaseError",
    "QueryError",
    "TransactionError",
    "DbConnectionError",
    "ConfigurationError",
    "DataFrameError",
    "NoSuchDatabaseError",
    "NoSuchTableError",
    "AuthenticationError",
    "TransactionContextManager",
    "DbTransactionProxy",
    "DbEventBus",
    "DbQueryHandler",
    "DataFrameHandler",
    "DbTransactionHandler",
    "DbBulkOperationHandler",
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
