"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Timer utilities for timeout handling in the unified task pool
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import ctypes
import threading
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
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class TimerThread:
    """
    Context manager that enforces a timeout on a thread.

    This class creates a timer that will raise a TimeoutError in
    the specified thread if the context hasn't been exited before
    the timeout expires.
    """

    def __init__(self, timeout: int, thread_id: int) -> None:
        """
        Initializes the TimerThread.

        Parameters
        ----------
        timeout : int
            Timeout duration in seconds.
        thread_id : int
            Identifier of the thread to timeout.
        """
        self.timeout = timeout
        self.thread_id = thread_id
        self.timer = threading.Timer(
            interval=self.timeout,
            function=self._timeout_thread,
            args=[],
        )

    def __enter__(self):
        """
        Starts the timer when entering the context.

        Returns
        -------
        TimerThread
            Self reference for context manager
        """
        self.timer.start()
        return self

    def __exit__(self, _type, _value, _traceback):
        """
        Cancels the timer when exiting the context.

        Parameters
        ----------
        _type : type
            Exception type if raised
        _value : Exception
            Exception value if raised
        _traceback : traceback
            Traceback if exception raised

        Returns
        -------
        bool
            False to propagate exceptions
        """
        self.timer.cancel()
        return False

    def _timeout_thread(self):
        """
        Raises a TimeoutError in the target thread.
        """
        basefunctions.get_logger(__name__).error("timeout in thread %d", self.thread_id)
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
