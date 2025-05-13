"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 implementation of output redirection for print statements

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import io
import threading
import functools
from abc import ABC, abstractmethod
from typing import TextIO, Any, Dict, Optional, Type, Union, List, Callable, TypeVar, cast
from datetime import datetime

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------
__all__ = ["OutputRedirector", "FileTarget", "DatabaseTarget", "MemoryTarget", "redirect_output"]

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
F = TypeVar("F", bound=Callable[..., Any])

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------
_thread_local = threading.local()


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class OutputTarget(ABC):
    """Abstract base class for different output targets."""

    @abstractmethod
    def write(self, text: str) -> None:
        """Write text to the target."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush the buffer."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the target."""
        pass


class OutputRedirector:
    """Class for redirecting print statements to different output targets."""

    def __init__(self, target: Optional[OutputTarget] = None, **kwargs: Any) -> None:
        """Initialize the redirector with a target.

        Args:
            target: the output target, if None a MemoryTarget will be created
            **kwargs: additional parameters for target configuration
        """
        self._target = target or MemoryTarget()
        self._original_stdout = None
        self._original_stderr = None
        self._redirect_stdout = kwargs.get("redirect_stdout", True)
        self._redirect_stderr = kwargs.get("redirect_stderr", False)
        self._stream = _RedirectStream(self._target)

    def start(self) -> None:
        """Start redirecting stdout/stderr."""
        if self._redirect_stdout and self._original_stdout is None:
            self._original_stdout = sys.stdout
            sys.stdout = self._stream

        if self._redirect_stderr and self._original_stderr is None:
            self._original_stderr = sys.stderr
            sys.stderr = self._stream

    def stop(self) -> None:
        """Stop redirecting and restore original streams."""
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
            self._original_stdout = None

        if self._original_stderr is not None:
            sys.stderr = self._original_stderr
            self._original_stderr = None

        self._stream.flush()

    def write(self, text: str) -> None:
        """Write text directly to the target.

        Args:
            text: the text to write
        """
        self._target.write(text)

    def flush(self) -> None:
        """Flush the buffer."""
        self._target.flush()

    def __enter__(self) -> "OutputRedirector":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit."""
        self.stop()


class _RedirectStream:
    """Internal class that mimics a file-like object."""

    def __init__(self, target: OutputTarget) -> None:
        """Initialize with an output target.

        Args:
            target: the output target to write to
        """
        self._target = target

    def write(self, text: str) -> None:
        """Write text to the target.

        Args:
            text: the text to write
        """
        if text:  # Don't write empty strings
            self._target.write(text)

    def flush(self) -> None:
        """Flush the buffer."""
        self._target.flush()


class FileTarget(OutputTarget):
    """Target for writing to a file."""

    def __init__(self, filename: str, mode: str = "a", encoding: str = "utf-8") -> None:
        """Initialize the file target.

        Args:
            filename: path to the output file
            mode: opening mode ('a' for append, 'w' for overwrite)
            encoding: file encoding
        """
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._file = open(filename, mode, encoding=encoding)

    def write(self, text: str) -> None:
        """Write text to the file."""
        self._file.write(text)

    def flush(self) -> None:
        """Flush the file buffer."""
        self._file.flush()

    def close(self) -> None:
        """Close the file."""
        self._file.close()


class DatabaseTarget(OutputTarget):
    """Target for writing to a database."""

    def __init__(
        self, connection: Any, table: str, fields: Optional[Dict[str, str]] = None
    ) -> None:
        """Initialize the database target.

        Args:
            connection: the database connection
            table: target table
            fields: dictionary with field names and data types
        """
        self._connection = connection
        self._table = table
        self._fields = fields or {"timestamp": "TIMESTAMP", "message": "TEXT"}
        self._buffer = []
        self._lock = threading.Lock()
        self._batch_size = 100

        # Create table if it doesn't exist
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure the target table exists in the database."""
        cursor = self._connection.cursor()

        # Generate field definitions
        field_defs = ", ".join([f"{field} {dtype}" for field, dtype in self._fields.items()])

        # Create table if not exists
        create_sql = f"CREATE TABLE IF NOT EXISTS {self._table} ({field_defs})"
        cursor.execute(create_sql)
        self._connection.commit()

    def write(self, text: str) -> None:
        """Write text to the database."""
        with self._lock:
            timestamp = datetime.now()
            self._buffer.append((timestamp, text))

            # If buffer reaches batch size, flush it
            if len(self._buffer) >= self._batch_size:
                self.flush()

    def flush(self) -> None:
        """Commit pending transactions."""
        with self._lock:
            if not self._buffer:
                return

            cursor = self._connection.cursor()

            # Prepare placeholders for the SQL query
            placeholders = ", ".join(["?"] * len(self._fields))

            # Prepare field names
            field_names = ", ".join(self._fields.keys())

            # Insert SQL
            insert_sql = f"INSERT INTO {self._table} ({field_names}) VALUES ({placeholders})"

            # For each buffered message
            for timestamp, message in self._buffer:
                # Create values tuple based on field order
                values = []
                for field in self._fields.keys():
                    if field == "timestamp":
                        values.append(timestamp)
                    elif field == "message":
                        values.append(message)
                    else:
                        values.append(None)  # Default for other fields

                cursor.execute(insert_sql, tuple(values))

            self._connection.commit()
            self._buffer.clear()

    def close(self) -> None:
        """Close the database connection."""
        self.flush()
        # Don't close the connection as it might be used elsewhere
        # Just ensure all data is committed


