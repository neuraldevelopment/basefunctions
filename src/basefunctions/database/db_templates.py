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

    # Docker Compose Template
    docker_compose_content = """# Docker Compose configuration for PostgreSQL database instance: {{ instance_name }}
version: '3.8'

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
      - ./bootstrap:/docker-entrypoint-initdb.d
    ports:
      - "{{ db_port }}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  pgadmin:
    image: dpage/pgadmin4
    container_name: {{ instance_name }}_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@{{ instance_name }}.local
      PGADMIN_DEFAULT_PASSWORD: "{{ password }}"
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
      PGADMIN_CONFIG_WTF_CSRF_ENABLED: 'False'
    volumes:
      - {{ data_dir }}/pgadmin:/var/lib/pgadmin
      - ./config/pgadmin_servers.json:/pgladmin4/servers.json
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/misc/ping"]
      interval: 60s
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
DO $$
BEGIN
    RAISE NOTICE 'Bootstrap completed for instance: {{ instance_name }}';
END
$$;"""

    # pgAdmin Servers Template
    pgadmin_content = """{
  "Servers": {
    "1": {
      "Name": "{{ instance_name }} - Local PostgreSQL",
      "Group": "neuraldevelopment",
      "Host": "postgres",
      "Port": 5432,
      "MaintenanceDB": "{{ instance_name }}",
      "Username": "postgres",
      "Password": "{{ password }}",
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

    # Docker Compose Template for MySQL
    docker_compose_content = """# Docker Compose configuration for MySQL database instance: {{ instance_name }}
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: {{ instance_name }}_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: "{{ password }}"
      MYSQL_DATABASE: {{ instance_name }}
      MYSQL_USER: mysql_user
      MYSQL_PASSWORD: "{{ password }}"
    volumes:
      - {{ data_dir }}/mysql:/var/lib/mysql
      - ./bootstrap:/docker-entrypoint-initdb.d
    ports:
      - "{{ db_port }}:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p{{ password }}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: {{ instance_name }}_phpmyadmin
    restart: unless-stopped
    environment:
      PMA_HOST: mysql
      PMA_PORT: 3306
      PMA_USER: root
      PMA_PASSWORD: "{{ password }}"
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      mysql:
        condition: service_healthy

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

    # Docker Compose Template for SQLite
    docker_compose_content = """# Docker Compose configuration for SQLite database instance: {{ instance_name }}
version: '3.8'

services:
  sqlite:
    image: nouchka/sqlite3:latest
    container_name: {{ instance_name }}_sqlite
    restart: unless-stopped
    volumes:
      - {{ data_dir }}/sqlite:/db
      - ./bootstrap:/docker-entrypoint-initdb.d
    working_dir: /db
    command: tail -f /dev/null  # Keep container running
    healthcheck:
      test: ["CMD", "ls", "/db/{{ instance_name }}.db"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  sqlite-browser:
    image: linuxserver/sqlitebrowser:latest
    container_name: {{ instance_name }}_sqlite_browser
    restart: unless-stopped
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
    restart: unless-stopped
    volumes:
      - {{ data_dir }}/sqlite:/data
    ports:
      - "{{ db_port }}:8080"
    command: ["sqlite_web", "/data/{{ instance_name }}.db", "--host", "0.0.0.0", "--port", "8080"]
    depends_on:
      sqlite:
        condition: service_healthy

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


def install_all_templates():
    """Install all database templates."""
    print("Installing database templates...")
    install_postgres_templates()
    install_mysql_templates()
    install_sqlite_templates()
    print("All templates installed successfully!")


if __name__ == "__main__":
    install_all_templates()
