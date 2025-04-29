"""
=============================================================================

 Licensed Materials, Property of Ralph Vogl, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Decorators for simplifying ThreadPool usage

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from types import FunctionType
from functools import wraps
from inspect import signature
import basefunctions


# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# FUNCTION DEFINITIONS
# -------------------------------------------------------------


def task_handler(message_type: str):
    """
    Decorator to wrap a function into a ThreadPoolRequestInterface class.

    Parameters
    ----------
    message_type : str
        The message type this handler should respond to.

    Returns
    -------
    An instance of a dynamically created class implementing process_request().
    """

    def decorator(func: FunctionType):
        param_names = list(signature(func).parameters)

        class WrappedHandler(basefunctions.ThreadPoolRequestInterface):
            def process_request(self, thread_local_data, input_queue, message):
                args = {
                    "thread_local_data": thread_local_data,
                    "input_queue": input_queue,
                    "message": message,
                }
                filtered_args = {k: args[k] for k in param_names if k in args}
                return func(**filtered_args)

        WrappedHandler.__name__ = f"{func.__name__}_Handler"
        WrappedHandler.message_type = message_type
        return WrappedHandler()

    return decorator


def debug_task(func):
    """
    Decorator to add debug output to task handlers.

    Parameters
    ----------
    func : callable
        The function to wrap.

    Returns
    -------
    callable
        The wrapped function with debug print.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[DEBUG] Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"[DEBUG] {func.__name__} returned {result}")
        return result

    return wrapper
