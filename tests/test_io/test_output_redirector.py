"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Pytest test suite for io.output_redirector module.
  Tests output redirection functionality including file, database, and memory targets.

  Log:
  v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# External imports
import io
import pytest
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock, patch, call

# Project imports
from basefunctions.io.output_redirector import (
    OutputTarget,
    OutputRedirector,
    FileTarget,
    DatabaseTarget,
    MemoryTarget,
    ThreadSafeOutputRedirector,
    _RedirectStream,
    redirect_output,
)

# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------


@pytest.fixture
def sample_text() -> str:
    """
    Provide sample text for testing.

    Returns
    -------
    str
        Sample text content
    """
    return "Test output message\n"


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """
    Create temporary file path for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    Path
        Path to temporary file
    """
    return tmp_path / "test_output.txt"


@pytest.fixture
def mock_db_manager() -> Mock:
    """
    Create mock database manager for testing.

    Returns
    -------
    Mock
        Mocked DbManager instance with configured behavior

    Notes
    -----
    Provides complete database operation mocking including instance,
    database, table operations, and transactions.
    """
    # ARRANGE
    mock_manager: Mock = Mock()
    mock_instance: Mock = Mock()
    mock_db: Mock = Mock()
    mock_transaction_context: Mock = Mock()

    # Configure mock chain
    mock_manager.get_instance.return_value = mock_instance
    mock_instance.get_database.return_value = mock_db
    mock_instance.get_type.return_value = "sqlite"
    mock_db.table_exists.return_value = False
    mock_db.execute.return_value = None
    mock_db.transaction.return_value.__enter__ = Mock(return_value=mock_transaction_context)
    mock_db.transaction.return_value.__exit__ = Mock(return_value=False)

    # RETURN
    return mock_manager


@pytest.fixture
def memory_target() -> MemoryTarget:
    """
    Create MemoryTarget instance for testing.

    Returns
    -------
    MemoryTarget
        Initialized memory target
    """
    return MemoryTarget()


# -------------------------------------------------------------
# TEST CASES: MemoryTarget
# -------------------------------------------------------------


def test_memory_target_write_stores_text_in_buffer(memory_target: MemoryTarget, sample_text: str) -> None:
    """
    Test MemoryTarget.write stores text correctly in memory buffer.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance
    sample_text : str
        Fixture providing sample text

    Returns
    -------
    None
        Test passes if text is stored in buffer
    """
    # ACT
    memory_target.write(sample_text)
    result: str = memory_target.get_buffer()

    # ASSERT
    assert result == sample_text


def test_memory_target_write_accumulates_multiple_writes(memory_target: MemoryTarget) -> None:
    """
    Test MemoryTarget.write accumulates multiple write operations.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance

    Returns
    -------
    None
        Test passes if all writes are accumulated
    """
    # ARRANGE
    texts: List[str] = ["First line\n", "Second line\n", "Third line\n"]
    expected: str = "".join(texts)

    # ACT
    for text in texts:
        memory_target.write(text)
    result: str = memory_target.get_buffer()

    # ASSERT
    assert result == expected


def test_memory_target_close_clears_buffer(memory_target: MemoryTarget, sample_text: str) -> None:
    """
    Test MemoryTarget.close clears the buffer and resets state.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance
    sample_text : str
        Fixture providing sample text

    Returns
    -------
    None
        Test passes if buffer is cleared after close
    """
    # ARRANGE
    memory_target.write(sample_text)

    # ACT
    memory_target.close()
    result: str = memory_target.get_buffer()

    # ASSERT
    assert result == ""


def test_memory_target_flush_does_nothing_but_succeeds(memory_target: MemoryTarget) -> None:
    """
    Test MemoryTarget.flush executes without error.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance

    Returns
    -------
    None
        Test passes if flush executes without exception

    Notes
    -----
    flush() is a no-op for MemoryTarget but must exist for interface compliance.
    """
    # ACT & ASSERT (no exception should be raised)
    memory_target.flush()


