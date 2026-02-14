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
  v1.4 : Added VERSION file deployment for runtime version access
  v1.5 : Added version comparison to prevent unnecessary commits
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
        result = subprocess.run(
            ["git", "tag", "-l", "v*.*.*"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

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


def get_current_commit_hash() -> str:
    """
    Get current commit hash.

    Returns
    -------
    str
        Current commit hash or empty string on error
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_commit_tags(commit_hash: str) -> list:
    """
    Get all tags pointing to specific commit.

    Parameters
    ----------
    commit_hash : str
        Commit hash to check

    Returns
    -------
    list
        List of version tags (e.g. ['v0.5.2']) or empty list
    """
    try:
        result = subprocess.run(
            ["git", "tag", "--points-at", commit_hash],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

        tags = result.stdout.strip().split("\n")
        tags = [t for t in tags if t and re.match(r"^v\d+\.\d+\.\d+$", t)]
        return tags

    except Exception:
        return []


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


def get_pyproject_version(pyproject_path: str) -> str:
    """
    Read current version from pyproject.toml.

    Parameters
    ----------
    pyproject_path : str
        Path to pyproject.toml

    Returns
    -------
    str
        Current version without 'v' prefix (e.g. '0.5.2') or empty string if not found
    """
    if not os.path.exists(pyproject_path):
        return ""

    try:
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"'
        match = re.search(pattern, content, re.MULTILINE)

        if match:
            return match.group(1)

        return ""

    except Exception:
        return ""


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


def find_package_init_file() -> str | None:
    """
    Find package __init__.py in src/ directory.

    Returns
    -------
    str | None
        Path to __init__.py or None if not found
    """
    src_dir = os.path.join(os.getcwd(), "src")
    if not os.path.exists(src_dir):
        return None

    # Find first package directory (skip __pycache__, ., ..)
    for item in os.listdir(src_dir):
        item_path = os.path.join(src_dir, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            init_file = os.path.join(item_path, "__init__.py")
            if os.path.exists(init_file):
                return init_file

    return None


def patch_init_version(init_file: str, package_name: str) -> bool:
    """
    Patch __init__.py with runtime-dynamic __version__ and get_version().

    Parameters
    ----------
    init_file : str
        Path to __init__.py
    package_name : str
        Package name (e.g., 'dbfunctions')

    Returns
    -------
    bool
        True if patched, False if already exists or error
    """
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already patched
        if '__version__' in content and 'get_version()' in content:
            print(f"ℹ {init_file} already has __version__ and get_version()")
            return False

        # Find insertion point (before __all__ or at end of imports)
        lines = content.split('\n')
        insert_pos = None

        # Look for __all__ definition
        for i, line in enumerate(lines):
            if line.strip().startswith('__all__'):
                insert_pos = i
                break

        # Fallback: after last import
        if insert_pos is None:
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().startswith(('from ', 'import ')):
                    insert_pos = i + 1
                    break

        if insert_pos is None:
            print(f"Error: Could not find insertion point in {init_file}")
            return False

        # Build version management block
        version_block = [
            '',
            '# -------------------------------------------------------------',
            '# VERSION MANAGEMENT',
            '# -------------------------------------------------------------',
            'from basefunctions.runtime.version import version as _get_version_string',
            '',
            '# Runtime-dynamisch: Bei jedem Import neu berechnet',
            '# Liefert installierte Version + Dev-Info falls im Development',
            f'__version__: str = _get_version_string("{package_name}")',
            '',
            '',
            'def get_version() -> str:',
            '    """',
            '    Get current package version with development information.',
            '    ',
            '    Returns',
            '    -------',
            '    str',
            '        Version string, e.g. "0.5.80" (deployed) or "0.5.80-dev+3" (development)',
            '    ',
            '    Examples',
            '    --------',
            f'    >>> import {package_name}',
            f'    >>> {package_name}.get_version()',
            '    \'0.5.80-dev+3\'',
            '    ',
            '    Notes',
            '    -----',
            '    This function returns the same value as `__version__` attribute.',
            '    Use whichever is more convenient for your use case.',
            '    """',
            '    return __version__',
            '',
            ''
        ]

        # Insert version block
        lines[insert_pos:insert_pos] = version_block

        # Join and update __all__ if it exists
        updated_content = '\n'.join(lines)

        # Add to __all__ if not present
        if '__all__' in updated_content:
            # Find __all__ = [ line
            all_pattern = r'(__all__\s*=\s*\[)'

            # Only add if not already there
            if '"__version__"' not in updated_content:
                replacement = r'\1\n    # Version Management\n    "__version__",\n    "get_version",'
                updated_content = re.sub(all_pattern, replacement, updated_content)

        # Write back
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✓ Patched {init_file} with __version__ and get_version()")
        return True

    except Exception as e:
        print(f"Error patching {init_file}: {e}")
        return False


def commit_version_change(version: str) -> bool:
    """
    Commit pyproject.toml and __init__.py version change.

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

        # Also add __init__.py if it was patched
        init_file = find_package_init_file()
        if init_file:
            subprocess.run(["git", "add", init_file], check=True, timeout=5)

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
        subprocess.run(
            ["git", "tag", "-a", version, "-m", f"Deployed version {version[1:]}"],
            check=True,
            timeout=10,
        )

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


def bootstrap_deploy(force: bool = False, version: str | None = None):
    """
    Deploy basefunctions using local development environment with venv.

    Parameters
    ----------
    force : bool
        Force deployment even if no changes detected
    version : str | None
        Version string to deploy
    """
    print("Bootstrap mode detected - deploying basefunctions using local environment")

    current_dir = os.getcwd()
    venv_python = os.path.join(current_dir, ".venv", "bin", "python")

    if not os.path.exists(venv_python):
        print("Error: Local .venv/bin/python not found in basefunctions development directory")
        sys.exit(1)

    try:
        # Build command arguments
        cmd_args = [venv_python, os.path.abspath(__file__), "--bootstrap-internal"]
        if force:
            cmd_args.append("--force")
        if version:
            cmd_args.extend(["--internal-version", version])

        # Re-execute this script with local venv python
        subprocess.run(cmd_args, check=True)

        print("Bootstrap deployment completed successfully")

    except subprocess.CalledProcessError as e:
        print(f"Bootstrap deployment failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Bootstrap deployment failed: {e}")
        sys.exit(1)


def bootstrap_deploy_internal(force: bool = False, version: str | None = None):
    """
    Internal bootstrap deployment called with correct venv.

    Parameters
    ----------
    force : bool
        Force deployment even if no changes detected
    version : str | None
        Version string to deploy
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

        # Deploy the module with force flag and version
        deployed, _ = deployment_manager.deploy_module(module_name, force=force, version=version)

        if not deployed:
            print(f"No deployment needed for {module_name} (no changes detected)")
            if not force:
                print("Use --force to deploy anyway")

    except Exception as e:
        print(f"Bootstrap deployment failed: {e}")
        sys.exit(1)


def normal_deploy(force: bool = False, version: str | None = None):
    """
    Deploy module using deployed basefunctions.

    Parameters
    ----------
    force : bool
        Force deployment even if no changes detected
    version : str | None
        Version string to deploy
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

        # Deploy the module with force flag and version
        deployed, _ = deployment_manager.deploy_module(module_name, force=force, version=version)

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
    parser.add_argument("--set-version", type=str, help="Set specific version (e.g. 2.3.5)")
    parser.add_argument("--no-push", action="store_true", help="Don't push git tags to remote")
    parser.add_argument(
        "--bootstrap-internal",
        action="store_true",
        help="Internal flag for bootstrap deployment (do not use manually)",
    )
    parser.add_argument("--internal-version", type=str, help="Internal version parameter (do not use manually)")

    return parser.parse_args()


def main():
    """
    Deploy current module using DeploymentManager with bootstrap detection and version management.
    """
    args = parse_arguments()

    # Check for internal bootstrap call
    if args.bootstrap_internal:
        bootstrap_deploy_internal(force=args.force, version=args.internal_version)
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
    version_already_set = False

    # Check if current commit already has a version tag
    current_commit = get_current_commit_hash()
    commit_tags = get_commit_tags(current_commit)

    if commit_tags:
        # Current commit already has version tag
        current_version = commit_tags[0]  # Use first tag if multiple
        version_already_set = True
        print(f"Current commit already tagged with: {current_version}")

    # Manual version setting
    if args.set_version:
        # Validate version format
        if not re.match(r"^\d+\.\d+\.\d+$", args.set_version):
            print("Error: Invalid version format (use X.Y.Z, e.g. 2.3.5)")
            sys.exit(1)

        # Check for conflicting flags
        if args.set_major or args.set_minor:
            print("Error: --set-version cannot be combined with --set-major or --set-minor")
            sys.exit(1)

        next_version = f"v{args.set_version}"

        if not version_already_set:
            current_version = "manual"
            print(f"Setting version to: {next_version}")
        else:
            print(f"Note: Current commit already tagged, will update to: {next_version}")
            current_version = commit_tags[0]
    else:
        # Automatic version calculation
        if not version_already_set:
            # No tag on current commit - calculate next version
            current_version = get_current_git_version()
            next_version = calculate_next_version(current_version, args.set_major, args.set_minor)

            print(f"Current version: {current_version}")
            print(f"Next version: {next_version}")
        else:
            # Current commit already tagged - no version change needed
            next_version = current_version
            print("Version already set for this commit, no version change needed")

    # Type guard: next_version must be set by now
    if next_version is None:
        print("Error: Version could not be determined")
        sys.exit(1)

    # Update pyproject.toml and commit only if version needs to change
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")
    version_without_v = next_version[1:]
    current_pyproject_version = get_pyproject_version(pyproject_path)

    if not version_already_set or args.set_version:
        # Check if version actually needs updating
        if current_pyproject_version == version_without_v:
            print(f"ℹ pyproject.toml already at version {version_without_v}, skipping commit")
        else:
            # Version needs updating
            if not update_pyproject_version(pyproject_path, version_without_v):
                print("Error: Failed to update pyproject.toml")
                sys.exit(1)

            # Patch __init__.py with version management
            module_name = os.path.basename(os.getcwd())
            init_file = find_package_init_file()
            if init_file:
                patch_init_version(init_file, module_name)

            if current_version == "manual":
                print(f"✓ Updated pyproject.toml (→ {version_without_v})")
            else:
                # Safe fallback for current_version display
                old_ver = current_pyproject_version or (current_version[1:] if current_version else "unknown")
                print(f"✓ Updated pyproject.toml ({old_ver} → {version_without_v})")

            # Commit version change
            if not commit_version_change(version_without_v):
                print("Error: Failed to commit version change")
                sys.exit(1)

            print("✓ Committed version change")

    # Execute deployment with version parameter
    if is_bootstrap_deployment():
        bootstrap_deploy(force=args.force, version=next_version)
    else:
        normal_deploy(force=args.force, version=next_version)

    # Create git tag after successful deployment (only if not already tagged)
    if not version_already_set or args.set_version:
        if create_git_tag(next_version, push=not args.no_push):
            if args.no_push:
                print(f"✓ Git tag {next_version} created (not pushed)")
            else:
                print(f"✓ Git tag {next_version} created and pushed")
        else:
            print("Warning: Deployment successful but git tag operation failed")
    else:
        print(f"✓ Version {next_version} already tagged")

    sys.exit(0)


if __name__ == "__main__":
    main()
