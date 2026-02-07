"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 CLI framework package exports
 Log:
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from .argument_parser import ArgumentParser
from .base_command import BaseCommand
from .cli_application import CLIApplication
from .command_metadata import ArgumentSpec, CommandMetadata
from .command_registry import CommandRegistry
from .completion_handler import CompletionHandler, cleanup_completion, setup_completion
from .context_manager import ContextManager
from .help_formatter import HelpFormatter
from .multiline_input import read_multiline_input
from .output_formatter import OutputFormatter, show_header, show_progress, show_result
from basefunctions.utils.progress_tracker import AliveProgressTracker, ProgressTracker

# -------------------------------------------------------------
# PUBLIC API
# -------------------------------------------------------------
__all__ = [
    # Core Classes
    "CLIApplication",
    "BaseCommand",
    "ContextManager",
    "CommandRegistry",
    "ArgumentParser",
    # Metadata
    "ArgumentSpec",
    "CommandMetadata",
    # UI/UX
    "HelpFormatter",
    "CompletionHandler",
    "setup_completion",
    "cleanup_completion",
    # Input
    "read_multiline_input",
    # Output
    "OutputFormatter",
    "show_header",
    "show_progress",
    "show_result",
    # Progress
    "ProgressTracker",
    "AliveProgressTracker",
]
