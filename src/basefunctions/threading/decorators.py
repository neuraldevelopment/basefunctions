"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

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
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
def task_handler(message_type: str):
    """
    decorator to wrap a function into a threadpoolrequestinterface class.

    parameters
    ----------
    message_type : str
        the message type this handler should respond to.

    returns
    -------
    decorator
        a decorator that converts a function to a threadpool handler class
    """

    def decorator(func: FunctionType):
        param_names = list(signature(func).parameters)

        class WrappedHandler(basefunctions.ThreadPoolRequestInterface):
            """
            dynamically created handler class implementing threadpoolrequestinterface.
            """

            def process_request(self, context, message):
                """
                processes request by calling the wrapped function with appropriate parameters.
                """
                # create argument dictionary based on function signature
                args = {
                    "context": context,
                    "message": message,
                    "thread_local_data": context.thread_local_data if context else None,
                    "input_queue": context.input_queue if context else None,
                }

                # filter args to match the wrapped function's parameters
                filtered_args = {k: args[k] for k in param_names if k in args}

                try:
                    # call the wrapped function
                    result = func(**filtered_args)

                    # handle different return formats
                    if isinstance(result, tuple) and len(result) == 2:
                        success, data = result
                    else:
                        success, data = True, result

                    # ensure proper return type
                    if not isinstance(success, bool):
                        raise TypeError("handler function must return (bool, Any)")

                    return success, data
                except Exception as e:
                    basefunctions.get_logger(__name__).error(
                        "exception in handler %s: %s", func.__name__, str(e)
                    )
                    return False, str(e)

        # set class attributes for better debugging
        WrappedHandler.__name__ = f"{func.__name__}_Handler"
        WrappedHandler.__module__ = func.__module__
        WrappedHandler.message_type = message_type

        # return the class, not an instance
        return WrappedHandler

    return decorator


def debug_task(func):
    """
    decorator to add debug output to task handlers.

    parameters
    ----------
    func : callable
        the function to wrap.

    returns
    -------
    callable
        the wrapped function with debug logging.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        basefunctions.get_logger(__name__).debug(
            "calling %s with args=%s, kwargs=%s", func.__name__, args, kwargs
        )

        result = func(*args, **kwargs)

        basefunctions.get_logger(__name__).debug("%s returned %s", func.__name__, result)

        return result

    return wrapper
