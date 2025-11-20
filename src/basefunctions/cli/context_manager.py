"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Generic context manager for CLI applications
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any
from basefunctions.utils.logging import setup_logger, get_logger

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

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


class ContextManager:
    """
    Generic context manager for CLI applications.

    Manages key-value context state with support for
    prompt generation and argument resolution.
    """

    def __init__(self, app_name: str = "cli"):
        """
        Initialize context manager.

        Parameters
        ----------
        app_name : str
            Application name for prompt
        """
        self.app_name = app_name
        self._context: dict[str, Any] = {}
        self.logger = get_logger(__name__)

    def set(self, key: str, value: Any) -> None:
        """
        Set context value.

        Parameters
        ----------
        key : str
            Context key
        value : Any
            Context value
        """
        self._context[key] = value
        self.logger.critical(f"context set: {key}={value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get context value.

        Parameters
        ----------
        key : str
            Context key
        default : Any
            Default value if key not found

        Returns
        -------
        Any
            Context value or default
        """
        return self._context.get(key, default)

    def clear(self, key: str | None = None) -> None:
        """
        Clear context.

        Parameters
        ----------
        key : Optional[str]
            Specific key to clear, or None for all
        """
        if key:
            if key in self._context:
                del self._context[key]
                self.logger.critical(f"context cleared: {key}")
        else:
            self._context.clear()
            self.logger.critical("context cleared: all")

    def has(self, key: str) -> bool:
        """
        Check if context key exists.

        Parameters
        ----------
        key : str
            Context key

        Returns
        -------
        bool
            True if key exists
        """
        return key in self._context

    def get_all(self) -> dict[str, Any]:
        """
        Get all context values.

        Returns
        -------
        Dict[str, Any]
            Copy of context dictionary
        """
        return self._context.copy()

    def get_prompt(self) -> str:
        """
        Generate context-aware prompt.

        Returns
        -------
        str
            Formatted prompt string
        """
        if not self._context:
            return f"{self.app_name}> "

        context_parts = []
        for key, value in sorted(self._context.items()):
            context_parts.append(f"{value}")

        context_str = ".".join(context_parts)
        return f"{self.app_name}[{context_str}]> "

    def resolve_argument(self, arg: str | None, context_key: str) -> str:
        """
        Resolve argument with context fallback.

        Resolution order:
        1. If arg contains "." -> parse and return both parts
        2. If arg provided -> combine with context
        3. If no arg -> use context only

        Parameters
        ----------
        arg : Optional[str]
            Provided argument
        context_key : str
            Context key for fallback

        Returns
        -------
        str
            Resolved value

        Raises
        ------
        ValueError
            If resolution fails
        """
        if arg:
            return arg

        value = self.get(context_key)
        if not value:
            raise ValueError(f"No {context_key} specified and no context set")

        return value

    def resolve_target(self, arg: str | None, primary_key: str, secondary_key: str) -> tuple[str, str]:
        """
        Resolve compound target (e.g., instance.database).

        Resolution rules:
        1. "primary.secondary" -> use both from arg
        2. "primary" -> use primary from arg, secondary from context
        3. None -> use both from context

        Parameters
        ----------
        arg : Optional[str]
            Provided argument
        primary_key : str
            Primary context key
        secondary_key : str
            Secondary context key

        Returns
        -------
        Tuple[str, str]
            (primary, secondary) values

        Raises
        ------
        ValueError
            If resolution fails
        """
        if arg and "." in arg:
            parts = arg.split(".", 1)
            return parts[0], parts[1]

        elif arg:
            primary = arg
            secondary = self.get(secondary_key)
            if not secondary:
                raise ValueError(f"No {secondary_key} specified and no context set")
            return primary, secondary

        else:
            primary = self.get(primary_key)
            secondary = self.get(secondary_key)
            if not primary or not secondary:
                raise ValueError(f"No {primary_key}.{secondary_key} specified and no context set")
            return primary, secondary
