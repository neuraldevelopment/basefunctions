"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : basefunctions

  Copyright (c) by Ralph Vogl

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

# NEW: Unified Task Pool
from basefunctions.threading.unified_task_pool import UnifiedTaskPool
from basefunctions.threading.thread_task_pool import ThreadTaskPool
from basefunctions.threading.process_pool import ProcessTaskPool
from basefunctions.threading.core import TaskMessage, TaskResult, TaskHandlerInterface
from basefunctions.threading.chainer import Chainer
from basefunctions.threading.decorators import (
    task_handler,
    result_handler,
    debug_task,
    middleware,
    apply_middlewares,
)
from basefunctions.threading.process_pool import ProcessTaskPool
from basefunctions.threading.recorder import Recorder
from basefunctions.threading.retry_handler import RetryHandler
from basefunctions.threading.scheduler import Scheduler
from basefunctions.threading.task_loader import TaskLoader


# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------

__all__ = [
    # Database
    "BaseDatabaseHandler",
    "BaseDatabaseConnector",
    # Thread Pool
    "UnifiedTaskPool",
    "ThreadTaskPool",
    "ProcessTaskPool",
    "TaskMessage",
    "TaskResult",
    "TaskHandlerInterface",
    "Chainer",
    "ProcessTaskPool",
    "Recorder",
    "RetryHandler",
    "Scheduler",
    "TaskLoader",
    "task_handler",
    "result_handler",
    "debug_task",
    "middleware",
    "apply_middlewares",
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


def get_default_unified_taskpool() -> UnifiedTaskPool:
    global _default_unified_taskpool
    if _default_unified_taskpool is None:
        _default_unified_taskpool = UnifiedTaskPool(
            num_threads=ConfigHandler().get_config_value(
                path="basefunctions/unifiedtaskpool/num_of_threads", default_value=5
            ),
            num_processes=ConfigHandler().get_config_value(
                path="basefunctions/unifiedtaskpool/num_of_processes", default_value=2
            ),
        )
    return _default_unified_taskpool


# -------------------------------------------------------------
# SINGLETON INSTANCES
# -------------------------------------------------------------

# Default Unified Task Pool (for both CPU- and IO-bound tasks)
_default_unified_taskpool = None
