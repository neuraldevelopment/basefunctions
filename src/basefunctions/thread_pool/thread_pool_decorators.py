"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Decorators for simplifying thread pool task handler creation

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import inspect
import os
import pickle
import sys
from functools import wraps
from types import FunctionType
from typing import Any, Callable, Dict, Optional, Tuple, Type

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


def thread_task(task_type: str):
    """
    Decorator to create a thread pool task handler from a function.

    This decorator wraps a function into a ThreadPoolRequestInterface
    class that can be registered with the thread pool.

    Parameters
    ----------
    task_type : str
        The task type this handler should respond to

    Returns
    -------
    Callable
        A decorator that converts a function to a thread pool handler class
    """

    def decorator(func: FunctionType):
        # Get function signature information
        sig = inspect.signature(func)
        param_names = list(sig.parameters)

        # Create dynamic handler class
        class ThreadTaskHandler(basefunctions.ThreadPoolRequestInterface):
            """
            Dynamically created handler class implementing ThreadPoolRequestInterface.
            """

            def process_request(
                self,
                context: basefunctions.ThreadPoolContext,
                message: basefunctions.ThreadPoolMessage,
            ) -> Tuple[bool, Any]:
                """
                Process request by calling the wrapped function with appropriate parameters.
                """
                # Create argument dictionary based on function signature
                args = {
                    "context": context,
                    "message": message,
                    "content": message.content,
                    "thread_local_data": context.thread_local_data if context else None,
                    "task_id": message.id,
                    "task_type": message.message_type,
                    "retry_count": message.retry,
                    "timeout": message.timeout,
                }

                # Filter args to match the wrapped function's parameters
                filtered_args = {k: args[k] for k in param_names if k in args}

                try:
                    # Call the wrapped function
                    result = func(**filtered_args)

                    # Handle different return formats
                    if isinstance(result, tuple) and len(result) == 2:
                        success, data = result
                    else:
                        success, data = True, result

                    # Ensure proper return type
                    if not isinstance(success, bool):
                        raise TypeError("Handler function must return (bool, Any)")

                    return success, data

                except Exception as e:
                    basefunctions.get_logger(__name__).error(
                        "Exception in handler %s: %s", func.__name__, str(e)
                    )
                    return False, str(e)

        # Set class attributes for better debugging
        ThreadTaskHandler.__name__ = f"{func.__name__}_Handler"
        ThreadTaskHandler.__module__ = func.__module__
        ThreadTaskHandler.task_type = task_type

        # Register handler with thread pool
        handler_class = ThreadTaskHandler
        thread_pool = basefunctions.get_thread_pool()
        thread_pool.register_handler(task_type, handler_class)

        # Return the original function for documentation/direct use
        return func

    return decorator


def corelet_task(task_type: str):
    """
    Decorator for corelet functions that will be executed in separate processes.

    This decorator creates a standalone process entry point for a function.

    Parameters
    ----------
    task_type : str
        The task type this corelet should respond to

    Returns
    -------
    Callable
        A decorator that wraps the function as a corelet entry point
    """

    def decorator(func: FunctionType):
        @wraps(func)
        def wrapper():
            """
            Main entry point for the corelet.
            """
            try:
                # Read message data from stdin
                message_data = sys.stdin.buffer.read()

                # Deserialize message
                message = pickle.loads(message_data)

                # Create empty context
                context = basefunctions.ThreadPoolContext(
                    process_info={"pid": os.getpid(), "argv": sys.argv}
                )

                # Call the handler function
                try:
                    result = func(context, message)

                    # Handle different return formats
                    if isinstance(result, tuple) and len(result) == 2:
                        success, data = result
                    else:
                        success, data = True, result

                except Exception as e:
                    basefunctions.get_logger(__name__).error(
                        "Exception in corelet %s: %s", func.__name__, str(e)
                    )
                    success = False
                    data = str(e)

                # Create result object
                result_obj = basefunctions.ThreadPoolResult(
                    message_type=message.message_type,
                    id=message.id,
                    success=success,
                    data=data,
                    original_message=message,
                )

                # Serialize and write result to stdout
                result_data = pickle.dumps(result_obj)
                sys.stdout.buffer.write(result_data)
                sys.stdout.buffer.flush()

                # Exit with success
                sys.exit(0)

            except Exception as e:
                # Log error
                basefunctions.get_logger(__name__).critical("Error in corelet: %s", str(e))
                sys.exit(1)

        # Save original function for documentation
        wrapper.handler_func = func
        wrapper.task_type = task_type

        return wrapper

    return decorator


def debug_task(func: FunctionType):
    """
    Decorator to add debug output to task handlers.

    Parameters
    ----------
    func : FunctionType
        The function to wrap

    Returns
    -------
    Callable
        The wrapped function with debug logging
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = basefunctions.get_logger(__name__)

        # Log call
        logger.debug("Calling %s with args=%s, kwargs=%s", func.__name__, args, kwargs)

        # Call original function
        result = func(*args, **kwargs)

        # Log result
        logger.debug("%s returned %s", func.__name__, result)

        return result

    return wrapper
