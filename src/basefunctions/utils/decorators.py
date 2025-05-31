"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  a simple framework for base functionalities in python

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------

from functools import wraps
from functools import lru_cache
from tabulate import tabulate
import atexit
import copy
import functools
import inspect
import logging
import time
import traceback
import threading
import tracemalloc
import os
import sys
import pprint
import functools
import basefunctions


# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINTIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS DEFINITIONS
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
        basefunctions.get_logger(__name__).info("runtime of %s: %.8f seconds", func.__name__, end_time - start_time)
        return result

    return wrapper


_singleton_instances = {}
_singleton_lock = threading.Lock()


def singleton(cls):
    """
    Ensure only one instance of the class exists (pickle-safe).
    """

    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in _singleton_instances:
            with _singleton_lock:
                if cls not in _singleton_instances:
                    _singleton_instances[cls] = cls(*args, **kwargs)
        return _singleton_instances[cls]

    class Wrapper(cls):
        def __new__(cls_, *args, **kwargs):
            return get_instance(*args, **kwargs)

        def __reduce__(self):
            return (get_instance, ())

    # Vollständige Metadata-Übertragung
    for attr in ("__name__", "__doc__", "__module__", "__qualname__"):
        if hasattr(cls, attr):
            setattr(Wrapper, attr, getattr(cls, attr))

    return Wrapper


def auto_property(cls):
    """
    Class decorator to automatically convert attributes starting with '_' into
    read/write properties and attributes starting with '_cached_' into read-only properties.

    Parameters:
    -----------
        cls:
            The class to decorate.

    Returns:
    --------
        type
            The modified class with added properties.
    """
    exclude = set(getattr(cls, "_auto_exclude", []))

    def make_property(name):
        return property(
            fget=lambda self: getattr(self, f"_{name}"),
            fset=lambda self, value: setattr(self, f"_{name}", value),
        )

    def make_cached_property(name):
        return property(fget=lambda self: getattr(self, f"_cached_{name}"))

    for key in list(cls.__dict__):
        if key.startswith("_") and not key.startswith("__") and key not in exclude:
            name = key[1:]
            if not hasattr(cls, name):
                setattr(cls, name, make_property(name))

        if key.startswith("_cached_"):
            name = key[len("_cached_") :]
            if not hasattr(cls, name):
                setattr(cls, name, make_cached_property(name))

    orig_setstate = getattr(cls, "__setstate__", None)

    def __setstate__(self, state):
        if orig_setstate:
            orig_setstate(self, state)
        else:
            self.__dict__.update(state)

        for k in list(self.__dict__):
            if k.startswith("_") and not k.startswith("__") and k not in exclude:
                name = k[1:]
                if not hasattr(type(self), name):
                    setattr(type(self), name, make_property(name))
            if k.startswith("_cached_"):
                name = k[len("_cached_") :]
                if not hasattr(type(self), name):
                    setattr(type(self), name, make_cached_property(name))

    cls.__setstate__ = __setstate__
    return cls


_global_log = []