class MemoryTarget(OutputTarget):
    """Target for storing in memory."""

    def __init__(self) -> None:
        """Initialize the memory buffer."""
        self._buffer = io.StringIO()

    def write(self, text: str) -> None:
        """Write text to memory."""
        self._buffer.write(text)

    def flush(self) -> None:
        """Dummy method for consistency."""
        pass

    def close(self) -> None:
        """Clear the memory."""
        value = self._buffer.getvalue()
        self._buffer.close()
        self._buffer = io.StringIO()
        return value

    def get_buffer(self) -> str:
        """Get the stored text."""
        return self._buffer.getvalue()


class ThreadSafeOutputRedirector(OutputRedirector):
    """Thread-safe version of OutputRedirector."""

    def __init__(self, target_factory, **kwargs):
        """Initialize with a target factory function.

        Args:
            target_factory: function that creates a new target for each thread
            **kwargs: additional parameters
        """
        self._target_factory = target_factory
        self._kwargs = kwargs
        self._lock = threading.Lock()

        # Store original streams
        self._original_stdout = None
        self._original_stderr = None
        self._redirect_stdout = kwargs.get("redirect_stdout", True)
        self._redirect_stderr = kwargs.get("redirect_stderr", False)

        # Initialize the thread local storage
        if not hasattr(_thread_local, "redirector"):
            _thread_local.redirector = {}

    def _get_thread_redirector(self):
        """Get or create a redirector for the current thread."""
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id not in _thread_local.redirector:
                # Create new target and redirector for this thread
                target = self._target_factory()
                _thread_local.redirector[thread_id] = OutputRedirector(
                    target,
                    redirect_stdout=self._redirect_stdout,
                    redirect_stderr=self._redirect_stderr,
                )

            return _thread_local.redirector[thread_id]

    def start(self) -> None:
        """Start redirecting for the current thread."""
        self._get_thread_redirector().start()

    def stop(self) -> None:
        """Stop redirecting for the current thread."""
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id in _thread_local.redirector:
                _thread_local.redirector[thread_id].stop()
                del _thread_local.redirector[thread_id]

    def write(self, text: str) -> None:
        """Write text directly to the target for the current thread."""
        self._get_thread_redirector().write(text)

    def flush(self) -> None:
        """Flush the buffer for the current thread."""
        self._get_thread_redirector().flush()


def redirect_output(
    target: Optional[Union[OutputTarget, str]] = None, stdout: bool = True, stderr: bool = False
) -> Callable[[F], F]:
    """Decorator to redirect output from functions.

    Args:
        target: output target or filename for redirection (creates FileTarget if string)
        stdout: whether to redirect stdout
        stderr: whether to redirect stderr

    Returns:
        decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # determine target based on input
            actual_target = None
            if target is not None:
                if isinstance(target, str):
                    # if target is a string, assume it's a filename
                    actual_target = FileTarget(target)
                else:
                    # otherwise use as-is
                    actual_target = target

            # create redirector
            redirector = OutputRedirector(
                target=actual_target, redirect_stdout=stdout, redirect_stderr=stderr
            )

            # execute function with redirection
            with redirector:
                return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
