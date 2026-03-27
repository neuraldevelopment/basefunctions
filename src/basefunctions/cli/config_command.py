"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 CLI command that reads and outputs the current system configuration.
 Provides operators a quick way to inspect active configuration at runtime.
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
import json

import basefunctions
from basefunctions.cli.base_command import BaseCommand
from basefunctions.cli.command_metadata import CommandMetadata
from basefunctions.utils.logging import get_logger

# =============================================================================
# LOGGING
# =============================================================================
logger = get_logger(__name__)

# =============================================================================
# CLASS DEFINITIONS
# =============================================================================


class ConfigCommand(BaseCommand):
    """
    CLI command group exposing the current system configuration.

    Provides a single `config` command that reads the active configuration
    from ConfigHandler and prints it as formatted JSON.
    """

    def register_commands(self) -> dict[str, CommandMetadata]:
        """
        Register the config command.

        Returns
        -------
        dict[str, CommandMetadata]
            Mapping of command name to metadata
        """
        return {
            "config": CommandMetadata(
                name="config",
                description="Show current system configuration",
                usage="config [package]",
                examples=["config", "config basefunctions"],
            )
        }

    def execute(self, command: str, args: list[str]) -> None:
        """
        Execute the config command.

        Parameters
        ----------
        command : str
            Command name — must be "config"
        args : list[str]
            Optional package name filter: [] for all, [package] for one section

        Raises
        ------
        ValueError
            If command is not "config"
        """
        if command != "config":
            logger.warning("Unknown command '%s' on ConfigCommand", command)
            raise ValueError(f"Unknown command: {command}")

        package = args[0] if args else None
        config = basefunctions.ConfigHandler().get_config_for_package(package)
        print(json.dumps(config, indent=2))