def assert_non_null_args(func):
    """
    Decorator to assert that no arguments passed to a function are None.

    Parameters:
    -----------
        func:
            The function to wrap with non-null argument checks.

    Returns:
    --------
        Callable
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


def log_instances(global_log: bool = False, param_maxlen: int = 80, tablefmt: str = "fancy_grid"):
    """
    Decorator to log each instance of function calls in a formatted table.

    Parameters:
    -----------
        global_log: bool, optional
            If True, logs will be printed globally; otherwise, per call. Default is False.
        param_maxlen: int, optional
            Maximum length of parameter values in the log. Default is 80.
        tablefmt: str, optional
            Table format for displaying logs. Default is "fancy_grid".

    Returns:
    --------
        Callable
            A decorator that logs function call details in a structured format.
    """

    def decorator(cls):
        # bei klassenspezifischem Logging: eigene Liste initialisieren
        if not global_log:
            cls._instance_log = []

        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # Aufruferkontext holen
            caller = inspect.stack()[1]
            file = caller.filename.split("/")[-1]
            line = caller.lineno
            location = f"{file}:{line}"

            # Parameter als String
            arg_repr = []
            if args:
                arg_repr.extend(repr(a) for a in args)
            if kwargs:
                arg_repr.extend(f"{k}={v!r}" for k, v in kwargs.items())
            param_str = ", ".join(arg_repr)
            if len(param_str) > param_maxlen:
                param_str = param_str[: param_maxlen - 3] + "..."

            entry = {
                "class": cls.__name__,
                "id": id(self),
                "location": location,
                "params": param_str,
            }

            if global_log:
                _global_log.append(entry)
            else:
                cls._instance_log.append(entry)

            # Original Initialisierung ausführen
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator


@atexit.register
def print_all_logged_instances():
    """
    Print all logged instances collected by decorators that track function calls.

    Parameters:
    -----------
        None

    Returns:
    --------
        None
            This function does not return a value.
    """
    if _global_log:
        print(f"\n📄 Constructor calls (global): {len(_global_log)} instance(s)\n")
        print(
            tabulate(
                [[i + 1, e["id"], e["class"], e["location"], e["params"]] for i, e in enumerate(_global_log)],
                headers=["#", "Object ID", "Class", "Created at", "Params"],
                tablefmt="fancy_grid",
            )
        )

    # classwise Logs (e.g. @log_instances(global_log=False))
    for obj in globals().values():
        if hasattr(obj, "_instance_log") and obj._instance_log:
            print(f"\n📦 {obj.__name__}: {len(obj._instance_log)} instance(s)\n")
            print(
                tabulate(
                    [
                        [i + 1, e["id"], e["class"], e["location"], e["params"]]
                        for i, e in enumerate(obj._instance_log)
                    ],
                    headers=["#", "Object ID", "Class", "Created at", "Params"],
                    tablefmt="fancy_grid",
                )
            )


def enable_logging(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="a",
):
    """
    Enable and configure logging with the given settings.

    Parameters:
    -----------
        level: int, optional
            Logging level (e.g., logging.DEBUG, logging.INFO). Default is logging.DEBUG.
        format: str, optional
            Format string for log messages. Default is "%(asctime)s [%(levelname)s] %(message)s".
        filemode: str, optional
            File mode for log output (e.g., "a" for append, "w" for overwrite). Default is "a".

    Returns:
    --------
        None
            This function does not return a value.
    """
    logging_initialized = {"done": False}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not logging_initialized["done"]:
                # Ermittle den Pfad zur aufrufenden Datei
                caller_frame = inspect.stack()[1]
                caller_file = caller_frame.filename
                base_filename = os.path.basename(caller_file)
                log_filename = base_filename + ".log"

                logging.basicConfig(level=level, format=format, filename=log_filename, filemode=filemode)
                logging.debug(f"Logging initialized in {log_filename}")
                logging_initialized["done"] = True
            return func(*args, **kwargs)

        return wrapper

    return decorator


def trace(func):
    """
    Decorator to trace function calls using debug-level logging.

    Parameters
    ----------
    func : callable
        The function to wrap for tracing.

    Returns
    -------
    callable
        A wrapped function that logs entry and exit with arguments and results.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        basefunctions.get_logger(__name__).debug("-> %s(%s, %s)", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        basefunctions.get_logger(__name__).debug("<- %s returned %s", func.__name__, result)
        return result

    return wrapper


def log(func):
    """
    Decorator to log the execution of a function, including its name and return value.

    Parameters:
    -----------
        func:
            The function to be logged.

    Returns:
    --------
        Callable
            A wrapped function that logs its execution details.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        logging.debug(f"{func.__name__} returned {result}")
        return result

    return wrapper


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
            basefunctions.get_logger(__name__).error("exception in %s: %s", func.__name__, str(e))

    return wrapper


def count_calls(func):
    """
    Decorator to count and log how many times a function has been called.

    Parameters
    ----------
    func : callable
        The function to wrap with a call counter.

    Returns
    -------
    callable
        A wrapped function that tracks and logs its call count.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        basefunctions.get_logger(__name__).info("%s has been called %d times", func.__name__, wrapper.call_count)
        return func(*args, **kwargs)

    wrapper.call_count = 0
    return wrapper


def log_stack(func):
    """
    Decorator to log the call stack each time the function is invoked.

    Parameters
    ----------
    func : callable
        The function to wrap for call stack logging.

    Returns
    -------
    callable
        A wrapped function that logs the current call stack when executed.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        basefunctions.get_logger(__name__).debug("stack trace for %s", func.__name__)
        traceback_str = "".join(traceback.format_stack())
        basefunctions.get_logger(__name__).debug(traceback_str)
        return func(*args, **kwargs)

    return wrapper


def freeze_args(func):
    """
    Decorator to freeze function arguments, making them immutable during execution.

    Parameters:
    -----------
        func:
            The function whose arguments should be treated as read-only.

    Returns:
    --------
        Callable
            A wrapped function with frozen arguments.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        frozen_args = copy.deepcopy(args)
        frozen_kwargs = copy.deepcopy(kwargs)
        return func(*frozen_args, **frozen_kwargs)

    return wrapper


def assert_output(expected):
    """
    Decorator to assert that the function's output matches the expected value.

    Parameters:
    -----------
        expected:
            The expected return value of the function.

    Returns:
    --------
        Callable
            A wrapped function that raises an AssertionError if the output does not match.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            assert result == expected, f"{func.__name__} -> {result}, expected {expected}"
            return result

        return wrapper

    return decorator


def log_types(func):
    """
    Decorator to log the types of arguments and the return value of a function.

    Parameters:
    -----------
        func:
            The function to wrap for type logging.

    Returns:
    --------
        Callable
            A wrapped function that logs argument and return value types.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"{func.__name__} arg types: {[type(arg).__name__ for arg in args]}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned type: {type(result).__name__}")
        return result

    return wrapper


