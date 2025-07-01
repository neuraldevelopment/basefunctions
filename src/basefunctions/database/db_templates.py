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
# LOGGING INITIALIZE
# -------------------------------------------------------------
# Enable logging for this module
basefunctions.setup_logger(__name__)

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
      - {{ data_dir }}/postgres:/var/lib/postgres/data
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
#  Description    : Simon monitoring script for Docker database instances
#  Generated      : {{ timestamp }}
# =====================================================================================

# *** INSTRUCTIONS: ***
# This script monitors and restarts Docker database services
# Uses Simon variables: DB_NAME and DB_PORT

# *** CUSTOM VARIABLES: ***
# DB_NAME: {DB_NAME}
# DB_PORT: {DB_PORT}

# *** CUSTOM RESULTS: ***
# 0: Success
# 1: Failure

# -------------------------------------------------------------
# SIMON VARIABLES
# -------------------------------------------------------------
SIMON_DB_NAME="{DB_NAME}"
SIMON_DB_PORT="{DB_PORT}"
INSTANCE_HOMEDIR="/Users/neutro2/.databases/instances/{DB_NAME}"
DOCKER_COMPOSE_PATH="/Users/neutro2/.databases/instances/{DB_NAME}/docker-compose.yml"

# -------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_docker_compose_running() {
    local compose_file="$1"
    local instance_dir="$2"
    
    if [[ ! -f "$compose_file" ]]; then
        log_message "ERROR: Docker Compose file not found: $compose_file"
        return 1
    fi
    
    cd "$instance_dir" || {
        log_message "ERROR: Cannot change to directory $instance_dir"
        return 1
    }
    
    # Get running containers for this compose project
    local container_ids
    container_ids=$(/usr/local/bin/docker compose -f "$compose_file" ps -q --status running 2>/dev/null)
    
    if [[ -z "$container_ids" ]]; then
        log_message "No running containers found for $SIMON_DB_NAME"
        return 1
    fi
    
    # Check if all expected containers are running
    local running_count
    running_count=$(echo "$container_ids" | wc -l | tr -d ' ')
    
    if [[ $running_count -gt 0 ]]; then
        log_message "Found $running_count running container(s) for $SIMON_DB_NAME"
        return 0
    else
        return 1
    fi
}

check_port_accessible() {
    local port="$1"
    local attempts="${2:-3}"
    local wait_time="${3:-2}"
    
    for ((i=1; i<=attempts; i++)); do
        if nc -z localhost "$port" 2>/dev/null; then
            log_message "Port $port is accessible"
            return 0
        fi
        if [[ $i -lt $attempts ]]; then
            sleep "$wait_time"
        fi
    done
    
    log_message "Port $port is not accessible after $attempts attempts"
    return 1
}

start_service() {
    log_message "Starting Docker Compose service for $SIMON_DB_NAME..."
    
    cd "$INSTANCE_HOMEDIR" || {
        log_message "ERROR: Cannot change to $INSTANCE_HOMEDIR"
        exit 1
    }
    
    # Cleanup first
    /usr/local/bin/docker compose -f "$DOCKER_COMPOSE_PATH" down 2>/dev/null
    
    # Start services
    if /usr/local/bin/docker compose -f "$DOCKER_COMPOSE_PATH" up -d; then
        log_message "Docker Compose started successfully"
        
        # Wait for service to be ready
        sleep 5
        
        if check_port_accessible "$SIMON_DB_PORT" 10 3; then
            log_message "Service $SIMON_DB_NAME is ready on port $SIMON_DB_PORT"
            return 0
        else
            log_message "Service started but port $SIMON_DB_PORT not accessible"
            return 1
        fi
    else
        log_message "ERROR: Failed to start Docker Compose"
        return 1
    fi
}

# -------------------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------------------
log_message "Monitoring service: $SIMON_DB_NAME on port $SIMON_DB_PORT"

# Check if service is running
if check_docker_compose_running "$DOCKER_COMPOSE_PATH" "$INSTANCE_HOMEDIR"; then
    if check_port_accessible "$SIMON_DB_PORT" 2 1; then
        log_message "Service $SIMON_DB_NAME is running properly"
        exit 0
    else
        log_message "Containers running but port $SIMON_DB_PORT not accessible - restarting"
    fi
