"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for ProgressTracker.
 Tests abstract progress tracker and tqdm implementation.

 Log:
 v1.0.0 : Initial test implementation
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
from basefunctions.cli import ProgressTracker, TqdmProgressTracker

# -------------------------------------------------------------
# TESTS
# -------------------------------------------------------------


def test_progress_tracker_is_abstract() -> None:
    """Test ProgressTracker cannot be instantiated."""
    # ACT & ASSERT
    with pytest.raises(TypeError):
        ProgressTracker()


def test_tqdm_tracker_raises_when_tqdm_not_installed() -> None:
    """Test TqdmProgressTracker raises ImportError when tqdm missing."""
    # ARRANGE
    with patch.dict('sys.modules', {'tqdm': None, 'tqdm.auto': None}):
        # ACT & ASSERT
        with pytest.raises(ImportError, match="requires tqdm"):
            TqdmProgressTracker(total=100)


def test_tqdm_tracker_context_manager_works() -> None:
    """Test TqdmProgressTracker works as context manager."""
    # ARRANGE
    try:
        import tqdm.auto
        
        # ACT & ASSERT - Should not raise
        with TqdmProgressTracker(total=10, desc="Test") as tracker:
            tracker.progress(5)
    except ImportError:
        pytest.skip("tqdm not installed")


def test_tqdm_tracker_is_thread_safe() -> None:  # CRITICAL TEST
    """Test TqdmProgressTracker progress method is thread-safe."""
    # ARRANGE
    try:
        import tqdm.auto
        
        tracker = TqdmProgressTracker(total=100, desc="Test")
        
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
        pytest.skip("tqdm not installed")
