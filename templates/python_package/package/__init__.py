"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : <package_name>

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  <package_name> - [Add your package description here]

=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from basefunctions.runtime.version import version as _get_version_string

# -------------------------------------------------------------
# Main package imports
# -------------------------------------------------------------
# from <package_name>.core.main_module import MainClass
# from <package_name>.utils.helpers import helper_function

# =============================================================================
# VERSION
# =============================================================================
__version__ = _get_version_string("<package_name>")


def get_version() -> str:
    """
    Return the current version of the package.

    Returns
    -------
    str
        Version string (e.g., "1.2.3" or "1.2.3-dev+5")
    """
    return __version__


# -------------------------------------------------------------
# EXPORT DEFINITIONS
# -------------------------------------------------------------
__all__ = [
    "get_version",
    # Add your public API exports here
    # "MainClass",
    # "helper_function",
]

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------
# Add any package initialization code here
