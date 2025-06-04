-- =============================================================================
-- Bootstrap script for PostgreSQL instance: {{ instance_name }}
-- Creates custom database with instance name
-- =============================================================================

-- Create custom database with instance name
CREATE DATABASE "{{ instance_name }}";

-- Grant permissions to postgres user
GRANT ALL PRIVILEGES ON DATABASE "{{ instance_name }}" TO postgres;