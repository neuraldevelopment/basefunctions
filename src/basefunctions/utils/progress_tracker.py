"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Progress tracking system with step-based interface
 Log:
 v1.0 : Initial implementation
 v2.0 : Complete redesign - step-based interface only
 v3.0 : Migration to alive-progress
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
import threading
from typing import Any

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ProgressTracker(ABC):
    """
    Abstract base class for progress tracking.

    Provides simple step-based progress tracking interface.
    """

    @abstractmethod
    def progress(self, n: int = 1) -> None:
        """
        Advance progress by n steps.

        Parameters
        ----------
        n : int, optional
            Number of steps completed, by default 1
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close progress tracker and cleanup resources."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()


class AliveProgressTracker(ProgressTracker):
    """
    Progress tracker using alive-progress for console output.

    Thread-safe wrapper around alive-progress bar.
    """

    def __init__(self, total: int | None = None, desc: str = "Processing"):
        """
        Initialize alive-progress tracker.

        Parameters
        ----------
        total : int, optional
            Expected total number of steps. If None, shows counter without percentage.
        desc : str, optional
            Description shown in progress bar, by default "Processing"
        """
        try:
            from alive_progress import alive_bar
            self._alive_bar = alive_bar
        except ImportError:
            raise ImportError(
                "AliveProgressTracker requires alive-progress.\n"
                "Install with: pip install alive-progress"
            )

        self._lock = threading.Lock()
        self._total = total
        self._desc = desc
        self._bar: Any = None
        self._context: Any = None
        self._started = False

    def _ensure_started(self) -> None:
        """Start the progress bar if not already started."""
        if not self._started:
            self._context = self._alive_bar(self._total, title=self._desc)
            self._bar = self._context.__enter__()
            self._started = True

    def progress(self, n: int = 1) -> None:
        """
        Update progress bar by n steps.

        Parameters
        ----------
        n : int, optional
            Number of steps completed, by default 1
        """
        with self._lock:
            self._ensure_started()
            if self._bar:
                self._bar(n)

    def close(self) -> None:
        """Close progress bar."""
        with self._lock:
            if self._started and self._context:
                try:
                    self._context.__exit__(None, None, None)
                except (ImportError, AttributeError):
                    # Ignore errors during Python shutdown
                    pass
                finally:
                    self._started = False
                    self._bar = None
                    self._context = None

    def __enter__(self):
        """Context manager entry - starts the progress bar."""
        with self._lock:
            self._ensure_started()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