def sanitize_args(func):
    """
    Decorator to sanitize function arguments before execution.

    Parameters:
    -----------
        func:
            The function whose arguments will be sanitized.

    Returns:
    --------
        Callable
            A wrapped function that processes and cleans its input arguments.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        new_args = [0 if isinstance(arg, float) and arg != arg else arg for arg in args]  # NaN -> 0
        return func(*new_args, **kwargs)

    return wrapper


def thread_safe(func):
    """
    Decorator to make a function thread-safe using a lock.

    Parameters:
    -----------
        func:
            The function to be made thread-safe.

    Returns:
    --------
        Callable
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
        basefunctions.get_logger(__name__).info(
            "%s used %.1fKB, peaked at %.1fKB", func.__name__, current / 1024, peak / 1024
        )
        return result

    return wrapper


def recursion_limit(limit):
    """
    Decorator to temporarily set a custom recursion limit for a function.

    Parameters:
    -----------
        limit: int
            The recursion limit to apply during the function execution.

    Returns:
    --------
        Callable
            A wrapped function that runs with the specified recursion limit.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            old_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(limit)
            try:
                return func(*args, **kwargs)
            finally:
                sys.setrecursionlimit(old_limit)

        return wrapper

    return decorator


def inspect_signature(func):
    """
    Decorator to log the function's signature and provided arguments at call time.

    Parameters:
    -----------
        func:
            The function to inspect and log.

    Returns:
    --------
        Callable
            A wrapped function that logs its signature and arguments when called.
    """
    sig = inspect.signature(func)
    print(f"Signature of {func.__name__}: {sig}")
    return func


def warn_if_slow(threshold):
    """
    Decorator to log a warning if the function execution time exceeds a threshold.

    Parameters:
    -----------
        threshold: float
            The time limit in seconds after which a warning is triggered.

    Returns:
    --------
        Callable
            A wrapped function that warns if it runs slower than the threshold.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            if duration > threshold:
                print(f"⚠️ Warning: {func.__name__} took {duration:.2f}s (limit: {threshold}s)")
            return result

        return wrapper

    return decorator


