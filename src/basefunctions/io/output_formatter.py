"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Formatted output utilities for tools with consistent styling
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import time
import threading
from typing import Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
DEFAULT_WIDTH = 80
BOX_WIDTH = 60
SUCCESS_SYMBOL = "✓"
ERROR_SYMBOL = "✗"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------
class OutputFormatter:
    """
    Thread-safe singleton for formatted tool output with table-style boxes.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.logger = basefunctions.get_logger(__name__)
            self.start_time = None
            self.current_tool = None
            self.initialized = True

    def show_header(self, title: str) -> None:
        """
        Show formatted header for tool start.

        Parameters
        ----------
        title : str
            Tool title/name
        """
        self.start_time = time.time()
        self.current_tool = title

        # Create proper box header like the table
        top_border = "┌" + "─" * (BOX_WIDTH - 2) + "┐"
        title_line = f"│ {title:<{BOX_WIDTH - 4}} │"
        bottom_border = "└" + "─" * (BOX_WIDTH - 2) + "┘"

        header = f"""
{top_border}
{title_line}
{bottom_border}"""

        print(header)
        self.logger.critical(f"Started: {title}")

    def show_progress(self, message: str) -> None:
        """
        Show formatted progress message.

        Parameters
        ----------
        message : str
            Progress message
        """
        formatted_message = f"  → {message}"
        print(formatted_message)

    def show_result(self, message: str, success: bool = True, details: Optional[dict] = None) -> None:
        """
        Show formatted result summary.

        Parameters
        ----------
        message : str
            Result message
        success : bool, optional
            Whether operation was successful
        details : Optional[dict], optional
            Additional details to display
        """
        # Calculate elapsed time
        elapsed_time = ""
        if self.start_time:
            elapsed = time.time() - self.start_time
            elapsed_time = f" ({elapsed:.1f}s)"

        # Create result box
        symbol = SUCCESS_SYMBOL if success else ERROR_SYMBOL
        status = "SUCCESS" if success else "ERROR"

        # Build content lines
        content_lines = []
        status_text = f"{symbol} {status}: {message}{elapsed_time}"
        content_lines.append(status_text)

        # Add details if provided
        if details:
            for key, value in details.items():
                content_lines.append(f"  {key}: {value}")

        # Create proper table-style box
        top_border = "┌" + "─" * (BOX_WIDTH - 2) + "┐"
        bottom_border = "└" + "─" * (BOX_WIDTH - 2) + "┘"

        result_lines = [top_border]

        for line in content_lines:
            formatted_line = f"│ {line:<{BOX_WIDTH - 4}} │"
            result_lines.append(formatted_line)

        result_lines.append(bottom_border)

        # Print result
        result_output = "\n".join(result_lines)
        print(result_output)

        # Log final result
        log_message = f"Completed: {self.current_tool} - {message}{elapsed_time}"
        if success:
            self.logger.critical(log_message)
        else:
            self.logger.critical(f"FAILED: {log_message}")


# Global formatter instance
_formatter = None
_formatter_lock = threading.Lock()


def _get_formatter() -> OutputFormatter:
    """
    Get global formatter instance (thread-safe).

    Returns
    -------
    OutputFormatter
        Global formatter instance
    """
    global _formatter
    if _formatter is None:
        with _formatter_lock:
            if _formatter is None:
                _formatter = OutputFormatter()
    return _formatter


def show_header(title: str) -> None:
    """
    Show formatted header for tool start.

    Parameters
    ----------
    title : str
        Tool title/name
    """
    _get_formatter().show_header(title)


def show_progress(message: str) -> None:
    """
    Show formatted progress message.

    Parameters
    ----------
    message : str
        Progress message
    """
    _get_formatter().show_progress(message)


def show_result(message: str, success: bool = True, details: Optional[dict] = None) -> None:
    """
    Show formatted result summary.

    Parameters
    ----------
    message : str
        Result message
    success : bool, optional
        Whether operation was successful
    details : Optional[dict], optional
        Additional details to display
    """
    _get_formatter().show_result(message, success, details)
