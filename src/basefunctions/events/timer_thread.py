"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Timer thread context manager for enforcing timeouts

  Log:
  v1.0 : Initial implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import ctypes
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
# Enable logging for this module
basefunctions.setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class TimerThread:
    """
    Context manager that enforces a timeout on a thread.

    Raises TimeoutError in the target thread if timeout is exceeded.
    """

    def __init__(self, timeout: int, thread_id: int) -> None:
        """
        Initialize the TimerThread.

        Parameters
        ----------
        timeout : int
            Timeout in seconds
        thread_id : int
            Target thread identifier
        """
        self.timeout = timeout
        self.thread_id = thread_id
        self.timer = threading.Timer(
            interval=self.timeout,
            function=self.timeout_thread,
            args=[],
        )

    def __enter__(self):
        """Start the timer when entering the context."""
        self.timer.start()

    def __exit__(self, _type, _value, _traceback):
        """Cancel the timer when exiting the context."""
        self.timer.cancel()

    def timeout_thread(self):
        """
        Raise a TimeoutError in the target thread.

        WARNING: This method uses PyThreadState_SetAsyncExc which is inherently unsafe
        and should only be used for specialized purposes. It can cause:
        - Deadlocks
        - Inconsistent interpreter state
        - Resource leaks if exception occurs in finally blocks
        - No guarantee the exception will be raised

        Consider using cooperative cancellation or signal-based timeout instead.
        """
        logger = basefunctions.get_logger(__name__)

        result = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )

        # Check result to ensure operation was successful
        if result == 0:
            # Thread ID not found - thread may have already exited
            logger.warning("Failed to raise timeout exception - thread %d not found", self.thread_id)
        elif result == 1:
            # Success - exactly one thread was affected
            logger.error("Timeout raised in thread %d", self.thread_id)
        else:
            # Critical error - multiple threads affected! Must undo the operation
            logger.critical(
                "CRITICAL: Timeout exception affected %d threads! Attempting to undo...",
                result
            )
            # Attempt to undo by clearing the exception
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.thread_id),
                None,
            )
            logger.critical("Exception cleared from affected threads")
