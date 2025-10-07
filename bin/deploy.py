#!/usr/bin/env python3
"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Simple deployment script that deploys the current module using DeploymentManager
  with bootstrap detection for self-deployment, force flag support and automatic
  version management via git tags

  Log:
  v1.0 : Initial implementation
  v1.1 : Added bootstrap detection for basefunctions self-deployment
  v1.2 : Added --force flag and proper return handling from DeploymentManager
  v1.3 : Added automatic version management with git tags
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import argparse
import subprocess
import re

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


def is_git_repository() -> bool:
    """
    Check if current directory is a git repository.

    Returns
    -------
    bool
        True if git repository exists
    """
    try:
        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def check_git_clean() -> bool:
    """
    Check if git working directory is clean.

    Returns
    -------
    bool
        True if no uncommitted changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5, check=True
        )
        return len(result.stdout.strip()) == 0
    except Exception:
        return False


def get_current_git_version() -> str:
    """
    Get current version from git tags.

    Returns
    -------
    str
        Current version (e.g. 'v0.5.1') or 'v0.0.0' if no tags exist
    """
    try:
        result = subprocess.run(["git", "tag", "-l", "v*.*.*"], capture_output=True, text=True, timeout=5, check=True)

        tags = result.stdout.strip().split("\n")
        tags = [t for t in tags if t and re.match(r"^v\d+\.\d+\.\d+$", t)]

        if not tags:
            return "v0.0.0"

        # Sort tags by version number
        def version_key(tag):
            parts = tag[1:].split(".")
            return tuple(int(p) for p in parts)

        tags.sort(key=version_key)
        return tags[-1]

    except Exception:
        return "v0.0.0"


def calculate_next_version(current_version: str, set_major: bool = False, set_minor: bool = False) -> str:
    """
    Calculate next version based on current version and flags.

    Parameters
    ----------
    current_version : str
        Current version (e.g. 'v0.5.1')
    set_major : bool
        Set major version (X+1.0.0)
    set_minor : bool
        Set minor version (X.Y+1.0)

    Returns
    -------
    str
        Next version (e.g. 'v0.5.2')
    """
    # Parse current version
    match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", current_version)
    if not match:
        return "v0.0.1"

    major, minor, patch = map(int, match.groups())

    if set_major:
        major += 1
        minor = 0
        patch = 0
    elif set_minor:
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"v{major}.{minor}.{patch}"


def update_pyproject_version(pyproject_path: str, new_version: str) -> bool:
    """
    Update version in pyproject.toml.

    Parameters
    ----------
    pyproject_path : str
        Path to pyproject.toml
    new_version : str
        New version without 'v' prefix (e.g. '0.5.2')

    Returns
    -------
    bool
        True if successful
    """
    if not os.path.exists(pyproject_path):
        print(f"Error: pyproject.toml not found at {pyproject_path}")
        return False

    try:
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find and replace version line
        pattern = r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"'
        new_line = f'version = "{new_version}"'

        if not re.search(pattern, content, re.MULTILINE):
            print("Error: version line not found in pyproject.toml")
            return False

        updated_content = re.sub(pattern, new_line, content, flags=re.MULTILINE)

        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return True

    except Exception as e:
        print(f"Error updating pyproject.toml: {e}")
        return False


def commit_version_change(version: str) -> bool:
    """
    Commit pyproject.toml version change.

    Parameters
    ----------
    version : str
        Version without 'v' prefix (e.g. '0.5.2')

    Returns
    -------
    bool
        True if successful
    """
    try:
        subprocess.run(["git", "add", "pyproject.toml"], check=True, timeout=5)

        subprocess.run(["git", "commit", "-m", f"Set version to {version}"], check=True, timeout=10)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error committing version change: {e}")
        return False


def create_git_tag(version: str, push: bool = True) -> bool:
    """
    Create and optionally push git tag.

    Parameters
    ----------
    version : str
        Version with 'v' prefix (e.g. 'v0.5.2')
    push : bool
        Push tag to remote

    Returns
    -------
    bool
        True if successful
    """
    try:
        # Create tag
        subprocess.run(["git", "tag", "-a", version, "-m", f"Deployed version {version[1:]}"], check=True, timeout=10)

        # Push tag if requested
        if push:
            subprocess.run(["git", "push", "origin", version], check=True, timeout=30)

            # Also push commits
            subprocess.run(["git", "push"], check=True, timeout=30)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Warning: Git tag operation failed: {e}")
        return False


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
    parser.add_argument("--set-major", action="store_true", help="Set major version (X+1.0.0)")
    parser.add_argument("--set-minor", action="store_true", help="Set minor version (X.Y+1.0)")
    parser.add_argument("--no-push", action="store_true", help="Don't push git tags to remote")
    parser.add_argument(
        "--bootstrap-internal",
        action="store_true",
        help="Internal flag for bootstrap deployment (do not use manually)",
    )

    return parser.parse_args()


def main():
    """
    Deploy current module using DeploymentManager with bootstrap detection and version management.
    """
    args = parse_arguments()

    # Check for internal bootstrap call
    if args.bootstrap_internal:
        bootstrap_deploy_internal(force=args.force)
        sys.exit(0)

    # Git repository check (required for deployment)
    if not is_git_repository():
        print("Error: Not a git repository")
        print("Deployment requires git for version management")
        sys.exit(1)

    # Check for uncommitted changes (blocking)
    if not check_git_clean():
        print("Error: Git working directory has uncommitted changes")
        print("Please commit or stash your changes before deploying")
        sys.exit(1)

    # Version management
    current_version = None
    next_version = None

    # Get current and calculate next version
    current_version = get_current_git_version()
    next_version = calculate_next_version(current_version, args.set_major, args.set_minor)

    print(f"Current version: {current_version}")
    print(f"Next version: {next_version}")

    # Update pyproject.toml
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")
    version_without_v = next_version[1:]

    if not update_pyproject_version(pyproject_path, version_without_v):
        print("Error: Failed to update pyproject.toml")
        sys.exit(1)

    print(f"✓ Updated pyproject.toml ({current_version[1:]} → {version_without_v})")

    # Commit version change
    if not commit_version_change(version_without_v):
        print("Error: Failed to commit version change")
        sys.exit(1)

    print("✓ Committed version change")

    # Execute deployment
    if is_bootstrap_deployment():
        bootstrap_deploy(force=args.force)
    else:
        normal_deploy(force=args.force)

    # Create git tag after successful deployment
    if create_git_tag(next_version, push=not args.no_push):
        if args.no_push:
            print(f"✓ Git tag {next_version} created (not pushed)")
        else:
            print(f"✓ Git tag {next_version} created and pushed")
    else:
        print(f"Warning: Deployment successful but git tag operation failed")

    sys.exit(0)


if __name__ == "__main__":
    main()