@pytest.mark.parametrize("invalid_input", [
    None,
    123,
    ["list", "of", "strings"],
    {"key": "value"},
])
def test_memory_target_write_handles_non_string_types(
    memory_target: MemoryTarget,
    invalid_input: Any
) -> None:
    """
    Test MemoryTarget.write handles non-string input types.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance
    invalid_input : Any
        Invalid input type to test

    Returns
    -------
    None
        Test passes if appropriate exception is raised

    Notes
    -----
    StringIO.write expects str type, should raise TypeError for other types.
    """
    # ACT & ASSERT
    with pytest.raises(TypeError):
        memory_target.write(invalid_input)


# -------------------------------------------------------------
# TEST CASES: FileTarget (CRITICAL)
# -------------------------------------------------------------


def test_file_target_creates_file_successfully(temp_file: Path, sample_text: str) -> None:  # CRITICAL TEST
    """
    Test FileTarget creates file and writes content correctly.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path
    sample_text : str
        Fixture providing sample text

    Returns
    -------
    None
        Test passes if file is created with correct content
    """
    # ARRANGE
    target: FileTarget = FileTarget(str(temp_file), mode="w")

    # ACT
    target.write(sample_text)
    target.flush()
    target.close()
    result: str = temp_file.read_text()

    # ASSERT
    assert temp_file.exists()
    assert result == sample_text


def test_file_target_append_mode_preserves_existing_content(temp_file: Path) -> None:  # CRITICAL TEST
    """
    Test FileTarget in append mode preserves existing file content.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if existing content is preserved
    """
    # ARRANGE
    existing_content: str = "Existing line\n"
    new_content: str = "New line\n"
    temp_file.write_text(existing_content)

    # ACT
    target: FileTarget = FileTarget(str(temp_file), mode="a")
    target.write(new_content)
    target.close()
    result: str = temp_file.read_text()

    # ASSERT
    assert result == existing_content + new_content


def test_file_target_write_mode_overwrites_existing_content(temp_file: Path) -> None:  # CRITICAL TEST
    """
    Test FileTarget in write mode overwrites existing file content.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if existing content is overwritten
    """
    # ARRANGE
    existing_content: str = "Existing line\n"
    new_content: str = "New line\n"
    temp_file.write_text(existing_content)

    # ACT
    target: FileTarget = FileTarget(str(temp_file), mode="w")
    target.write(new_content)
    target.close()
    result: str = temp_file.read_text()

    # ASSERT
    assert result == new_content
    assert existing_content not in result


def test_file_target_handles_utf8_encoding_correctly(temp_file: Path) -> None:
    """
    Test FileTarget handles UTF-8 encoding with special characters.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if UTF-8 characters are preserved
    """
    # ARRANGE
    unicode_text: str = "Test with unicode: äöü ñ 中文 🚀\n"
    target: FileTarget = FileTarget(str(temp_file), mode="w", encoding="utf-8")

    # ACT
    target.write(unicode_text)
    target.close()
    result: str = temp_file.read_text(encoding="utf-8")

    # ASSERT
    assert result == unicode_text


def test_file_target_close_can_be_called_multiple_times(temp_file: Path) -> None:  # CRITICAL TEST
    """
    Test FileTarget.close can be called multiple times safely.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if multiple close calls don't raise exception
    """
    # ARRANGE
    target: FileTarget = FileTarget(str(temp_file), mode="w")
    target.write("test")

    # ACT & ASSERT
    target.close()
    target.close()  # Should not raise exception


def test_file_target_raises_error_when_writing_to_closed_file(temp_file: Path) -> None:  # CRITICAL TEST
    """
    Test FileTarget raises error when writing to closed file.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if ValueError is raised
    """
    # ARRANGE
    target: FileTarget = FileTarget(str(temp_file), mode="w")
    target.close()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="I/O operation on closed file"):
        target.write("test")


