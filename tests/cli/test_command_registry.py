"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for CommandRegistry.
 Tests command registration and dispatch with comprehensive error handling.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import List

# Project imports
from basefunctions.cli import CommandRegistry, BaseCommand, ContextManager, CommandMetadata, ArgumentSpec

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def registry() -> CommandRegistry:
    """Provide CommandRegistry instance."""
    return CommandRegistry()


@pytest.fixture
def mock_handler(mock_context_manager) -> BaseCommand:
    """Provide mock BaseCommand handler."""

    class TestHandler(BaseCommand):
        def register_commands(self):
            return {
                "test": CommandMetadata("test", "Test cmd", "test", []),
                "other": CommandMetadata("other", "Other cmd", "other", []),
            }

        def execute(self, command: str, args: List[str]) -> None:
            pass

    return TestHandler(mock_context_manager)


# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_register_group_adds_handler(registry: CommandRegistry, mock_handler: BaseCommand) -> None:
    """Test register_group adds handler to registry."""
    # ACT
    registry.register_group("test_group", mock_handler)

    # ASSERT
    handlers = registry.get_handlers("test_group")
    assert len(handlers) == 1
    assert handlers[0] == mock_handler


def test_register_group_supports_multiple_handlers(
    registry: CommandRegistry, mock_handler: BaseCommand, mock_context_manager: ContextManager
) -> None:
    """Test multiple handlers can register to same group."""

    # ARRANGE
    class SecondHandler(BaseCommand):
        def register_commands(self):
            return {"second": CommandMetadata("second", "desc", "usage", [])}

        def execute(self, command: str, args: List[str]) -> None:
            pass

    handler2 = SecondHandler(mock_context_manager)

    # ACT
    registry.register_group("group", mock_handler)
    registry.register_group("group", handler2)

    # ASSERT
    handlers = registry.get_handlers("group")
    assert len(handlers) == 2


def test_register_alias_stores_single_command(registry: CommandRegistry) -> None:
    """Test register_alias stores command without group."""
    # ACT
    registry.register_alias("ll", "list")

    # ASSERT
    aliases = registry.get_all_aliases()
    assert aliases["ll"] == ("", "list")


def test_register_alias_stores_group_command(registry: CommandRegistry) -> None:
    """Test register_alias stores group and command."""
    # ACT
    registry.register_alias("gs", "git status")

    # ASSERT
    aliases = registry.get_all_aliases()
    assert aliases["gs"] == ("git", "status")


def test_resolve_alias_returns_original_when_not_alias(registry: CommandRegistry) -> None:
    """Test resolve_alias returns input when not an alias."""
    # ACT
    cmd, subcmd = registry.resolve_alias("command", "subcommand")

    # ASSERT
    assert cmd == "command"
    assert subcmd == "subcommand"


def test_resolve_alias_resolves_correctly(registry: CommandRegistry) -> None:
    """Test resolve_alias resolves to target command."""
    # ARRANGE
    registry.register_alias("gs", "git status")

    # ACT
    cmd, subcmd = registry.resolve_alias("gs", None)

    # ASSERT
    assert cmd == "git"
    assert subcmd == "status"


def test_dispatch_executes_correct_handler(registry: CommandRegistry, mock_handler: BaseCommand) -> None:
    """Test dispatch calls correct handler."""
    # ARRANGE
    registry.register_group("group", mock_handler)

    # ACT & ASSERT - Should not raise
    registry.dispatch("group", "test", [])


def test_dispatch_raises_when_group_not_found(registry: CommandRegistry) -> None:  # CRITICAL TEST
    """Test dispatch raises ValueError for unknown group."""
    # ACT & ASSERT
    with pytest.raises(ValueError, match="Unknown command group"):
        registry.dispatch("nonexistent", "command", [])


def test_dispatch_raises_when_command_not_found(
    registry: CommandRegistry, mock_handler: BaseCommand
) -> None:  # CRITICAL TEST
    """Test dispatch raises ValueError for unknown command."""
    # ARRANGE
    registry.register_group("group", mock_handler)

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Unknown command"):
        registry.dispatch("group", "nonexistent", [])
