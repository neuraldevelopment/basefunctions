"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for CommandMetadata and ArgumentSpec.
 Tests metadata structures for CLI commands.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest

# Project imports
from basefunctions.cli import CommandMetadata, ArgumentSpec

# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_get_required_args_returns_only_required(sample_command_metadata: CommandMetadata) -> None:
    """Test get_required_args filters required arguments."""
    # ARRANGE
    metadata = CommandMetadata(
        name="test",
        description="Test",
        usage="test",
        args=[ArgumentSpec("req", "string", required=True), ArgumentSpec("opt", "string", required=False)],
    )

    # ACT
    required = metadata.get_required_args()

    # ASSERT
    assert len(required) == 1
    assert required[0].name == "req"


def test_validate_args_count_returns_true_when_valid(sample_command_metadata: CommandMetadata) -> None:
    """Test validate_args_count returns True for valid count."""
    # ARRANGE
    metadata = CommandMetadata(
        name="test", description="Test", usage="test", args=[ArgumentSpec("arg", "string", required=True)]
    )

    # ACT
    result = metadata.validate_args_count(1)

    # ASSERT
    assert result is True


def test_validate_args_count_returns_false_when_too_few(sample_command_metadata: CommandMetadata) -> None:
    """Test validate_args_count returns False for too few args."""
    # ARRANGE
    metadata = CommandMetadata(
        name="test", description="Test", usage="test", args=[ArgumentSpec("arg", "string", required=True)]
    )

    # ACT
    result = metadata.validate_args_count(0)

    # ASSERT
    assert result is False