@pytest.mark.parametrize("malicious_path", [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "../../outside_project/secrets.txt",
])
def test_file_target_handles_path_traversal_attempts(
    tmp_path: Path,
    malicious_path: str
) -> None:  # CRITICAL TEST
    """
    Test FileTarget behavior with path traversal attempts.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory
    malicious_path : str
        Malicious path pattern to test

    Returns
    -------
    None
        Test passes if path is handled safely

    Notes
    -----
    FileTarget does not validate paths - this is by design.
    Callers must validate paths before passing to FileTarget.
    This test documents current behavior.
    """
    # ARRANGE
    test_path: Path = tmp_path / malicious_path

    # ACT
    # FileTarget will attempt to create the file
    # This may fail or create parent directories depending on OS
    try:
        target: FileTarget = FileTarget(str(test_path), mode="w")
        target.write("test")
        target.close()
        # If successful, file should exist at resolved path
        assert test_path.exists()
    except (FileNotFoundError, PermissionError, OSError):
        # Expected for invalid paths
        pass


def test_file_target_raises_error_when_directory_not_exists(tmp_path: Path) -> None:  # CRITICAL TEST
    """
    Test FileTarget raises error when parent directory doesn't exist.

    Parameters
    ----------
    tmp_path : Path
        Pytest builtin fixture for temporary directory

    Returns
    -------
    None
        Test passes if FileNotFoundError is raised
    """
    # ARRANGE
    nonexistent_dir: Path = tmp_path / "nonexistent" / "directory" / "file.txt"

    # ACT & ASSERT
    with pytest.raises(FileNotFoundError):
        FileTarget(str(nonexistent_dir), mode="w")


@pytest.mark.parametrize("invalid_mode", [
    "invalid",
    "rb",  # binary mode not supported for text
    "wb",
])
def test_file_target_raises_error_for_invalid_mode(
    temp_file: Path,
    invalid_mode: str
) -> None:  # CRITICAL TEST
    """
    Test FileTarget raises error for invalid file modes.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path
    invalid_mode : str
        Invalid file mode to test

    Returns
    -------
    None
        Test passes if ValueError is raised
    """
    # ACT & ASSERT
    with pytest.raises(ValueError):
        FileTarget(str(temp_file), mode=invalid_mode)


def test_file_target_destructor_closes_file_automatically(temp_file: Path) -> None:
    """
    Test FileTarget.__del__ closes file on garbage collection.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if file is closed after garbage collection
    """
    # ARRANGE
    target: FileTarget = FileTarget(str(temp_file), mode="w")
    target.write("test")
    file_handle = target._file

    # ACT
    del target  # Trigger garbage collection

    # ASSERT
    assert file_handle.closed


def test_file_target_flush_persists_data_to_disk(temp_file: Path) -> None:
    """
    Test FileTarget.flush persists data to disk immediately.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if flush makes data immediately readable
    """
    # ARRANGE
    target: FileTarget = FileTarget(str(temp_file), mode="w")

    # ACT
    target.write("buffered content")
    target.flush()

    # ASSERT
    # Data should be readable even while file is still open
    result: str = temp_file.read_text()
    assert result == "buffered content"

    # Cleanup
    target.close()


# -------------------------------------------------------------
# TEST CASES: DatabaseTarget (CRITICAL)
# -------------------------------------------------------------


def test_database_target_creates_table_if_not_exists(mock_db_manager: Mock) -> None:  # CRITICAL TEST
    """
    Test DatabaseTarget creates table if it doesn't exist.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if CREATE TABLE is executed
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")

    # ACT
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )

    # ASSERT
    mock_db.table_exists.assert_called_once_with("test_table")
    mock_db.execute.assert_called_once()
    # Verify CREATE TABLE statement was executed
    call_args = mock_db.execute.call_args[0][0]
    assert "CREATE TABLE" in call_args
    assert "test_table" in call_args


def test_database_target_does_not_create_table_if_exists(mock_db_manager: Mock) -> None:
    """
    Test DatabaseTarget skips table creation if table exists.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if CREATE TABLE is not executed
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    mock_db.table_exists.return_value = True

    # ACT
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="existing_table"
    )

    # ASSERT
    mock_db.table_exists.assert_called_once_with("existing_table")
    mock_db.execute.assert_not_called()


