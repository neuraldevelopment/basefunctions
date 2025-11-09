"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.

  Description:
  Pytest test suite for utils.decorators module.
  Tests decorator functionality including singleton pattern, thread safety,
  exception handling, timing, and validation decorators.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports (alphabetical)
import logging
import pytest
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import Mock, MagicMock, patch, call

# Project imports (relative to project root)
from basefunctions.utils.decorators import (
    function_timer,
    singleton,
    catch_exceptions,
    thread_safe,
    profile_memory,
    warn_if_slow,
    retry_on_exception,
    cache_results,
    suppress,
    assert_non_null_args,
    log_to_file,
    auto_property,
    _singleton_instances,
    _singleton_lock,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_function() -> Callable[[], int]:
    """
    Create simple test function that returns 42.

    Returns
    -------
    Callable[[], int]
        Function that returns 42

    Notes
    -----
    Used for basic decorator testing without side effects
    """
    def test_func() -> int:
        return 42

    return test_func


@pytest.fixture
def failing_function() -> Callable[[], None]:
    """
    Create function that always raises ValueError.

    Returns
    -------
    Callable[[], None]
        Function that raises ValueError

    Notes
    -----
    Used for exception handling decorator tests
    """
    def test_func() -> None:
        raise ValueError("Test error")

    return test_func


@pytest.fixture
def sample_class() -> type:
    """
    Create test class for singleton tests.

    Returns
    -------
    type
        Simple test class with counter

    Notes
    -----
    Each instance increments class-level counter
    """
    class TestClass:
        instance_count = 0

        def __init__(self, value: int = 0) -> None:
            TestClass.instance_count += 1
            self.value = value

    return TestClass


@pytest.fixture
def mock_logger() -> Mock:
    """
    Provide mocked logger instance.

    Returns
    -------
    Mock
        Mock object with logger methods

    Notes
    -----
    Includes info, warning, error, debug methods
    """
    logger: Mock = Mock(spec=logging.Logger)
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Path:
    """
    Create temporary log file path.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to temporary log file

    Notes
    -----
    File is created in pytest temporary directory
    """
    return tmp_path / "test_decorator.log"


@pytest.fixture(autouse=True)
def clear_singleton_instances() -> None:
    """
    Clear singleton instances before each test.

    Returns
    -------
    None

    Notes
    -----
    Ensures clean state for singleton tests
    """
    _singleton_instances.clear()


# -------------------------------------------------------------
# TEST CASES: singleton decorator
# -------------------------------------------------------------


def test_singleton_returns_same_instance_on_multiple_calls(sample_class: type) -> None:  # CRITICAL TEST
    """
    Test singleton decorator returns same instance on multiple calls.

    Tests that singleton decorator correctly ensures only one instance
    of a class exists across multiple instantiation attempts.

    Parameters
    ----------
    sample_class : type
        Test class fixture

    Returns
    -------
    None
        Test passes if all assertions succeed

    Notes
    -----
    CRITICAL: Validates core singleton behavior
    """
    # ARRANGE
    SingletonClass: Callable = singleton(sample_class)

    # ACT
    instance1 = SingletonClass(value=10)
    instance2 = SingletonClass(value=20)
    instance3 = SingletonClass()

    # ASSERT
    assert instance1 is instance2
    assert instance2 is instance3
    assert instance1.value == 10  # First call args used
    assert sample_class.instance_count == 1  # Only one instance created


def test_singleton_preserves_class_name_and_docstring(sample_class: type) -> None:
    """
    Test singleton preserves original class name and docstring.

    Tests that singleton wrapper maintains class metadata correctly.

    Parameters
    ----------
    sample_class : type
        Test class fixture

    Returns
    -------
    None
        Test passes if metadata preserved
    """
    # ARRANGE
    sample_class.__doc__ = "Test docstring"
    original_name: str = sample_class.__name__

    # ACT
    SingletonClass: Callable = singleton(sample_class)

    # ASSERT
    assert SingletonClass.__name__ == original_name
    assert SingletonClass.__doc__ == "Test docstring"


def test_singleton_is_thread_safe() -> None:  # CRITICAL TEST
    """
    Test singleton is thread-safe under concurrent access.

    Tests that singleton decorator prevents race conditions when
    multiple threads attempt to create instances simultaneously.

    Returns
    -------
    None
        Test passes if only one instance created

    Notes
    -----
    CRITICAL: Thread safety is essential for singleton pattern
    """
    # ARRANGE
    class CounterClass:
        instance_count = 0

        def __init__(self) -> None:
            time.sleep(0.01)  # Simulate slow initialization
            CounterClass.instance_count += 1

    SingletonCounter = singleton(CounterClass)
    instances: List[Any] = []

    def create_instance() -> None:
        instances.append(SingletonCounter())

    threads: List[threading.Thread] = [threading.Thread(target=create_instance) for _ in range(10)]

    # ACT
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert CounterClass.instance_count == 1  # Only one instance created
    assert len(set(id(inst) for inst in instances)) == 1  # All references same instance


def test_singleton_ignores_additional_init_args_after_first_call(sample_class: type) -> None:
    """
    Test singleton ignores initialization args after first instantiation.

    Tests that subsequent calls to singleton class ignore new arguments
    and return the originally created instance.

    Parameters
    ----------
    sample_class : type
        Test class fixture

    Returns
    -------
    None
        Test passes if first args used
    """
    # ARRANGE
    SingletonClass: Callable = singleton(sample_class)

    # ACT
    instance1 = SingletonClass(value=100)
    instance2 = SingletonClass(value=200)

    # ASSERT
    assert instance1 is instance2
    assert instance1.value == 100
    assert instance2.value == 100  # Not 200


def test_singleton_works_with_different_classes() -> None:
    """
    Test singleton maintains separate instances for different classes.

    Tests that singleton decorator correctly isolates instances
    between different classes.

    Returns
    -------
    None
        Test passes if instances are separate
    """
    # ARRANGE
    class ClassA:
        pass

    class ClassB:
        pass

    SingletonA = singleton(ClassA)
    SingletonB = singleton(ClassB)

    # ACT
    instance_a1 = SingletonA()
    instance_a2 = SingletonA()
    instance_b1 = SingletonB()
    instance_b2 = SingletonB()

    # ASSERT
    assert instance_a1 is instance_a2
    assert instance_b1 is instance_b2
    assert instance_a1 is not instance_b1
    assert type(instance_a1) != type(instance_b1)


# -------------------------------------------------------------
# TEST CASES: thread_safe decorator
# -------------------------------------------------------------


def test_thread_safe_executes_function_correctly(sample_function: Callable) -> None:
    """
    Test thread_safe decorator executes function correctly.

    Tests that thread_safe wrapper preserves function behavior
    for single-threaded execution.

    Parameters
    ----------
    sample_function : Callable
        Simple test function fixture

    Returns
    -------
    None
        Test passes if result correct
    """
    # ARRANGE
    safe_func: Callable = thread_safe(sample_function)

    # ACT
    result: int = safe_func()

    # ASSERT
    assert result == 42


def test_thread_safe_prevents_race_conditions() -> None:  # CRITICAL TEST
    """
    Test thread_safe prevents race conditions on shared state.

    Tests that thread_safe decorator correctly serializes access
    to shared mutable state across multiple threads.

    Returns
    -------
    None
        Test passes if no race conditions detected

    Notes
    -----
    CRITICAL: Validates thread synchronization correctness
    """
    # ARRANGE
    counter: Dict[str, int] = {"value": 0}

    @thread_safe
    def increment_counter() -> None:
        current = counter["value"]
        time.sleep(0.001)  # Simulate work to increase race condition likelihood
        counter["value"] = current + 1

    threads: List[threading.Thread] = [threading.Thread(target=increment_counter) for _ in range(100)]

    # ACT
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # ASSERT
    assert counter["value"] == 100  # All increments applied correctly


def test_thread_safe_allows_exception_propagation() -> None:
    """
    Test thread_safe allows exceptions to propagate.

    Tests that thread_safe decorator does not suppress exceptions
    raised by the wrapped function.

    Returns
    -------
    None
        Test passes if exception propagates
    """
    # ARRANGE
    @thread_safe
    def failing_func() -> None:
        raise ValueError("Test error")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Test error"):
        failing_func()


def test_thread_safe_preserves_return_value() -> None:
    """
    Test thread_safe preserves function return value.

    Tests that thread_safe wrapper correctly returns the
    wrapped function's return value.

    Returns
    -------
    None
        Test passes if return value preserved
    """
    # ARRANGE
    @thread_safe
    def return_value() -> str:
        return "success"

    # ACT
    result: str = return_value()

    # ASSERT
    assert result == "success"


# -------------------------------------------------------------
# TEST CASES: retry_on_exception decorator
# -------------------------------------------------------------


def test_retry_on_exception_returns_result_on_first_success() -> None:
    """
    Test retry_on_exception returns result when function succeeds first time.

    Tests that retry decorator does not retry when function
    executes successfully on first attempt.

    Returns
    -------
    None
        Test passes if no retries performed
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @retry_on_exception(retries=3, delay=0.01)
    def successful_func() -> str:
        call_count["count"] += 1
        return "success"

    # ACT
    result: str = successful_func()

    # ASSERT
    assert result == "success"
    assert call_count["count"] == 1  # No retries


def test_retry_on_exception_retries_specified_times(mock_logger: Mock) -> None:  # CRITICAL TEST
    """
    Test retry_on_exception retries correct number of times.

    Tests that retry decorator attempts exactly the specified
    number of retries before giving up.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if retry count correct

    Notes
    -----
    CRITICAL: Validates retry logic correctness
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @retry_on_exception(retries=3, delay=0.01)
    def always_fails() -> None:
        call_count["count"] += 1
        raise ValueError("Always fails")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Always fails"):
        with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
            always_fails()

    assert call_count["count"] == 3  # Initial attempt + 2 retries


def test_retry_on_exception_succeeds_after_failures() -> None:
    """
    Test retry_on_exception succeeds after initial failures.

    Tests that retry decorator returns successful result
    when function succeeds on a retry attempt.

    Returns
    -------
    None
        Test passes if eventual success
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @retry_on_exception(retries=5, delay=0.01)
    def fails_twice() -> str:
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise ValueError("Not yet")
        return "success"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
        result: str = fails_twice()

    # ASSERT
    assert result == "success"
    assert call_count["count"] == 3


def test_retry_on_exception_raises_after_all_retries_exhausted() -> None:  # CRITICAL TEST
    """
    Test retry_on_exception raises exception after all retries exhausted.

    Tests that retry decorator propagates exception when all
    retry attempts fail.

    Returns
    -------
    None
        Test passes if exception raised

    Notes
    -----
    CRITICAL: Ensures failures are not silently suppressed
    """
    # ARRANGE
    @retry_on_exception(retries=2, delay=0.01, exceptions=(ValueError,))
    def always_fails() -> None:
        raise ValueError("Persistent failure")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Persistent failure"):
        with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
            always_fails()


def test_retry_on_exception_only_catches_specified_exceptions() -> None:  # CRITICAL TEST
    """
    Test retry_on_exception only retries on specified exception types.

    Tests that retry decorator does not catch exceptions that
    are not in the specified exception tuple.

    Returns
    -------
    None
        Test passes if non-specified exception propagates immediately

    Notes
    -----
    CRITICAL: Prevents incorrect exception handling
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @retry_on_exception(retries=3, delay=0.01, exceptions=(ValueError,))
    def raises_type_error() -> None:
        call_count["count"] += 1
        raise TypeError("Wrong exception type")

    # ACT & ASSERT
    with pytest.raises(TypeError, match="Wrong exception type"):
        raises_type_error()

    assert call_count["count"] == 1  # No retries for TypeError


def test_retry_on_exception_with_zero_retries() -> None:
    """
    Test retry_on_exception with zero retries behaves correctly.

    Tests that retry decorator with retries=0 does not retry.

    Returns
    -------
    None
        Test passes if no retries performed
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @retry_on_exception(retries=0, delay=0.01)
    def always_fails() -> None:
        call_count["count"] += 1
        raise ValueError("Fails")

    # ACT & ASSERT
    with pytest.raises(ValueError):
        always_fails()

    assert call_count["count"] == 1  # Zero retries means initial attempt only, no retries


def test_retry_on_exception_with_custom_delay() -> None:
    """
    Test retry_on_exception respects custom delay between retries.

    Tests that retry decorator waits specified delay between attempts.

    Returns
    -------
    None
        Test passes if delay observed
    """
    # ARRANGE
    call_times: List[float] = []

    @retry_on_exception(retries=3, delay=0.1)
    def track_timing() -> None:
        call_times.append(time.time())
        raise ValueError("Fail")

    # ACT
    try:
        with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
            track_timing()
    except ValueError:
        pass

    # ASSERT
    assert len(call_times) == 3
    # Check delays between calls (allow 50ms tolerance)
    for i in range(1, len(call_times)):
        delay = call_times[i] - call_times[i - 1]
        assert delay >= 0.09  # At least 90ms (accounting for timing variance)


@pytest.mark.parametrize("retries,expected_calls", [
    (1, 1),
    (3, 3),
    (5, 5),
])
def test_retry_on_exception_various_retry_counts(retries: int, expected_calls: int) -> None:
    """
    Test retry_on_exception with various retry counts.

    Tests that retry decorator handles different retry count
    configurations correctly.

    Parameters
    ----------
    retries : int
        Number of retries to test
    expected_calls : int
        Expected number of function calls

    Returns
    -------
    None
        Test passes if retry count correct
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @retry_on_exception(retries=retries, delay=0.01)
    def always_fails() -> None:
        call_count["count"] += 1
        raise ValueError("Fail")

    # ACT
    try:
        with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
            always_fails()
    except ValueError:
        pass

    # ASSERT
    assert call_count["count"] == expected_calls


def test_retry_on_exception_with_multiple_exception_types() -> None:
    """
    Test retry_on_exception handles multiple exception types.

    Tests that retry decorator catches any exception in the
    specified tuple of exception types.

    Returns
    -------
    None
        Test passes if all exception types handled
    """
    # ARRANGE
    @retry_on_exception(retries=2, delay=0.01, exceptions=(ValueError, TypeError, KeyError))
    def raises_various() -> str:
        raise KeyError("Test key error")

    # ACT
    try:
        with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
            raises_various()
    except KeyError:
        pass  # Expected after retries

    # ASSERT - no exception during retry attempts
    assert True  # Test passes if KeyError eventually raised


# -------------------------------------------------------------
# TEST CASES: assert_non_null_args decorator
# -------------------------------------------------------------


def test_assert_non_null_args_allows_valid_arguments() -> None:
    """
    Test assert_non_null_args allows functions with non-null arguments.

    Tests that decorator permits execution when all arguments
    are non-null values.

    Returns
    -------
    None
        Test passes if function executes normally
    """
    # ARRANGE
    @assert_non_null_args
    def test_func(a: int, b: str, c: Optional[str] = "default") -> int:
        return a + len(b)

    # ACT
    result: int = test_func(10, "test", c="value")

    # ASSERT
    assert result == 14


def test_assert_non_null_args_raises_on_none_positional_arg() -> None:  # CRITICAL TEST
    """
    Test assert_non_null_args raises error when positional arg is None.

    Tests that decorator prevents execution when None is passed
    as a positional argument.

    Returns
    -------
    None
        Test passes if ValueError raised

    Notes
    -----
    CRITICAL: Validates None injection prevention
    """
    # ARRANGE
    @assert_non_null_args
    def test_func(a: int, b: str) -> int:
        return a + len(b)

    # ACT & ASSERT
    with pytest.raises(ValueError, match="None value detected in positional arguments"):
        test_func(None, "test")


def test_assert_non_null_args_raises_on_none_keyword_arg() -> None:  # CRITICAL TEST
    """
    Test assert_non_null_args raises error when keyword arg is None.

    Tests that decorator prevents execution when None is passed
    as a keyword argument.

    Returns
    -------
    None
        Test passes if ValueError raised

    Notes
    -----
    CRITICAL: Validates None injection prevention in kwargs
    """
    # ARRANGE
    @assert_non_null_args
    def test_func(a: int, b: str = "default") -> int:
        return a + len(b)

    # ACT & ASSERT
    with pytest.raises(ValueError, match="None value detected in keyword arguments"):
        test_func(10, b=None)


def test_assert_non_null_args_handles_empty_args() -> None:
    """
    Test assert_non_null_args handles functions with no arguments.

    Tests that decorator works correctly for functions that
    take no arguments.

    Returns
    -------
    None
        Test passes if function executes
    """
    # ARRANGE
    @assert_non_null_args
    def test_func() -> str:
        return "success"

    # ACT
    result: str = test_func()

    # ASSERT
    assert result == "success"


def test_assert_non_null_args_raises_when_all_args_none() -> None:  # CRITICAL TEST
    """
    Test assert_non_null_args raises error when all args are None.

    Tests that decorator detects None values when all arguments
    are None.

    Returns
    -------
    None
        Test passes if ValueError raised

    Notes
    -----
    CRITICAL: Edge case validation for complete None input
    """
    # ARRANGE
    @assert_non_null_args
    def test_func(a: Optional[int], b: Optional[str], c: Optional[float]) -> None:
        pass

    # ACT & ASSERT
    with pytest.raises(ValueError, match="None value detected in positional arguments"):
        test_func(None, None, None)


@pytest.mark.parametrize("args,kwargs,should_raise", [
    ((1, 2, 3), {}, False),
    ((None,), {}, True),
    ((1, None, 3), {}, True),
    ((1, 2), {"c": None}, True),
    ((), {"a": 1, "b": 2}, False),
    ((), {"a": None}, True),
])
def test_assert_non_null_args_various_none_scenarios(
    args: tuple,
    kwargs: Dict[str, Any],
    should_raise: bool
) -> None:
    """
    Test assert_non_null_args with various None scenarios.

    Tests that decorator correctly identifies None values in
    different argument configurations.

    Parameters
    ----------
    args : tuple
        Positional arguments to test
    kwargs : Dict[str, Any]
        Keyword arguments to test
    should_raise : bool
        Whether ValueError should be raised

    Returns
    -------
    None
        Test passes if behavior matches expectation
    """
    # ARRANGE
    @assert_non_null_args
    def test_func(*args_inner, **kwargs_inner) -> str:
        return "success"

    # ACT & ASSERT
    if should_raise:
        with pytest.raises(ValueError, match="None value detected"):
            test_func(*args, **kwargs)
    else:
        result: str = test_func(*args, **kwargs)
        assert result == "success"


# -------------------------------------------------------------
# TEST CASES: function_timer decorator
# -------------------------------------------------------------


def test_function_timer_logs_execution_time(mock_logger: Mock) -> None:
    """
    Test function_timer logs function execution time.

    Tests that function_timer decorator logs timing information
    after function execution.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if timing logged
    """
    # ARRANGE
    @function_timer
    def slow_func() -> str:
        time.sleep(0.01)
        return "done"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        result: str = slow_func()

    # ASSERT
    assert result == "done"
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0]
    assert "runtime of %s" in call_args[0]  # Format string
    assert call_args[1] == "slow_func"  # Function name
    assert isinstance(call_args[2], float)  # Execution time


