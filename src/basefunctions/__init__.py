"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

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
from basefunctions.config.config_handler import ConfigHandler
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

from basefunctions.utils.observer import Observer, Subject
from basefunctions.config.secret_handler import SecretHandler
from basefunctions.threading.threadpool import (
    ThreadPoolMessage,
    ThreadPoolHookObjectInterface,
    ThreadPoolUserObjectInterface,
    ThreadPool,
)

from basefunctions.database.database_handler import (
    BaseDatabaseHandler,
    BaseDatabaseConnector,
)

__all__ = [
    "BaseDatabaseHandler",
    "BaseDatabaseConnector",
    "ThreadPool",
    "ThreadPoolMessage",
    "ThreadPoolHookObjectInterface",
    "ThreadPoolUserObjectInterface",
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
    "Observer",
    "Subject",
    "ConfigHandler",
    "SecretHandler",
]

# load default config
ConfigHandler().load_default_config("basefunctions")


def get_default_threadpool() -> ThreadPool:
    """
    returns the default threadpool

    Returns:
    --------
    ThreadPool: the default threadpool
    """
    return default_threadpool


# create a default thread pool, this should be used from all other modules
default_threadpool = ThreadPool(
    num_of_threads=ConfigHandler().get_config_value(
        path="basefunctions/threadpool/num_of_threads", default_value=10
    ),
    default_thread_pool_user_object=None,
)
