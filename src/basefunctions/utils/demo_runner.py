"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Streamlined demo runner with auto-execution and structured output
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import atexit
import time
import traceback
from typing import List, Tuple, Callable, Optional, Dict
import tabulate
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
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DemoRunner:
    """
    Streamlined demo runner with automatic execution and structured output.
    Collects demo functions via decorator, captures print statements,
    and provides clean tabulated results with timing.
    """

    def __init__(self) -> None:
        """Initialize demo runner with empty collections."""
        self._demos: List[Tuple[str, Callable]] = []
        self._results: List[Tuple[str, bool, float, str]] = []
        self._demo_prints: Dict[str, List[str]] = {}
        self._current_demo: Optional[str] = None

        # Register auto-execution on script exit
        atexit.register(self._auto_run)

    def run(self, name: str) -> Callable:
        """
        Decorator for automatic demo registration.

        Parameters
        ----------
        name : str
            Name/identifier of the demo

        Returns
        -------
        Callable
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            self._demos.append((name, func))
            return func

        return decorator

    @staticmethod
    def print(message: str) -> None:
        """
        Collect print statements for structured output.

        Parameters
        ----------
        message : str
            Message to collect for current demo
        """
        # Get current demo runner instance
        runner = _get_global_runner()
        if runner._current_demo:
            if runner._current_demo not in runner._demo_prints:
                runner._demo_prints[runner._current_demo] = []
            runner._demo_prints[runner._current_demo].append(str(message))

    def _execute_demo(self, demo_func: Callable, name: str) -> Tuple[bool, float, str]:
        """
        Execute single demo with timing and error capture.

        Parameters
        ----------
        demo_func : Callable
            Demo function to execute
        name : str
            Demo name for context

        Returns
        -------
        Tuple[bool, float, str]
            Success status, duration in seconds, error message
        """
        self._current_demo = name
        start_time = time.perf_counter()

        try:
            demo_func()
            duration = time.perf_counter() - start_time
            return True, duration, ""
        except Exception as e:
            duration = time.perf_counter() - start_time
            error_msg = str(e).split("\n")[0]  # First line only
            return False, duration, error_msg
        finally:
            self._current_demo = None

    def _collect_prints(self, demo_name: str) -> List[str]:
        """
        Get collected prints for specific demo.

        Parameters
        ----------
        demo_name : str
            Name of demo to get prints for

        Returns
        -------
        List[str]
            List of collected print messages
        """
        return self._demo_prints.get(demo_name, [])

    def _format_demo_output(self, demo_name: str, prints: List[str]) -> None:
        """
        Format and print demo output section.

        Parameters
        ----------
        demo_name : str
            Name of the demo
        prints : List[str]
            List of print messages to format
        """
        if prints:
            print(f"{demo_name}:")
            for message in prints:
                print(f"  {message}")
            print()  # Empty line after demo output

    def _format_results_table(self) -> str:
        """
        Create formatted results table using tabulate.

        Returns
        -------
        str
            Formatted table string
        """
        if not self._results:
            return "No demo results available"

        headers = ["Demo Name", "Status", "Duration"]
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
            return "Summary: No demos executed"

        passed = sum(1 for _, success, _, _ in self._results if success)
        total = len(self._results)
        total_time = sum(duration for _, _, duration, _ in self._results)

        return f"Summary: {passed}/{total} passed • {total_time:.3f}s total"

    def _auto_run(self) -> None:
        """Execute all registered demos automatically with structured output."""
        if not self._demos:
            return

        # Execute all demos
        for name, demo_func in self._demos:
            success, duration, error = self._execute_demo(demo_func, name)
            self._results.append((name, success, duration, error))

        # Format output
        print()  # Initial spacing

        # Print demo outputs
        for name, _ in self._demos:
            prints = self._collect_prints(name)
            if prints:
                self._format_demo_output(name, prints)

        # Print results table
        print(self._format_results_table())
        print()

        # Print summary
        print(self._format_summary())


# -------------------------------------------------------------
# GLOBAL INSTANCE
# -------------------------------------------------------------

_global_runner: Optional[DemoRunner] = None


def _get_global_runner() -> DemoRunner:
    """Get or create global demo runner instance."""
    global _global_runner
    if _global_runner is None:
        _global_runner = DemoRunner()
    return _global_runner


# -------------------------------------------------------------
# PUBLIC API
# -------------------------------------------------------------


def run(name: str) -> Callable:
    """
    Register demo function for automatic execution.

    Parameters
    ----------
    name : str
        Name/identifier of the demo

    Returns
    -------
    Callable
        Decorator function
    """
    return _get_global_runner().run(name)


def print(message: str) -> None:
    """
    Collect print statement for structured demo output.

    Parameters
    ----------
    message : str
        Message to collect and display
    """
    DemoRunner.print(message)
