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

from basefunctions.utils.observer import Observer, Subject
from basefunctions.database.database_handler import (
    BaseDatabaseHandler,
    BaseDatabaseConnector,
)

from basefunctions.threading.thread_pool import (
    ThreadPoolMessage,
    ThreadPoolResult,
    ThreadPoolRequestInterface,
    ThreadPoolResultInterface,
    ThreadPool,
)
from basefunctions.threading.decorators import task_handler, debug_task
from basefunctions.threading.downloader import url_downloader

# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------

__all__ = [
    # Database
    "BaseDatabaseHandler",
    "BaseDatabaseConnector",
    # Thread Pool
    "ThreadPoolMessage",
    "ThreadPoolResult",
    "ThreadPool",
    "ThreadPoolRequestInterface",
    "ThreadPoolResultInterface",
    "task_handler",
    "debug_task",
    "url_downloader",
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
    # Observer
    "Observer",
    "Subject",
    # Config / Secrets
    "ConfigHandler",
    "SecretHandler",
]

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------

# load default config
ConfigHandler().load_default_config("basefunctions")


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