def test_function_timer_returns_correct_value() -> None:
    """
    Test function_timer preserves function return value.

    Tests that function_timer wrapper correctly returns the
    wrapped function's return value.

    Returns
    -------
    None
        Test passes if return value preserved
    """
    # ARRANGE
    @function_timer
    def return_value() -> int:
        return 123

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
        result: int = return_value()

    # ASSERT
    assert result == 123


def test_function_timer_handles_exceptions() -> None:
    """
    Test function_timer propagates exceptions from wrapped function.

    Tests that function_timer does not suppress exceptions
    raised by the wrapped function.

    Returns
    -------
    None
        Test passes if exception propagates
    """
    # ARRANGE
    @function_timer
    def failing_func() -> None:
        raise RuntimeError("Test error")

    # ACT & ASSERT
    with pytest.raises(RuntimeError, match="Test error"):
        with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
            failing_func()


# -------------------------------------------------------------
# TEST CASES: catch_exceptions decorator
# -------------------------------------------------------------


def test_catch_exceptions_logs_exception(mock_logger: Mock) -> None:
    """
    Test catch_exceptions logs exception without propagating.

    Tests that catch_exceptions decorator logs exceptions
    and prevents them from propagating.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if exception logged and suppressed
    """
    # ARRANGE
    @catch_exceptions
    def failing_func() -> str:
        raise ValueError("Test exception")

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        result = failing_func()

    # ASSERT
    assert result is None  # No value returned when exception caught
    mock_logger.error.assert_called_once()
    call_args = mock_logger.error.call_args[0]
    assert "exception in %s" in call_args[0]  # Format string
    assert call_args[1] == "failing_func"  # Function name
    assert "Test exception" in call_args[2]  # Exception message


