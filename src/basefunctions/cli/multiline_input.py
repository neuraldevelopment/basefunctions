"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Read multiline input with custom completion callbacks
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import logging
from typing import Callable

# =============================================================================
# LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================


def read_multiline_input(
    prompt: str,
    continuation_prompt: str,
    is_complete: Callable[[str], bool],
) -> str:
    """
    Read multiple lines of input until completion condition is met.

    Reads lines from user input and accumulates them in a buffer until
    the provided completion callback returns True. Handles EOF and
    keyboard interrupts gracefully.

    Parameters
    ----------
    prompt : str
        Prompt to display for the first line
    continuation_prompt : str
        Prompt to display for continuation lines
    is_complete : Callable[[str], bool]
        Callback function that receives the accumulated buffer and
        returns True when input is complete

    Returns
    -------
    str
        Accumulated input with leading/trailing whitespace stripped,
        or empty string if EOF/KeyboardInterrupt occurs

    Examples
    --------
    >>> # Read SQL commands until semicolon
    >>> sql = read_multiline_input(
    ...     "SQL> ",
    ...     "...> ",
    ...     lambda b: ";" in b
    ... )
    """
    buffer = ""
    first_line = True

    while True:
        current_prompt = prompt if first_line else continuation_prompt
        first_line = False

        try:
            line = input(current_prompt)
        except (EOFError, KeyboardInterrupt):
            return ""

        buffer += line + "\n"

        if is_complete(buffer):
            return buffer.strip()
