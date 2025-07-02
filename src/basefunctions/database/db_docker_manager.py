"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Docker-based database instance management with Registry-driven template rendering

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, List, Optional, Any, Tuple
import os
import json
import subprocess
import datetime
import jinja2
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
DB_BASE = os.path.expanduser("~/.databases")
CONFIG_DIR = os.path.join(DB_BASE, "config")
INSTANCES_DIR = os.path.join(DB_BASE, "instances")
TEMPLATE_BASE = os.path.join(DB_BASE, "templates")

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbDockerManager:
    """
    Manages Docker-based database instances with Registry-driven template rendering and lifecycle management.
    Supports all database types registered in the Registry with full Docker integration.
    """

    def __init__(self) -> None:
        """
        Initialize DbDockerManager with Registry access.

        raises
        ------
        basefunctions.DbConfigurationError
            if initialization fails
        """
        self.logger = basefunctions.get_logger(__name__)
        self.registry = basefunctions.get_registry()

    # =================================================================
    # DOCKER LIFECYCLE
    # =================================================================

    def create_instance(self, db_type: str, instance_name: str, password: str) -> "basefunctions.DbInstance":
        """
        Create a complete Docker-based database instance using Registry validation.

        parameters
        ----------
        db_type : str
            database type (validated against Registry)
        instance_name : str
            name for the new instance
        password : str
            database password

        returns
        -------
        basefunctions.DbInstance
            created database instance

        raises
        ------
        basefunctions.DbValidationError
            if parameters are invalid
        basefunctions.DbInstanceError
            if instance creation fails
        """
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not password:
            raise basefunctions.DbValidationError("password cannot be empty")

        # Validate db_type using Registry
        try:
            self.registry.validate_db_type(db_type)
        except basefunctions.DbValidationError as e:
            raise basefunctions.DbValidationError(f"unsupported database type: {str(e)}") from e

        # Check if database type supports Docker
        if not self.registry.supports_feature(db_type, "docker_support"):
            raise basefunctions.DbValidationError(f"database type '{db_type}' does not support Docker deployment")

        # Initialize variables to avoid UnboundLocalError in cleanup
        db_port = admin_port = None

        try:
            # Check if instance already exists
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if basefunctions.check_if_dir_exists(instance_dir):
                raise basefunctions.DbInstanceError(f"instance '{instance_name}' already exists")

            # Allocate ports using Registry
            db_port, admin_port = self._allocate_ports(db_type)

            # Create instance directory structure
            self._create_instance_structure(instance_name)

            # Create data directories
            data_dir = os.path.join(instance_dir, "data")
            basefunctions.create_directory(data_dir)

            # Render and save templates
            templates = self._render_templates(db_type, instance_name, password, db_port, admin_port, data_dir)

            # Save docker-compose.yml
            compose_file = os.path.join(instance_dir, "docker-compose.yml")
            with open(compose_file, "w") as f:
                f.write(templates["docker_compose"])

            # Save bootstrap script if available
            if templates.get("bootstrap"):
                bootstrap_dir = os.path.join(instance_dir, "bootstrap")
                basefunctions.create_directory(bootstrap_dir)

                # Different file extensions for different database types
                bootstrap_file = self._get_bootstrap_filename(db_type, bootstrap_dir)
                with open(bootstrap_file, "w") as f:
                    f.write(templates["bootstrap"])

            # Save additional config files based on database type
            self._save_additional_configs(db_type, instance_dir, templates)

            # Create instance configuration using Registry
            config = self._create_instance_config(db_type, instance_name, password, db_port, admin_port, data_dir)

            # Save instance configuration
            config_file = os.path.join(instance_dir, "config.json")
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            # Start the Docker containers
            self._docker_compose_up(instance_dir)

            # Generate Simon monitoring scripts
            self._generate_simon_scripts(instance_name, db_port, instance_dir, db_type)

            self.logger.info(
                f"created Docker instance '{instance_name}' of type '{db_type}' on ports {db_port}/{admin_port}"
            )

            # Return DbInstance object
            return basefunctions.DbInstance(instance_name, config)

        except Exception as e:
            self.logger.critical(f"failed to create Docker instance '{instance_name}': {str(e)}")
            # Cleanup on failure
            self._cleanup_failed_instance(instance_name, db_port, admin_port)
            raise basefunctions.DbInstanceError(f"failed to create Docker instance '{instance_name}': {str(e)}") from e

    def delete_instance(self, instance_name: str, force: bool = False) -> bool:
        """
        Delete a Docker instance completely with robust error handling.

        parameters
        ----------
        instance_name : str
            name of the instance to delete
        force : bool
            if True, attempt deletion even if some steps fail

        returns
        -------
        bool
            True if instance was completely deleted, False if major issues occurred
        """
        if not instance_name:
            return False

        instance_dir = os.path.join(INSTANCES_DIR, instance_name)

        # Track success/failure of each step
        steps_status = {
            "instance_exists": False,
            "config_loaded": False,
            "containers_stopped": False,
            "volumes_removed": False,
            "ports_freed": False,
            "directory_removed": False,
        }

        errors = []
        db_port = admin_port = None

        try:
            # Step 1: Check if instance exists
            if not basefunctions.check_if_dir_exists(instance_dir):
                self.logger.warning(f"instance '{instance_name}' directory not found")
                if not force:
                    return False
                # In force mode, this is not a failure
                steps_status["instance_exists"] = True
                steps_status["directory_removed"] = True
            else:
                steps_status["instance_exists"] = True
                self.logger.info(f"found instance directory: {instance_dir}")

            # Step 2: Load config to get ports (best effort)
            config_file = os.path.join(instance_dir, "config.json")
            if basefunctions.check_if_file_exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        config = json.load(f)
                        ports = config.get("ports", {})
                        db_port = ports.get("db")
                        admin_port = ports.get("admin")
                        steps_status["config_loaded"] = True
                        self.logger.info(f"loaded config - db_port: {db_port}, admin_port: {admin_port}")
                except Exception as e:
                    errors.append(f"failed to load config: {str(e)}")
                    self.logger.warning(f"config load failed: {str(e)}")
                    if not force:
                        # In non-force mode, config loading failure is acceptable
                        pass
            else:
                self.logger.warning("config.json not found")
                if not force:
                    errors.append("config.json not found")

            # Step 3: Stop and remove containers (most critical)
            try:
                if steps_status["instance_exists"]:
                    self._docker_compose_down(instance_dir, remove_volumes=True)
                    steps_status["containers_stopped"] = True
                    steps_status["volumes_removed"] = True
                    self.logger.info("containers and volumes removed successfully")
                else:
                    # Try to stop containers by name even if directory missing
                    self._force_remove_containers_by_name(instance_name)
                    steps_status["containers_stopped"] = True
                    steps_status["volumes_removed"] = True
            except Exception as e:
                error_msg = f"failed to stop containers: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

                if force:
                    # In force mode, try alternative cleanup
                    try:
                        self._force_remove_containers_by_name(instance_name)
                        steps_status["containers_stopped"] = True
                        self.logger.info("force container removal succeeded")
                    except Exception as force_e:
                        errors.append(f"force container removal failed: {str(force_e)}")
                        self.logger.error(f"force container removal failed: {str(force_e)}")

            # Step 4: Free allocated ports (non-critical)
            if db_port and admin_port:
                try:
                    self._free_ports(db_port, admin_port)
                    steps_status["ports_freed"] = True
                    self.logger.info(f"freed ports {db_port}, {admin_port}")
                except Exception as e:
                    error_msg = f"failed to free ports: {str(e)}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
                    # Port freeing failure is not critical
                    if force:
                        steps_status["ports_freed"] = True
            else:
                # No ports to free
                steps_status["ports_freed"] = True

            # Step 5: Remove instance directory (critical)
            if steps_status["instance_exists"]:
                try:
                    basefunctions.remove_directory(instance_dir)
                    steps_status["directory_removed"] = True
                    self.logger.info(f"removed instance directory: {instance_dir}")
                except Exception as e:
                    error_msg = f"failed to remove directory: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

                    if force:
                        # In force mode, try system rm -rf
                        try:
                            import subprocess

                            subprocess.run(["rm", "-rf", instance_dir], check=True)
                            steps_status["directory_removed"] = True
                            self.logger.info("force directory removal succeeded")
                        except Exception as force_e:
                            errors.append(f"force directory removal failed: {str(force_e)}")
                            self.logger.error(f"force directory removal failed: {str(force_e)}")

            # Evaluate overall success
            critical_steps = ["containers_stopped", "directory_removed"]
            critical_success = all(steps_status[step] for step in critical_steps)

            if critical_success:
                self.logger.info(f"successfully deleted Docker instance '{instance_name}'")

                # Log any non-critical issues
                if errors:
                    self.logger.warning(f"deletion completed with {len(errors)} minor issues: {'; '.join(errors)}")

                return True
            else:
                # Critical failure
                failed_steps = [step for step in critical_steps if not steps_status[step]]
                self.logger.error(f"critical deletion failure - failed steps: {failed_steps}")

                if errors:
                    self.logger.error(f"deletion errors: {'; '.join(errors)}")

                return False

        except Exception as e:
            self.logger.error(f"unexpected error during deletion of '{instance_name}': {str(e)}")
            errors.append(f"unexpected error: {str(e)}")
            return False

    def _force_remove_containers_by_name(self, instance_name: str) -> None:
        """
        Force remove containers by name pattern when compose down fails.

        parameters
        ----------
        instance_name : str
            instance name to build container name pattern
        """
        import subprocess

        try:
            # Find containers with instance name pattern
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={instance_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                container_names = result.stdout.strip().split("\n")
                self.logger.info(f"found containers to force remove: {container_names}")

                for container_name in container_names:
                    if container_name.strip():
                        # Force stop and remove each container
                        subprocess.run(["docker", "stop", container_name.strip()], capture_output=True, check=False)
                        subprocess.run(
                            ["docker", "rm", "-f", container_name.strip()], capture_output=True, check=False
                        )
                        self.logger.info(f"force removed container: {container_name.strip()}")

            # Also try to remove any volumes with instance name pattern
            volume_result = subprocess.run(
                ["docker", "volume", "ls", "--filter", f"name={instance_name}", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=False,
            )

            if volume_result.returncode == 0 and volume_result.stdout.strip():
                volume_names = volume_result.stdout.strip().split("\n")
                for volume_name in volume_names:
                    if volume_name.strip():
                        subprocess.run(
                            ["docker", "volume", "rm", "-f", volume_name.strip()], capture_output=True, check=False
                        )
                        self.logger.info(f"force removed volume: {volume_name.strip()}")

        except Exception as e:
            self.logger.warning(f"force container removal encountered error: {str(e)}")
            raise

    def start_instance(self, instance_name: str) -> bool:
        """
        Start a Docker instance.

        parameters
        ----------
        instance_name : str
            name of the instance to start

        returns
        -------
        bool
            True if instance was started, False otherwise
        """
        if not instance_name:
            return False

        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if not basefunctions.check_if_dir_exists(instance_dir):
                self.logger.warning(f"instance '{instance_name}' not found")
                return False

            self._docker_compose_up(instance_dir)
            self.logger.info(f"started Docker instance '{instance_name}'")
            return True

        except Exception as e:
            self.logger.warning(f"error starting Docker instance '{instance_name}': {str(e)}")
            return False

    def stop_instance(self, instance_name: str) -> bool:
        """
        Stop a Docker instance.

        parameters
        ----------
        instance_name : str
            name of the instance to stop

        returns
        -------
        bool
            True if instance was stopped, False otherwise
        """
        if not instance_name:
            return False

        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if not basefunctions.check_if_dir_exists(instance_dir):
                self.logger.warning(f"instance '{instance_name}' not found")
                return False

            self._docker_compose_down(instance_dir, remove_volumes=False)
            self.logger.info(f"stopped Docker instance '{instance_name}'")
            return True

        except Exception as e:
            self.logger.warning(f"error stopping Docker instance '{instance_name}': {str(e)}")
            return False

    # =================================================================
    # SIMPLE APP INTERFACE (KISS)
    # =================================================================

    def get_instance_status(self, instance_name: str) -> Dict[str, str]:
        """
        Get simple status of a single instance.

        parameters
        ----------
        instance_name : str
            name of the instance

        returns
        -------
        Dict[str, str]
            {"status": "running/stopped/error", "error": "error message if any"}
        """
        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if not basefunctions.check_if_dir_exists(instance_dir):
                return {"status": "error", "error": f"instance '{instance_name}' not found"}

            # Check if docker-compose.yml exists
            compose_file = os.path.join(instance_dir, "docker-compose.yml")
            if not basefunctions.check_if_file_exists(compose_file):
                return {"status": "error", "error": "docker-compose.yml not found"}

            # Check container status
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"], cwd=instance_dir, capture_output=True, text=True, check=False
            )

            if result.returncode != 0:
                return {"status": "stopped", "error": ""}

            container_ids = result.stdout.strip().split("\n")
            if not container_ids or container_ids == [""]:
                return {"status": "stopped", "error": ""}

            # Check if containers are actually running
            running_containers = 0
            for container_id in container_ids:
                if container_id:
                    inspect_result = subprocess.run(
                        ["docker", "inspect", container_id, "--format", "{{.State.Status}}"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if inspect_result.returncode == 0 and inspect_result.stdout.strip() == "running":
                        running_containers += 1

            if running_containers > 0:
                return {"status": "running", "error": ""}
            else:
                return {"status": "stopped", "error": ""}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_all_instances_status(self) -> Dict[str, Dict]:
        """
        Get status of all instances.

        returns
        -------
        Dict[str, Dict]
            {"instance1": {"status": "running", "error": ""}, "instance2": {...}}
        """
        all_status = {}

        try:
            if not basefunctions.check_if_dir_exists(INSTANCES_DIR):
                return all_status

            # Get all instance directories
            for item in os.listdir(INSTANCES_DIR):
                item_path = os.path.join(INSTANCES_DIR, item)
                if basefunctions.check_if_dir_exists(item_path):
                    all_status[item] = self.get_instance_status(item)

        except Exception as e:
            self.logger.warning(f"error getting all instances status: {str(e)}")

        return all_status

    def get_instance_info(self, instance_name: str) -> Dict[str, Any]:
        """
        Get instance information for connection.

        parameters
        ----------
        instance_name : str
            name of the instance

        returns
        -------
        Dict[str, Any]
            {"ports": {...}, "type": "postgres", "connection": {...}, "error": "..."}
        """
        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            config_file = os.path.join(instance_dir, "config.json")

            if not basefunctions.check_if_file_exists(config_file):
                return {"error": f"config file not found for instance '{instance_name}'"}

            with open(config_file, "r") as f:
                config = json.load(f)

            return {
                "type": config.get("type", "unknown"),
                "ports": config.get("ports", {}),
                "connection": config.get("connection", {}),
                "created_at": config.get("created_at", ""),
                "data_dir": config.get("data_dir", ""),
                "error": "",
            }

        except Exception as e:
            return {"error": str(e)}

    def install_default_templates(self) -> bool:
        """
        Install default templates for all Registry-supported database types.

        returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Delegate ALL template installation to db_templates
            import basefunctions.database.db_templates as templates

            templates.install_all_templates()
            return True

        except Exception as e:
            self.logger.critical(f"failed to install default templates: {str(e)}")
            return False

    # =================================================================
    # PRIVATE HELPER METHODS
    # =================================================================

    def _allocate_ports(self, db_type: str) -> Tuple[int, int]:
        """
        Allocate free ports consistently for all database types.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        Tuple[int, int]
            (db_port, admin_port)
        """
        try:
            basefunctions.create_directory(CONFIG_DIR)
            ports_file = os.path.join(CONFIG_DIR, "ports.json")

            if basefunctions.check_if_file_exists(ports_file):
                with open(ports_file, "r") as f:
                    ports_data = json.load(f)
            else:
                ports_data = {"used_ports": [], "next_port": 2000}

            used_ports = set(ports_data.get("used_ports", []))
            next_port = max(ports_data.get("next_port", 2000), 2000)

            # Find first two free ports
            while next_port in used_ports or next_port + 1 in used_ports:
                next_port += 2

            db_port, admin_port = next_port, next_port + 1

            # Mark as used
            used_ports.update([db_port, admin_port])

            # Save
            ports_data["used_ports"] = list(used_ports)
            ports_data["next_port"] = admin_port + 1

            with open(ports_file, "w") as f:
                json.dump(ports_data, f, indent=2)

            return db_port, admin_port

        except Exception as e:
            self.logger.warning(f"error allocating ports: {str(e)}")
            return 2000, 2001  # ultimate fallback

    def _cleanup_failed_instance(self, instance_name: str, db_port: Optional[int], admin_port: Optional[int]) -> None:
        """
        Cleanup after failed instance creation.

        parameters
        ----------
        instance_name : str
            name of the failed instance
        db_port : Optional[int]
            allocated db port to free
        admin_port : Optional[int]
            allocated admin port to free
        """
        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if basefunctions.check_if_dir_exists(instance_dir):
                basefunctions.remove_directory(instance_dir)

            if db_port and admin_port:
                self._free_ports(db_port, admin_port)

        except Exception as e:
            self.logger.warning(f"error during cleanup: {str(e)}")

    def _free_ports(self, db_port: int, admin_port: int) -> None:
        """
        Free ports - they will be automatically reused in next allocation.

        parameters
        ----------
        db_port : int
            database port to free
        admin_port : int
            admin port to free
        """
        try:
            ports_file = os.path.join(CONFIG_DIR, "ports.json")

            if not basefunctions.check_if_file_exists(ports_file):
                return

            with open(ports_file, "r") as f:
                ports_data = json.load(f)

            used_ports = set(ports_data.get("used_ports", []))
            used_ports.discard(db_port)
            used_ports.discard(admin_port)

            ports_data["used_ports"] = list(used_ports)
            ports_data["next_port"] = min(used_ports) if used_ports else 2000

            with open(ports_file, "w") as f:
                json.dump(ports_data, f, indent=2)

        except Exception as e:
            self.logger.warning(f"error freeing ports: {str(e)}")

    def _create_instance_structure(self, instance_name: str) -> None:
        """
        Create the directory structure for a new database instance.

        parameters
        ----------
        instance_name : str
            name of the instance
        """
        instance_dir = os.path.join(INSTANCES_DIR, instance_name)

        # Create instance directories using basefunctions
        directories = [
            instance_dir,
            os.path.join(instance_dir, "bootstrap"),
            os.path.join(instance_dir, "config"),
            os.path.join(instance_dir, "data"),
            os.path.join(instance_dir, "logs"),
        ]

        for directory in directories:
            basefunctions.create_directory(directory)

    def _render_templates(
        self, db_type: str, instance_name: str, password: str, db_port: int, admin_port: int, data_dir: str
    ) -> Dict[str, str]:
        """
        Render templates using Jinja2 from Registry-validated template paths.

        parameters
        ----------
        db_type : str
            database type (validated against Registry)
        instance_name : str
            instance name
        password : str
            database password
        db_port : int
            database port
        admin_port : int
            admin interface port
        data_dir : str
            data directory path

        returns
        -------
        Dict[str, str]
            rendered templates

        raises
        ------
        basefunctions.DbConfigurationError
            if template rendering fails
        """
        try:
            # Check if database type has templates using Registry
            if not self.registry.has_templates(db_type):
                raise basefunctions.DbConfigurationError(f"no templates available for database type '{db_type}'")

            # Template directory in ~/.databases/templates/docker/{db_type}/
            template_dir = os.path.join(TEMPLATE_BASE, "docker", db_type)

            if not basefunctions.check_if_dir_exists(template_dir):
                raise basefunctions.DbConfigurationError(f"template directory not found: {template_dir}")

            # Setup Jinja2 environment
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir), autoescape=jinja2.select_autoescape(["html", "xml"])
            )

            # Template variables
            template_vars = {
                "instance_name": instance_name,
                "db_password": password,
                "password": password,
                "db_port": db_port,
                "admin_port": admin_port,
                "data_dir": data_dir,
                "db_type": db_type,
                "auto_restart": True,
            }

            templates = {}

            # Render docker-compose.yml
            try:
                compose_template = env.get_template("docker-compose.yml.j2")
                templates["docker_compose"] = compose_template.render(**template_vars)
            except Exception as e:
                raise basefunctions.DbConfigurationError(f"failed to render docker-compose template: {str(e)}")

            # Render bootstrap script if available
            try:
                bootstrap_template_name = self._get_bootstrap_template_name(db_type)
                bootstrap_template = env.get_template(bootstrap_template_name)
                templates["bootstrap"] = bootstrap_template.render(**template_vars)
            except jinja2.TemplateNotFound:
                # Bootstrap template is optional
                pass
            except Exception as e:
                self.logger.warning(f"failed to render bootstrap template: {str(e)}")

            # Render database-specific additional templates
            additional_templates = self._get_additional_template_names(db_type)
            for template_key, template_name in additional_templates.items():
                try:
                    template = env.get_template(template_name)
                    templates[template_key] = template.render(**template_vars)
                except jinja2.TemplateNotFound:
                    # Additional templates are optional
                    pass
                except Exception as e:
                    self.logger.warning(f"failed to render {template_key} template: {str(e)}")

            return templates

        except Exception as e:
            self.logger.critical(f"template rendering failed: {str(e)}")
            raise basefunctions.DbConfigurationError(f"template rendering failed: {str(e)}") from e

    def _get_bootstrap_template_name(self, db_type: str) -> str:
        """
        Get bootstrap template name based on database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        str
            bootstrap template filename
        """
        if db_type == "redis":
            return "bootstrap.sh.j2"
        else:
            return "bootstrap.sql.j2"

    def _get_bootstrap_filename(self, db_type: str, bootstrap_dir: str) -> str:
        """
        Get bootstrap filename based on database type.

        parameters
        ----------
        db_type : str
            database type
        bootstrap_dir : str
            bootstrap directory path

        returns
        -------
        str
            bootstrap file path
        """
        if db_type == "redis":
            return os.path.join(bootstrap_dir, "init.sh")
        elif db_type == "sqlite3":
            return os.path.join(bootstrap_dir, "init.sql")
        else:
            return os.path.join(bootstrap_dir, "init.sql")

    def _get_additional_template_names(self, db_type: str) -> Dict[str, str]:
        """
        Get additional template names for database type.

        parameters
        ----------
        db_type : str
            database type

        returns
        -------
        Dict[str, str]
            mapping of template_key to template_filename
        """
        if db_type == "postgres":
            return {"pgadmin_servers": "pgadmin_servers.json.j2"}
        elif db_type == "redis":
            return {"redis_conf": "redis.conf.j2"}
        else:
            return {}

    def _save_additional_configs(self, db_type: str, instance_dir: str, templates: Dict[str, str]) -> None:
        """
        Save additional configuration files based on database type.

        parameters
        ----------
        db_type : str
            database type
        instance_dir : str
            instance directory path
        templates : Dict[str, str]
            rendered templates
        """
        config_dir = os.path.join(instance_dir, "config")

        if db_type == "postgres" and templates.get("pgadmin_servers"):
            servers_file = os.path.join(config_dir, "pgadmin_servers.json")
            with open(servers_file, "w") as f:
                f.write(templates["pgadmin_servers"])

        elif db_type == "redis" and templates.get("redis_conf"):
            basefunctions.create_directory(config_dir)
            redis_conf_file = os.path.join(config_dir, "redis.conf")
            with open(redis_conf_file, "w") as f:
                f.write(templates["redis_conf"])

    def _create_instance_config(
        self, db_type: str, instance_name: str, password: str, db_port: int, admin_port: int, data_dir: str
    ) -> Dict[str, Any]:
        """
        Create instance configuration using Registry-based database metadata.

        parameters
        ----------
        db_type : str
            database type
        instance_name : str
            instance name
        password : str
            database password
        db_port : int
            database port
        admin_port : int
            admin port
        data_dir : str
            data directory

        returns
        -------
        Dict[str, Any]
            instance configuration
        """
        # Get database configuration from Registry
        db_config = self.registry.get_db_config(db_type)

        # Base configuration
        config = {
            "type": db_type,
            "mode": "docker",
            "ports": {"db": db_port, "admin": admin_port},
            "created_at": datetime.datetime.now().isoformat(),
            "data_dir": data_dir,
        }

        # Database-specific connection configuration using Registry metadata
        if db_type == "redis":
            config["connection"] = {
                "host": "localhost",
                "port": db_port,
                "password": password,
            }
        elif db_type == "postgres":
            config["connection"] = {
                "host": "localhost",
                "user": "postgres",
                "password": password,
                "port": db_port,
            }
        elif db_type == "mysql":
            config["connection"] = {
                "host": "localhost",
                "user": "root",
                "password": password,
                "port": db_port,
            }
        elif db_type == "sqlite3":
            config["connection"] = {
                "database_file": f"{data_dir}/sqlite/{instance_name}.db",
            }

        return config

    def _docker_compose_up(self, instance_dir: str) -> None:
        """
        Start Docker Compose services.

        parameters
        ----------
        instance_dir : str
            instance directory containing docker-compose.yml

        raises
        ------
        basefunctions.DbInstanceError
            if docker compose up fails
        """
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"], cwd=instance_dir, capture_output=True, text=True, check=True
            )
            self.logger.debug(f"docker compose up output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"docker compose up failed: {e.stderr}")
            raise basefunctions.DbInstanceError(f"docker compose up failed: {e.stderr}") from e
        except FileNotFoundError:
            raise basefunctions.DbInstanceError("docker command not found - is Docker installed?")

    def _docker_compose_down(self, instance_dir: str, remove_volumes: bool = False) -> None:
        """
        Stop Docker Compose services.

        parameters
        ----------
        instance_dir : str
            instance directory containing docker-compose.yml
        remove_volumes : bool
            whether to remove volumes

        raises
        ------
        basefunctions.DbInstanceError
            if docker compose down fails
        """
        try:
            cmd = ["docker", "compose", "down"]
            if remove_volumes:
                cmd.extend(["-v", "--remove-orphans"])

            result = subprocess.run(cmd, cwd=instance_dir, capture_output=True, text=True, check=True)
            self.logger.debug(f"docker compose down output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"docker compose down failed: {e.stderr}")
            raise basefunctions.DbInstanceError(f"docker compose down failed: {e.stderr}") from e
        except FileNotFoundError:
            raise basefunctions.DbInstanceError("docker command not found - is Docker installed?")

    def _cleanup_failed_instance(self, instance_name: str, db_port: Optional[int], admin_port: Optional[int]) -> None:
        """
        Cleanup after failed instance creation.

        parameters
        ----------
        instance_name : str
            name of the failed instance
        db_port : Optional[int]
            allocated db port to free
        admin_port : Optional[int]
            allocated admin port to free
        """
        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if basefunctions.check_if_dir_exists(instance_dir):
                basefunctions.remove_directory(instance_dir)

            if db_port and admin_port:
                self._free_ports(db_port, admin_port)

        except Exception as e:
            self.logger.warning(f"error during cleanup: {str(e)}")

    def _generate_simon_scripts(self, instance_name: str, db_port: int, instance_dir: str, db_type: str) -> None:
        """
        Generate Simon monitoring scripts for the database instance.

        parameters
        ----------
        instance_name : str
            name of the database instance
        db_port : int
            database port number
        instance_dir : str
            instance directory path
        db_type : str
            database type for specialized monitoring

        raises
        ------
        basefunctions.DbConfigurationError
            if Simon script generation fails
        """
        try:
            # Create simon directory
            simon_dir = os.path.join(instance_dir, "simon")
            basefunctions.create_directory(simon_dir)

            # Render Simon script template with database type
            script_content = self._render_simon_script_template(instance_name, db_port, instance_dir, db_type)

            # Save Simon script
            script_file = os.path.join(simon_dir, "monitor_script.sh")
            with open(script_file, "w") as f:
                f.write(script_content)

            # Make script executable
            import stat

            current_permissions = os.stat(script_file).st_mode
            os.chmod(script_file, current_permissions | stat.S_IEXEC)

            self.logger.info(f"generated Simon monitoring script for {db_type} instance '{instance_name}'")

        except Exception as e:
            self.logger.warning(f"failed to generate Simon scripts for '{instance_name}': {str(e)}")
            # Don't raise - Simon script generation failure shouldn't break instance creation

    def _render_simon_script_template(self, instance_name: str, db_port: int, instance_dir: str, db_type: str) -> str:
        """
        Render Simon monitoring script template with instance-specific values.

        parameters
        ----------
        instance_name : str
            name of the database instance
        db_port : int
            database port number
        instance_dir : str
            instance directory path
        db_type : str
            database type for specialized health checks

        returns
        -------
        str
            rendered Simon script content

        raises
        ------
        basefunctions.DbConfigurationError
            if template rendering fails
        """
        try:
            import datetime

            # Simon template directory
            simon_template_dir = os.path.join(TEMPLATE_BASE, "simon")

            if not basefunctions.check_if_dir_exists(simon_template_dir):
                raise basefunctions.DbConfigurationError(f"Simon template directory not found: {simon_template_dir}")

            # Setup Jinja2 environment
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(simon_template_dir),
                autoescape=jinja2.select_autoescape(["html", "xml"]),
            )

            # Template variables with database type
            template_vars = {
                "instance_name": instance_name,
                "db_port": db_port,
                "instance_home_dir": instance_dir,
                "timestamp": datetime.datetime.now().isoformat(),
                "db_type": db_type,
            }

            # Render Simon script template
            try:
                script_template = env.get_template("monitor_script.sh.j2")
                return script_template.render(**template_vars)
            except Exception as e:
                raise basefunctions.DbConfigurationError(f"failed to render Simon script template: {str(e)}")

        except Exception as e:
            self.logger.critical(f"Simon script template rendering failed: {str(e)}")
            raise basefunctions.DbConfigurationError(f"Simon script template rendering failed: {str(e)}") from e
