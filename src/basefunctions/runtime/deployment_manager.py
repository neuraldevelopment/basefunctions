"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Module deployment logic with combined change detection and context validation

  Log:
  v1.0 : Initial implementation
  v1.1 : Fixed hash storage path to use consistent deployment directory system
  v1.2 : Added local dependency installation from deployed packages
  v1.3 : Added dependency timestamp tracking for automatic change detection
  v1.4 : Added NO_VENV_TOOLS list for tools that should not activate venv
  v1.5 : Added force flag, bin/templates monitoring, and proper return handling
  v1.6 : Migrated to VenvUtils for platform-aware and robust venv operations
  v1.7 : Extended deploy_module to return version information
  v1.8 : Removed VERSION file deployment (using package metadata instead)
  v1.9 : Improved exception handling with specific exception types and logging
  v1.10: Added path validation before destructive operations for safety
  v1.11: Modified local package installation to use ppip with fallback to pip
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import shutil
import hashlib
import subprocess
import sys
from typing import List, Optional, Tuple
from pathlib import Path
from basefunctions.utils.logging import setup_logger, get_logger
import basefunctions

# Conditional TOML library import
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
HASH_STORAGE_SUBPATH = "deployment/hashes"

# Tools that should NOT activate their virtual environment
NO_VENV_TOOLS = [
    "clean_virtual_environment.py",
    "clean_virtual_environment",
    "ppip.py",
    "ppip",
    "update_packages.py",
    "update_packages",
    "deploy_manager.py",
    "deploy_manager",
]
# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
setup_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------


class DeploymentError(Exception):
    """Exception raised during deployment operations."""


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


