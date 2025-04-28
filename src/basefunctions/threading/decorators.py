"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Decorators and middleware system for task registration, result handling,
  debugging, and function wrapping within the unified task execution system.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import functools


# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

TASK_HANDLER_REGISTRY = {}
RESULT_HANDLER_REGISTRY = {}
MIDDLEWARES = []


# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------


def task_handler(msg_type, run_on_own_core=False):
    """
    Decorator to register a function as a task handler.

    Parameters:
        msg_type (str): The message type the handler processes.
        run_on_own_core (bool): Whether to run the handler in a separate process.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func):
        func._msg_type = msg_type
        func._run_on_own_core = run_on_own_core
        TASK_HANDLER_REGISTRY[msg_type] = func
        return func

    return decorator


def result_handler(msg_type):
    """
    Decorator to register a function as a result handler for a specific msg_type.

    Parameters:
        msg_type (str): The message type the result handler is responsible for.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func):
        RESULT_HANDLER_REGISTRY.setdefault(msg_type, []).append(func)
        return func

    return decorator


def debug_task(func):
    """
    Decorator to automatically log task execution for debugging purposes.

    Parameters:
        func (Callable): The task function to wrap.

    Returns:
        Callable: The wrapped function.
    """

    @functools.wraps(func)
    def wrapper(message, *args, **kwargs):
        print(f"[DEBUG] Starting task {message.msg_type} with content {message.content}")
        try:
            result = func(message, *args, **kwargs)
            print(f"[DEBUG] Task {message.msg_type} succeeded with result {result.result}")
            return result
        except Exception as e:
            print(f"[DEBUG] Task {message.msg_type} failed with error: {e}")
            raise

    return wrapper


def middleware(middleware_func):
    """
    Decorator to register a global middleware function.

    Parameters:
        middleware_func (Callable): The middleware function to register.

    Returns:
        Callable: The middleware function.
    """
    MIDDLEWARES.append(middleware_func)
    return middleware_func


def apply_middlewares(func):
    """
    Applies all registered middleware functions to the given function.

    Parameters:
        func (Callable): The function to wrap with middlewares.

    Returns:
        Callable: The wrapped function.
    """

    @functools.wraps(func)
    def wrapped(message, *args, **kwargs):
        chain = func
        for mw in reversed(MIDDLEWARES):
            chain = mw(chain)
        return chain(message, *args, **kwargs)

    return wrapped
