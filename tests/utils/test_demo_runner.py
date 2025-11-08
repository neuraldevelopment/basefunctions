"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Pytest test suite for demo_runner module.
 Tests class-based demo runner with auto-execution and structured output.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from unittest.mock import Mock, MagicMock, patch, call
import time

# Project imports
from basefunctions.utils.demo_runner import (
    DemoRunner,
    run,
    test,
    _get_global_runner,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_atexit(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """
    Mock atexit.register to prevent automatic execution during tests.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture

    Returns
    -------
    Mock
        Mocked atexit.register function

    Notes
    -----
    Prevents DemoRunner from registering auto-run on instantiation.
    """
    # ARRANGE
    mock_register: Mock = Mock()
    monkeypatch.setattr("basefunctions.utils.demo_runner.atexit.register", mock_register)

    # RETURN
    return mock_register


@pytest.fixture
def demo_runner(mock_atexit: Mock) -> DemoRunner:
    """
    Create fresh DemoRunner instance for isolated testing.

    Parameters
    ----------
    mock_atexit : Mock
        Mocked atexit.register to prevent auto-execution

    Returns
    -------
    DemoRunner
        Fresh DemoRunner instance with mocked atexit

    Notes
    -----
    Each test gets isolated DemoRunner to avoid state leakage.
    """
    # ARRANGE & RETURN
    return DemoRunner()


@pytest.fixture
def sample_test_class() -> type:
    """
    Provide valid test class with decorated test methods.

    Returns
    -------
    type
        Test class with @test decorated methods and setup/teardown

    Notes
    -----
    Simulates typical test class structure for DemoRunner.
    """
    # ARRANGE
    class SampleTest:
        def __init__(self) -> None:
            self.setup_called: bool = False
            self.teardown_called: bool = False
            self.test_results: List[str] = []

        def setup(self) -> None:
            """Setup method called before tests."""
            self.setup_called = True

        def test_method_one(self) -> None:
            """First test method."""
            self.test_results.append("test_one")

        def test_method_two(self) -> None:
            """Second test method."""
            self.test_results.append("test_two")

        def teardown(self) -> None:
            """Teardown method called after tests."""
            self.teardown_called = True

    # Mark test methods with @test decorator
    SampleTest.test_method_one._test_name = "test_one"
    SampleTest.test_method_two._test_name = "test_two"

    # RETURN
    return SampleTest


@pytest.fixture
def failing_test_class() -> type:
    """
    Provide test class with methods that raise exceptions.

    Returns
    -------
    type
        Test class where setup, tests, and teardown raise exceptions

    Notes
    -----
    Used to test error handling and exception propagation.
    """
    # ARRANGE
    class FailingTest:
        def setup(self) -> None:
            """Setup that raises exception."""
            raise RuntimeError("Setup failed")

        def test_failing_method(self) -> None:
            """Test method that raises exception."""
            raise ValueError("Test failed")

        def teardown(self) -> None:
            """Teardown that raises exception."""
            raise RuntimeError("Teardown failed")

    # Mark test method
    FailingTest.test_failing_method._test_name = "failing_test"

    # RETURN
    return FailingTest


@pytest.fixture
def class_without_setup_teardown() -> type:
    """
    Provide test class without setup/teardown methods.

    Returns
    -------
    type
        Test class with only test methods, no lifecycle hooks

    Notes
    -----
    Tests that DemoRunner handles optional setup/teardown correctly.
    """
    # ARRANGE
    class MinimalTest:
        def test_simple(self) -> None:
            """Simple test without setup/teardown."""
            pass

    # Mark test method
    MinimalTest.test_simple._test_name = "simple_test"

    # RETURN
    return MinimalTest


@pytest.fixture
def class_with_no_tests() -> type:
    """
    Provide test class with no decorated test methods.

    Returns
    -------
    type
        Test class without any @test decorated methods

    Notes
    -----
    Tests edge case where class has no tests to execute.
    """
    # ARRANGE
    class EmptyTest:
        def setup(self) -> None:
            """Setup with no tests."""
            pass

        def regular_method(self) -> None:
            """Regular method, not a test."""
            pass

    # RETURN
    return EmptyTest


@pytest.fixture
def non_instantiable_class() -> type:
    """
    Provide class that cannot be instantiated.

    Returns
    -------
    type
        Class with __init__ that raises exception

    Notes
    -----
    Tests handling of instantiation failures.
    """
    # ARRANGE
    class BrokenTest:
        def __init__(self) -> None:
            raise TypeError("Cannot instantiate this class")

        def test_never_runs(self) -> None:
            """This test will never run."""
            pass

    # Mark test method
    BrokenTest.test_never_runs._test_name = "never_runs"

    # RETURN
    return BrokenTest


# -------------------------------------------------------------
# TEST CASES: DemoRunner.__init__
# -------------------------------------------------------------


def test_demo_runner_initializes_with_empty_collections(mock_atexit: Mock) -> None:
    """
    Test DemoRunner initializes with empty test classes and results.

    Tests that new DemoRunner instance starts with no registered
    tests and no results collected.

    Parameters
    ----------
    mock_atexit : Mock
        Mocked atexit.register

    Returns
    -------
    None
        Test passes if initialization is correct
    """
    # ARRANGE & ACT
    runner: DemoRunner = DemoRunner()

    # ASSERT
    assert runner._test_classes == []
    assert runner._results == []


def test_demo_runner_registers_atexit_handler(mock_atexit: Mock) -> None:
    """
    Test DemoRunner registers auto-run with atexit on initialization.

    Tests that DemoRunner.__init__ calls atexit.register with
    the _auto_run method.

    Parameters
    ----------
    mock_atexit : Mock
        Mocked atexit.register

    Returns
    -------
    None
        Test passes if atexit.register called correctly
    """
    # ARRANGE & ACT
    runner: DemoRunner = DemoRunner()

    # ASSERT
    mock_atexit.assert_called_once_with(runner._auto_run)


# -------------------------------------------------------------
# TEST CASES: DemoRunner.run (decorator)
# -------------------------------------------------------------


def test_run_decorator_registers_test_class(demo_runner: DemoRunner, sample_test_class: type) -> None:
    """
    Test run decorator registers test class with suite name.

    Tests that using @run decorator adds test class to
    internal _test_classes list.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class fixture

    Returns
    -------
    None
        Test passes if class registered correctly
    """
    # ARRANGE
    suite_name: str = "sample_suite"

    # ACT
    decorator: Callable = demo_runner.run(suite_name)
    decorated_class: type = decorator(sample_test_class)

    # ASSERT
    assert len(demo_runner._test_classes) == 1
    assert demo_runner._test_classes[0] == (suite_name, sample_test_class)


def test_run_decorator_returns_class_unchanged(demo_runner: DemoRunner, sample_test_class: type) -> None:
    """
    Test run decorator returns original class unchanged.

    Tests that @run decorator does not modify the test class,
    allowing normal class usage.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class fixture

    Returns
    -------
    None
        Test passes if class returned unchanged
    """
    # ARRANGE
    suite_name: str = "sample_suite"

    # ACT
    decorator: Callable = demo_runner.run(suite_name)
    decorated_class: type = decorator(sample_test_class)

    # ASSERT
    assert decorated_class is sample_test_class


def test_run_decorator_accepts_multiple_classes(demo_runner: DemoRunner, sample_test_class: type) -> None:
    """
    Test run decorator can register multiple test classes.

    Tests that multiple test classes can be registered
    with different suite names.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class fixture

    Returns
    -------
    None
        Test passes if multiple classes registered
    """
    # ARRANGE
    class SecondTest:
        def test_method(self) -> None:
            """Second test method."""
            pass

    SecondTest.test_method._test_name = "test_second"

    # ACT
    demo_runner.run("suite_one")(sample_test_class)
    demo_runner.run("suite_two")(SecondTest)

    # ASSERT
    assert len(demo_runner._test_classes) == 2
    assert demo_runner._test_classes[0][0] == "suite_one"
    assert demo_runner._test_classes[1][0] == "suite_two"


def test_run_decorator_handles_empty_suite_name(demo_runner: DemoRunner, sample_test_class: type) -> None:
    """
    Test run decorator accepts empty string as suite name.

    Tests that decorator works with edge case of empty suite name.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class fixture

    Returns
    -------
    None
        Test passes if empty suite name handled
    """
    # ARRANGE
    suite_name: str = ""

    # ACT
    decorator: Callable = demo_runner.run(suite_name)
    decorated_class: type = decorator(sample_test_class)

    # ASSERT
    assert len(demo_runner._test_classes) == 1
    assert demo_runner._test_classes[0][0] == ""


# -------------------------------------------------------------
# TEST CASES: test decorator (module-level)
# -------------------------------------------------------------


def test_test_decorator_marks_method_with_test_name() -> None:
    """
    Test @test decorator adds _test_name attribute to method.

    Tests that @test decorator sets _test_name attribute
    on decorated function for DemoRunner detection.

    Returns
    -------
    None
        Test passes if _test_name attribute set correctly
    """
    # ARRANGE
    test_name: str = "my_test_case"

    # ACT
    @test(test_name)
    def sample_method() -> None:
        """Sample test method."""
        pass

    # ASSERT
    assert hasattr(sample_method, "_test_name")
    assert sample_method._test_name == test_name


def test_test_decorator_preserves_original_function() -> None:
    """
    Test @test decorator preserves original function behavior.

    Tests that decorated function still executes normally
    and returns expected values.

    Returns
    -------
    None
        Test passes if function behavior preserved
    """
    # ARRANGE
    @test("test_case")
    def sample_method() -> str:
        """Sample method that returns value."""
        return "result"

    # ACT
    result: str = sample_method()

    # ASSERT
    assert result == "result"


def test_test_decorator_handles_empty_test_name() -> None:
    """
    Test @test decorator accepts empty string as test name.

    Tests edge case of empty test name string.

    Returns
    -------
    None
        Test passes if empty name handled
    """
    # ARRANGE & ACT
    @test("")
    def sample_method() -> None:
        """Sample method with empty test name."""
        pass

    # ASSERT
    assert hasattr(sample_method, "_test_name")
    assert sample_method._test_name == ""


# -------------------------------------------------------------
# TEST CASES: DemoRunner._get_test_methods (IMPORTANT)
# -------------------------------------------------------------


def test_get_test_methods_finds_decorated_methods(demo_runner: DemoRunner, sample_test_class: type) -> None:
    """
    Test _get_test_methods finds all @test decorated methods.

    Tests that method correctly identifies and extracts
    methods marked with @test decorator.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class with decorated methods

    Returns
    -------
    None
        Test passes if all decorated methods found
    """
    # ACT
    test_methods: List[Tuple[str, Callable]] = demo_runner._get_test_methods(sample_test_class)

    # ASSERT
    assert len(test_methods) == 2
    test_names: List[str] = [name for name, _ in test_methods]
    assert "test_one" in test_names
    assert "test_two" in test_names


def test_get_test_methods_ignores_undecorated_methods(demo_runner: DemoRunner) -> None:
    """
    Test _get_test_methods ignores methods without @test decorator.

    Tests that regular methods (setup, teardown, helpers) are
    not included in test methods list.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if undecorated methods ignored
    """
    # ARRANGE
    class MixedTest:
        def setup(self) -> None:
            """Setup method without decorator."""
            pass

        def helper_method(self) -> None:
            """Helper method without decorator."""
            pass

        def test_decorated(self) -> None:
            """Decorated test method."""
            pass

    MixedTest.test_decorated._test_name = "decorated_test"

    # ACT
    test_methods: List[Tuple[str, Callable]] = demo_runner._get_test_methods(MixedTest)

    # ASSERT
    assert len(test_methods) == 1
    assert test_methods[0][0] == "decorated_test"


def test_get_test_methods_returns_empty_list_for_class_without_tests(
    demo_runner: DemoRunner, class_with_no_tests: type
) -> None:
    """
    Test _get_test_methods returns empty list when no tests found.

    Tests edge case where test class has no @test decorated methods.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    class_with_no_tests : type
        Test class without decorated methods

    Returns
    -------
    None
        Test passes if empty list returned
    """
    # ACT
    test_methods: List[Tuple[str, Callable]] = demo_runner._get_test_methods(class_with_no_tests)

    # ASSERT
    assert test_methods == []


def test_get_test_methods_handles_mixed_decorated_undecorated(demo_runner: DemoRunner) -> None:
    """
    Test _get_test_methods correctly filters mixed method types.

    Tests that method extracts only decorated methods from
    class with both decorated and undecorated methods.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if only decorated methods extracted
    """
    # ARRANGE
    class MixedMethodsTest:
        def undecorated_one(self) -> None:
            """Not a test."""
            pass

        def test_decorated_one(self) -> None:
            """Test one."""
            pass

        def undecorated_two(self) -> None:
            """Not a test."""
            pass

        def test_decorated_two(self) -> None:
            """Test two."""
            pass

    MixedMethodsTest.test_decorated_one._test_name = "test_1"
    MixedMethodsTest.test_decorated_two._test_name = "test_2"

    # ACT
    test_methods: List[Tuple[str, Callable]] = demo_runner._get_test_methods(MixedMethodsTest)

    # ASSERT
    assert len(test_methods) == 2
    test_names: List[str] = [name for name, _ in test_methods]
    assert "test_1" in test_names
    assert "test_2" in test_names


# -------------------------------------------------------------
# TEST CASES: DemoRunner._execute_test_suite (CRITICAL)
# -------------------------------------------------------------


def test_execute_test_suite_runs_all_test_methods_successfully(
    demo_runner: DemoRunner, sample_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite executes all decorated test methods.

    Tests that all @test decorated methods are found and executed
    when test suite runs successfully.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class with multiple tests

    Returns
    -------
    None
        Test passes if all test methods executed
    """
    # ARRANGE
    suite_name: str = "sample_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, sample_test_class)

    # ASSERT
    # Should have setup + 2 tests + teardown = 4 results
    assert len(results) == 4
    test_names: List[str] = [name for name, _, _, _ in results]
    assert "sample_suite.setup" in test_names
    assert "sample_suite.test_one" in test_names
    assert "sample_suite.test_two" in test_names
    assert "sample_suite.teardown" in test_names


def test_execute_test_suite_runs_setup_and_teardown(
    demo_runner: DemoRunner, sample_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite calls setup and teardown methods.

    Tests that lifecycle methods (setup/teardown) are executed
    before and after test methods.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class with setup/teardown

    Returns
    -------
    None
        Test passes if setup and teardown called
    """
    # ARRANGE
    suite_name: str = "sample_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, sample_test_class)

    # ASSERT
    result_dict: Dict[str, bool] = {name: success for name, success, _, _ in results}
    assert result_dict["sample_suite.setup"] is True
    assert result_dict["sample_suite.teardown"] is True


def test_execute_test_suite_records_timing_correctly(
    demo_runner: DemoRunner, sample_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite records execution duration for each test.

    Tests that timing information is captured using time.perf_counter
    and recorded in results.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class

    Returns
    -------
    None
        Test passes if timing recorded correctly
    """
    # ARRANGE
    suite_name: str = "sample_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, sample_test_class)

    # ASSERT
    for name, success, duration, error in results:
        assert isinstance(duration, float)
        assert duration >= 0.0


def test_execute_test_suite_continues_when_setup_fails(
    demo_runner: DemoRunner, failing_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite continues test execution when setup fails.

    Tests that test methods are still executed even if setup
    raises an exception.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    failing_test_class : type
        Test class with failing setup

    Returns
    -------
    None
        Test passes if tests run despite setup failure
    """
    # ARRANGE
    suite_name: str = "failing_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, failing_test_class)

    # ASSERT
    result_dict: Dict[str, Tuple[bool, str]] = {name: (success, error) for name, success, _, error in results}

    # Setup should have failed
    assert result_dict["failing_suite.setup"][0] is False
    assert "Setup failed" in result_dict["failing_suite.setup"][1]

    # Test should still run (and fail)
    assert "failing_suite.failing_test" in result_dict


def test_execute_test_suite_continues_when_test_method_fails(
    demo_runner: DemoRunner, failing_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite records failure when test method raises exception.

    Tests that exceptions in test methods are caught and recorded
    as failures with error messages.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    failing_test_class : type
        Test class with failing test method

    Returns
    -------
    None
        Test passes if test failure recorded correctly
    """
    # ARRANGE
    suite_name: str = "failing_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, failing_test_class)

    # ASSERT
    test_results: Dict[str, Tuple[bool, str]] = {
        name: (success, error) for name, success, _, error in results if "failing_test" in name
    }

    assert len(test_results) == 1
    test_name: str = "failing_suite.failing_test"
    assert test_results[test_name][0] is False
    assert "Test failed" in test_results[test_name][1]


def test_execute_test_suite_continues_when_teardown_fails(
    demo_runner: DemoRunner, failing_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite records teardown failure correctly.

    Tests that teardown exceptions are caught and recorded
    without preventing other test execution.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    failing_test_class : type
        Test class with failing teardown

    Returns
    -------
    None
        Test passes if teardown failure recorded
    """
    # ARRANGE
    suite_name: str = "failing_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, failing_test_class)

    # ASSERT
    result_dict: Dict[str, Tuple[bool, str]] = {name: (success, error) for name, success, _, error in results}

    # Teardown should have failed
    assert result_dict["failing_suite.teardown"][0] is False
    assert "Teardown failed" in result_dict["failing_suite.teardown"][1]


def test_execute_test_suite_handles_instantiation_failure(
    demo_runner: DemoRunner, non_instantiable_class: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite handles class instantiation failure.

    Tests that if test class __init__ raises exception, it is
    caught and recorded as instantiation failure.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    non_instantiable_class : type
        Class that cannot be instantiated

    Returns
    -------
    None
        Test passes if instantiation failure recorded
    """
    # ARRANGE
    suite_name: str = "broken_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, non_instantiable_class)

    # ASSERT
    assert len(results) == 1
    name, success, duration, error = results[0]
    assert name == "broken_suite.instantiation"
    assert success is False
    assert "Cannot instantiate this class" in error


def test_execute_test_suite_handles_class_without_setup(
    demo_runner: DemoRunner, class_without_setup_teardown: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite works when class has no setup method.

    Tests that setup is optional and test execution proceeds
    without it.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    class_without_setup_teardown : type
        Test class without setup/teardown

    Returns
    -------
    None
        Test passes if tests run without setup
    """
    # ARRANGE
    suite_name: str = "minimal_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(
        suite_name, class_without_setup_teardown
    )

    # ASSERT
    result_names: List[str] = [name for name, _, _, _ in results]
    assert "minimal_suite.setup" not in result_names
    assert "minimal_suite.simple_test" in result_names


def test_execute_test_suite_handles_class_without_teardown(
    demo_runner: DemoRunner, class_without_setup_teardown: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite works when class has no teardown method.

    Tests that teardown is optional and test execution completes
    without it.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    class_without_setup_teardown : type
        Test class without setup/teardown

    Returns
    -------
    None
        Test passes if tests run without teardown
    """
    # ARRANGE
    suite_name: str = "minimal_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(
        suite_name, class_without_setup_teardown
    )

    # ASSERT
    result_names: List[str] = [name for name, _, _, _ in results]
    assert "minimal_suite.teardown" not in result_names
    assert "minimal_suite.simple_test" in result_names


def test_execute_test_suite_handles_class_with_no_test_methods(
    demo_runner: DemoRunner, class_with_no_tests: type
) -> None:  # CRITICAL TEST
    """
    Test _execute_test_suite handles class with no decorated test methods.

    Tests edge case where class has setup/teardown but no tests,
    ensuring no crash occurs.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    class_with_no_tests : type
        Test class without test methods

    Returns
    -------
    None
        Test passes if handled gracefully
    """
    # ARRANGE
    suite_name: str = "empty_suite"

    # ACT
    results: List[Tuple[str, bool, float, str]] = demo_runner._execute_test_suite(suite_name, class_with_no_tests)

    # ASSERT
    # Should only have setup, no tests, no teardown (since no teardown defined)
    assert len(results) == 1
    assert results[0][0] == "empty_suite.setup"


# -------------------------------------------------------------
# TEST CASES: DemoRunner._format_results_table (IMPORTANT)
# -------------------------------------------------------------


def test_format_results_table_creates_table_with_headers(demo_runner: DemoRunner) -> None:
    """
    Test _format_results_table creates formatted table with headers.

    Tests that table formatting includes column headers
    (Test Name, Status, Duration).

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if headers present in output
    """
    # ARRANGE
    demo_runner._results = [
        ("test_suite.test_one", True, 0.123, ""),
        ("test_suite.test_two", False, 0.456, "Error message"),
    ]

    # ACT
    table: str = demo_runner._format_results_table()

    # ASSERT
    assert "Test Name" in table
    assert "Status" in table
    assert "Duration" in table


def test_format_results_table_includes_all_results(demo_runner: DemoRunner) -> None:
    """
    Test _format_results_table includes all test results in output.

    Tests that all results from _results list are included
    in formatted table.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if all results in table
    """
    # ARRANGE
    demo_runner._results = [
        ("test_suite.test_one", True, 0.123, ""),
        ("test_suite.test_two", False, 0.456, "Error"),
        ("test_suite.test_three", True, 0.789, ""),
    ]

    # ACT
    table: str = demo_runner._format_results_table()

    # ASSERT
    assert "test_suite.test_one" in table
    assert "test_suite.test_two" in table
    assert "test_suite.test_three" in table
    assert "PASSED" in table
    assert "FAILED" in table


def test_format_results_table_handles_empty_results(demo_runner: DemoRunner) -> None:
    """
    Test _format_results_table handles empty results list gracefully.

    Tests edge case where no tests have been executed,
    returning informative message.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if appropriate message returned
    """
    # ARRANGE
    demo_runner._results = []

    # ACT
    table: str = demo_runner._format_results_table()

    # ASSERT
    assert table == "No test results available"


def test_format_results_table_formats_duration_correctly(demo_runner: DemoRunner) -> None:
    """
    Test _format_results_table formats duration with 3 decimal places.

    Tests that duration values are formatted as seconds with
    3 decimal precision (e.g., "0.123s").

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if duration formatted correctly
    """
    # ARRANGE
    demo_runner._results = [("test_suite.test_one", True, 0.123456, "")]

    # ACT
    table: str = demo_runner._format_results_table()

    # ASSERT
    assert "0.123s" in table


# -------------------------------------------------------------
# TEST CASES: DemoRunner._format_summary (IMPORTANT)
# -------------------------------------------------------------


def test_format_summary_shows_pass_fail_counts(demo_runner: DemoRunner) -> None:
    """
    Test _format_summary displays correct pass/fail counts.

    Tests that summary line includes correct count of
    passed and total tests.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if counts correct
    """
    # ARRANGE
    demo_runner._results = [
        ("test_one", True, 0.1, ""),
        ("test_two", True, 0.2, ""),
        ("test_three", False, 0.3, "Error"),
    ]

    # ACT
    summary: str = demo_runner._format_summary()

    # ASSERT
    assert "2/3 passed" in summary


def test_format_summary_shows_total_time(demo_runner: DemoRunner) -> None:
    """
    Test _format_summary displays total execution time.

    Tests that summary includes sum of all test durations
    formatted with 3 decimal places.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if total time correct
    """
    # ARRANGE
    demo_runner._results = [
        ("test_one", True, 0.1, ""),
        ("test_two", True, 0.2, ""),
        ("test_three", True, 0.3, ""),
    ]

    # ACT
    summary: str = demo_runner._format_summary()

    # ASSERT
    assert "0.600s total" in summary


def test_format_summary_handles_empty_results(demo_runner: DemoRunner) -> None:
    """
    Test _format_summary handles empty results gracefully.

    Tests edge case where no tests executed, returning
    informative message.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if appropriate message returned
    """
    # ARRANGE
    demo_runner._results = []

    # ACT
    summary: str = demo_runner._format_summary()

    # ASSERT
    assert summary == "Summary: No tests executed"


# -------------------------------------------------------------
# TEST CASES: DemoRunner._auto_run (CRITICAL)
# -------------------------------------------------------------


def test_auto_run_executes_all_registered_suites(
    demo_runner: DemoRunner, sample_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _auto_run executes all registered test suites.

    Tests that calling _auto_run processes all test classes
    registered via @run decorator.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class

    Returns
    -------
    None
        Test passes if all suites executed
    """
    # ARRANGE
    demo_runner._test_classes = [("suite_one", sample_test_class)]

    # ACT
    with patch("builtins.print") as mock_print:
        demo_runner._auto_run()

    # ASSERT
    assert len(demo_runner._results) > 0
    result_names: List[str] = [name for name, _, _, _ in demo_runner._results]
    assert any("suite_one" in name for name in result_names)


def test_auto_run_prints_results_table_and_summary(
    demo_runner: DemoRunner, sample_test_class: type
) -> None:  # CRITICAL TEST
    """
    Test _auto_run prints formatted results table and summary.

    Tests that _auto_run outputs both the results table
    and summary line to stdout.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance
    sample_test_class : type
        Sample test class

    Returns
    -------
    None
        Test passes if print called correctly
    """
    # ARRANGE
    demo_runner._test_classes = [("suite", sample_test_class)]

    # ACT
    with patch("builtins.print") as mock_print:
        demo_runner._auto_run()

    # ASSERT
    # Should print table, empty line, summary
    assert mock_print.call_count >= 2
    # First call should be table (contains headers)
    first_call_output: str = str(mock_print.call_args_list[0])
    assert "Test Name" in first_call_output or "suite" in first_call_output


def test_auto_run_does_nothing_when_no_tests_registered(demo_runner: DemoRunner) -> None:  # CRITICAL TEST
    """
    Test _auto_run does nothing when no test classes registered.

    Tests early return when _test_classes is empty,
    preventing unnecessary execution.

    Parameters
    ----------
    demo_runner : DemoRunner
        Fresh DemoRunner instance

    Returns
    -------
    None
        Test passes if no output produced
    """
    # ARRANGE
    demo_runner._test_classes = []

    # ACT
    with patch("builtins.print") as mock_print:
        demo_runner._auto_run()

    # ASSERT
    mock_print.assert_not_called()
    assert demo_runner._results == []


# -------------------------------------------------------------
# TEST CASES: Module-level run() function (IMPORTANT)
# -------------------------------------------------------------


def test_module_run_function_uses_global_runner(monkeypatch: pytest.MonkeyPatch, mock_atexit: Mock) -> None:
    """
    Test module-level run() function uses global runner singleton.

    Tests that calling basefunctions.utils.demo_runner.run()
    delegates to global DemoRunner instance.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture
    mock_atexit : Mock
        Mocked atexit.register

    Returns
    -------
    None
        Test passes if global runner used
    """
    # ARRANGE
    # Reset global runner to None to test creation
    import basefunctions.utils.demo_runner as demo_module

    original_runner: Optional[DemoRunner] = demo_module._global_runner
    demo_module._global_runner = None

    class TestClass:
        pass

    # ACT
    decorator: Callable = run("test_suite")
    decorated: type = decorator(TestClass)

    # ASSERT
    assert demo_module._global_runner is not None
    assert len(demo_module._global_runner._test_classes) == 1

    # CLEANUP
    demo_module._global_runner = original_runner


# -------------------------------------------------------------
# TEST CASES: _get_global_runner() function (IMPORTANT)
# -------------------------------------------------------------


def test_get_global_runner_creates_singleton(monkeypatch: pytest.MonkeyPatch, mock_atexit: Mock) -> None:
    """
    Test _get_global_runner creates singleton DemoRunner instance.

    Tests that first call to _get_global_runner creates
    new DemoRunner and stores it globally.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture
    mock_atexit : Mock
        Mocked atexit.register

    Returns
    -------
    None
        Test passes if singleton created
    """
    # ARRANGE
    import basefunctions.utils.demo_runner as demo_module

    original_runner: Optional[DemoRunner] = demo_module._global_runner
    demo_module._global_runner = None

    # ACT
    runner: DemoRunner = _get_global_runner()

    # ASSERT
    assert runner is not None
    assert isinstance(runner, DemoRunner)
    assert demo_module._global_runner is runner

    # CLEANUP
    demo_module._global_runner = original_runner


def test_get_global_runner_returns_same_instance(monkeypatch: pytest.MonkeyPatch, mock_atexit: Mock) -> None:
    """
    Test _get_global_runner returns same instance on repeated calls.

    Tests singleton pattern - multiple calls should return
    identical DemoRunner instance.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture
    mock_atexit : Mock
        Mocked atexit.register

    Returns
    -------
    None
        Test passes if same instance returned
    """
    # ARRANGE
    import basefunctions.utils.demo_runner as demo_module

    original_runner: Optional[DemoRunner] = demo_module._global_runner
    demo_module._global_runner = None

    # ACT
    runner1: DemoRunner = _get_global_runner()
    runner2: DemoRunner = _get_global_runner()

    # ASSERT
    assert runner1 is runner2

    # CLEANUP
    demo_module._global_runner = original_runner


# -------------------------------------------------------------
# INTEGRATION TEST: Full workflow
# -------------------------------------------------------------


def test_full_workflow_from_decoration_to_execution(
    monkeypatch: pytest.MonkeyPatch, mock_atexit: Mock
) -> None:  # CRITICAL TEST
    """
    Test complete workflow: decoration, registration, and execution.

    Tests integration of all components: @run decorator registers
    test class, @test marks methods, and _auto_run executes them.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture
    mock_atexit : Mock
        Mocked atexit.register

    Returns
    -------
    None
        Test passes if full workflow completes successfully
    """
    # ARRANGE
    import basefunctions.utils.demo_runner as demo_module

    original_runner: Optional[DemoRunner] = demo_module._global_runner
    demo_module._global_runner = None

    # Create test class with decorators
    @run("integration_test")
    class IntegrationTest:
        def __init__(self) -> None:
            self.executed: List[str] = []

        @test("first_test")
        def test_one(self) -> None:
            """First test method."""
            self.executed.append("test_one")

        @test("second_test")
        def test_two(self) -> None:
            """Second test method."""
            self.executed.append("test_two")

    # ACT
    runner: DemoRunner = _get_global_runner()
    with patch("builtins.print"):
        runner._auto_run()

    # ASSERT
    assert len(runner._results) == 2
    result_names: List[str] = [name for name, _, _, _ in runner._results]
    assert "integration_test.first_test" in result_names
    assert "integration_test.second_test" in result_names

    # All tests should pass
    all_passed: bool = all(success for _, success, _, _ in runner._results)
    assert all_passed is True

    # CLEANUP
    demo_module._global_runner = original_runner
