"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Runtime path detection for development and deployment environments

  Log:
  v1.0 : Initial implementation
  v1.1 : Updated imports for two-phase package structure
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from basefunctions.runtime.runtime_functions import (
    get_runtime_path,
    get_runtime_component_path,
    get_runtime_config_path,
    get_runtime_template_path,
    create_bootstrap_package_structure,
    create_full_package_structure,
    ensure_bootstrap_package_structure,
    create_root_structure,
    get_bootstrap_config_path,
)

# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------
__all__ = [
    "get_runtime_path",
    "get_runtime_component_path",
    "get_runtime_config_path",
    "get_runtime_template_path",
    "create_bootstrap_package_structure",
    "create_full_package_structure",
    "ensure_bootstrap_package_structure",
    "create_root_structure",
    "get_bootstrap_config_path",
]
