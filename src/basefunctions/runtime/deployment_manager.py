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
from typing import List, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
HASH_STORAGE_SUBPATH = "deployment/hashes"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------


class DeploymentError(Exception):
    """Exception raised during deployment operations."""

    pass


# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


@basefunctions.singleton
class DeploymentManager:
    """
    Singleton for handling module deployment with change detection and context validation.
    """

    def __init__(self):
        self.logger = basefunctions.get_logger(__name__)

    def deploy_module(self, module_name: str) -> None:
        """
        Deploy specific module with context validation and change detection.

        Parameters
        ----------
        module_name : str
            Name of the module to deploy

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
        if not self._detect_changes(module_name, source_path):
            print(f"No changes detected for {module_name}")
            return

        self.logger.critical(f"Deploying {module_name} from {source_path} to {target_path}")

        # Clean target if exists
        if os.path.exists(target_path):
            shutil.rmtree(target_path)

        # Deployment components
        self._deploy_venv(source_path, target_path)
        self._deploy_templates(source_path, target_path)
        self._deploy_configs(target_path)
        self._deploy_bin_tools(source_path, target_path, module_name)

        # Update hash for next detection
        self._update_hash(module_name, source_path)

        self.logger.critical(f"Successfully deployed {module_name}")
        print(f"Successfully deployed {module_name}")

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
            shutil.rmtree(target_path)
            self.logger.critical(f"Cleaned deployment for {module_name}")
            print(f"Cleaned deployment for {module_name}")

        # Remove global wrappers
        global_bin = os.path.join(basefunctions.runtime.get_bootstrap_deployment_directory(), "bin")
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
        Calculate combined hash from source code and pip environment.

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

        combined = f"{src_hash}:{pip_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()

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

        for root, dirs, files in os.walk(src_dir):
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
                [pip_executable, "list", "--format=freeze"], capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                return "pip-error"

            packages = sorted(result.stdout.strip().split("\n"))
            return hashlib.sha256("".join(packages).encode()).hexdigest()

        except Exception:
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
            with open(hash_file, "r") as f:
                return f.read().strip()
        except Exception:
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
            with open(hash_file, "w") as f:
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

    def _deploy_venv(self, source_path: str, target_path: str) -> None:
        """
        Deploy virtual environment by creating fresh venv and installing current module.

        Parameters
        ----------
        source_path : str
            Source module path
        target_path : str
            Target deployment path
        """
        source_venv = os.path.join(source_path, ".venv")
        target_venv = os.path.join(target_path, "venv")

        if not os.path.exists(source_venv):
            return

        try:
            # Create fresh virtual environment
            os.makedirs(os.path.dirname(target_venv), exist_ok=True)
            subprocess.run([sys.executable, "-m", "venv", target_venv], check=True, timeout=120)

            # Upgrade pip to latest version
            pip_executable = os.path.join(target_venv, "bin", "pip")
            subprocess.run([pip_executable, "install", "--upgrade", "pip"], check=True, timeout=120)

            # Install current module
            subprocess.run([pip_executable, "install", source_path], check=True, timeout=300)

            self.logger.critical(f"Created fresh virtual environment at {target_venv}")
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

            # Create global wrappers
            global_bin = os.path.join(basefunctions.runtime.get_bootstrap_deployment_directory(), "bin")
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
        wrapper_path = os.path.join(global_bin, tool_name)
        venv_path = os.path.join(target_path, "venv")
        tool_path = os.path.join(target_path, "bin", tool_name)

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

            except Exception:
                # Wrapper not readable - skip
                continue
