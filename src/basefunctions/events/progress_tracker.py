"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Progress tracking system for EventBus with tqdm support

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Optional
import threading
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# LOGGING INITIALIZE
# -------------------------------------------------------------
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class ProgressTracker(ABC):
    """
    Abstract base class for progress tracking in EventBus.

    Provides lifecycle callbacks for event processing:
    - on_event_published: Event enters the system
    - on_event_started: Handler begins processing
    - on_event_completed: Handler finished (success or failure)
    """

    @abstractmethod
    def on_event_published(self, event_id: str, event_type: str) -> None:
        """
        Called when event is published to EventBus.

        Parameters
        ----------
        event_id : str
            Unique event identifier
        event_type : str
            Type of event
        """
        pass

    @abstractmethod
    def on_event_started(self, event_id: str, event_type: str) -> None:
        """
        Called when handler starts processing event.

        Parameters
        ----------
        event_id : str
            Unique event identifier
        event_type : str
            Type of event
        """
        pass

    @abstractmethod
    def on_event_completed(self, event_id: str, event_type: str, success: bool) -> None:
        """
        Called when handler completes event processing.

        Parameters
        ----------
        event_id : str
            Unique event identifier
        event_type : str
            Type of event
        success : bool
            True if processing succeeded, False otherwise
        """
        pass


class NoOpProgressTracker(ProgressTracker):
    """
    Default progress tracker that does nothing.

    Used when no progress tracking is needed.
    Zero overhead implementation.
    """

    def on_event_published(self, event_id: str, event_type: str) -> None:
        pass

    def on_event_started(self, event_id: str, event_type: str) -> None:
        pass

    def on_event_completed(self, event_id: str, event_type: str, success: bool) -> None:
        pass


class TqdmProgressTracker(ProgressTracker):
    """
    Progress tracker using tqdm for console output.

    Displays progress bar with statistics during event processing.
    Thread-safe implementation.
    """

    def __init__(self, total: Optional[int] = None, desc: str = "Processing"):
        """
        Initialize tqdm progress tracker.

        Parameters
        ----------
        total : int, optional
            Expected total number of events. If None, shows counter without percentage.
        desc : str, optional
            Description shown in progress bar. Default is "Processing".
        """
        try:
            import tqdm.auto

            self._tqdm_module = tqdm.auto
        except ImportError:
            raise ImportError("TqdmProgressTracker requires tqdm.\n" "Install with: pip install tqdm")

        self._lock = threading.Lock()
        self._pbar = self._tqdm_module.tqdm(total=total, desc=desc)
        self._started_count = 0
        self._completed_count = 0
        self._success_count = 0
        self._failed_count = 0

    def on_event_published(self, event_id: str, event_type: str) -> None:
        """Update total if not set during init."""
        with self._lock:
            if self._pbar.total is None:
                self._pbar.total = self._pbar.n + 1
                self._pbar.refresh()

    def on_event_started(self, event_id: str, event_type: str) -> None:
        """Track started events."""
        with self._lock:
            self._started_count += 1

    def on_event_completed(self, event_id: str, event_type: str, success: bool) -> None:
        """Update progress bar and statistics."""
        with self._lock:
            self._completed_count += 1
            if success:
                self._success_count += 1
            else:
                self._failed_count += 1

            # Update progress bar
            self._pbar.update(1)

            # Update postfix with statistics
            self._pbar.set_postfix({"success": self._success_count, "failed": self._failed_count})

    def close(self) -> None:
        """Close progress bar."""
        self._pbar.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close on context exit."""
        self.close()
