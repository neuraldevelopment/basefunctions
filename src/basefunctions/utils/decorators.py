"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Clean decorator collection - only useful decorators without spam

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from functools import lru_cache, wraps
import functools
import threading
import time
import tracemalloc
from basefunctions.utils.logging import setup_logger, get_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_singleton_instances = {}
_singleton_lock = threading.Lock()

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def function_timer(func):
    """
    Decorator to measure and log the execution time of a function.

    Parameters
    ----------
    func : callable
        The function whose execution time is to be measured.

    Returns
    -------
    callable
        A wrapped function that logs its execution time when called.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        get_logger(__name__).info("runtime of %s: %.8f seconds", func.__name__, end_time - start_time)
        return result

    return wrapper


def singleton(cls):
    """
    Ensure only one instance of the class exists (pickle-safe).

    Parameters
    ----------
    cls : type
        The class to make singleton

    Returns
    -------
    type
        The singleton class
    """

    def get_instance(*args, **kwargs):
        if cls not in _singleton_instances:
            with _singleton_lock:
                if cls not in _singleton_instances:
                    _singleton_instances[cls] = cls(*args, **kwargs)
        return _singleton_instances[cls]

    get_instance.__name__ = cls.__name__
    get_instance.__doc__ = cls.__doc__
    return get_instance


def catch_exceptions(func):
    """
    Decorator to catch and log exceptions raised by the function.

    Parameters
    ----------
    func : callable
        The function to wrap with exception handling.

    Returns
    -------
    callable
        A wrapped function that logs exceptions and prevents crashes.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            get_logger(__name__).error("exception in %s: %s", func.__name__, str(e))

    return wrapper


def thread_safe(func):
    """
    Decorator to make a function thread-safe using a lock.

    Parameters
    ----------
    func : callable
        The function to be made thread-safe.

    Returns
    -------
    callable
        A wrapped function that ensures thread-safe execution.
    """
    lock = threading.Lock()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)

    return wrapper


def profile_memory(func):
    """
    Decorator to profile and log memory usage of a function.

    Parameters
    ----------
    func : callable
        The function to profile.

    Returns
    -------
    callable
        A wrapped function that logs memory usage statistics.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        get_logger(__name__).info(
            "%s used %.1fKB, peaked at %.1fKB", func.__name__, current / 1024, peak / 1024
        )
        return result

    return wrapper


def warn_if_slow(threshold):
    """
    Decorator to log a warning if the function execution time exceeds a threshold.

    Parameters
    ----------
    threshold : float
        The time limit in seconds after which a warning is triggered.

    Returns
    -------
    callable
        A wrapped function that warns if it runs slower than the threshold.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            if duration > threshold:
                get_logger(__name__).warning(
                    "%s took %.2fs (limit: %.2fs)", func.__name__, duration, threshold
                )
            return result

        return wrapper

    return decorator


def retry_on_exception(retries=3, delay=1, exceptions=(Exception,)):
    """
    Decorator to retry a function if specified exceptions are raised.

    Parameters
    ----------
    retries : int, optional
        Number of retry attempts. Default is 3.
    delay : int or float, optional
        Delay in seconds between retries. Default is 1.
    exceptions : tuple, optional
        Tuple of exception types to catch and retry on. Default is (Exception,).

    Returns
    -------
    callable
        A wrapped function that retries on failure.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < retries - 1:
                        get_logger(__name__).warning(
                            "%s failed (%s), retrying (%d/%d)...", func.__name__, str(e), attempt + 1, retries
                        )
                        time.sleep(delay)
                    else:
                        raise
            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_results(func):
    """
    Decorator to cache the results of a function to avoid redundant computations.

    Parameters
    ----------
    func : callable
        The function whose results will be cached.

    Returns
    -------
    callable
        A wrapped function that returns cached results when available.
    """
    cached_func = lru_cache(maxsize=None)(func)
    return cached_func


def suppress(*exceptions):
    """
    Decorator to suppress specified exceptions raised by the function.

    Parameters
    ----------
    exceptions : tuple
        Exception types to suppress during function execution.

    Returns
    -------
    callable
        A wrapped function that ignores the specified exceptions.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                get_logger(__name__).debug("%s suppressed exception %s", func.__name__, exceptions)

        return wrapper

    return decorator


def assert_non_null_args(func):
    """
    Decorator to assert that no arguments passed to a function are None.

    Parameters
    ----------
    func : callable
        The function to wrap with non-null argument checks.

    Returns
    -------
    callable
        A wrapped function that raises an error if any argument is None.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if any(arg is None for arg in args):
            raise ValueError("None value detected in positional arguments")
        if any(value is None for value in kwargs.values()):
            raise ValueError("None value detected in keyword arguments")
        return func(*args, **kwargs)

    return wrapper


def log_to_file(file: str, level: str = "DEBUG"):
    """
    Decorator to redirect function logging to specific file.

    Parameters
    ----------
    file : str
        Log file path
    level : str
        Log level for this function (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns
    -------
    callable
        Decorator function

    Example
    -------
    @log_to_file("debug_functions.log", level="DEBUG")
    def my_function():
        logger = get_logger(__name__)
        logger.debug("This goes to debug_functions.log")
    """

    def decorator(func):
        # Setup logger for this specific function
        func_logger_name = f"{func.__module__}.{func.__name__}"
        setup_logger(func_logger_name, level=level, file=file)
        func_logger = get_logger(func_logger_name)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_logger.info("Calling %s", func.__name__)
            try:
                result = func(*args, **kwargs)
                func_logger.info("Finished %s", func.__name__)
                return result
            except Exception as e:
                func_logger.error("Exception in %s: %s", func.__name__, str(e))
                raise

        return wrapper

    return decorator


def auto_property(func):
    """
    Decorator to create a property with automatic getter/setter.

    Parameters
    ----------
    func : callable
        The function to convert to a property.

    Returns
    -------
    property
        A property with getter and setter.
    """
    attr_name = f"_{func.__name__}"

    def getter(self):
        return getattr(self, attr_name, None)

    def setter(self, value):
        setattr(self, attr_name, value)

    return property(getter, setter)