def test_database_target_write_buffers_messages(mock_db_manager: Mock, sample_text: str) -> None:  # CRITICAL TEST
    """
    Test DatabaseTarget.write buffers messages before database flush.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager
    sample_text : str
        Fixture providing sample text

    Returns
    -------
    None
        Test passes if messages are buffered without immediate DB write
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )
    # Reset mock to ignore table creation calls
    mock_db.execute.reset_mock()

    # ACT
    target.write(sample_text)

    # ASSERT
    assert len(target._buffer) == 1
    # No INSERT should be executed yet (only CREATE TABLE in __init__)
    assert mock_db.execute.call_count == 0


def test_database_target_flush_writes_buffered_messages(mock_db_manager: Mock) -> None:  # CRITICAL TEST
    """
    Test DatabaseTarget.flush writes all buffered messages to database.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if all buffered messages are written
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )
    messages: List[str] = ["Message 1\n", "Message 2\n", "Message 3\n"]
    for msg in messages:
        target.write(msg)

    # Reset mock to ignore table creation
    mock_db.execute.reset_mock()

    # ACT
    target.flush()

    # ASSERT
    assert len(target._buffer) == 0
    # Should have executed INSERT for each message
    assert mock_db.execute.call_count == len(messages)


def test_database_target_auto_flushes_when_buffer_full(mock_db_manager: Mock) -> None:  # CRITICAL TEST
    """
    Test DatabaseTarget automatically flushes when buffer reaches batch size.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if auto-flush occurs at batch_size threshold
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )
    target._batch_size = 3  # Set low batch size for testing
    mock_db.execute.reset_mock()

    # ACT
    target.write("Message 1\n")
    target.write("Message 2\n")
    assert len(target._buffer) == 2  # Not flushed yet
    target.write("Message 3\n")  # Should trigger auto-flush

    # ASSERT
    assert len(target._buffer) == 0  # Buffer cleared after auto-flush
    assert mock_db.execute.call_count == 3  # All messages written


def test_database_target_flush_handles_empty_buffer(mock_db_manager: Mock) -> None:
    """
    Test DatabaseTarget.flush handles empty buffer gracefully.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if flush with empty buffer succeeds
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )
    mock_db.execute.reset_mock()

    # ACT & ASSERT
    target.flush()  # Should not raise exception
    assert mock_db.execute.call_count == 0


def test_database_target_close_flushes_remaining_buffer(mock_db_manager: Mock) -> None:  # CRITICAL TEST
    """
    Test DatabaseTarget.close flushes remaining buffered data.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if close() flushes all pending data
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )
    target.write("Pending message\n")
    mock_db.execute.reset_mock()

    # ACT
    target.close()

    # ASSERT
    assert len(target._buffer) == 0
    assert mock_db.execute.call_count == 1


def test_database_target_uses_custom_fields(mock_db_manager: Mock) -> None:  # CRITICAL TEST
    """
    Test DatabaseTarget uses custom field definitions correctly.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if custom fields are used in table creation

    Notes
    -----
    Custom fields allow extending beyond default timestamp/message schema.
    """
    # ARRANGE
    custom_fields: Dict[str, str] = {
        "id": "INTEGER PRIMARY KEY",
        "timestamp": "TIMESTAMP",
        "level": "VARCHAR(10)",
        "message": "TEXT"
    }
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")

    # ACT
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="custom_table",
        fields=custom_fields
    )

    # ASSERT
    call_args = mock_db.execute.call_args[0][0]
    assert "id INTEGER PRIMARY KEY" in call_args
    assert "level VARCHAR(10)" in call_args


def test_database_target_is_thread_safe(mock_db_manager: Mock) -> None:
    """
    Test DatabaseTarget handles concurrent writes safely.

    Parameters
    ----------
    mock_db_manager : Mock
        Fixture providing mocked database manager

    Returns
    -------
    None
        Test passes if concurrent writes don't corrupt buffer

    Notes
    -----
    DatabaseTarget uses threading.Lock to protect buffer operations.
    """
    # ARRANGE
    mock_db = mock_db_manager.get_instance("test_instance").get_database("test_db")
    target: DatabaseTarget = DatabaseTarget(
        db_manager=mock_db_manager,
        instance_name="test_instance",
        db_name="test_db",
        table="test_table"
    )
    target._batch_size = 1000  # Prevent auto-flush during test

    # ACT
    def write_messages(count: int) -> None:
        for i in range(count):
            target.write(f"Message {i}\n")

    threads: List[threading.Thread] = []
    thread_count: int = 10
    messages_per_thread: int = 100

    for _ in range(thread_count):
        thread = threading.Thread(target=write_messages, args=(messages_per_thread,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # ASSERT
    expected_messages: int = thread_count * messages_per_thread
    assert len(target._buffer) == expected_messages


# -------------------------------------------------------------
# TEST CASES: OutputRedirector (IMPORTANT)
# -------------------------------------------------------------


def test_output_redirector_redirects_stdout_to_memory() -> None:  # IMPORTANT TEST
    """
    Test OutputRedirector redirects stdout to MemoryTarget correctly.

    Returns
    -------
    None
        Test passes if stdout is captured in memory target
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target, redirect_stdout=True)
    test_message: str = "Test stdout message"

    # ACT
    redirector.start()
    print(test_message, end="")
    redirector.stop()
    result: str = target.get_buffer()

    # ASSERT
    assert result == test_message


