"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Docker-based database instance management with template rendering
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import json
import subprocess
import datetime
from typing import Dict, List, Optional, Any, Tuple
import jinja2
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------
DB_BASE = os.path.expanduser("~/.databases")
CONFIG_DIR = os.path.join(DB_BASE, "config")
INSTANCES_DIR = os.path.join(DB_BASE, "instances")
TEMPLATE_BASE = os.path.join(DB_BASE, "templates")

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class DbDockerManager:
    """
    Manages Docker-based database instances with template rendering and lifecycle management.
    Uses basefunctions.filefunctions for file operations and ~/.databases/templates for templates.
    """

    def __init__(self) -> None:
        """
        Initialize DbDockerManager.

        raises
        ------
        basefunctions.DbConfigurationError
            if initialization fails
        """
        self.logger = basefunctions.get_logger(__name__)

    # =================================================================
    # DOCKER LIFECYCLE
    # =================================================================

    def create_instance(self, db_type: str, instance_name: str, password: str) -> "basefunctions.DbInstance":
        """
        Create a complete Docker-based database instance.

        parameters
        ----------
        db_type : str
            database type (postgres, mysql, sqlite3)
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
        if not db_type:
            raise basefunctions.DbValidationError("db_type cannot be empty")
        if not instance_name:
            raise basefunctions.DbValidationError("instance_name cannot be empty")
        if not password:
            raise basefunctions.DbValidationError("password cannot be empty")

        if db_type not in ["postgres", "mysql", "sqlite3"]:
            raise basefunctions.DbValidationError(f"unsupported database type: {db_type}")

        try:
            # Check if instance already exists
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if basefunctions.check_if_dir_exists(instance_dir):
                raise basefunctions.DbInstanceError(f"instance '{instance_name}' already exists")

            # Allocate ports
            db_port, admin_port = self._allocate_ports()

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
                bootstrap_file = os.path.join(bootstrap_dir, "init.sql")
                with open(bootstrap_file, "w") as f:
                    f.write(templates["bootstrap"])

            # Save additional config files
            if templates.get("pgadmin_servers"):
                config_dir = os.path.join(instance_dir, "config")
                servers_file = os.path.join(config_dir, "pgadmin_servers.json")
                with open(servers_file, "w") as f:
                    f.write(templates["pgadmin_servers"])

            # Create instance configuration
            config = {
                "type": "postgresql" if db_type == "postgres" else db_type,
                "mode": "docker",
                "connection": {
                    "host": "localhost",
                    "user": "postgres" if db_type == "postgres" else "root",
                    "password": password,
                },
                "ports": {"db": db_port, "admin": admin_port},
                "created_at": datetime.datetime.now().isoformat(),
                "data_dir": data_dir,
            }

            # Save instance configuration
            config_file = os.path.join(instance_dir, "config.json")
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            # Start the Docker containers
            self._docker_compose_up(instance_dir)

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

    def delete_instance(self, instance_name: str) -> bool:
        """
        Delete a Docker instance completely.

        parameters
        ----------
        instance_name : str
            name of the instance to delete

        returns
        -------
        bool
            True if instance was deleted, False if it didn't exist
        """
        if not instance_name:
            return False

        try:
            instance_dir = os.path.join(INSTANCES_DIR, instance_name)
            if not basefunctions.check_if_dir_exists(instance_dir):
                self.logger.warning(f"instance '{instance_name}' not found for deletion")
                return False

            # Load config to get ports for cleanup
            config_file = os.path.join(instance_dir, "config.json")
            db_port = admin_port = None
            if basefunctions.check_if_file_exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        config = json.load(f)
                        ports = config.get("ports", {})
                        db_port = ports.get("db")
                        admin_port = ports.get("admin")
                except Exception as e:
                    self.logger.warning(f"failed to load config for port cleanup: {str(e)}")

            # Stop and remove containers
            self._docker_compose_down(instance_dir, remove_volumes=True)

            # Free allocated ports
            if db_port and admin_port:
                self._free_ports(db_port, admin_port)

            # Remove instance directory
            basefunctions.remove_directory(instance_dir)

            self.logger.info(f"deleted Docker instance '{instance_name}'")
            return True

        except Exception as e:
            self.logger.warning(f"error deleting Docker instance '{instance_name}': {str(e)}")
            return False

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
        Install default templates if missing.

        returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Ensure template base directory exists
            basefunctions.create_directory(TEMPLATE_BASE)

            # Install templates for each database type
            for db_type in ["postgres", "mysql", "sqlite3"]:
                template_dir = os.path.join(TEMPLATE_BASE, "docker", db_type)
                basefunctions.create_directory(template_dir)

                # Check if docker-compose template exists
                compose_template = os.path.join(template_dir, "docker-compose.yml.j2")
                if not basefunctions.check_if_file_exists(compose_template):
                    # Install basic template
                    self._install_basic_template(db_type, template_dir)

            return True

        except Exception as e:
            self.logger.critical(f"failed to install default templates: {str(e)}")
            return False

    def _install_basic_template(self, db_type: str, template_dir: str) -> None:
        """
        Install basic template for database type.

        parameters
        ----------
        db_type : str
            database type
        template_dir : str
            template directory path
        """
        if db_type == "postgres":
            compose_content = """version: '3.8'
