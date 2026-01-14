"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Command registration and dispatch system
 Log:
 v1.0 : Initial implementation
 v1.1 : Fixed multi-handler support for same group
 v1.2 : Added lazy loading pattern with cache
 v1.3 : Fixed lazy loading collision bug for root-level commands
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import importlib
from basefunctions.utils.logging import setup_logger, get_logger
import basefunctions

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


class CommandRegistry:
    """
    Command registration and dispatch system.

    Manages command groups, aliases, and routing with
    support for both grouped and root-level commands.
    Supports multiple handlers per group.
    """

    def __init__(self):
        """Initialize command registry."""
        self.logger = get_logger(__name__)
        self._groups: dict[str, list[basefunctions.cli.BaseCommand]] = {}
        self._lazy_groups: dict[str, list[str]] = {}
        self._handler_cache: dict[str, basefunctions.cli.BaseCommand] = {}
        self._aliases: dict[str, tuple[str, str]] = {}
        self._context = None

    def set_context(self, context) -> None:
        """
        Set context manager for lazy handler instantiation.

        Parameters
        ----------
        context : ContextManager
            Context manager instance
        """
        self._context = context

    def register_group(self, group_name: str, command_handler: basefunctions.cli.BaseCommand) -> None:
        """
        Register command group.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level commands)
        command_handler : BaseCommand
            Command handler instance
        """
        if group_name not in self._groups:
            self._groups[group_name] = []

        self._groups[group_name].append(command_handler)
        self.logger.info(
            f"registered command group: {group_name or 'root'} (handler #{len(self._groups[group_name])})"
        )

    def register_group_lazy(self, group_name: str, module_path: str) -> None:
        """
        Register command group with lazy loading.

        Handler will be imported and instantiated on first access.

        Parameters
        ----------
        group_name : str
            Group name (empty string for root-level commands)
        module_path : str
            Module path in format "module.path:ClassName"
            Example: "dbfunctions.dbadmin.list_commands:ListCommands"

        Raises
        ------
        ValueError
            If module_path format is invalid
        """
        if ":" not in module_path:
            raise ValueError(f"Invalid module_path format: {module_path}. Expected 'module.path:ClassName'")

        if group_name not in self._lazy_groups:
            self._lazy_groups[group_name] = []

        self._lazy_groups[group_name].append(module_path)
        self.logger.info(f"registered lazy command group: {group_name or 'root'} -> {module_path} (handler #{len(self._lazy_groups[group_name])})")

    def register_alias(self, alias: str, target: str) -> None:
        """
        Register command alias.

        Parameters
        ----------
        alias : str
            Alias name
        target : str
            Target command (format: "group command" or "command")
        """
        parts = target.split(None, 1)
        if len(parts) == 2:
            self._aliases[alias] = (parts[0], parts[1])
        else:
            self._aliases[alias] = ("", parts[0])
        self.logger.info(f"registered alias: {alias} -> {target}")

    def resolve_alias(self, command: str, subcommand: str | None) -> tuple[str, str | None]:
        """
        Resolve command alias.

        Parameters
        ----------
        command : str
            Command name
        subcommand : Optional[str]
            Subcommand name

        Returns
        -------
        Tuple[str, Optional[str]]
            (resolved_command, resolved_subcommand)
        """
        if command in self._aliases and subcommand is None:
            return self._aliases[command]
        return command, subcommand

    def _import_handler(self, module_path: str) -> basefunctions.cli.BaseCommand:
        """
        Import and instantiate lazy handler.

        Parameters
        ----------
        module_path : str
            Module path in format "module.path:ClassName"

        Returns
        -------
        BaseCommand
            Instantiated handler

        Raises
        ------
        ModuleNotFoundError
            If module cannot be imported
        AttributeError
            If class not found in module
        RuntimeError
            If handler instantiation fails or context not set
        """
        if module_path in self._handler_cache:
            return self._handler_cache[module_path]

        if not self._context:
            raise RuntimeError("Context not set. Call set_context() before lazy loading handlers.")

        try:
            module_name, class_name = module_path.rsplit(":", 1)
        except ValueError as e:
            raise ValueError(f"Ungültiges module_path Format: {module_path}") from e

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(f"Modul nicht gefunden: {module_name}") from e

        try:
            handler_class = getattr(module, class_name)
        except AttributeError as e:
            raise AttributeError(f"Klasse '{class_name}' nicht gefunden in Modul {module_name}") from e

        try:
            handler = handler_class(self._context)
        except Exception as e:
            raise RuntimeError(f"Handler-Instanziierung fehlgeschlagen für {class_name}: {str(e)}") from e

        self._handler_cache[module_path] = handler
        self.logger.info(f"lazy loaded handler: {module_path}")

        return handler

    def get_handlers(self, group_name: str) -> list[basefunctions.cli.BaseCommand]:
        """
        Get all command handlers for group.

        Supports both eager and lazy-loaded handlers.

        Parameters
        ----------
        group_name : str
            Group name

        Returns
        -------
        List[BaseCommand]
            List of command handlers (empty list if none found)

        Raises
        ------
        ModuleNotFoundError
            If lazy module cannot be imported
        AttributeError
            If lazy handler class not found
        RuntimeError
            If lazy handler instantiation fails
        """
        handlers = self._groups.get(group_name, []).copy()

        if group_name in self._lazy_groups:
            for module_path in self._lazy_groups[group_name]:
                handler = self._import_handler(module_path)
                handlers.append(handler)

        return handlers

    def get_handler(self, group_name: str) -> basefunctions.cli.BaseCommand | None:
        """
        Get first command handler for group.

        DEPRECATED: Use get_handlers() instead for multi-handler support.

        Parameters
        ----------
        group_name : str
            Group name

        Returns
        -------
        Optional[BaseCommand]
            First command handler or None
        """
        handlers = self.get_handlers(group_name)
        return handlers[0] if handlers else None

    def get_all_groups(self) -> list[str]:
        """
        Get all registered groups.

        Returns
        -------
        List[str]
            Group names
        """
        return list(self._groups.keys())

    def get_all_aliases(self) -> dict[str, tuple[str, str]]:
        """
        Get all registered aliases.

        Returns
        -------
        Dict[str, Tuple[str, str]]
            Alias to (group, command) mapping
        """
        return self._aliases.copy()

    def dispatch(self, group_name: str, command: str, args: list[str]) -> bool:
        """
        Dispatch command to handler.

        Supports both eager and lazy-loaded handlers.

        Parameters
        ----------
        group_name : str
            Group name
        command : str
            Command name
        args : List[str]
            Command arguments

        Returns
        -------
        bool
            True if dispatched successfully

        Raises
        ------
        ValueError
            If group or command not found
        ModuleNotFoundError
            If lazy module cannot be imported
        AttributeError
            If lazy handler class not found
        RuntimeError
            If lazy handler instantiation fails
        """
        handlers = self.get_handlers(group_name)
        if not handlers:
            raise ValueError(f"Unknown command group: {group_name}")

        for handler in handlers:
            if handler.validate_command(command):
                handler.execute(command, args)
                return True

        all_commands = []
        for handler in handlers:
            all_commands.extend(handler.get_available_commands())

        available = ", ".join(sorted(set(all_commands)))
        raise ValueError(f"Unknown command: {command}\nAvailable: {available}")

    def get_command_metadata(self, group_name: str, command: str) -> basefunctions.cli.CommandMetadata | None:
        """
        Get command metadata.

        Parameters
        ----------
        group_name : str
            Group name
        command : str
            Command name

        Returns
        -------
        Optional[CommandMetadata]
            Command metadata or None
        """
        handlers = self.get_handlers(group_name)

        for handler in handlers:
            metadata = handler.get_command_metadata(command)
            if metadata:
                return metadata

        return None
