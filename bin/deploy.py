#!/usr/bin/env python3
"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Simple deployment script that deploys the current module using DeploymentManager
  with bootstrap detection for self-deployment and force flag support

  Log:
  v1.0 : Initial implementation
  v1.1 : Added bootstrap detection for basefunctions self-deployment
  v1.2 : Added --force flag and proper return handling from DeploymentManager
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import argparse

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


def is_bootstrap_deployment() -> bool:
    """
    Check if we are deploying basefunctions itself (bootstrap scenario).

    Returns
    -------
    bool
        True if bootstrap deployment detected
    """
    module_name = os.path.basename(os.getcwd())
    return module_name == "basefunctions"


def bootstrap_deploy(force: bool = False):
    """
    Deploy basefunctions using local development environment with venv.

    Parameters
    ----------
    force : bool
        Force deployment even if no changes detected
    """
    print("Bootstrap mode detected - deploying basefunctions using local environment")

    current_dir = os.getcwd()
    venv_python = os.path.join(current_dir, ".venv", "bin", "python")

    if not os.path.exists(venv_python):
        print("Error: Local .venv/bin/python not found in basefunctions development directory")
        sys.exit(1)

    try:
        import subprocess

        # Build command arguments
        cmd_args = [venv_python, os.path.abspath(__file__), "--bootstrap-internal"]
        if force:
            cmd_args.append("--force")

        # Re-execute this script with local venv python
        result = subprocess.run(cmd_args, check=True)

        print("Bootstrap deployment completed successfully")

    except subprocess.CalledProcessError as e:
        print(f"Bootstrap deployment failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Bootstrap deployment failed: {e}")
        sys.exit(1)


def bootstrap_deploy_internal(force: bool = False):
    """
    Internal bootstrap deployment called with correct venv.

    Parameters
    ----------
    force : bool
        Force deployment even if no changes detected
    """
    # Add local src to Python path for import
    current_dir = os.getcwd()
    src_dir = os.path.join(current_dir, "src")

    if not os.path.exists(src_dir):
        print("Error: src directory not found in basefunctions development directory")
        sys.exit(1)

    sys.path.insert(0, src_dir)

    try:
        # Import basefunctions from local src
        import basefunctions

        # Get module name
        module_name = os.path.basename(current_dir)

        # Get DeploymentManager instance
        deployment_manager = basefunctions.DeploymentManager()

        # Deploy the module with force flag
        deployed = deployment_manager.deploy_module(module_name, force=force)

        if not deployed:
            print(f"No deployment needed for {module_name} (no changes detected)")
            if not force:
                print("Use --force to deploy anyway")

    except Exception as e:
        print(f"Bootstrap deployment failed: {e}")
        sys.exit(1)


def normal_deploy(force: bool = False):
    """
    Deploy module using deployed basefunctions.

    Parameters
    ----------
    force : bool
        Force deployment even if no changes detected
    """
    try:
        import basefunctions

        # Get current module name from directory
        module_name = os.path.basename(os.getcwd())

        if not module_name:
            print("Error: Could not determine module name from current directory")
            sys.exit(1)

        # Get DeploymentManager instance
        deployment_manager = basefunctions.DeploymentManager()

        # Deploy the module with force flag
        deployed = deployment_manager.deploy_module(module_name, force=force)

        if not deployed:
            print(f"No deployment needed for {module_name} (no changes detected)")
            if not force:
                print("Use --force to deploy anyway")

    except basefunctions.DeploymentError as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error during deployment: {e}")
        sys.exit(1)


def parse_arguments():
    """
    Parse command line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Deploy current module using DeploymentManager")
    parser.add_argument("--force", action="store_true", help="Force deployment even if no changes detected")
    parser.add_argument(
        "--bootstrap-internal",
        action="store_true",
        help="Internal flag for bootstrap deployment (do not use manually)",
    )

    return parser.parse_args()


def main():
    """
    Deploy current module using DeploymentManager with bootstrap detection.
    """
    args = parse_arguments()

    # Check for internal bootstrap call
    if args.bootstrap_internal:
        bootstrap_deploy_internal(force=args.force)
        sys.exit(0)

    if is_bootstrap_deployment():
        bootstrap_deploy(force=args.force)
    else:
        normal_deploy(force=args.force)

    sys.exit(0)


if __name__ == "__main__":
    main()
