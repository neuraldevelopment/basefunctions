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
import basefunctions

# -------------------------------------------------------------
# TEST UTILITIES
# -------------------------------------------------------------
@pytest.fixture
def temp_file():
    """fixture to create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8') as f:
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
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()

# -------------------------------------------------------------
# TEST CASES
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
            
        # verify
        with open(temp_file, 'r', encoding='utf-8') as f:
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
            db_connection, 
            "output_logs",
            {"timestamp": "TIMESTAMP", "message": "TEXT"}
        )
        
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
        assert count == 2
        
        cursor.execute("SELECT message FROM output_logs ORDER BY timestamp")
        messages = cursor.fetchall()
        assert messages[0][0] == "log entry 1\n"
        assert messages[1][0] == "log entry 2\n"
    
    def test_redirect_stderr(self):
        """test redirecting stderr"""
        # setup
        memory_target = basefunctions.MemoryTarget()
        
        # test with stderr redirection
        with basefunctions.OutputRedirector(memory_target, redirect_stderr=True, redirect_stdout=False):
            sys.stderr.write("error message")
            
        # verify
        buffer_content = memory_target.get_buffer()
        assert "error message" in buffer_content
    
    def test_thread_safety(self):
        """test thread-safe redirector"""
        # setup
        results = []
        
        def target_factory():
            return basefunctions.MemoryTarget()
        
        redirector = basefunctions.ThreadSafeOutputRedirector(target_factory)
        
        # function to run in threads
        def thread_func(thread_id):
            with redirector:
                print(f"Thread {thread_id} output")
                # Add small delay to increase chance of thread overlap
                time.sleep(0.01)
        
        # run multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=thread_func, args=(i,))
            threads.append(t)
            t.start()
            
        # wait for all threads to complete
        for t in threads:
            t.join()
    
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