def test_output_redirector_redirects_stderr_to_memory() -> None:  # IMPORTANT TEST
    """
    Test OutputRedirector redirects stderr to MemoryTarget correctly.

    Returns
    -------
    None
        Test passes if stderr is captured in memory target
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target, redirect_stdout=False, redirect_stderr=True)
    test_message: str = "Test stderr message"

    # ACT
    redirector.start()
    print(test_message, file=sys.stderr, end="")
    redirector.stop()
    result: str = target.get_buffer()

    # ASSERT
    assert result == test_message


def test_output_redirector_restores_original_stdout_after_stop() -> None:  # IMPORTANT TEST
    """
    Test OutputRedirector restores original stdout after stop.

    Returns
    -------
    None
        Test passes if sys.stdout is restored to original value
    """
    # ARRANGE
    original_stdout = sys.stdout
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target)

    # ACT
    redirector.start()
    assert sys.stdout != original_stdout
    redirector.stop()

    # ASSERT
    assert sys.stdout == original_stdout


def test_output_redirector_stop_without_start_is_safe() -> None:
    """
    Test OutputRedirector.stop can be called without prior start.

    Returns
    -------
    None
        Test passes if stop without start doesn't raise exception
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target)

    # ACT & ASSERT
    redirector.stop()  # Should not raise exception


def test_output_redirector_start_can_be_called_multiple_times() -> None:
    """
    Test OutputRedirector.start can be called multiple times safely.

    Returns
    -------
    None
        Test passes if multiple start calls don't cause issues

    Notes
    -----
    Second start() call should be no-op if already started.
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target)

    # ACT
    redirector.start()
    redirector.start()  # Second call should be safe

    # ACT & ASSERT
    print("test", end="")
    redirector.stop()
    assert target.get_buffer() == "test"


def test_output_redirector_context_manager_redirects_output() -> None:  # IMPORTANT TEST
    """
    Test OutputRedirector context manager redirects output correctly.

    Returns
    -------
    None
        Test passes if context manager captures output
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    test_message: str = "Context manager test"

    # ACT
    with OutputRedirector(target):
        print(test_message, end="")

    # ASSERT
    assert target.get_buffer() == test_message


def test_output_redirector_context_manager_restores_on_exception() -> None:  # IMPORTANT TEST
    """
    Test OutputRedirector context manager restores stdout on exception.

    Returns
    -------
    None
        Test passes if stdout is restored after exception in context
    """
    # ARRANGE
    original_stdout = sys.stdout
    target: MemoryTarget = MemoryTarget()

    # ACT & ASSERT
    try:
        with OutputRedirector(target):
            raise ValueError("Test exception")
    except ValueError:
        pass

    assert sys.stdout == original_stdout