@basefunctions.singleton
class DeploymentManager:
    """
    Singleton for handling module deployment with change detection and context validation.
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    def _validate_deployment_path(self, path: str) -> None:
        """
        Validate path before destructive operations to prevent accidental deletions.

        Parameters
        ----------
        path : str
            Path to validate

        Raises
        ------
        DeploymentError
            If path is unsafe for destructive operations

        Notes
        -----
        Performs multiple safety checks:
        - Rejects system directories (/, /usr, /etc, etc.)
        - Rejects home directory
        - Ensures path is within deployment directory
        - Validates minimum path depth from deployment root

        Examples
        --------
        >>> manager = DeploymentManager()
        >>> manager._validate_deployment_path("~/.neuraldevelopment/packages/mymodule")  # OK
        >>> manager._validate_deployment_path("/")  # Raises DeploymentError
        >>> manager._validate_deployment_path("~")  # Raises DeploymentError
        """
        if not path:
            raise DeploymentError("Path cannot be empty")

        # Normalize and resolve path
        normalized_path = os.path.abspath(os.path.expanduser(path))

        # CRITICAL CHECKS - System directory protection
        system_directories = [
            "/",
            "/usr",
            "/bin",
            "/sbin",
            "/etc",
            "/var",
            "/tmp",
            "/boot",
            "/dev",
            "/proc",
            "/sys",
            "/lib",
            "/lib64",
            "/opt",
            "/srv",
        ]

        for sys_dir in system_directories:
            if normalized_path == sys_dir or normalized_path.startswith(sys_dir + "/"):
                raise DeploymentError(
                    f"CRITICAL: Cannot perform destructive operation on system directory: {normalized_path}"
                )

        # Home directory protection
        home_dir = os.path.expanduser("~")
        if normalized_path == home_dir:
            raise DeploymentError(
                f"CRITICAL: Cannot perform destructive operation on home directory: {normalized_path}"
            )

        # Deployment directory validation
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        normalized_deploy_dir = os.path.abspath(os.path.expanduser(deploy_dir))

        # Path must contain deployment directory
        if not normalized_path.startswith(normalized_deploy_dir):
            raise DeploymentError(
                f"Path must be within deployment directory.\n"
                f"Path: {normalized_path}\n"
                f"Expected to start with: {normalized_deploy_dir}"
            )

        # Path depth validation - must be at least 1 level deep from deployment root
        # e.g., ~/.neuraldevelopment/packages (minimum 1 part after deploy_dir)
        relative_path = normalized_path[len(normalized_deploy_dir) :].lstrip("/")
        path_parts = [p for p in relative_path.split("/") if p]

        if len(path_parts) < 1:
            raise DeploymentError(
                f"Path too shallow for destructive operation.\n"
                f"Path: {normalized_path}\n"
                f"Must be at least 1 level deep from deployment root"
            )

    def deploy_module(self, module_name: str, force: bool = False, version: str = None) -> Tuple[bool, str]:
        """
        Deploy specific module with context validation and change detection.

        Parameters
        ----------
        module_name : str
            Name of the module to deploy
        force : bool
            Force deployment even if no changes detected
        version : str, optional
            Version string for logging (e.g. 'v0.5.2')

        Returns
        -------
        Tuple[bool, str]
            (deployed, version) - True if deployment was performed with version string

        Raises
        ------
        DeploymentError
            If user not in development directory or deployment fails
        """
        if not module_name:
            raise DeploymentError("Module name must be provided")

        # Context validation - user must be in development directory of this module
        cwd = os.getcwd()
        dev_paths = basefunctions.runtime.find_development_path(module_name)

        if not dev_paths:
            raise DeploymentError(f"Module '{module_name}' not found in any development directory")

        # Find the dev path user is currently in
        current_module_path = None
        for dev_path in dev_paths:
            if cwd.startswith(dev_path):
                current_module_path = dev_path
                break

        if current_module_path is None:
            raise DeploymentError(
                f"You must be inside the development directory of '{module_name}' to deploy it!\n"
                f"Current: {cwd}\n"
                f"Expected: Inside one of {dev_paths}"
            )

        source_path = current_module_path
        target_path = basefunctions.runtime.get_deployment_path(module_name)

        # Change detection
        if not force and not self._detect_changes(module_name, source_path):
            print(f"No changes detected for {module_name}")
            return False, version or "unknown"

        version_info = f" {version}" if version else ""
        self.logger.critical(f"Deploying {module_name}{version_info} from {source_path} to {target_path}")

        # Clean target if exists (with path validation)
        if os.path.exists(target_path):
            self._validate_deployment_path(target_path)
            shutil.rmtree(target_path)

        # Create logs subdirectory (KISSS-style)
        os.makedirs(target_path, exist_ok=True)
        os.makedirs(os.path.join(target_path, "logs"), exist_ok=True)

        # Deployment components
        self._deploy_venv(source_path, target_path)
        self._deploy_templates(source_path, target_path)
        self._deploy_configs(target_path)
        self._deploy_bin_tools(source_path, target_path, module_name)

        # Update hash for next detection
        self._update_hash(module_name, source_path)

        self.logger.critical(f"Successfully deployed {module_name}{version_info}")
        print(f"✓ Successfully deployed {module_name}{version_info}")

        return True, version or "unknown"

    def clean_deployment(self, module_name: str) -> None:
        """
        Delete complete deployment for fresh start.

        Parameters
        ----------
        module_name : str
            Name of the module to clean
        """
        if not module_name:
            raise DeploymentError("Module name must be provided")

        target_path = basefunctions.runtime.get_deployment_path(module_name)

        if os.path.exists(target_path):
            self._validate_deployment_path(target_path)
            shutil.rmtree(target_path)
            self.logger.critical(f"Cleaned deployment for {module_name}")
            print(f"Cleaned deployment for {module_name}")

        # Remove global wrappers
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        global_bin = os.path.join(os.path.abspath(os.path.expanduser(deploy_dir)), "bin")
        self._remove_module_wrappers(global_bin, module_name)

        # Remove stored hash
        self._remove_stored_hash(module_name)

    def _detect_changes(self, module_name: str, source_path: str) -> bool:
        """
        Detect changes using combined hash strategy.

        Parameters
        ----------
        module_name : str
            Module name for hash storage
        source_path : str
            Source path to analyze

        Returns
        -------
        bool
            True if changes detected, False otherwise
        """
        # Check if deployment exists - if not, force deployment
        target_path = basefunctions.runtime.get_deployment_path(module_name)
        if not os.path.exists(target_path):
            return True

        current_hash = self._calculate_combined_hash(source_path)
        stored_hash = self._get_stored_hash(module_name)

        return current_hash != stored_hash

    def _calculate_combined_hash(self, module_path: str) -> str:
        """
        Calculate combined hash from source code, bin tools, templates, pip environment and dependency timestamps.

        Parameters
        ----------
        module_path : str
            Path to module

        Returns
        -------
        str
            Combined SHA256 hash
        """
        src_hash = self._hash_src_files(module_path) if self._has_src_directory(module_path) else "no-src"
        pip_hash = self._hash_pip_freeze(os.path.join(module_path, ".venv"))
        bin_hash = self._hash_bin_files(module_path)
        templates_hash = self._hash_template_files(module_path)
        dependency_timestamps = self._get_dependency_timestamps(module_path)

        combined = f"{src_hash}:{pip_hash}:{bin_hash}:{templates_hash}:{dependency_timestamps}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _hash_bin_files(self, module_path: str) -> str:
        """
        Calculate hash for all files in bin directory.

        Parameters
        ----------
        module_path : str
            Path to module

        Returns
        -------
        str
            SHA256 hash of bin files
        """
        bin_files = []
        bin_dir = os.path.join(module_path, "bin")

        if not os.path.exists(bin_dir):
            return "no-bin"

        for root, _, files in os.walk(bin_dir):
            for file in files:
                filepath = os.path.join(root, file)
                mtime = os.path.getmtime(filepath)
                bin_files.append(f"{filepath}:{mtime}")

        return hashlib.sha256("".join(sorted(bin_files)).encode()).hexdigest()

    def _hash_template_files(self, module_path: str) -> str:
        """
        Calculate hash for all files in templates directory.

        Parameters
        ----------
        module_path : str
            Path to module

        Returns
        -------
        str
            SHA256 hash of template files
        """
        template_files = []
        templates_dir = os.path.join(module_path, "templates")

        if not os.path.exists(templates_dir):
            return "no-templates"

        for root, _, files in os.walk(templates_dir):
            for file in files:
                filepath = os.path.join(root, file)
                mtime = os.path.getmtime(filepath)
                template_files.append(f"{filepath}:{mtime}")

        return hashlib.sha256("".join(sorted(template_files)).encode()).hexdigest()

    def _get_dependency_timestamps(self, module_path: str) -> str:
        """
        Get timestamps of all local dependencies for change detection.

        Parameters
        ----------
        module_path : str
            Path to module

        Returns
        -------
        str
            Combined timestamp string of all local dependencies
        """
        local_deps = self._parse_project_dependencies(module_path)
        available_local = self._get_available_local_packages()

        # Filter to only local dependencies that are actually available
        relevant_deps = [dep for dep in local_deps if dep in available_local]

        if not relevant_deps:
            return "no-local-deps"

        timestamps = []
        for dep in sorted(relevant_deps):  # Sort for consistent hash
            timestamp = self._get_deployment_timestamp(dep)
            timestamps.append(f"{dep}:{timestamp}")

        return hashlib.sha256("|".join(timestamps).encode()).hexdigest()

    def _get_deployment_timestamp(self, package_name: str) -> str:
        """
        Get deployment timestamp for a package.

        Parameters
        ----------
        package_name : str
            Package name

        Returns
        -------
        str
            Timestamp string or 'not-deployed'
        """
        deploy_path = basefunctions.runtime.get_deployment_path(package_name)

        if not os.path.exists(deploy_path):
            return "not-deployed"

        try:
            # Get the most recent modification time from the deployment directory
            latest_mtime = 0
            for root, _, files in os.walk(deploy_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    mtime = os.path.getmtime(file_path)
                    latest_mtime = max(latest_mtime, mtime)

            return str(latest_mtime)
        except OSError as e:
            self.logger.warning(f"Failed to get deployment timestamp for {package_name}: {e}")
            return "timestamp-error"
        except Exception as e:
            self.logger.warning(f"Unexpected error getting deployment timestamp for {package_name}: {e}")
            return "timestamp-error"

    def _has_src_directory(self, module_path: str) -> bool:
        """
        Check if module has src directory.

        Parameters
        ----------
        module_path : str
            Path to module

        Returns
        -------
        bool
            True if src directory exists
        """
        return os.path.exists(os.path.join(module_path, "src"))

    def _hash_src_files(self, module_path: str) -> str:
        """
        Calculate hash for all Python files in src directory.

        Parameters
        ----------
        module_path : str
            Path to module

        Returns
        -------
        str
            SHA256 hash of source files
        """
        src_files = []
        src_dir = os.path.join(module_path, "src")

        if not os.path.exists(src_dir):
            return "no-src"

        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    mtime = os.path.getmtime(filepath)
                    src_files.append(f"{filepath}:{mtime}")

        return hashlib.sha256("".join(sorted(src_files)).encode()).hexdigest()

    def _hash_pip_freeze(self, venv_path: str) -> str:
        """
        Calculate hash from pip freeze output.

        Parameters
        ----------
        venv_path : str
            Path to virtual environment

        Returns
        -------
        str
            SHA256 hash of pip packages
        """
        if not os.path.exists(venv_path):
            return "no-venv"

        pip_executable = os.path.join(venv_path, "bin", "pip")

        if not os.path.exists(pip_executable):
            return "no-pip"

        try:
            result = subprocess.run(
                [pip_executable, "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return "pip-error"

            packages = sorted(result.stdout.strip().split("\n"))
            return hashlib.sha256("".join(packages).encode()).hexdigest()

        except subprocess.TimeoutExpired as e:
            self.logger.warning(f"Timeout running pip list for {venv_path}: {e}")
            return "pip-timeout"
        except subprocess.SubprocessError as e:
            self.logger.warning(f"Subprocess error running pip list for {venv_path}: {e}")
            return "pip-exception"
        except Exception as e:
            self.logger.warning(f"Unexpected error running pip list for {venv_path}: {e}")
            return "pip-exception"

    def _get_stored_hash(self, module_name: str) -> Optional[str]:
        """
        Get stored hash for module.

        Parameters
        ----------
        module_name : str
            Module name

        Returns
        -------
        Optional[str]
            Stored hash or None if not found
        """
        hash_file = self._get_hash_file_path(module_name)

        if not os.path.exists(hash_file):
            return None

        try:
            with open(hash_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Expected when no hash exists yet
            return None
        except OSError as e:
            self.logger.warning(f"Failed to read stored hash for {module_name}: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Unexpected error reading stored hash for {module_name}: {e}")
            return None

    def _update_hash(self, module_name: str, source_path: str) -> None:
        """
        Update stored hash for module.

        Parameters
        ----------
        module_name : str
            Module name
        source_path : str
            Source path to calculate hash from
        """
        hash_file = self._get_hash_file_path(module_name)
        os.makedirs(os.path.dirname(hash_file), exist_ok=True)

        current_hash = self._calculate_combined_hash(source_path)

        try:
            with open(hash_file, "w", encoding="utf-8") as f:
                f.write(current_hash)
        except Exception as e:
            self.logger.critical(f"Failed to update hash for {module_name}: {e}")

    def _remove_stored_hash(self, module_name: str) -> None:
        """
        Remove stored hash for module.

        Parameters
        ----------
        module_name : str
            Module name
        """
        hash_file = self._get_hash_file_path(module_name)

        if os.path.exists(hash_file):
            try:
                os.remove(hash_file)
            except Exception as e:
                self.logger.critical(f"Failed to remove hash for {module_name}: {e}")

    def _get_hash_file_path(self, module_name: str) -> str:
        """
        Get hash file path for module using consistent deployment directory system.

        Parameters
        ----------
        module_name : str
            Module name

        Returns
        -------
        str
            Path to hash file
        """
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        normalized_deploy_dir = os.path.abspath(os.path.expanduser(deploy_dir))
        hash_dir = os.path.join(normalized_deploy_dir, HASH_STORAGE_SUBPATH)
        return os.path.join(hash_dir, f"{module_name}.hash")

    def _get_available_local_packages(self) -> List[str]:
        """
        Get list of available local packages from deployment directory.

        Returns
        -------
        List[str]
            List of available package names
        """
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        packages_dir = os.path.join(os.path.abspath(os.path.expanduser(deploy_dir)), "packages")

        if not os.path.exists(packages_dir):
            return []

        try:
            return [name for name in os.listdir(packages_dir) if os.path.isdir(os.path.join(packages_dir, name))]
        except FileNotFoundError:
            # Expected when deployment directory doesn't exist yet
            return []
        except OSError as e:
            self.logger.warning(f"Failed to list packages in {packages_dir}: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Unexpected error listing packages in {packages_dir}: {e}")
            return []

    def _parse_project_dependencies(self, source_path: str) -> List[str]:
        """
        Parse dependencies from pyproject.toml using proper TOML parser.

        Parameters
        ----------
        source_path : str
            Path to source directory containing pyproject.toml

        Returns
        -------
        List[str]
            List of dependency package names
        """
        pyproject_file = os.path.join(source_path, "pyproject.toml")

        if not os.path.exists(pyproject_file):
            return []

        if tomllib is None:
            self.logger.warning("Neither tomllib nor tomli available. Install tomli for Python <3.11")
            return []

        try:
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)

            # Extract dependencies from [project] section
            dependencies = data.get("project", {}).get("dependencies", [])

            # Extract package names (remove version specifiers)
            packages = []
            for dep in dependencies:
                if isinstance(dep, str):
                    # Split on common version specifiers and take first part
                    pkg_name = dep.split(">=")[0].split("==")[0].split("~=")[0].split("<")[0].split(">")[0]
                    pkg_name = pkg_name.split("[")[0].strip()  # Remove extras
                    packages.append(pkg_name)

            return packages

        except FileNotFoundError:
            self.logger.warning(f"pyproject.toml not found: {pyproject_file}")
            return []
        except Exception as e:
            self.logger.warning(f"Could not parse {pyproject_file}: {e}")
            return []

    def _get_local_dependencies_intersection(self, source_path: str) -> List[str]:
        """
        Get intersection of project dependencies and available local packages.

        Parameters
        ----------
        source_path : str
            Path to source directory

        Returns
        -------
        List[str]
            List of local dependencies to install
        """
        available_local = self._get_available_local_packages()
        project_deps = self._parse_project_dependencies(source_path)

        return [dep for dep in project_deps if dep in available_local]

    def _install_local_package_with_venvutils(self, venv_path: Path, package_name: str) -> None:
        """
        Install local package from deployment directory using ppip or VenvUtils.

        Parameters
        ----------
        venv_path : Path
            Path to virtual environment
        package_name : str
            Name of the package to install

        Raises
        ------
        DeploymentError
            If installation fails

        Notes
        -----
        Attempts to use ppip for local-first installation with automatic dependency
        resolution. Falls back to direct pip installation if ppip is not available.
        """
        deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
        package_path = os.path.join(os.path.abspath(os.path.expanduser(deploy_dir)), "packages", package_name)

        if not os.path.exists(package_path):
            raise DeploymentError(f"Local package '{package_name}' not found at {package_path}")

        try:
            # Try ppip first (handles dependencies automatically)
            try:
                basefunctions.VenvUtils.install_with_ppip([package_name], venv_path, fallback_to_pip=False)
                self.logger.critical(f"Installed local dependency via ppip: {package_name}")
                return
            except basefunctions.VenvUtilsError:
                # ppip not available, fallback to direct installation
                self.logger.info(f"ppip not available, using direct pip installation for {package_name}")

            # Fallback: Direct installation without dependency resolution
            basefunctions.VenvUtils.run_pip_command(
                ["install", package_path], venv_path, timeout=300, capture_output=False
            )
            self.logger.critical(f"Installed local dependency: {package_name}")
        except basefunctions.VenvUtilsError as e:
            raise DeploymentError(f"Failed to install local package '{package_name}': {e}")

    def _copy_package_structure(self, source_path: str, target_path: str) -> None:
        """
        Copy complete package structure for pip installation.

        Parameters
        ----------
        source_path : str
            Source module path
        target_path : str
            Target deployment path
        """
        # Files to copy
        files_to_copy = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "README.md",
            "LICENSE",
        ]

        # Directories to copy
        dirs_to_copy = ["src", "templates", "config"]

        # Copy files
        for filename in files_to_copy:
            source_file = os.path.join(source_path, filename)
            target_file = os.path.join(target_path, filename)

            if os.path.exists(source_file):
                try:
                    shutil.copy2(source_file, target_file)
                    self.logger.critical(f"Copied package file: {filename}")
                except Exception as e:
                    self.logger.critical(f"Failed to copy {filename}: {e}")

        # Copy directories
        for dirname in dirs_to_copy:
            source_dir = os.path.join(source_path, dirname)
            target_dir = os.path.join(target_path, dirname)

            if os.path.exists(source_dir):
                try:
                    if os.path.exists(target_dir):
                        self._validate_deployment_path(target_dir)
                        shutil.rmtree(target_dir)
                    shutil.copytree(source_dir, target_dir)
                    self.logger.critical(f"Copied package directory: {dirname}")
                except Exception as e:
                    self.logger.critical(f"Failed to copy directory {dirname}: {e}")

    def _deploy_venv(self, source_path: str, target_path: str) -> None:
        """
        Deploy virtual environment by creating fresh venv and installing dependencies.

        Parameters
        ----------
        source_path : str
            Source module path
        target_path : str
            Target deployment path
        """
        source_venv = os.path.join(source_path, ".venv")
        target_venv_path = Path(target_path) / "venv"

        if not os.path.exists(source_venv):
            return

        try:
            # Create fresh virtual environment
            os.makedirs(os.path.dirname(target_venv_path), exist_ok=True)
            subprocess.run(
                [sys.executable, "-m", "venv", str(target_venv_path)],
                check=True,
                timeout=120,
            )

            # Copy complete package structure to make it pip-installable
            self._copy_package_structure(source_path, target_path)

            # Upgrade pip using VenvUtils (silent)
            basefunctions.VenvUtils.upgrade_pip(target_venv_path, capture_output=True)

            # Install local dependencies first (visible)
            local_deps = self._get_local_dependencies_intersection(source_path)
            for dep in local_deps:
                self._install_local_package_with_venvutils(target_venv_path, dep)

            # Install current module using VenvUtils (visible)
            basefunctions.VenvUtils.run_pip_command(
                ["install", source_path],
                target_venv_path,
                timeout=300,
                capture_output=False,
            )

            self.logger.critical(f"Created fresh virtual environment at {target_venv_path}")
        except basefunctions.VenvUtilsError as e:
            raise DeploymentError(f"Failed to create virtual environment: {e}")
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to create virtual environment: {e}")
        except Exception as e:
            raise DeploymentError(f"Failed to deploy virtual environment: {e}")

    def _deploy_templates(self, source_path: str, target_path: str) -> None:
        """
        Deploy templates from source to target - always fresh copy.

        Parameters
        ----------
        source_path : str
            Source module path
        target_path : str
            Target deployment path
        """
        source_templates = os.path.join(source_path, "templates")
        target_templates = os.path.join(target_path, "templates")

        if not os.path.exists(source_templates):
            return

        try:
            if os.path.exists(target_templates):
                self._validate_deployment_path(target_templates)
                shutil.rmtree(target_templates)

            os.makedirs(os.path.dirname(target_templates), exist_ok=True)
            shutil.copytree(source_templates, target_templates)
            self.logger.critical(f"Deployed templates to {target_templates}")
        except Exception as e:
            raise DeploymentError(f"Failed to deploy templates: {e}")

    def _deploy_configs(self, target_path: str) -> None:
        """
        Deploy configs from templates - protect existing user configs.

        Parameters
        ----------
        target_path : str
            Target deployment path
        """
        config_dir = os.path.join(target_path, "config")
        template_dir = os.path.join(target_path, "templates", "config")

        if not os.path.exists(template_dir):
            return

        try:
            os.makedirs(config_dir, exist_ok=True)

            for template_file in os.listdir(template_dir):
                config_file = os.path.join(config_dir, template_file)

                if os.path.exists(config_file):
                    # User config exists - skip (protected)
                    continue
                else:
                    # Generate from template
                    template_path = os.path.join(template_dir, template_file)
                    shutil.copy2(template_path, config_file)

            self.logger.critical(f"Deployed configs to {config_dir}")
        except Exception as e:
            raise DeploymentError(f"Failed to deploy configs: {e}")

    def _deploy_bin_tools(self, source_path: str, target_path: str, module_name: str) -> None:
        """
        Deploy binary tools and create global wrappers.

        Parameters
        ----------
        source_path : str
            Source module path
        target_path : str
            Target deployment path
        module_name : str
            Module name for wrapper generation
        """
        source_bin = os.path.join(source_path, "bin")
        if not os.path.exists(source_bin):
            return
        try:
            # Copy tools to deployment
            target_bin = os.path.join(target_path, "bin")
            os.makedirs(target_bin, exist_ok=True)
            shutil.copytree(source_bin, target_bin, dirs_exist_ok=True)

            # Make all bin tools executable
            for tool in os.listdir(target_bin):
                tool_path = os.path.join(target_bin, tool)
                if os.path.isfile(tool_path):
                    os.chmod(tool_path, 0o755)

            # Create global wrappers
            deploy_dir = basefunctions.runtime.get_bootstrap_deployment_directory()
            global_bin = os.path.join(os.path.abspath(os.path.expanduser(deploy_dir)), "bin")
            os.makedirs(global_bin, exist_ok=True)

            for tool in os.listdir(source_bin):
                if os.path.isfile(os.path.join(source_bin, tool)):
                    self._create_wrapper(global_bin, tool, module_name, target_path)

            self.logger.critical(f"Deployed bin tools for {module_name}")
        except Exception as e:
            raise DeploymentError(f"Failed to deploy bin tools: {e}")

    def _create_wrapper(self, global_bin: str, tool_name: str, module_name: str, target_path: str) -> None:
        """
        Create wrapper script for tool in global bin directory.

        Parameters
        ----------
        global_bin : str
            Global bin directory path
        tool_name : str
            Name of the tool
        module_name : str
            Module name
        target_path : str
            Target deployment path
        """
        # Remove .py extension if present for wrapper name
        wrapper_name = tool_name.replace(".py", "") if tool_name.endswith(".py") else tool_name
        wrapper_path = os.path.join(global_bin, wrapper_name)
        venv_path = os.path.join(target_path, "venv")
        tool_path = os.path.join(target_path, "bin", tool_name)

        # Check if tool should run without venv activation
        if tool_name in NO_VENV_TOOLS:
            wrapper_content = f"""#!/bin/bash
