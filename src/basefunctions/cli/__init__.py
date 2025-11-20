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
from .command_metadata import ArgumentSpec, CommandMetadata
from .context_manager import ContextManager
from .base_command import BaseCommand
from .argument_parser import ArgumentParser
from .command_registry import CommandRegistry
from .cli_application import CLIApplication
from .help_formatter import HelpFormatter
from .completion_handler import CompletionHandler, setup_completion, cleanup_completion
from .output_formatter import OutputFormatter, show_header, show_progress, show_result
from .progress_tracker import ProgressTracker, TqdmProgressTracker

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
    # Output
    "OutputFormatter",
    "show_header",
    "show_progress",
    "show_result",
    # Progress
    "ProgressTracker",
    "TqdmProgressTracker",
]