def test_output_redirector_write_method_writes_directly_to_target() -> None:
    """
    Test OutputRedirector.write writes directly to target.

    Returns
    -------
    None
        Test passes if write method bypasses stream redirection
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target)
    test_message: str = "Direct write test"

    # ACT
    redirector.write(test_message)

    # ASSERT
    assert target.get_buffer() == test_message


def test_output_redirector_flush_flushes_target() -> None:
    """
    Test OutputRedirector.flush calls target flush method.

    Returns
    -------
    None
        Test passes if flush is propagated to target
    """
    # ARRANGE
    mock_target: Mock = Mock(spec=OutputTarget)
    redirector: OutputRedirector = OutputRedirector(mock_target)

    # ACT
    redirector.flush()

    # ASSERT
    mock_target.flush.assert_called_once()


def test_output_redirector_uses_memory_target_by_default() -> None:
    """
    Test OutputRedirector creates MemoryTarget when no target provided.

    Returns
    -------
    None
        Test passes if default target is MemoryTarget
    """
    # ARRANGE & ACT
    redirector: OutputRedirector = OutputRedirector()

    # ASSERT
    assert isinstance(redirector._target, MemoryTarget)


def test_output_redirector_redirects_both_stdout_and_stderr() -> None:
    """
    Test OutputRedirector can redirect both stdout and stderr simultaneously.

    Returns
    -------
    None
        Test passes if both streams are captured
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()
    redirector: OutputRedirector = OutputRedirector(target, redirect_stdout=True, redirect_stderr=True)

    # ACT
    redirector.start()
    print("stdout message", end="")
    print("stderr message", file=sys.stderr, end="")
    redirector.stop()

    # ASSERT
    result: str = target.get_buffer()
    assert "stdout message" in result
    assert "stderr message" in result


# -------------------------------------------------------------
# TEST CASES: _RedirectStream
# -------------------------------------------------------------


def test_redirect_stream_writes_to_target(memory_target: MemoryTarget, sample_text: str) -> None:
    """
    Test _RedirectStream.write forwards text to target.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance
    sample_text : str
        Fixture providing sample text

    Returns
    -------
    None
        Test passes if text is forwarded to target
    """
    # ARRANGE
    stream: _RedirectStream = _RedirectStream(memory_target)

    # ACT
    stream.write(sample_text)

    # ASSERT
    assert memory_target.get_buffer() == sample_text


def test_redirect_stream_ignores_empty_strings(memory_target: MemoryTarget) -> None:
    """
    Test _RedirectStream.write ignores empty strings.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance

    Returns
    -------
    None
        Test passes if empty strings are not written to target
    """
    # ARRANGE
    stream: _RedirectStream = _RedirectStream(memory_target)

    # ACT
    stream.write("")
    stream.write("actual content")

    # ASSERT
    assert memory_target.get_buffer() == "actual content"


def test_redirect_stream_flush_calls_target_flush(memory_target: MemoryTarget) -> None:
    """
    Test _RedirectStream.flush forwards flush to target.

    Parameters
    ----------
    memory_target : MemoryTarget
        Fixture providing memory target instance

    Returns
    -------
    None
        Test passes if flush is forwarded to target
    """
    # ARRANGE
    mock_target: Mock = Mock(spec=OutputTarget)
    stream: _RedirectStream = _RedirectStream(mock_target)

    # ACT
    stream.flush()

    # ASSERT
    mock_target.flush.assert_called_once()


# -------------------------------------------------------------
# TEST CASES: ThreadSafeOutputRedirector (IMPORTANT)
# -------------------------------------------------------------


