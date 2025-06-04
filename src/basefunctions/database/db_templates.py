"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Template installer for Docker database instances
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def install_postgres_templates():
    """Install PostgreSQL Docker templates to ~/.databases/templates/"""

    template_base = os.path.expanduser("~/.databases/templates/docker/postgres")
    basefunctions.create_directory(template_base)

    # Docker Compose Template - KORRIGIERT mit funktionierendem Template
    docker_compose_content = """# Docker Compose configuration for PostgreSQL database instance: {{ instance_name }}
version: '3.8'

services:
  postgres:
    image: postgres:14
    container_name: {{ instance_name }}_postgres
    user: "999:999"
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      POSTGRES_PASSWORD: "{{ db_password }}"
      POSTGRES_USER: postgres
      POSTGRES_DB: postgres
    volumes:
      - {{ data_dir }}/postgres:/var/lib/postgresql/data
      - ./bootstrap:/docker-entrypoint-initdb.d
    ports:
      - "{{ db_port }}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 30s

  pgadmin:
    image: dpage/pgadmin4
    container_name: {{ instance_name }}_pgadmin
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: "{{ db_password }}"
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
      PGADMIN_CONFIG_WTF_CSRF_ENABLED: 'False'
    volumes:
      - {{ data_dir }}/pgadmin:/var/lib/pgadmin
      - ./config/pgadmin_servers.json:/pgadmin4/servers.json
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/misc/ping"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 60s

networks:
  default:
    name: {{ instance_name }}_network"""

    # Bootstrap SQL Template
    bootstrap_content = """-- =============================================================================
-- Bootstrap script for PostgreSQL instance: {{ instance_name }}
-- Creates additional databases and sets up basic configuration
-- =============================================================================

-- Ensure we're connected to the main database
\\c postgres;

-- Create the instance database
CREATE DATABASE {{ instance_name }};

-- Connect to instance database
\\c {{ instance_name }};

-- Create extensions that are commonly used
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Grant all privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE {{ instance_name }} TO postgres;

-- Set up basic configuration
ALTER DATABASE {{ instance_name }} SET timezone TO 'UTC';
ALTER DATABASE {{ instance_name }} SET log_statement TO 'all';

-- Create a demo table for testing
CREATE TABLE IF NOT EXISTS demo_connection_test (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_data TEXT DEFAULT 'Instance {{ instance_name }} is ready'
);

-- Insert test data
INSERT INTO demo_connection_test (test_data) VALUES ('Bootstrap completed successfully');

-- Log completion
DO $
BEGIN
    RAISE NOTICE 'Bootstrap completed for instance: {{ instance_name }}';
END
$;"""

    # pgAdmin Servers Template - KORRIGIERT - NUR NEURALDEVELOPMENT GROUP
    pgadmin_content = """{
  "Servers": {
    "1": {
      "Name": "{{ instance_name }}",
      "Group": "Servers",
      "Host": "{{ instance_name }}_postgres",
      "Port": 5432,
      "MaintenanceDB": "{{ instance_name }}",
      "Username": "postgres",
      "Password": "{{ db_password }}",
      "SSLMode": "prefer",
      "Comment": "Auto-configured PostgreSQL server for instance {{ instance_name }}"
    }
  }
}"""

    # Write template files
    templates = [
        ("docker-compose.yml.j2", docker_compose_content),
        ("bootstrap.sql.j2", bootstrap_content),
        ("pgadmin_servers.json.j2", pgadmin_content),
    ]

    for filename, content in templates:
        file_path = os.path.join(template_base, filename)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Created: {file_path}")

    print(f"PostgreSQL templates installed to: {template_base}")