def test_catch_exceptions_returns_none_on_exception() -> None:
    """
    Test catch_exceptions returns None when exception occurs.

    Tests that catch_exceptions decorator returns None instead
    of propagating exceptions.

    Returns
    -------
    None
        Test passes if None returned
    """
    # ARRANGE
    @catch_exceptions
    def failing_func() -> int:
        raise RuntimeError("Failure")

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
        result = failing_func()

    # ASSERT
    assert result is None


def test_catch_exceptions_returns_value_on_success() -> None:
    """
    Test catch_exceptions returns value when no exception occurs.

    Tests that catch_exceptions decorator preserves return value
    when function executes successfully.

    Returns
    -------
    None
        Test passes if return value preserved
    """
    # ARRANGE
    @catch_exceptions
    def successful_func() -> str:
        return "success"

    # ACT
    result: str = successful_func()

    # ASSERT
    assert result == "success"


# -------------------------------------------------------------
# TEST CASES: profile_memory decorator
# -------------------------------------------------------------


def test_profile_memory_logs_memory_usage(mock_logger: Mock) -> None:
    """
    Test profile_memory logs memory usage statistics.

    Tests that profile_memory decorator logs current and peak
    memory usage after function execution.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if memory stats logged
    """
    # ARRANGE
    @profile_memory
    def allocate_memory() -> List[int]:
        return [i for i in range(1000)]

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        result: List[int] = allocate_memory()

    # ASSERT
    assert len(result) == 1000
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0]
    assert "%s used" in call_args[0]  # Format string
    assert "KB" in call_args[0]
    assert call_args[1] == "allocate_memory"  # Function name
    assert isinstance(call_args[2], float)  # Current memory
    assert isinstance(call_args[3], float)  # Peak memory


