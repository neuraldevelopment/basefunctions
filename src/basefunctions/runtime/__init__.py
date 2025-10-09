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
  v1.2 : Added DeploymentManager and deployment-specific functions
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from basefunctions.runtime.runtime_functions import (
    get_runtime_path,
    get_runtime_component_path,
    get_runtime_config_path,
    get_runtime_log_path,
    get_runtime_template_path,
    create_bootstrap_package_structure,
    create_full_package_structure,
    ensure_bootstrap_package_structure,
    create_root_structure,
    get_bootstrap_config_path,
    get_bootstrap_deployment_directory,
    get_bootstrap_development_directories,
    get_deployment_path,
    find_development_path,
)
from basefunctions.runtime.deployment_manager import DeploymentManager, DeploymentError
from basefunctions.runtime.venv_utils import VenvUtils, VenvUtilsError
from basefunctions.runtime.version import version, versions

# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------
__all__ = [
    "get_runtime_path",
    "get_runtime_component_path",
    "get_runtime_config_path",
    "get_runtime_log_path",
    "get_runtime_template_path",
    "create_bootstrap_package_structure",
    "create_full_package_structure",
    "ensure_bootstrap_package_structure",
    "create_root_structure",
    "get_bootstrap_config_path",
    "get_bootstrap_deployment_directory",
    "get_bootstrap_development_directories",
    "get_deployment_path",
    "find_development_path",
    "DeploymentManager",
    "DeploymentError",
    "VenvUtils",
    "VenvUtilsError",
    "version",
    "versions",
]