def install_mysql_templates():
    """Install MySQL Docker templates to ~/.databases/templates/"""

    template_base = os.path.expanduser("~/.databases/templates/docker/mysql")
    basefunctions.create_directory(template_base)

    # Docker Compose Template for MySQL - KORRIGIERT
    docker_compose_content = """# Docker Compose configuration for MySQL database instance: {{ instance_name }}
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: {{ instance_name }}_mysql
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      MYSQL_ROOT_PASSWORD: "{{ db_password }}"
      MYSQL_DATABASE: {{ instance_name }}
      MYSQL_USER: mysql_user
      MYSQL_PASSWORD: "{{ db_password }}"
    volumes:
      - {{ data_dir }}/mysql:/var/lib/mysql
      - ./bootstrap:/docker-entrypoint-initdb.d
    ports:
      - "{{ db_port }}:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p{{ db_password }}"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 30s

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: {{ instance_name }}_phpmyadmin
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      PMA_HOST: mysql
      PMA_PORT: 3306
      PMA_USER: root
      PMA_PASSWORD: "{{ db_password }}"
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      mysql:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 60s

networks:
  default:
    name: {{ instance_name }}_network"""

    # Bootstrap SQL Template for MySQL
    bootstrap_content = """-- =============================================================================
-- Bootstrap script for MySQL instance: {{ instance_name }}
-- Creates additional databases and sets up basic configuration
-- =============================================================================

USE {{ instance_name }};

-- Create a demo table for testing
CREATE TABLE IF NOT EXISTS demo_connection_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_data TEXT DEFAULT 'Instance {{ instance_name }} is ready'
);

-- Insert test data
INSERT INTO demo_connection_test (test_data) VALUES ('Bootstrap completed successfully');"""

    # Write template files
    templates = [("docker-compose.yml.j2", docker_compose_content), ("bootstrap.sql.j2", bootstrap_content)]

    for filename, content in templates:
        file_path = os.path.join(template_base, filename)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Created: {file_path}")

    print(f"MySQL templates installed to: {template_base}")


def install_sqlite_templates():
    """Install SQLite Docker templates to ~/.databases/templates/"""

    template_base = os.path.expanduser("~/.databases/templates/docker/sqlite3")
    basefunctions.create_directory(template_base)

    # Docker Compose Template for SQLite - KORRIGIERT
    docker_compose_content = """# Docker Compose configuration for SQLite database instance: {{ instance_name }}
version: '3.8'

services:
  sqlite:
    image: nouchka/sqlite3:latest
    container_name: {{ instance_name }}_sqlite
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    volumes:
      - {{ data_dir }}/sqlite:/db
      - ./bootstrap:/docker-entrypoint-initdb.d
    working_dir: /db
    command: tail -f /dev/null
    healthcheck:
      test: ["CMD", "ls", "/db/{{ instance_name }}.db"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 10s

  sqlite-browser:
    image: linuxserver/sqlitebrowser:latest
    container_name: {{ instance_name }}_sqlite_browser
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Munich
    volumes:
      - {{ data_dir }}/sqlite:/db
      - {{ data_dir }}/config:/config
    ports:
      - "{{ admin_port }}:3000"
    depends_on:
      sqlite:
        condition: service_healthy

  sqlite-web:
    image: coleifer/sqlite-web
    container_name: {{ instance_name }}_sqlite_web
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    volumes:
      - {{ data_dir }}/sqlite:/data
    ports:
      - "{{ db_port }}:8080"
    command: ["sqlite_web", "/data/{{ instance_name }}.db", "--host", "0.0.0.0", "--port", "8080"]
    depends_on:
      sqlite:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 30s

networks:
  default:
    name: {{ instance_name }}_network"""

    # Bootstrap SQL Template for SQLite
    bootstrap_content = """-- =============================================================================
-- Bootstrap script for SQLite instance: {{ instance_name }}
-- Creates database file and sets up basic configuration
-- =============================================================================

-- Create a demo table for testing
CREATE TABLE IF NOT EXISTS demo_connection_test (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    test_data TEXT DEFAULT 'Instance {{ instance_name }} is ready'
);

-- Insert test data
INSERT INTO demo_connection_test (test_data) VALUES ('Bootstrap completed successfully');

-- Create some indexes for performance
CREATE INDEX IF NOT EXISTS idx_demo_created_at ON demo_connection_test(created_at);

-- Enable foreign keys (good practice)
PRAGMA foreign_keys = ON;

-- Set journal mode to WAL for better concurrency
PRAGMA journal_mode = WAL;"""

    # Init script to create database file
    init_content = '''#!/bin/bash
# =============================================================================
# Initialization script for SQLite instance: {{ instance_name }}
# Creates database file and runs bootstrap SQL
# =============================================================================

DB_FILE="/db/{{ instance_name }}.db"
BOOTSTRAP_SQL="/docker-entrypoint-initdb.d/bootstrap.sql"

echo "Initializing SQLite database: $DB_FILE"

# Create database file if it doesn't exist
if [ ! -f "$DB_FILE" ]; then
    echo "Creating new SQLite database file..."
    sqlite3 "$DB_FILE" "SELECT 1;"
    echo "Database file created: $DB_FILE"
fi

# Run bootstrap SQL if it exists
if [ -f "$BOOTSTRAP_SQL" ]; then
    echo "Running bootstrap SQL script..."
    sqlite3 "$DB_FILE" < "$BOOTSTRAP_SQL"
    echo "Bootstrap SQL completed"
else
    echo "No bootstrap SQL found, skipping..."
fi

echo "SQLite initialization completed for instance: {{ instance_name }}"'''

    # Write template files
    templates = [
        ("docker-compose.yml.j2", docker_compose_content),
        ("bootstrap.sql.j2", bootstrap_content),
        ("init.sh.j2", init_content),
    ]

    for filename, content in templates:
        file_path = os.path.join(template_base, filename)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Created: {file_path}")

    print(f"SQLite templates installed to: {template_base}")


