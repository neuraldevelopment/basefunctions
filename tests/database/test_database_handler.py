"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment, Munich

  Project : backtraderfunctions - DatabaseHandler Tests

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Simple test file for BaseDatabaseHandler and connectors

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import tempfile

import basefunctions as bf

# -------------------------------------------------------------
# TESTING FUNCTIONS
# -------------------------------------------------------------


def test_sqlite_connector():
    # Setup temporary SQLite file
    temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(temp_db_fd)

    try:
        handler = bf.BaseDatabaseHandler()
        connector = handler.register_connector(
            "test_sqlite", "sqlite3", {"database": temp_db_path}
        )

        handler.connect("test_sqlite")
        assert handler.is_connected("test_sqlite") is True, "Connection should be active."

        handler.execute(
            "test_sqlite", "CREATE TABLE IF NOT EXISTS test_table (id <PRIMARYKEY>, name TEXT);"
        )
        assert (
            handler.check_if_table_exists("test_sqlite", "test_table") is True
        ), "Table should exist."

        handler.execute("test_sqlite", "INSERT INTO test_table (name) VALUES (?)", ("Alice",))
        handler.execute("test_sqlite", "INSERT INTO test_table (name) VALUES (?)", ("Bob",))

        result = handler.fetch_one(
            "test_sqlite", "SELECT * FROM test_table WHERE name = ?", ("Alice",)
        )
        assert result is not None, "Fetch one should return a result."
        assert result["name"] == "Alice", "Fetched name should be 'Alice'."

        results = handler.fetch_all("test_sqlite", "SELECT * FROM test_table")
        assert len(results) == 2, "Should fetch two rows."

        handler.begin_transaction("test_sqlite")
        handler.execute("test_sqlite", "INSERT INTO test_table (name) VALUES (?)", ("Charlie",))
        handler.rollback("test_sqlite")

        results_after_rollback = handler.fetch_all("test_sqlite", "SELECT * FROM test_table")
        assert len(results_after_rollback) == 2, "Rollback should undo last insert."

        handler.begin_transaction("test_sqlite")
        handler.execute("test_sqlite", "INSERT INTO test_table (name) VALUES (?)", ("Charlie",))
        handler.commit("test_sqlite")

        results_after_commit = handler.fetch_all("test_sqlite", "SELECT * FROM test_table")
        assert len(results_after_commit) == 3, "Commit should persist insert."

        handler.close("test_sqlite")
        assert handler.is_connected("test_sqlite") is False, "Connection should be closed."

    finally:
        os.remove(temp_db_path)


# -------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------
if __name__ == "__main__":
    print("Running SQLite connector tests...")
    test_sqlite_connector()
    print("All tests passed.")
