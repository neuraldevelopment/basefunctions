"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Timer thread context manager for enforcing timeouts

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import ctypes
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

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
        """Raise a TimeoutError in the target thread."""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
        basefunctions.get_logger(__name__).error("Timeout in thread %d", self.thread_id)
