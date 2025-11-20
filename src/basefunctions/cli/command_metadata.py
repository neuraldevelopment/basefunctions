"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Command metadata structures for CLI framework
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from dataclasses import dataclass, field
from collections.abc import Callable

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
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


@dataclass
class ArgumentSpec:
    """
    Argument specification for commands.

    Parameters
    ----------
    name : str
        Argument name
    arg_type : str
        Type of argument (string, int, file, instance, database)
    required : bool
        Whether argument is required
    context_key : Optional[str]
        Context key for fallback resolution
    choices : Optional[List[str]]
        Valid choices for argument
    completion_func : Optional[Callable]
        Custom completion function
    description : str
        Argument description
    """

    name: str
    arg_type: str
    required: bool = True
    context_key: str | None = None
    choices: list[str] | None = None
    completion_func: Callable | None = None
    description: str = ""


@dataclass
class CommandMetadata:
    """
    Command metadata for registration and execution.

    Parameters
    ----------
    name : str
        Command name
    description : str
        Command description
    usage : str
        Usage string
    args : List[ArgumentSpec]
        Command arguments
    examples : List[str]
        Usage examples
    requires_context : bool
        Whether command requires context
    context_keys : Optional[List[str]]
        Required context keys
    aliases : List[str]
        Command aliases
    """

    name: str
    description: str
    usage: str
    args: list[ArgumentSpec] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    requires_context: bool = False
    context_keys: list[str] | None = None
    aliases: list[str] = field(default_factory=list)

    def get_required_args(self) -> list[ArgumentSpec]:
        """
        Get required arguments.

        Returns
        -------
        List[ArgumentSpec]
            Required arguments only
        """
        return [arg for arg in self.args if arg.required]

    def get_optional_args(self) -> list[ArgumentSpec]:
        """
        Get optional arguments.

        Returns
        -------
        List[ArgumentSpec]
            Optional arguments only
        """
        return [arg for arg in self.args if not arg.required]

    def validate_args_count(self, provided_count: int) -> bool:
        """
        Validate argument count.

        Parameters
        ----------
        provided_count : int
            Number of provided arguments

        Returns
        -------
        bool
            True if valid
        """
        required = len(self.get_required_args())
        total = len(self.args)
        return required <= provided_count <= total
