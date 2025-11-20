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
 v3.0 : Moved to basefunctions.cli package
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
import threading

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
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
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
        n : int
            Number of steps completed
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


class TqdmProgressTracker(ProgressTracker):
    """
    Progress tracker using tqdm for console output.

    Thread-safe wrapper around tqdm progress bar.
    """

    def __init__(self, total: int | None = None, desc: str = "Processing"):
        """
        Initialize tqdm progress tracker.

        Parameters
        ----------
        total : Optional[int]
            Expected total number of steps
        desc : str
            Description shown in progress bar
        """
        try:
            import tqdm.auto

            self._tqdm_module = tqdm.auto
        except ImportError:
            raise ImportError("TqdmProgressTracker requires tqdm. Install with: pip install tqdm")

        self._lock = threading.Lock()
        self._pbar = self._tqdm_module.tqdm(total=total, desc=desc)

    def progress(self, n: int = 1) -> None:
        """
        Update progress bar by n steps.

        Parameters
        ----------
        n : int
            Number of steps completed
        """
        with self._lock:
            self._pbar.update(n)

    def close(self) -> None:
        """Close progress bar."""
        self._pbar.close()