def test_thread_safe_redirector_creates_separate_targets_per_thread() -> None:  # IMPORTANT TEST
    """
    Test ThreadSafeOutputRedirector creates separate targets for each thread.

    Returns
    -------
    None
        Test passes if each thread has isolated target

    Notes
    -----
    Thread safety is critical to prevent data corruption in concurrent scenarios.
    """
    # ARRANGE
    def target_factory() -> MemoryTarget:
        return MemoryTarget()

    redirector: ThreadSafeOutputRedirector = ThreadSafeOutputRedirector(target_factory)
    results: Dict[int, str] = {}

    def thread_function(thread_id: int, message: str) -> None:
        with redirector:
            print(message, end="")
            # Store result (each thread should have own target)
            results[thread_id] = redirector._get_thread_redirector()._target.get_buffer()

    # ACT
    threads: List[threading.Thread] = []
    thread_messages: Dict[int, str] = {
        0: "Thread 0 message",
        1: "Thread 1 message",
        2: "Thread 2 message",
    }

    for tid, msg in thread_messages.items():
        thread = threading.Thread(target=thread_function, args=(tid, msg))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # ASSERT
    for tid, expected_msg in thread_messages.items():
        assert results[tid] == expected_msg


def test_thread_safe_redirector_cleans_up_thread_resources_on_stop() -> None:
    """
    Test ThreadSafeOutputRedirector cleans up thread-local resources.

    Returns
    -------
    None
        Test passes if thread resources are removed after stop
    """
    # ARRANGE
    def target_factory() -> MemoryTarget:
        return MemoryTarget()

    redirector: ThreadSafeOutputRedirector = ThreadSafeOutputRedirector(target_factory)

    # ACT
    redirector.start()
    thread_id: int = threading.get_ident()
    assert thread_id in redirector._get_thread_redirector()._target.__dict__

    redirector.stop()

    # ASSERT
    # Thread resources should be cleaned up
    # Note: Implementation stores in _thread_local.redirector dict
    from basefunctions.io.output_redirector import _thread_local
    if hasattr(_thread_local, "redirector"):
        assert thread_id not in _thread_local.redirector


# -------------------------------------------------------------
# TEST CASES: redirect_output decorator (IMPORTANT)
# -------------------------------------------------------------


def test_redirect_output_decorator_captures_function_output(temp_file: Path) -> None:  # IMPORTANT TEST
    """
    Test redirect_output decorator captures function output to file.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if function output is redirected to file
    """
    # ARRANGE
    @redirect_output(target=str(temp_file), stdout=True)
    def test_function() -> str:
        print("Function output")
        return "return value"

    # ACT
    result: str = test_function()
    content: str = temp_file.read_text()

    # ASSERT
    assert result == "return value"
    assert "Function output" in content


