#!/usr/bin/env python3
"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Simple deployment script that deploys the current module using DeploymentManager

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


def main():
    """
    Deploy current module using DeploymentManager.
    """
    try:
        # Get current module name from directory
        module_name = os.path.basename(os.getcwd())

        if not module_name:
            print("Error: Could not determine module name from current directory")
            sys.exit(1)

        # Get DeploymentManager instance
        deployment_manager = basefunctions.DeploymentManager()

        # Deploy the module
        deployment_manager.deploy_module(module_name)

        sys.exit(0)

    except basefunctions.DeploymentError as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error during deployment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
