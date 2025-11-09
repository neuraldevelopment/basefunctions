"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Formatted output utilities for CLI tools with consistent styling
 Log:
 v1.0 : Initial implementation
 v1.1 : Fixed text wrapping for long content
 v1.2 : Added global convenience functions for direct API access
 v2.0 : Moved to basefunctions.cli package
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import threading
from typing import Optional
from basefunctions.utils.logging import setup_logger, get_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
BOX_WIDTH = 80
SUCCESS_SYMBOL = "✓"
ERROR_SYMBOL = "✗"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
setup_logger(__name__)

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
    Thread-safe formatter for CLI tool output with table-style boxes.
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
            self.logger = get_logger(__name__)
            self.start_time = None
            self.current_tool = None
            self.initialized = True

    def show_header(self, title: str) -> None:
        """
        Show formatted header.

        Parameters
        ----------
        title : str
            Tool title
        """
        self.start_time = time.time()
        self.current_tool = title

        if len(title) > BOX_WIDTH - 4:
            title = title[: BOX_WIDTH - 7] + "..."

        top_border = "┌" + "─" * (BOX_WIDTH - 2) + "┐"
        title_line = f"│ {title:<{BOX_WIDTH - 4}} │"
        bottom_border = "└" + "─" * (BOX_WIDTH - 2) + "┘"

        header = f"\n{top_border}\n{title_line}\n{bottom_border}"

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
        if len(message) > BOX_WIDTH - 6:
            message = message[: BOX_WIDTH - 9] + "..."

        formatted_message = f"  → {message}"
        print(formatted_message)

    def show_result(self, message: str, success: bool = True, details: Optional[dict] = None) -> None:
        """
        Show formatted result summary.

        Parameters
        ----------
        message : str
            Result message
        success : bool
            Whether operation was successful
        details : Optional[dict]
            Additional details to display
        """
        elapsed_time = ""
        if self.start_time:
            elapsed = time.time() - self.start_time
            elapsed_time = f" ({elapsed:.1f}s)"

        symbol = SUCCESS_SYMBOL if success else ERROR_SYMBOL
        status = "SUCCESS" if success else "ERROR"

        content_lines = []
        status_text = f"{symbol} {status}: {message}{elapsed_time}"

        if len(status_text) > BOX_WIDTH - 4:
            max_msg_len = BOX_WIDTH - 4 - len(f"{symbol} {status}: ") - len(elapsed_time)
            if len(message) > max_msg_len:
                short_message = message[: max_msg_len - 3] + "..."
                status_text = f"{symbol} {status}: {short_message}{elapsed_time}"

        content_lines.append(status_text)

        if details:
            for key, value in details.items():
                detail_line = f"  {key}: {value}"
                if len(detail_line) > BOX_WIDTH - 4:
                    if len(str(value)) > BOX_WIDTH - 8 - len(key):
                        content_lines.append(f"  {key}:")
                        value_str = str(value)
                        if len(value_str) > BOX_WIDTH - 8:
                            value_str = value_str[: BOX_WIDTH - 11] + "..."
                        content_lines.append(f"    {value_str}")
                    else:
                        detail_line = detail_line[: BOX_WIDTH - 7] + "..."
                        content_lines.append(detail_line)
                else:
                    content_lines.append(detail_line)

        top_border = "┌" + "─" * (BOX_WIDTH - 2) + "┐"
        bottom_border = "└" + "─" * (BOX_WIDTH - 2) + "┘"

        result_lines = [top_border]

        for line in content_lines:
            if len(line) > BOX_WIDTH - 4:
                line = line[: BOX_WIDTH - 7] + "..."
            formatted_line = f"│ {line:<{BOX_WIDTH - 4}} │"
            result_lines.append(formatted_line)

        result_lines.append(bottom_border)

        result_output = "\n".join(result_lines)
        print(result_output)

        log_message = f"Completed: {self.current_tool} - {message}{elapsed_time}"
        if success:
            self.logger.critical(log_message)
        else:
            self.logger.critical(f"FAILED: {log_message}")


_formatter = None
_formatter_lock = threading.Lock()


def _get_formatter() -> OutputFormatter:
    """
    Get global formatter instance.

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
    Show formatted header.

    Parameters
    ----------
    title : str
        Tool title
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
    success : bool
        Whether operation was successful
    details : Optional[dict]
        Additional details to display
    """
    _get_formatter().show_result(message, success, details)