# Auto-generated wrapper for {tool_name} from module {module_name} (no venv)
exec {tool_path} "$@"
"""
        else:
            wrapper_content = f"""#!/bin/bash
# Auto-generated wrapper for {tool_name} from module {module_name}
source {venv_path}/bin/activate
exec {tool_path} "$@"
"""

        try:
            with open(wrapper_path, "w") as f:
                f.write(wrapper_content)

            os.chmod(wrapper_path, 0o755)
        except Exception as e:
            self.logger.critical(f"Failed to create wrapper for {tool_name}: {e}")
            raise

    def _remove_module_wrappers(self, global_bin: str, module_name: str) -> None:
        """
        Remove wrappers by parsing functional code - not comments.

        Parameters
        ----------
        global_bin : str
            Global bin directory path
        module_name : str
            Module name
        """
        if not os.path.exists(global_bin):
            return

        for wrapper_file in os.listdir(global_bin):
            wrapper_path = os.path.join(global_bin, wrapper_file)

            if not os.path.isfile(wrapper_path):
                continue

            try:
                with open(wrapper_path, "r") as f:
                    content = f.read()

                # Check functional code - not comments
                if f"packages/{module_name}/" in content:
                    os.remove(wrapper_path)

            except (OSError, UnicodeDecodeError):
                # Wrapper not readable or not a text file - skip silently
                continue
            except Exception as e:
                # Unexpected error - log and continue
                self.logger.debug(f"Error processing wrapper {wrapper_file}: {e}")
                continue