services:
  postgres:
    image: postgres:14
    container_name: {{ instance_name }}_postgres
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: "{{ password }}"
      POSTGRES_USER: postgres
      POSTGRES_DB: {{ instance_name }}
    volumes:
      - {{ data_dir }}/postgres:/var/lib/postgresql/data
    ports:
      - "{{ db_port }}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  pgadmin:
    image: dpage/pgadmin4
    container_name: {{ instance_name }}_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@{{ instance_name }}.local
      PGADMIN_DEFAULT_PASSWORD: "{{ password }}"
    volumes:
      - {{ data_dir }}/pgadmin:/var/lib/pgadmin
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      - postgres
"""
        elif db_type == "mysql":
            compose_content = """version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: {{ instance_name }}_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: "{{ password }}"
      MYSQL_DATABASE: {{ instance_name }}
    volumes:
      - {{ data_dir }}/mysql:/var/lib/mysql
    ports:
      - "{{ db_port }}:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: {{ instance_name }}_phpmyadmin
    restart: unless-stopped
    environment:
      PMA_HOST: mysql
      PMA_USER: root
      PMA_PASSWORD: "{{ password }}"
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      - mysql
"""
        else:  # sqlite3
            compose_content = """version: '3.8'
services:
  sqlite:
    image: nouchka/sqlite3:latest
    container_name: {{ instance_name }}_sqlite
    restart: unless-stopped
    volumes:
      - {{ data_dir }}/sqlite:/db
    working_dir: /db
    command: tail -f /dev/null

  sqlite-web:
    image: coleifer/sqlite-web
    container_name: {{ instance_name }}_sqlite_web
    restart: unless-stopped
    volumes:
      - {{ data_dir }}/sqlite:/data
    ports:
      - "{{ db_port }}:8080"
    command: ["sqlite_web", "/data/{{ instance_name }}.db", "--host", "0.0.0.0"]
    depends_on:
      - sqlite
"""

        # Write docker-compose template
        compose_file = os.path.join(template_dir, "docker-compose.yml.j2")
        with open(compose_file, "w") as f:
            f.write(compose_content)

    # =================================================================
    # PRIVATE HELPER METHODS
    # =================================================================

    def _allocate_ports(self) -> Tuple[int, int]:
        """
        Allocate free ports for database and admin interface.

        returns
        -------
        Tuple[int, int]
            (db_port, admin_port)
        """
        try:
            # Ensure config directory exists
            basefunctions.create_directory(CONFIG_DIR)

            ports_file = os.path.join(CONFIG_DIR, "ports.json")

            if basefunctions.check_if_file_exists(ports_file):
                with open(ports_file, "r") as f:
                    ports_data = json.load(f)
            else:
                ports_data = {"used_ports": {"db": [], "admin": []}, "last_assigned": 2000}

            used_db_ports = set(ports_data.get("used_ports", {}).get("db", []))
            used_admin_ports = set(ports_data.get("used_ports", {}).get("admin", []))
            last_assigned = ports_data.get("last_assigned", 2000)

            # Find next available ports
            db_port = last_assigned + 1
            while db_port in used_db_ports:
                db_port += 1

            admin_port = db_port + 1
            while admin_port in used_admin_ports or admin_port == db_port:
                admin_port += 1

            # Update ports file
            if "used_ports" not in ports_data:
                ports_data["used_ports"] = {"db": [], "admin": []}

            ports_data["used_ports"]["db"].append(db_port)
            ports_data["used_ports"]["admin"].append(admin_port)
            ports_data["last_assigned"] = max(db_port, admin_port)

            with open(ports_file, "w") as f:
                json.dump(ports_data, f, indent=2)

            return db_port, admin_port

        except Exception as e:
            self.logger.warning(f"error allocating ports: {str(e)}")
            # Fallback to basic allocation
            return 2000, 2001

    def _free_ports(self, db_port: int, admin_port: int) -> None:
        """
        Free allocated ports.

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

            # Remove from used ports
            if "used_ports" in ports_data:
                if "db" in ports_data["used_ports"] and db_port in ports_data["used_ports"]["db"]:
                    ports_data["used_ports"]["db"].remove(db_port)
                if "admin" in ports_data["used_ports"] and admin_port in ports_data["used_ports"]["admin"]:
                    ports_data["used_ports"]["admin"].remove(admin_port)

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
        Render templates using Jinja2 from ~/.databases/templates/.

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
                "password": password,
                "db_port": db_port,
                "admin_port": admin_port,
                "data_dir": data_dir,
                "db_type": db_type,
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
                bootstrap_template = env.get_template("bootstrap.sql.j2")
                templates["bootstrap"] = bootstrap_template.render(**template_vars)
            except jinja2.TemplateNotFound:
                # Bootstrap template is optional
                pass
            except Exception as e:
                self.logger.warning(f"failed to render bootstrap template: {str(e)}")

            # Render pgAdmin servers config if available
            try:
                pgadmin_template = env.get_template("pgadmin_servers.json.j2")
                templates["pgadmin_servers"] = pgadmin_template.render(**template_vars)
            except jinja2.TemplateNotFound:
                # pgAdmin template is optional
                pass
            except Exception as e:
                self.logger.warning(f"failed to render pgadmin template: {str(e)}")

            return templates

        except Exception as e:
            self.logger.critical(f"template rendering failed: {str(e)}")
            raise basefunctions.DbConfigurationError(f"template rendering failed: {str(e)}") from e

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
