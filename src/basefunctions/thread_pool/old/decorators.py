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
import sys
import pickle
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
def thread_handler(message_type: str):
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


def corelet_handler(message_type: str):
    """
    decorator for corelet functions that will be executed in separate processes.

    parameters
    ----------
    message_type : str
        the message type this corelet should respond to.

    returns
    -------
    decorator
        a decorator that wraps the function in a corelet handler
    """

    def decorator(func):
        def wrapper():
            """
            main entry point for the corelet.
            """
            try:
                # read message data from stdin
                message_data = sys.stdin.buffer.read()

                # deserialize message
                message = pickle.loads(message_data)

                # call the handler function
                try:
                    result = func(message)

                    # handle different return formats
                    if isinstance(result, tuple) and len(result) == 2:
                        success, data = result
                    else:
                        success, data = True, result

                except Exception as e:
                    success = False
                    data = str(e)

                # create result object
                result_obj = basefunctions.ThreadPoolResult(
                    message_type=message.message_type,
                    id=message.id,
                    success=success,
                    data=data,
                    original_message=message,
                )

                # serialize and write result to stdout
                result_data = pickle.dumps(result_obj)
                sys.stdout.buffer.write(result_data)
                sys.stdout.buffer.flush()

                # exit with success
                sys.exit(0)

            except Exception as e:
                print(f"Error in corelet: {str(e)}", file=sys.stderr)
                sys.exit(1)

        # save original function for documentation
        wrapper.handler_func = func
        wrapper.message_type = message_type

        return wrapper

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