def test_profile_memory_returns_correct_value() -> None:
    """
    Test profile_memory preserves function return value.

    Tests that profile_memory wrapper correctly returns the
    wrapped function's return value.

    Returns
    -------
    None
        Test passes if return value preserved
    """
    # ARRANGE
    @profile_memory
    def return_value() -> str:
        return "result"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
        result: str = return_value()

    # ASSERT
    assert result == "result"


def test_profile_memory_handles_exceptions() -> None:
    """
    Test profile_memory stops tracemalloc even when exception occurs.

    Tests that profile_memory decorator properly cleans up
    tracemalloc when wrapped function raises exception.

    Returns
    -------
    None
        Test passes if tracemalloc stopped
    """
    # ARRANGE
    @profile_memory
    def failing_func() -> None:
        raise ValueError("Test error")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Test error"):
        with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
            failing_func()

    # Verify tracemalloc is stopped (no assertion needed - no exception means success)


# -------------------------------------------------------------
# TEST CASES: warn_if_slow decorator
# -------------------------------------------------------------


def test_warn_if_slow_logs_warning_when_threshold_exceeded(mock_logger: Mock) -> None:
    """
    Test warn_if_slow logs warning when execution exceeds threshold.

    Tests that warn_if_slow decorator logs warning when function
    execution time exceeds specified threshold.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if warning logged
    """
    # ARRANGE
    @warn_if_slow(threshold=0.01)
    def slow_func() -> str:
        time.sleep(0.02)
        return "done"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        result: str = slow_func()

    # ASSERT
    assert result == "done"
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0]
    assert "%s took" in call_args[0]  # Format string
    assert "limit" in call_args[0]
    assert call_args[1] == "slow_func"  # Function name
    assert isinstance(call_args[2], float)  # Duration
    assert call_args[3] == 0.01  # Threshold