def test_redirect_output_decorator_with_memory_target() -> None:  # IMPORTANT TEST
    """
    Test redirect_output decorator with MemoryTarget.

    Returns
    -------
    None
        Test passes if output is captured in memory target
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()

    @redirect_output(target=target, stdout=True)
    def test_function() -> None:
        print("Memory output", end="")

    # ACT
    test_function()

    # ASSERT
    assert target.get_buffer() == "Memory output"


def test_redirect_output_decorator_uses_memory_target_when_none() -> None:
    """
    Test redirect_output decorator creates MemoryTarget when target is None.

    Returns
    -------
    None
        Test passes if default MemoryTarget is used
    """
    # ARRANGE
    @redirect_output(target=None, stdout=True)
    def test_function() -> None:
        print("Default target output")

    # ACT & ASSERT (should not raise exception)
    test_function()


def test_redirect_output_decorator_restores_stdout_after_exception() -> None:  # IMPORTANT TEST
    """
    Test redirect_output decorator restores stdout after function exception.

    Returns
    -------
    None
        Test passes if stdout is restored despite exception
    """
    # ARRANGE
    original_stdout = sys.stdout

    @redirect_output(target=MemoryTarget(), stdout=True)
    def failing_function() -> None:
        raise ValueError("Test error")

    # ACT & ASSERT
    try:
        failing_function()
    except ValueError:
        pass

    assert sys.stdout == original_stdout


def test_redirect_output_decorator_preserves_function_metadata() -> None:
    """
    Test redirect_output decorator preserves function name and docstring.

    Returns
    -------
    None
        Test passes if functools.wraps preserves metadata
    """
    # ARRANGE
    @redirect_output(target=MemoryTarget())
    def documented_function() -> None:
        """This function has documentation."""
        pass

    # ASSERT
    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This function has documentation."


def test_redirect_output_decorator_handles_function_arguments() -> None:
    """
    Test redirect_output decorator forwards function arguments correctly.

    Returns
    -------
    None
        Test passes if decorated function receives all arguments
    """
    # ARRANGE
    target: MemoryTarget = MemoryTarget()

    @redirect_output(target=target, stdout=True)
    def function_with_args(a: int, b: str, c: Optional[int] = None) -> str:
        print(f"{a}, {b}, {c}")
        return f"Result: {a + (c or 0)}"

    # ACT
    result: str = function_with_args(10, "test", c=5)

    # ASSERT
    assert result == "Result: 15"
    assert "10, test, 5" in target.get_buffer()


@pytest.mark.parametrize("invalid_target", [
    123,
    ["list"],
    {"dict": "value"},
])
def test_redirect_output_decorator_handles_invalid_target_types(invalid_target: Any) -> None:
    """
    Test redirect_output decorator behavior with invalid target types.

    Parameters
    ----------
    invalid_target : Any
        Invalid target type to test

    Returns
    -------
    None
        Test passes if decorator handles invalid types appropriately
    """
    # ARRANGE
    @redirect_output(target=invalid_target, stdout=True)
    def test_function() -> None:
        print("test")

    # ACT & ASSERT
    # Should raise AttributeError when trying to use invalid target
    with pytest.raises(AttributeError):
        test_function()


def test_redirect_output_decorator_can_redirect_stderr(temp_file: Path) -> None:
    """
    Test redirect_output decorator can redirect stderr instead of stdout.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if stderr is redirected to file
    """
    # ARRANGE
    @redirect_output(target=str(temp_file), stdout=False, stderr=True)
    def test_function() -> None:
        print("This goes to stderr", file=sys.stderr)

    # ACT
    test_function()
    content: str = temp_file.read_text()

    # ASSERT
    assert "This goes to stderr" in content


# -------------------------------------------------------------
# INTEGRATION TESTS
# -------------------------------------------------------------


def test_integration_file_target_with_redirector(temp_file: Path) -> None:
    """
    Integration test: OutputRedirector with FileTarget.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if complete workflow succeeds
    """
    # ARRANGE
    target: FileTarget = FileTarget(str(temp_file), mode="w")
    redirector: OutputRedirector = OutputRedirector(target)

    # ACT
    with redirector:
        print("Line 1")
        print("Line 2")
        print("Line 3")

    target.close()
    result: str = temp_file.read_text()

    # ASSERT
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result


def test_integration_multiple_redirectors_sequential(temp_file: Path) -> None:
    """
    Integration test: Multiple sequential redirections.

    Parameters
    ----------
    temp_file : Path
        Fixture providing temporary file path

    Returns
    -------
    None
        Test passes if sequential redirections work correctly
    """
    # ARRANGE
    target1: MemoryTarget = MemoryTarget()
    target2: MemoryTarget = MemoryTarget()

    # ACT
    with OutputRedirector(target1):
        print("First redirection", end="")

    with OutputRedirector(target2):
        print("Second redirection", end="")

    # ASSERT
    assert target1.get_buffer() == "First redirection"
    assert target2.get_buffer() == "Second redirection"


def test_integration_nested_redirections() -> None:
    """
    Integration test: Nested output redirections.

    Returns
    -------
    None
        Test passes if nested redirections work correctly

    Notes
    -----
    Inner redirection should override outer redirection.
    """
    # ARRANGE
    target1: MemoryTarget = MemoryTarget()
    target2: MemoryTarget = MemoryTarget()

    # ACT
    with OutputRedirector(target1):
        print("Outer start", end="")
        with OutputRedirector(target2):
            print("Inner", end="")
        print("Outer end", end="")

    # ASSERT
    # Inner redirection captures "Inner"
    assert target2.get_buffer() == "Inner"
    # Outer redirection captures "Outer start" and "Outer end"
    assert "Outer start" in target1.get_buffer()
    assert "Outer end" in target1.get_buffer()
    assert "Inner" not in target1.get_buffer()
