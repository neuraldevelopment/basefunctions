"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Timer thread for enforcing execution timeouts in the thread pool

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import ctypes
import threading
from typing import Optional
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

    This class acts as a context manager that monitors the execution
    time of a thread and raises a TimeoutError if it exceeds the
    specified timeout.
    """

    __slots__ = ("timeout", "thread_id", "timer")

    def __init__(self, timeout: int, thread_id: int) -> None:
        """
        Initialize a timer thread.

        Parameters
        ----------
        timeout : int
            Timeout in seconds
        thread_id : int
            ID of the thread to monitor
        """
        self.timeout: int = timeout
        self.thread_id: int = thread_id
        self.timer: Optional[threading.Thread] = threading.Timer(
            interval=self.timeout,
            function=self.timeout_thread,
            args=[],
        )

    def __enter__(self):
        """
        Start the timer when entering the context.

        Returns
        -------
        TimerThread
            This timer thread instance
        """
        self.timer.start()
        return self

    def __exit__(self, _type, _value, _traceback):
        """
        Cancel the timer when exiting the context.

        Parameters
        ----------
        _type : type
            Exception type
        _value : Exception
            Exception value
        _traceback : traceback
            Exception traceback
        """
        self.timer.cancel()

    def timeout_thread(self):
        """
        Raise a TimeoutError in the target thread.

        This method uses the Python C API to asynchronously raise
        a TimeoutError exception in the monitored thread.
        """
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )
        basefunctions.get_logger(__name__).error("Timeout in thread %d", self.thread_id)