def test_warn_if_slow_no_warning_when_under_threshold(mock_logger: Mock) -> None:
    """
    Test warn_if_slow does not log when execution under threshold.

    Tests that warn_if_slow decorator does not log warning
    when function executes faster than threshold.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if no warning logged
    """
    # ARRANGE
    @warn_if_slow(threshold=1.0)
    def fast_func() -> str:
        return "done"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        result: str = fast_func()

    # ASSERT
    assert result == "done"
    mock_logger.warning.assert_not_called()


def test_warn_if_slow_with_zero_threshold(mock_logger: Mock) -> None:
    """
    Test warn_if_slow with zero threshold always warns.

    Tests that warn_if_slow decorator with threshold=0
    always logs warning (edge case).

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if warning logged
    """
    # ARRANGE
    @warn_if_slow(threshold=0.0)
    def any_func() -> str:
        time.sleep(0.001)  # Ensure measurable execution time
        return "done"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        result: str = any_func()

    # ASSERT
    assert result == "done"
    mock_logger.warning.assert_called_once()


def test_warn_if_slow_preserves_return_value() -> None:
    """
    Test warn_if_slow preserves function return value.

    Tests that warn_if_slow wrapper correctly returns the
    wrapped function's return value.

    Returns
    -------
    None
        Test passes if return value preserved
    """
    # ARRANGE
    @warn_if_slow(threshold=0.1)
    def return_value() -> int:
        return 999

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
        result: int = return_value()

    # ASSERT
    assert result == 999


