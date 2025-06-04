-- Bootstrap script for SQLite instance: {{ instance_name }}
-- This must be executed manually using the sqlite container

-- Create a test table
CREATE TABLE IF NOT EXISTS test_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    value INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some test data
INSERT INTO test_table (name, value) VALUES
    ('Example 1', 100),
    ('Example 2', 200),
    ('Example 3', 300);

-- Print message
SELECT 'SQLite database initialization complete for {{ instance_name }}';