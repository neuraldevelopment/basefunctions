#!/bin/bash
# =====================================================================================
#  Project        : prodtools
#  Filename       : {{ service_name }}_simon_monitor.sh
#  Description    : Simon monitoring script for {{ service_name }} database
# =====================================================================================

# Script saved from Dejal Simon
# Script is for Bourne-Again Shell: /bin/bash

# *** INSTRUCTIONS: ***
# 
# This script monitors and restarts the Docker service if needed

# *** CUSTOM VARIABLES: ***
# 
# NAME: {{ service_name }}
# DB_PORT: {{ db_port }}

# *** CUSTOM RESULTS: ***
# 
# 0: (Success)
# 1: (Failure)

# -------------------------------------------------------------
# VALIDATE INPUT AND BUILD VARIABLES
# -------------------------------------------------------------
if [[ -z "$SERVICE_NAME" ]]; then
    SERVICE_NAME="{{ service_name }}"
fi
if [[ -z "$DB_PORT" ]]; then
    DB_PORT="{{ db_port }}"
fi

# -------------------------------------------------------------
# DERIVED VARIABLES
# -------------------------------------------------------------
INSTANCE_HOMEDIR="/Users/neutro2/.databases/instances/${SERVICE_NAME}"
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
    echo "Service '${SERVICE_NAME}' is not running properly. Attempting to start..."
    
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
            echo "Successfully started service '${SERVICE_NAME}'"
            exit 0
        else
            echo "Service started but database not ready on port $DB_PORT"
            exit 1
        fi
    else
        # No port to check, just wait a bit and assume success
        echo "Waiting for service ${SERVICE_NAME} to initialize..."
        sleep 10
        echo "Successfully started service '${SERVICE_NAME}'"
        exit 0
    fi
else
    echo "Service '${SERVICE_NAME}' is running properly."
    exit 0
fi