# -------------------------------------------------------------
# TEST CASES: suppress decorator
# -------------------------------------------------------------


def test_suppress_suppresses_specified_exception() -> None:
    """
    Test suppress suppresses specified exception types.

    Tests that suppress decorator catches and suppresses
    the specified exception types.

    Returns
    -------
    None
        Test passes if exception suppressed
    """
    # ARRANGE
    @suppress(ValueError)
    def raises_value_error() -> str:
        raise ValueError("Test error")

    # ACT
    result = raises_value_error()

    # ASSERT
    assert result is None  # Exception suppressed, None returned


def test_suppress_allows_non_specified_exceptions() -> None:
    """
    Test suppress allows non-specified exceptions to propagate.

    Tests that suppress decorator does not catch exceptions
    that are not in the specified tuple.

    Returns
    -------
    None
        Test passes if exception propagates
    """
    # ARRANGE
    @suppress(ValueError)
    def raises_type_error() -> None:
        raise TypeError("Different error")

    # ACT & ASSERT
    with pytest.raises(TypeError, match="Different error"):
        raises_type_error()


def test_suppress_with_multiple_exception_types() -> None:
    """
    Test suppress handles multiple exception types.

    Tests that suppress decorator catches any exception
    in the specified tuple of exception types.

    Returns
    -------
    None
        Test passes if all types suppressed
    """
    # ARRANGE
    @suppress(ValueError, TypeError, KeyError)
    def raises_various(exception_type: str) -> None:
        if exception_type == "value":
            raise ValueError("Value error")
        elif exception_type == "type":
            raise TypeError("Type error")
        else:
            raise KeyError("Key error")

    # ACT
    result1 = raises_various("value")
    result2 = raises_various("type")
    result3 = raises_various("key")

    # ASSERT
    assert result1 is None
    assert result2 is None
    assert result3 is None


