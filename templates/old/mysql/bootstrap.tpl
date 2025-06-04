-- Bootstrap script for MySQL instance: {{ instance_name }}
-- This script runs when the container is first initialized

-- Switch to the test database
USE testdb;

-- Create a test table
CREATE TABLE IF NOT EXISTS test_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some test data
INSERT INTO test_table (name, value) VALUES
    ('Example 1', 100),
    ('Example 2', 200),
    ('Example 3', 300);

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON testdb.* TO 'appuser'@'%';
FLUSH PRIVILEGES;

-- Print message to logs
SELECT 'MySQL database initialization complete for {{ instance_name }}' AS message;
