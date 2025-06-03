"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Demo runner with test result formatting and CLI argument support
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import List, Tuple, Callable, Optional
from tabulate import tabulate
import sys
import os
import datetime
import argparse
import logging

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


class DemoRunner:
    """
    Demo runner with test result formatting and clean tabulation.
    Supports multiple test patterns: decorator, function reference, lambda, and manual.
    Includes CLI argument support for log configuration.
    """

    @staticmethod
    def disable_global_logging() -> None:
        """Disable all logging globally (affects entire application)."""
        logging.getLogger().setLevel(logging.CRITICAL + 1)
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)

    @staticmethod
    def init_logging(log_level: str = "INFO") -> str:
        """
        Initialize global logging redirection at script start.
        Call this BEFORE any other imports to capture all logs.

        Parameters
        ----------
        log_level : str, optional
            Logging level (DEBUG, INFO, WARNING, ERROR), by default "INFO"

        Returns
        -------
        str
            Log file path that was configured
        """
        # Get script name for log file
        script_name = os.path.basename(sys.argv[0])
        if script_name.endswith(".py"):
            log_file = script_name[:-3] + ".log.txt"
        else:
            log_file = "demo.log.txt"

        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Configure root logger to redirect ALL logs to file
        log_format = "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format, datefmt="%H:%M:%S"))

        root_logger.addHandler(file_handler)
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # Prevent logs from going to console
        root_logger.propagate = False

        return log_file

    def __init__(
        self, max_width: int = 150, error_width: int = 80, log_file: Optional[str] = None, log_level: str = "INFO"
    ):
        """
        Initialize demo runner with automatic log file setup and CLI argument parsing.

        Parameters
        ----------
        max_width : int, optional
            Maximum total width of output table, by default 150
        error_width : int, optional
            Maximum width for error message wrapping, by default 80
        log_file : str, optional
            Custom log file path, by default None (auto-generated)
        log_level : str, optional
            Logging level (DEBUG, INFO, WARNING, ERROR), by default "INFO"
        """
        self.max_width = max_width
        self.error_width = error_width
        self.results: List[Tuple[str, bool, Optional[str]]] = []
        self._registered_tests: List[Tuple[str, Callable]] = []

        # Parse CLI arguments for logging configuration
        self._parse_log_args()

        # Override with provided parameters if given
        if log_file is not None:
            self.log_file = log_file
        if log_level != "INFO":
            self.log_level = log_level.upper()

        # Setup logging
        self._setup_logging()

    def _parse_log_args(self) -> None:
        """Parse CLI arguments for log configuration."""
        # Create parser for log-related arguments only
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--log-file", type=str, help="Custom log file path")
        parser.add_argument(
            "--log-level",
            type=str,
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Logging level (default: INFO)",
        )

        # Parse known args to avoid conflicts with other CLI parsers
        try:
            args, _ = parser.parse_known_args()
            self.log_file = args.log_file
            self.log_level = args.log_level
        except:
            # Fallback if parsing fails
            self.log_file = None
            self.log_level = "INFO"

    def _setup_logging(self) -> None:
        """Setup logging configuration (simplified since global logging already configured)."""
        # Log file should already be determined by init_logging or CLI args
        if self.log_file is None:
            # Fallback - determine from calling script
            frame = sys._getframe(2)
            while frame:
                filename = frame.f_code.co_filename
                if filename != __file__ and not filename.startswith("<"):
                    calling_script = os.path.basename(filename)
                    if calling_script.endswith(".py"):
                        self.log_file = calling_script[:-3] + ".log.txt"
                        break
                frame = frame.f_back
            else:
                self.log_file = "demo_runner.log.txt"

        # Get existing logger (should already be configured by init_logging)
        self.logger = logging.getLogger("DemoRunner")

        # Update log level if needed
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))

        # Log initialization
        self.logger.info(f"DemoRunner initialized - Log Level: {self.log_level}")
        self.logger.info(f"Using log file: {self.log_file}")

    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Write message to log file with specified level.

        Parameters
        ----------
        message : str
            Message to log
        level : str, optional
            Log level (DEBUG, INFO, WARNING, ERROR), by default "INFO"
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)

    def test(self, test_name: str):
        """
        Decorator for automatic test registration.

        Parameters
        ----------
        test_name : str
            Name/identifier of the test

        Returns
        -------
        Callable
            Decorator function
        """

        def decorator(func):
            self._registered_tests.append((test_name, func))
            return func

        return decorator

    def add_result(self, test_name: str, success: bool, error: Optional[str] = None) -> None:
        """
        Add test result with internal boolean tracking and logging.

        Parameters
        ----------
        test_name : str
            Name/identifier of the test
        success : bool
            Whether the test passed
        error : str, optional
            Error message if test failed, by default None
        """
        # Store result with boolean success flag and optional error
        self.results.append((test_name, success, error))

        # Log the result
        if success:
            self._log(f"Test '{test_name}': PASSED", "INFO")
        else:
            self._log(f"Test '{test_name}': FAILED", "ERROR")
            if error:
                self._log(f"  Error: {error}", "ERROR")

    def _wrap_text(self, text: str, width: int) -> str:
        """
        Wrap text to specified width with word-aware breaking.

        Parameters
        ----------
        text : str
            Text to wrap
        width : int
            Maximum width per line

        Returns
        -------
        str
            Wrapped text with newlines
        """
        if len(text) <= width:
            return text

        # Simple word-aware wrapping
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def run_test(self, test_name: str, test_func: Callable, *args, **kwargs) -> bool:
        """
        Run test function and automatically add result with logging.
        Supports both parameterless functions and functions with arguments.

        Parameters
        ----------
        test_name : str
            Name/identifier of the test
        test_func : Callable
            Test function to execute
        *args
            Positional arguments passed to test function
        **kwargs
            Keyword arguments passed to test function

        Returns
        -------
        bool
            True if test passed, False if failed
        """
        self._log(f"Starting test '{test_name}'", "DEBUG")
        try:
            if args or kwargs:
                test_func(*args, **kwargs)
            else:
                test_func()
            self.add_result(test_name, True)
            return True
        except Exception as e:
            self._log(f"Exception in test '{test_name}': {str(e)}", "DEBUG")
            self.add_result(test_name, False, str(e))
            return False

    def run_all_tests(self) -> None:
        """Run all decorator-registered tests with logging."""
        self._log(f"Running {len(self._registered_tests)} registered tests", "INFO")
        for test_name, test_func in self._registered_tests:
            self.run_test(test_name, test_func)

    def print_results(self, title: str = "Demo Results") -> None:
        """
        Print formatted results table with exact width control.

        Parameters
        ----------
        title : str, optional
            Title for the demo results section, by default "Demo Results"
        """
        print(f"\n{title}")
        print("=" * min(len(title), self.max_width))

        # Log the results summary
        self._log(f"=== {title} ===", "INFO")

        # Check if we have results
        if not self.results:
            print("No demo results to display")
            self._log("No demo results to display", "WARNING")
            return

        # Simple approach: build each line and pad to exact width
        def make_line_exact_width(content):
            if len(content) >= self.max_width:
                return content[: self.max_width]
            else:
                return content + " " * (self.max_width - len(content))

        # Calculate reasonable column split
        test_width = int(self.max_width * 0.4) - 4  # Leave space for borders
        result_width = self.max_width - test_width - 7  # 7 chars for | | | structure

        # Build table lines
        lines = []

        # Top border
        separator = "+" + "-" * (test_width + 2) + "+" + "-" * (result_width + 2) + "+"
        lines.append(make_line_exact_width(separator))

        # Header
        header = f"| {'Test'.ljust(test_width)} | {'Result'.ljust(result_width)} |"
        lines.append(make_line_exact_width(header))

        # Header separator
        header_sep = "+" + "=" * (test_width + 2) + "+" + "=" * (result_width + 2) + "+"
        lines.append(make_line_exact_width(header_sep))

        # Data rows
        for test_name, success, error in self.results:
            # Prepare test name
            test_display = test_name[:test_width] if len(test_name) > test_width else test_name

            # Prepare result
            if success:
                result_text = "PASSED"
            else:
                if error:
                    error_clean = error.replace("\n", " ").replace("\r", " ")
                    max_error = result_width - 8  # Space for "FAILED: "
                    if len(error_clean) > max_error:
                        error_clean = error_clean[: max_error - 3] + "..."
                    result_text = f"FAILED: {error_clean}"
                else:
                    result_text = "FAILED"

            result_display = result_text[:result_width] if len(result_text) > result_width else result_text

            # Build row
            row = f"| {test_display.ljust(test_width)} | {result_display.ljust(result_width)} |"
            lines.append(make_line_exact_width(row))

            # Row separator
            lines.append(make_line_exact_width(separator))

        # Print all lines
        for line in lines:
            print(line)

        # Summary
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        summary_text = f"Summary: {passed}/{total} tests passed"
        print(f"\n{summary_text}")

        # Log summary
        self._log(summary_text, "INFO")
        if passed < total:
            self._log(f"{total - passed} tests failed", "WARNING")
        else:
            self._log("All tests passed", "INFO")

        # Log detailed results
        for test_name, success, error in self.results:
            if not success and error:
                self._log(f"Failed test '{test_name}' details: {error}", "DEBUG")

    def print_performance_table(
        self, performance_data: List[Tuple[str, str]], title: str = "Performance Results"
    ) -> None:
        """
        Print performance results table without PASSED/FAILED status.

        Parameters
        ----------
        performance_data : List[Tuple[str, str]]
            List of (metric_name, metric_value) tuples
        title : str, optional
            Title for the performance section, by default "Performance Results"
        """
        print(f"\n{title}")
        print("=" * min(len(title), self.max_width))

        # Log the performance summary
        self._log(f"=== {title} ===", "INFO")

        # Check if we have data
        if not performance_data:
            print("No performance data to display")
            self._log("No performance data to display", "WARNING")
            return

        # Simple approach: build each line and pad to exact width
        def make_line_exact_width(content):
            if len(content) >= self.max_width:
                return content[: self.max_width]
            else:
                return content + " " * (self.max_width - len(content))

        # Calculate reasonable column split - more space for values
        metric_width = int(self.max_width * 0.3) - 4  # 30% for metric names
        value_width = self.max_width - metric_width - 7  # Rest for values

        # Build table lines
        lines = []

        # Top border
        separator = "+" + "-" * (metric_width + 2) + "+" + "-" * (value_width + 2) + "+"
        lines.append(make_line_exact_width(separator))

        # Header
        header = f"| {'Metric'.ljust(metric_width)} | {'Value'.ljust(value_width)} |"
        lines.append(make_line_exact_width(header))

        # Header separator
        header_sep = "+" + "=" * (metric_width + 2) + "+" + "=" * (value_width + 2) + "+"
        lines.append(make_line_exact_width(header_sep))

        # Data rows
        for metric_name, metric_value in performance_data:
            # Prepare metric name
            metric_display = metric_name[:metric_width] if len(metric_name) > metric_width else metric_name

            # Prepare value
            value_display = metric_value[:value_width] if len(metric_value) > value_width else metric_value

            # Build row
            row = f"| {metric_display.ljust(metric_width)} | {value_display.ljust(value_width)} |"
            lines.append(make_line_exact_width(row))

            # Row separator
            lines.append(make_line_exact_width(separator))

        # Print all lines
        for line in lines:
            print(line)

        # Log performance data
        for metric_name, metric_value in performance_data:
            self._log(f"Performance: {metric_name} = {metric_value}", "INFO")

    def clear_results(self) -> None:
        """Clear all stored results and registered tests for reuse."""
        self.results = []
        self._registered_tests = []

    def get_summary(self) -> Tuple[int, int]:
        """
        Get demo summary statistics.

        Returns
        -------
        Tuple[int, int]
            Tuple of (passed_count, total_count)
        """
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        return passed, total

    def has_failures(self) -> bool:
        """
        Check if any tests failed.

        Returns
        -------
        bool
            True if any test failed, False if all passed
        """
        return any(not success for _, success, _ in self.results)

    def get_failed_tests(self) -> List[Tuple[str, str]]:
        """
        Get list of failed tests with their error messages.

        Returns
        -------
        List[Tuple[str, str]]
            List of (test_name, error_message) for failed tests
        """
        failed = []
        for test_name, success, error in self.results:
            if not success:
                error_msg = error or "No error details available"
                failed.append((test_name, error_msg))
        return failed
