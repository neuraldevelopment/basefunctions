"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Simple test suite for corelet process lifecycle management monitoring APIs.

 Log:
 v1.0.0 : Initial test implementation for corelet lifecycle monitoring
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard Library
import time

# Third-party
import pytest

# Project modules
import basefunctions


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def clean_singleton():
    """Clean EventBus singleton before test."""
    from basefunctions.utils.decorators import _singleton_instances

    for cls in list(_singleton_instances.keys()):
        if cls.__name__ == "EventBus":
            del _singleton_instances[cls]
            break
    yield


# -------------------------------------------------------------
# TEST CASES - MONITORING API
# -------------------------------------------------------------


def test_corelet_count_initially_zero(clean_singleton):
    """
    Test get_corelet_count returns 0 initially.

    Parameters
    ----------
    clean_singleton : None
        Cleanup fixture
    """
    bus = basefunctions.EventBus(num_threads=2)
    assert bus.get_corelet_count() == 0


def test_corelet_metrics_structure(clean_singleton):
    """
    Test get_corelet_metrics returns correct structure.

    Parameters
    ----------
    clean_singleton : None
        Cleanup fixture
    """
    bus = basefunctions.EventBus(num_threads=2)
    metrics = bus.get_corelet_metrics()

    assert isinstance(metrics, dict)
    assert "active_corelets" in metrics
    assert "worker_threads" in metrics
    assert "max_corelets" in metrics
    assert metrics["active_corelets"] == 0
    assert metrics["worker_threads"] == 2
    assert metrics["max_corelets"] == 2


def test_corelet_metrics_consistency(clean_singleton):
    """
    Test corelet metrics are internally consistent.

    Parameters
    ----------
    clean_singleton : None
        Cleanup fixture
    """
    bus = basefunctions.EventBus(num_threads=4)
    metrics = bus.get_corelet_metrics()

    # max_corelets should equal worker_threads
    assert metrics["max_corelets"] == metrics["worker_threads"]

    # active_corelets should be bounded
    assert 0 <= metrics["active_corelets"] <= metrics["max_corelets"]


def test_register_corelet_tracking(clean_singleton):
    """
    Test internal _register_corelet method updates count.

    Parameters
    ----------
    clean_singleton : None
        Cleanup fixture
    """
    bus = basefunctions.EventBus(num_threads=2)

    # Initially zero
    assert bus.get_corelet_count() == 0

    # Register a corelet
    bus._register_corelet(thread_id=12345, process_id=99999)

    # Count should increase
    assert bus.get_corelet_count() == 1

    # Metrics should reflect it
    metrics = bus.get_corelet_metrics()
    assert metrics["active_corelets"] == 1


def test_corelet_tracking_thread_safe(clean_singleton):
    """
    Test corelet tracking is thread-safe.

    Parameters
    ----------
    clean_singleton : None
        Cleanup fixture
    """
    import threading

    bus = basefunctions.EventBus(num_threads=2)

    # Register from multiple threads
    def register():
        tid = threading.get_ident()
        bus._register_corelet(tid, 10000 + tid)

    threads = [threading.Thread(target=register) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Count should be 10 (one per thread)
    assert bus.get_corelet_count() == 10
