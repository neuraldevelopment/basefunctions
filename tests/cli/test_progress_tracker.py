"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ProgressTracker.
 Tests abstract progress tracker and alive-progress implementation.

 Log:
 v1.0.0 : Initial test implementation
 v2.0.0 : Migration to alive-progress
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import pytest
import threading
from unittest.mock import Mock, patch

# Project imports
from basefunctions.utils.progress_tracker import ProgressTracker, AliveProgressTracker

# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_progress_tracker_is_abstract() -> None:
    """Test ProgressTracker cannot be instantiated."""
    # ACT & ASSERT
    with pytest.raises(TypeError):
        ProgressTracker()


def test_alive_tracker_raises_when_alive_progress_not_installed() -> None:
    """Test AliveProgressTracker raises ImportError when alive-progress missing."""
    # ARRANGE
    with patch.dict("sys.modules", {"alive_progress": None}):
        # ACT & ASSERT
        with pytest.raises(ImportError, match="requires alive-progress"):
            AliveProgressTracker(total=100)


def test_alive_tracker_context_manager_works() -> None:
    """Test AliveProgressTracker works as context manager."""
    # ARRANGE
    try:
        from alive_progress import alive_bar

        # ACT & ASSERT - Should not raise
        with AliveProgressTracker(total=10, desc="Test") as tracker:
            tracker.progress(5)
    except ImportError:
        pytest.skip("alive-progress not installed")


def test_alive_tracker_is_thread_safe() -> None:  # CRITICAL TEST
    """Test AliveProgressTracker progress method is thread-safe."""
    # ARRANGE
    try:
        from alive_progress import alive_bar

        tracker = AliveProgressTracker(total=100, desc="Test")

        def increment():
            for _ in range(10):
                tracker.progress(1)

        threads = [threading.Thread(target=increment) for _ in range(5)]

        # ACT
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # ASSERT - Should not crash
        tracker.close()
    except ImportError:
        pytest.skip("alive-progress not installed")