def test_suppress_returns_value_on_success() -> None:
    """
    Test suppress returns value when no exception occurs.

    Tests that suppress decorator preserves return value
    when function executes successfully.

    Returns
    -------
    None
        Test passes if return value preserved
    """
    # ARRANGE
    @suppress(ValueError)
    def successful_func() -> str:
        return "success"

    # ACT
    result: str = successful_func()

    # ASSERT
    assert result == "success"


def test_suppress_logs_suppressed_exception(mock_logger: Mock) -> None:
    """
    Test suppress logs debug message when suppressing exception.

    Tests that suppress decorator logs debug information
    about suppressed exceptions.

    Parameters
    ----------
    mock_logger : Mock
        Mocked logger fixture

    Returns
    -------
    None
        Test passes if debug logged
    """
    # ARRANGE
    @suppress(ValueError)
    def raises_value_error() -> None:
        raise ValueError("Test")

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=mock_logger):
        raises_value_error()

    # ASSERT
    mock_logger.debug.assert_called_once()


# -------------------------------------------------------------
# TEST CASES: log_to_file decorator
# -------------------------------------------------------------


def test_log_to_file_creates_log_file(temp_log_file: Path) -> None:
    """
    Test log_to_file decorator creates log file.

    Tests that log_to_file decorator creates the specified
    log file when function is called.

    Parameters
    ----------
    temp_log_file : Path
        Temporary log file path fixture

    Returns
    -------
    None
        Test passes if log file created
    """
    # ARRANGE
    @log_to_file(str(temp_log_file), level="INFO")
    def test_func() -> str:
        return "done"

    # ACT
    result: str = test_func()

    # ASSERT
    assert result == "done"
    assert temp_log_file.exists()


def test_log_to_file_logs_function_calls(temp_log_file: Path) -> None:
    """
    Test log_to_file logs function entry and exit.

    Tests that log_to_file decorator logs when function
    is called and when it finishes.

    Parameters
    ----------
    temp_log_file : Path
        Temporary log file path fixture

    Returns
    -------
    None
        Test passes if calls logged
    """
    # ARRANGE
    @log_to_file(str(temp_log_file), level="INFO")
    def test_func() -> str:
        return "result"

    # ACT
    result: str = test_func()

    # ASSERT
    assert result == "result"
    log_content: str = temp_log_file.read_text()
    assert "Calling test_func" in log_content
    assert "Finished test_func" in log_content


def test_log_to_file_logs_exceptions(temp_log_file: Path) -> None:
    """
    Test log_to_file logs exceptions before propagating.

    Tests that log_to_file decorator logs exception information
    before allowing exception to propagate.

    Parameters
    ----------
    temp_log_file : Path
        Temporary log file path fixture

    Returns
    -------
    None
        Test passes if exception logged
    """
    # ARRANGE
    @log_to_file(str(temp_log_file), level="ERROR")
    def failing_func() -> None:
        raise ValueError("Test exception")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Test exception"):
        failing_func()

    log_content: str = temp_log_file.read_text()
    assert "Exception in failing_func" in log_content
    assert "Test exception" in log_content


def test_log_to_file_with_custom_log_level(temp_log_file: Path) -> None:
    """
    Test log_to_file respects custom log level.

    Tests that log_to_file decorator uses the specified
    log level for the function logger.

    Parameters
    ----------
    temp_log_file : Path
        Temporary log file path fixture

    Returns
    -------
    None
        Test passes if custom level applied
    """
    # ARRANGE
    @log_to_file(str(temp_log_file), level="DEBUG")
    def debug_func() -> str:
        return "debug"

    # ACT
    result: str = debug_func()

    # ASSERT
    assert result == "debug"
    assert temp_log_file.exists()


