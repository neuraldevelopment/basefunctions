"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Class-based demo runner with auto-execution and structured output

 Log:
 v1.0 : Initial implementation
 v2.0 : Redesigned for class-based test suites only
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from collections.abc import Callable
import atexit
import time
import tabulate
import inspect

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DemoRunner:
    """
    Class-based demo runner with automatic execution and structured output.
    """

    def __init__(self) -> None:
        """Initialize demo runner with empty collections."""
        self._test_classes: list[tuple[str, type]] = []
        self._results: list[tuple[str, bool, float, str]] = []

        # Register auto-execution on script exit
        atexit.register(self._auto_run)

    def run(self, suite_name: str) -> Callable:
        """
        Decorator for automatic test class registration.

        Parameters
        ----------
        suite_name : str
            Name/identifier of the test suite

        Returns
        -------
        Callable
            Decorator function
        """

        def decorator(test_class: type) -> type:
            self._test_classes.append((suite_name, test_class))
            return test_class

        return decorator

    def _get_test_methods(self, test_class: type) -> list[tuple[str, Callable]]:
        """
        Get all methods marked with @test decorator from test class.

        Parameters
        ----------
        test_class : type
            Test class to inspect

        Returns
        -------
        List[Tuple[str, Callable]]
            List of (test_name, method) tuples
        """
        test_methods = []

        for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
            if hasattr(method, "_test_name"):
                test_methods.append((method._test_name, method))

        return test_methods

    def _execute_test_suite(self, suite_name: str, test_class: type) -> list[tuple[str, bool, float, str]]:
        """
        Execute complete test suite with setup/teardown.

        Parameters
        ----------
        suite_name : str
            Name of the test suite
        test_class : type
            Test class to execute

        Returns
        -------
        List[Tuple[str, bool, float, str]]
            List of (test_name, success, duration, error) tuples
        """
        suite_results = []

        try:
            # Instantiate test class
            test_instance = test_class()

            # Run setup if available
            if hasattr(test_instance, "setup") and callable(test_instance.setup):
                start_time = time.perf_counter()
                try:
                    test_instance.setup()
                    duration = time.perf_counter() - start_time
                    suite_results.append((f"{suite_name}.setup", True, duration, ""))
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    error_msg = str(e).split("\n")[0]
                    suite_results.append((f"{suite_name}.setup", False, duration, error_msg))
                    # Continue with tests even if setup fails

            # Get and execute test methods
            test_methods = self._get_test_methods(test_class)

            for test_name, test_method in test_methods:
                start_time = time.perf_counter()
                full_test_name = f"{suite_name}.{test_name}"

                try:
                    # Bind method to instance and execute
                    bound_method = test_method.__get__(test_instance, test_class)
                    bound_method()
                    duration = time.perf_counter() - start_time
                    suite_results.append((full_test_name, True, duration, ""))
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    error_msg = str(e).split("\n")[0]
                    suite_results.append((full_test_name, False, duration, error_msg))

            # Run teardown if available
            if hasattr(test_instance, "teardown") and callable(test_instance.teardown):
                start_time = time.perf_counter()
                try:
                    test_instance.teardown()
                    duration = time.perf_counter() - start_time
                    suite_results.append((f"{suite_name}.teardown", True, duration, ""))
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    error_msg = str(e).split("\n")[0]
                    suite_results.append((f"{suite_name}.teardown", False, duration, error_msg))

        except Exception as e:
            # Class instantiation failed
            error_msg = str(e).split("\n")[0]
            suite_results.append((f"{suite_name}.instantiation", False, 0.0, error_msg))

        return suite_results

    def _format_results_table(self) -> str:
        """
        Create formatted results table using tabulate.

        Returns
        -------
        str
            Formatted table string
        """
        if not self._results:
            return "No test results available"

        headers = ["Test Name", "Status", "Duration"]
        table_data = []

        for name, success, duration, error in self._results:
            status = "PASSED" if success else "FAILED"
            duration_str = f"{duration:.3f}s"
            table_data.append([name, status, duration_str])

        return tabulate.tabulate(table_data, headers=headers, tablefmt="grid")

    def _format_summary(self) -> str:
        """
        Create summary line with pass/fail counts and total time.

        Returns
        -------
        str
            Formatted summary string
        """
        if not self._results:
            return "Summary: No tests executed"

        passed = sum(1 for _, success, _, _ in self._results if success)
        total = len(self._results)
        total_time = sum(duration for _, _, duration, _ in self._results)

        return f"Summary: {passed}/{total} passed • {total_time:.3f}s total"

    def _auto_run(self) -> None:
        """Execute all registered test classes automatically with structured output."""
        if not self._test_classes:
            return

        # Execute all test suites
        for suite_name, test_class in self._test_classes:
            suite_results = self._execute_test_suite(suite_name, test_class)
            self._results.extend(suite_results)

        # Print results table
        print(self._format_results_table())
        print()

        # Print summary
        print(self._format_summary())


# -------------------------------------------------------------
# GLOBAL INSTANCE
# -------------------------------------------------------------

_global_runner: DemoRunner | None = None


def _get_global_runner() -> DemoRunner:
    """Get or create global demo runner instance."""
    global _global_runner
    if _global_runner is None:
        _global_runner = DemoRunner()
    return _global_runner


# -------------------------------------------------------------
# PUBLIC API
# -------------------------------------------------------------


def run(suite_name: str) -> Callable:
    """
    Register test class for automatic execution.

    Parameters
    ----------
    suite_name : str
        Name/identifier of the test suite

    Returns
    -------
    Callable
        Decorator function
    """
    return _get_global_runner().run(suite_name)


def test(test_name: str) -> Callable:
    """
    Mark method as test case.

    Parameters
    ----------
    test_name : str
        Name/identifier of the test case

    Returns
    -------
    Callable
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func._test_name = test_name
        return func

    return decorator