def retry_on_exception(retries=3, delay=1, exceptions=(Exception,)):
    """
    Decorator to retry a function if specified exceptions are raised.

    Parameters:
    -----------
        retries: int, optional
            Number of retry attempts. Default is 3.
        delay: int or float, optional
            Delay in seconds between retries. Default is 1.
        exceptions: tuple, optional
            Tuple of exception types to catch and retry on. Default is (Exception,).

    Returns:
    --------
        Callable
            A wrapped function that retries on failure.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"{func.__name__} failed ({e}), retrying ({attempt+1}/{retries})...")
                    time.sleep(delay)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_results(func):
    """
    Decorator to cache the results of a function to avoid redundant computations.

    Parameters:
    -----------
        func:
            The function whose results will be cached.

    Returns:
    --------
        Callable
            A wrapped function that returns cached results when available.
    """
    cached_func = lru_cache(maxsize=None)(func)
    return cached_func


def suppress(*exceptions):
    """
    Decorator to suppress specified exceptions raised by the function.

    Parameters:
    -----------
        exceptions:
            Exception types to suppress during function execution.

    Returns:
    --------
        Callable
            A wrapped function that ignores the specified exceptions.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                print(f"{func.__name__} suppressed exception {exceptions}")

        return wrapper

    return decorator


def log_class_methods(cls):
    """
    Class decorator to log calls to all methods of a class.

    Parameters:
    -----------
        cls:
            The class whose method calls will be logged.

    Returns:
    --------
        type
            The modified class with logging added to its methods.
    """
    for attr in dir(cls):
        if callable(getattr(cls, attr)) and not attr.startswith("__"):
            setattr(cls, attr, log(getattr(cls, attr)))
    return cls


def debug_all(func):
    """
    Decorator that combines multiple debugging utilities for a function.

    Applies call stack logging, execution timing, call logging, and exception catching.

    Parameters:
    -----------
        func:
            The function to wrap with full debugging tools.

    Returns:
    --------
        Callable
            A wrapped function with comprehensive debugging capabilities.
    """

    @log_stack
    @timeit
    @log_call
    @catch_exceptions
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def track_variable_changes(func):
    """
    Decorator to track and log changes in local variables during function execution.

    Parameters:
    -----------
        func:
            The function to wrap for variable change tracking.

    Returns:
    --------
        Callable
            A wrapped function that logs any changes in local variables.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        is_method = len(args) > 0 and hasattr(args[0], "__dict__")
        self_obj = args[0] if is_method else None

        before_attrs = copy.deepcopy(self_obj.__dict__) if self_obj else {}
        local_vars_before = {}

        changes = []

        def tracer(frame, event, arg):
            nonlocal local_vars_before, changes

            if frame.f_code != func.__code__:
                return tracer

            if event == "call":
                local_vars_before.update(copy.deepcopy(frame.f_locals))
            elif event == "return":
                after = frame.f_locals
                for key in after:
                    if key not in local_vars_before:
                        changes.append(("local", key, "new", after[key]))
                    elif after[key] != local_vars_before[key]:
                        changes.append(("local", key, "changed", after[key]))
                for key in local_vars_before:
                    if key not in after:
                        changes.append(("local", key, "deleted", None))
            return tracer

        sys.setprofile(tracer)
        result = func(*args, **kwargs)
        sys.setprofile(None)

        if self_obj:
            after_attrs = self_obj.__dict__
            for key in after_attrs:
                if key not in before_attrs:
                    changes.append(("attr", key, "new", after_attrs[key]))
                elif after_attrs[key] != before_attrs[key]:
                    changes.append(("attr", key, "changed", after_attrs[key]))
            for key in before_attrs:
                if key not in after_attrs:
                    changes.append(("attr", key, "deleted", None))

        print(f"\n[track_all_changes] Changes in {func.__name__}:")
        for scope, name, kind, value in changes:
            scope_str = "self." if scope == "attr" else ""
            print(f" - {scope_str}{name}: {kind} -> {pprint.pformat(value)}")

        return result

    return wrapper
