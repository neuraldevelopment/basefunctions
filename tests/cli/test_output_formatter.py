"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.

 Description:
 Pytest test suite for OutputFormatter.
 Tests thread-safe formatted output with singleton pattern.

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

# Project imports
from basefunctions.cli import OutputFormatter

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def formatter() -> OutputFormatter:
    """Provide OutputFormatter instance."""
    return OutputFormatter()


# -------------------------------------------------------------
# TESTS: Singleton Pattern - CRITICAL
# -------------------------------------------------------------


def test_new_returns_singleton_instance(formatter: OutputFormatter) -> None:
    """Test __new__ returns same instance."""
    # ACT
    formatter2 = OutputFormatter()

    # ASSERT
    assert formatter is formatter2


def test_new_is_thread_safe(formatter: OutputFormatter) -> None:  # CRITICAL TEST
    """Test __new__ singleton is thread-safe."""
    # ARRANGE
    instances = []

    def create_formatter():
        instances.append(OutputFormatter())

    threads = [threading.Thread(target=create_formatter) for _ in range(10)]

    # ACT
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ASSERT
    assert all(inst is instances[0] for inst in instances)


def test_show_header_displays_formatted_box(formatter: OutputFormatter, capsys) -> None:
    """Test show_header displays formatted header box."""
    # ACT
    formatter.show_header("Test Title")

    # ASSERT
    captured = capsys.readouterr()
    assert "Test Title" in captured.out
    assert "┌" in captured.out
    assert "└" in captured.out


def test_show_result_includes_elapsed_time(formatter: OutputFormatter, capsys) -> None:
    """Test show_result includes elapsed time when start_time set."""
    # ARRANGE
    formatter.show_header("Test")

    # ACT
    formatter.show_result("Complete", success=True)

    # ASSERT
    captured = capsys.readouterr()
    assert "s)" in captured.out  # Elapsed time in seconds