else
    log_message "Service $SIMON_DB_NAME is not running - starting"
fi

# Start/restart service
if start_service; then
    log_message "Successfully started service $SIMON_DB_NAME"
    exit 0
else
    log_message "Failed to start service $SIMON_DB_NAME"
    exit 1
fi"""

    # Write template file
    template_file = os.path.join(template_base, "monitor_script.sh.j2")
    with open(template_file, "w") as f:
        f.write(monitor_script_content)
    print(f"Created: {template_file}")

    print(f"Simon templates installed to: {template_base}")


def install_redis_templates():
    """Install Redis Docker templates to ~/.databases/templates/"""
    print("install redis")
    template_base = os.path.expanduser("~/.databases/templates/docker/redis")
    basefunctions.create_directory(template_base)

    # Docker Compose Template for Redis
    docker_compose_content = """# Docker Compose configuration for Redis database instance: {{ instance_name }}
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: {{ instance_name }}_redis
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    command: redis-server /usr/local/etc/redis/redis.conf
    environment:
      - REDIS_PASSWORD={{ db_password }}
    volumes:
      - {{ data_dir }}/redis:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - ./bootstrap:/docker-entrypoint-initdb.d
    ports:
      - "{{ db_port }}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "{{ db_password }}", "ping"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 10s

  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: {{ instance_name }}_redis_commander
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      - REDIS_HOSTS=local:{{ instance_name }}_redis:6379:0:{{ db_password }}
      - HTTP_USER=admin
      - HTTP_PASSWORD={{ db_password }}
      - PORT=8081
    ports:
      - "{{ admin_port }}:8081"
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8081/"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 20s

networks:
  default:
    name: {{ instance_name }}_network"""

    # Redis Configuration Template
    redis_conf_content = """# Redis configuration for instance: {{ instance_name }}

# Network
bind 0.0.0.0
port 6379
protected-mode yes

# Authentication
requirepass {{ db_password }}

# General
daemonize no
loglevel notice
databases 16

# Persistence
save 900 1
save 300 10
save 60 10000

dbfilename dump.rdb
dir /data

# AOF Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Memory Management
maxmemory-policy allkeys-lru

# Timeouts
timeout 300
tcp-keepalive 300

# Client Output Buffer Limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128"""

    # Bootstrap Script Template
    bootstrap_content = """#!/bin/bash
# =============================================================================
# Bootstrap script for Redis instance: {{ instance_name }}
# Initializes Redis with basic configuration and test data
# =============================================================================

echo "Initializing Redis instance: {{ instance_name }}"

# Wait for Redis to be ready
until redis-cli -h {{ instance_name }}_redis -p 6379 -a "{{ db_password }}" ping; do
    echo "Waiting for Redis..."
    sleep 2
done

echo "Redis is ready, setting up initial data..."

# Set some initial test data
redis-cli -h {{ instance_name }}_redis -p 6379 -a "{{ db_password }}" <<EOF
SET demo:instance "{{ instance_name }}"
SET demo:initialized "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SET demo:status "Bootstrap completed successfully"
HSET demo:info instance "{{ instance_name }}" port "{{ db_port }}" admin_port "{{ admin_port }}"
LPUSH demo:logs "Instance {{ instance_name }} initialized"
LPUSH demo:logs "Bootstrap script completed"
SADD demo:features "key-value" "hashes" "lists" "sets" "pub-sub"
EOF

echo "Redis initialization completed for instance: {{ instance_name }}"
echo "Test the connection with: redis-cli -h localhost -p {{ db_port }} -a {{ db_password }}"
echo "Access Redis Commander at: http://localhost:{{ admin_port }}"
"""
    # Write template files
    templates = [
        ("docker-compose.yml.j2", docker_compose_content),
        ("redis.conf.j2", redis_conf_content),
        ("bootstrap.sh.j2", bootstrap_content),
    ]

    for filename, content in templates:
        file_path = os.path.join(template_base, filename)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Created: {file_path}")

    print(f"Redis templates installed to: {template_base}")


def install_all_templates():
    """Install all database templates."""
    print("Installing database templates...")
    install_postgres_templates()
    install_mysql_templates()
    install_sqlite_templates()
    install_redis_templates()
    install_simon_templates()
    print("All templates installed successfully!")


if __name__ == "__main__":
    install_all_templates()