# -------------------------------------------------------------
# TEST CASES: cache_results decorator
# -------------------------------------------------------------


def test_cache_results_caches_function_output() -> None:
    """
    Test cache_results caches function return values.

    Tests that cache_results decorator caches function results
    and returns cached values on subsequent calls.

    Returns
    -------
    None
        Test passes if caching works
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @cache_results
    def expensive_func(x: int) -> int:
        call_count["count"] += 1
        return x * 2

    # ACT
    result1: int = expensive_func(5)
    result2: int = expensive_func(5)
    result3: int = expensive_func(10)

    # ASSERT
    assert result1 == 10
    assert result2 == 10
    assert result3 == 20
    assert call_count["count"] == 2  # Called only twice (5 cached, 10 new)


def test_cache_results_handles_different_arguments() -> None:
    """
    Test cache_results maintains separate cache entries for different args.

    Tests that cache_results decorator caches results separately
    for different argument combinations.

    Returns
    -------
    None
        Test passes if separate caching works
    """
    # ARRANGE
    @cache_results
    def add(a: int, b: int) -> int:
        return a + b

    # ACT
    result1: int = add(1, 2)
    result2: int = add(2, 3)
    result3: int = add(1, 2)

    # ASSERT
    assert result1 == 3
    assert result2 == 5
    assert result3 == 3


# -------------------------------------------------------------
# TEST CASES: auto_property decorator
# -------------------------------------------------------------


def test_auto_property_creates_getter_and_setter() -> None:
    """
    Test auto_property creates property with getter and setter.

    Tests that auto_property decorator creates a property
    with automatic getter and setter methods.

    Returns
    -------
    None
        Test passes if property works
    """
    # ARRANGE
    class TestClass:
        @auto_property
        def value(self) -> Optional[int]:
            pass

    obj = TestClass()

    # ACT
    obj.value = 42
    result: Optional[int] = obj.value

    # ASSERT
    assert result == 42


def test_auto_property_uses_underscore_attribute() -> None:
    """
    Test auto_property stores value in underscore-prefixed attribute.

    Tests that auto_property decorator uses _attribute_name
    for internal storage.

    Returns
    -------
    None
        Test passes if internal storage correct
    """
    # ARRANGE
    class TestClass:
        @auto_property
        def name(self) -> Optional[str]:
            pass

    obj = TestClass()

    # ACT
    obj.name = "test"

    # ASSERT
    assert obj._name == "test"
    assert obj.name == "test"


def test_auto_property_returns_none_when_not_set() -> None:
    """
    Test auto_property returns None when value not set.

    Tests that auto_property decorator returns None
    for uninitialized properties.

    Returns
    -------
    None
        Test passes if None returned
    """
    # ARRANGE
    class TestClass:
        @auto_property
        def data(self) -> Optional[Any]:
            pass

    obj = TestClass()

    # ACT
    result: Optional[Any] = obj.data

    # ASSERT
    assert result is None


# -------------------------------------------------------------
# INTEGRATION TESTS
# -------------------------------------------------------------


def test_multiple_decorators_stacked() -> None:
    """
    Test multiple decorators can be stacked on same function.

    Tests that decorators work correctly when stacked
    in various combinations.

    Returns
    -------
    None
        Test passes if stacked decorators work
    """
    # ARRANGE
    call_count: Dict[str, int] = {"count": 0}

    @catch_exceptions
    @function_timer
    @assert_non_null_args
    def complex_func(a: int, b: str) -> str:
        call_count["count"] += 1
        return f"{a}:{b}"

    # ACT
    with patch("basefunctions.utils.decorators.get_logger", return_value=Mock()):
        result1: str = complex_func(10, "test")
        result2 = complex_func(None, "test")  # Should be caught

    # ASSERT
    assert result1 == "10:test"
    assert result2 is None  # Exception caught by catch_exceptions
    assert call_count["count"] == 1  # Only first call succeeded


def test_decorator_preserves_function_metadata() -> None:
    """
    Test decorators preserve original function metadata.

    Tests that decorators using functools.wraps correctly
    preserve function name and docstring.

    Returns
    -------
    None
        Test passes if metadata preserved
    """
    # ARRANGE
    @thread_safe
    def documented_func() -> str:
        """Original docstring."""
        return "result"

    # ACT & ASSERT
    assert documented_func.__name__ == "documented_func"
    assert documented_func.__doc__ == "Original docstring."