def install_simon_templates():
    """Install Simon monitoring script templates to ~/.databases/templates/"""

    template_base = os.path.expanduser("~/.databases/templates/simon")
    basefunctions.create_directory(template_base)

    # Simon monitoring script template
    monitor_script_content = """#!/bin/bash
# =====================================================================================
#  Project        : basefunctions
#  Filename       : monitor_script.sh
#  Description    : Auto-generated Simon monitoring script for {{ instance_name }}
#  Generated      : {{ timestamp }}
# =====================================================================================

# Script saved from Dejal Simon
# Script is for Bourne-Again Shell: /bin/bash

# *** INSTRUCTIONS: ***
# 
# This script monitors and restarts the Docker service if needed

# *** CUSTOM VARIABLES: ***
# 
# NAME: {{ instance_name }}
# DB_PORT: {{ db_port }}

# *** CUSTOM RESULTS: ***
# 
# 0: (Success)
# 1: (Failure)

# -------------------------------------------------------------
# VALIDATE INPUT AND BUILD VARIABLES
# -------------------------------------------------------------
if [[ -z "$SERVICE_NAME" ]]; then
    SERVICE_NAME="{{ instance_name }}"
fi
if [[ -z "$DB_PORT" ]]; then
    DB_PORT="{{ db_port }}"
fi

# -------------------------------------------------------------
# DERIVED VARIABLES
# -------------------------------------------------------------
INSTANCE_HOMEDIR="{{ instance_home_dir }}"
DOCKER_COMPOSE_PATH="${INSTANCE_HOMEDIR}/docker-compose.yml"

# -------------------------------------------------------------
# FUNCTION TO CHECK IF DOCKER COMPOSE SERVICE IS RUNNING
# -------------------------------------------------------------
check_docker_compose_status() {
    local compose_file="$1"
    local instance_dir="$2"
    
    # Check if docker-compose.yml exists
    if [[ ! -f "$compose_file" ]]; then
        echo "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    # Change to instance directory
    cd "$instance_dir" || {
        echo "Error: Could not change to directory $instance_dir"
        return 1
    }
    
    # Get container IDs for this compose project
    local container_ids
    container_ids=$(/usr/local/bin/docker compose -f "$compose_file" ps -q 2>/dev/null)
    
    if [[ -z "$container_ids" ]]; then
        echo "No containers found for compose project"
        return 1
    fi
    
    # Check each container status
    local all_running=true
    while IFS= read -r container_id; do
        if [[ -n "$container_id" ]]; then
            # Get container status using docker inspect
            local status
            status=$(/usr/local/bin/docker inspect --format='{% raw %}{{.State.Status}}{% endraw %}' "$container_id" 2>/dev/null)
            
            if [[ "$status" != "running" ]]; then
                echo "Container $container_id is not running (status: $status)"
                all_running=false
            fi
        fi
    done <<< "$container_ids"
    
    if [[ "$all_running" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# -------------------------------------------------------------
# FUNCTION TO CHECK PORT ACCESSIBILITY (ADDITIONAL VALIDATION)
# -------------------------------------------------------------
check_port_accessibility() {
    local port="$1"
    local max_attempts="${2:-5}"  # Default to 5 attempts if not specified
    local wait_time="${3:-5}"     # Default to 5 seconds between attempts
    local attempt=1
    
    echo "Checking port $port accessibility (max $max_attempts attempts, ${wait_time}s intervals)..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if nc -z localhost "$port" 2>/dev/null; then
            echo "Port $port is accessible"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Port $port not accessible"
        if [[ $attempt -lt $max_attempts ]]; then
            sleep "$wait_time"
        fi
        ((attempt++))
    done
    
    echo "Port $port is not accessible after $max_attempts attempts"
    return 1
}

# -------------------------------------------------------------
# COMBINED SERVICE CHECK
# -------------------------------------------------------------
check_service_running() {
    echo "Checking Docker Compose service status for ${SERVICE_NAME}..."
    
    if check_docker_compose_status "$DOCKER_COMPOSE_PATH" "$INSTANCE_HOMEDIR"; then
        echo "All containers are running"
        
        # Additional check: test port accessibility if specified
        if [[ -n "$DB_PORT" ]]; then
            echo "Checking database port accessibility..."
            # For service checks during monitoring, use fewer attempts
            if check_port_accessibility "$DB_PORT" 3 2; then
                echo "Service ${SERVICE_NAME} is fully operational"
                return 0
            else
                echo "Containers running but port $DB_PORT not accessible"
                return 1
            fi
        else
            # No port specified, assume running containers = working service
            return 0
        fi
    else
        echo "Docker Compose service ${SERVICE_NAME} is not running properly"
        return 1
    fi
}

# -------------------------------------------------------------
# FUNCTION TO WAIT FOR DATABASE TO BE READY AFTER START
# -------------------------------------------------------------
wait_for_database_ready() {
    local port="$1"
    echo "Waiting for database to be ready on port $port..."
    
    # First wait for containers to be in running state
    sleep 5
    
    # Then wait for database port to be accessible with more patience
    if check_port_accessibility "$port" 12 5; then
        echo "Database is ready!"
        return 0
    else
        echo "Database failed to become ready within timeout"
        return 1
    fi
}

# -------------------------------------------------------------
# ACTIVATE ENVIRONMENT
# -------------------------------------------------------------
activate_environment() {
    if [[ -d "$INSTANCE_HOMEDIR/.venv" ]]; then
        source "$INSTANCE_HOMEDIR/.venv/bin/activate"
    fi
}

# -------------------------------------------------------------
# START SERVICE
# -------------------------------------------------------------
if ! check_service_running; then
    echo "Service \'${SERVICE_NAME}\' is not running properly. Attempting to start..."
    
    # Activate Python environment
    activate_environment
    
    cd "$INSTANCE_HOMEDIR" || { 
        echo "Error: Could not change to directory $INSTANCE_HOMEDIR"
        exit 1
    }
    
    # Stop any existing containers first (cleanup)
    echo "Cleaning up existing containers..."
    /usr/local/bin/docker compose -f "$DOCKER_COMPOSE_PATH" stop 2>/dev/null
    /usr/local/bin/docker compose -f "$DOCKER_COMPOSE_PATH" rm -f 2>/dev/null
    
    # Start the service
    echo "Starting Docker Compose services..."
    /usr/local/bin/docker compose -f "$DOCKER_COMPOSE_PATH" up -d
    
    # Wait for database to be ready (longer timeout for startup)
    if [[ -n "$DB_PORT" ]]; then
        if wait_for_database_ready "$DB_PORT"; then
            echo "Successfully started service \'${SERVICE_NAME}\'"
            exit 0
        else
            echo "Service started but database not ready on port $DB_PORT"
            exit 1
        fi
    else
        # No port to check, just wait a bit and assume success
        echo "Waiting for service ${SERVICE_NAME} to initialize..."
        sleep 10
        echo "Successfully started service \'${SERVICE_NAME}\'"
        exit 0
    fi
else
    echo "Service \'${SERVICE_NAME}\' is running properly."
    exit 0
fi"""

    # Write template file
    template_file = os.path.join(template_base, "monitor_script.sh.j2")
    with open(template_file, "w") as f:
        f.write(monitor_script_content)
    print(f"Created: {template_file}")

    print(f"Simon templates installed to: {template_base}")


def install_all_templates():
    """Install all database templates."""
    print("Installing database templates...")
    install_postgres_templates()
    install_mysql_templates()
    install_sqlite_templates()
    install_simon_templates()
    print("All templates installed successfully!")


if __name__ == "__main__":
    install_all_templates()
