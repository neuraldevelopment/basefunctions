"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for HelpFormatter.
 Tests help text generation and formatting.

 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
from typing import Dict

# Project imports
from basefunctions.cli import HelpFormatter, CommandMetadata, ArgumentSpec

# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_format_command_list_returns_message_when_empty() -> None:
    """Test format_command_list returns message for empty dict."""
    # ARRANGE
    commands: Dict[str, CommandMetadata] = {}

    # ACT
    result = HelpFormatter.format_command_list(commands)

    # ASSERT
    assert "No commands available" in result


def test_format_command_list_formats_correctly(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_list formats commands correctly."""
    # ARRANGE
    commands = {"test": sample_command_metadata}

    # ACT
    result = HelpFormatter.format_command_list(commands)

    # ASSERT
    assert "test_cmd" in result or "test" in result


def test_format_command_details_includes_all_sections(sample_command_metadata: CommandMetadata) -> None:
    """Test format_command_details includes command, description, usage."""
    # ACT
    result = HelpFormatter.format_command_details(sample_command_metadata)

    # ASSERT
    assert "Command:" in result
    assert "Description:" in result
    assert "Usage:" in result
