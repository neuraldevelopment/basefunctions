"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 test cases for output redirection classes

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import sys
import pytest
import sqlite3
import tempfile
import threading
import time
from io import StringIO
from datetime import datetime
import basefunctions


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------
@pytest.fixture
def temp_file():
    """fixture to create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(delete=False, mode="w+", encoding="utf-8") as f:
        temp_path = f.name

    yield temp_path

    # cleanup after test
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def db_connection():
    """fixture to create an in-memory sqlite database for testing"""
    # register adapter for datetime objects
    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())

    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


# -------------------------------------------------------------
# TEST CLASSES
# -------------------------------------------------------------
class TestOutputRedirector:
    """test cases for the OutputRedirector class"""

    def test_file_target(self, temp_file):
        """test redirecting output to a file"""
        # setup
        file_target = basefunctions.FileTarget(temp_file)

        # test with context manager
        with basefunctions.OutputRedirector(file_target):
            print("line 1")
            print("line 2")

        # explicitly close file to avoid resource warning
        file_target.close()

        # verify
        with open(temp_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "line 1" in content
        assert "line 2" in content

    def test_memory_target(self):
        """test redirecting output to memory"""
        # setup
        memory_target = basefunctions.MemoryTarget()

        # test with manual start/stop
        redirector = basefunctions.OutputRedirector(memory_target)
        redirector.start()
        print("captured text")
        redirector.stop()

        # verify
        buffer_content = memory_target.get_buffer()
        assert "captured text" in buffer_content

    def test_database_target(self, db_connection):
        """test redirecting output to database"""
        # setup
        db_target = basefunctions.DatabaseTarget(
            db_connection, "output_logs", {"timestamp": "TEXT", "message": "TEXT"}
        )

        # start with fresh table
        cursor = db_connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS output_logs")
        db_connection.commit()

        # create table
        db_target._ensure_table_exists()

        # test
        with basefunctions.OutputRedirector(db_target):
            print("log entry 1")
            print("log entry 2")

        # force flush
        db_target.flush()

        # verify
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM output_logs")
        count = cursor.fetchone()[0]

        # accept that multiple entries might be created per print
        assert count > 0

        cursor.execute("SELECT message FROM output_logs")
        messages = [row[0] for row in cursor.fetchall()]
        combined_messages = "".join(messages)

        assert "log entry 1" in combined_messages
        assert "log entry 2" in combined_messages

    def test_redirect_stderr(self):
        """test redirecting stderr"""
        # setup
        memory_target = basefunctions.MemoryTarget()

        # test with stderr redirection
        with basefunctions.OutputRedirector(
            memory_target, redirect_stderr=True, redirect_stdout=False
        ):
            sys.stderr.write("error message")

        # verify
        buffer_content = memory_target.get_buffer()
        assert "error message" in buffer_content

    def test_direct_write(self):
        """test direct writing to target"""
        # setup
        memory_target = basefunctions.MemoryTarget()
        redirector = basefunctions.OutputRedirector(memory_target)

        # test direct write
        redirector.write("direct message")
        redirector.flush()

        # verify
        buffer_content = memory_target.get_buffer()
        assert "direct message" in buffer_content

    def test_flush(self):
        """test flush method"""
        # setup
        memory_target = basefunctions.MemoryTarget()

        # test
        with basefunctions.OutputRedirector(memory_target):
            print("text before flush", end="")
            sys.stdout.flush()
            print("text after flush", end="")

        # verify
        buffer_content = memory_target.get_buffer()
        assert "text before flush" in buffer_content
        assert "text after flush" in buffer_content

    def test_nested_redirectors(self):
        """test nested output redirectors"""
        # setup
        memory_target1 = basefunctions.MemoryTarget()
        memory_target2 = basefunctions.MemoryTarget()

        # test nested redirectors
        with basefunctions.OutputRedirector(memory_target1):
            print("outer redirector")

            with basefunctions.OutputRedirector(memory_target2):
                print("inner redirector")

            print("back to outer")

        # verify
        assert "outer redirector" in memory_target1.get_buffer()
        assert "back to outer" in memory_target1.get_buffer()
        assert "inner redirector" in memory_target2.get_buffer()
        assert "outer redirector" not in memory_target2.get_buffer()

    def test_thread_safety(self):
        """test basic thread safety with individual redirectors per thread"""
        results = []
        lock = threading.Lock()

        def thread_func(thread_id):
            """function to run in threads"""
            # Jeder Thread benutzt seinen eigenen Memory-Target und Redirector
            memory_target = basefunctions.MemoryTarget()
            redirector = basefunctions.OutputRedirector(memory_target)

            try:
                # Start redirection
                redirector.start()
                # Print something unique to this thread
                print(f"Thread {thread_id} output")
                # Stop redirection
                redirector.stop()

                # Save the output with the thread ID
                with lock:
                    results.append((thread_id, memory_target.get_buffer()))
            except Exception as e:
                with lock:
                    results.append((thread_id, f"ERROR: {str(e)}"))

        # Create and start threads
        threads = []
        thread_count = 5
        for i in range(thread_count):
            t = threading.Thread(target=thread_func, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Check that we got results from all threads
        assert len(results) == thread_count, f"Expected {thread_count} results, got {len(results)}"

        # Verify each thread captured its own output
        for thread_id, output in results:
            if "ERROR" in output:
                pytest.fail(f"Thread {thread_id} had an error: {output}")
            assert f"Thread {thread_id} output" in output
