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
from basefunctions.utils.logging import setup_logger, get_logger

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
setup_logger(__name__)

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class TimerThread:
    """
    Context manager that enforces execution timeout by raising TimeoutError in target thread.

    TimerThread implements a timeout mechanism using Python's ctypes and
    PyThreadState_SetAsyncExc to asynchronously raise TimeoutError in a
    target thread after a specified duration. It is designed to enforce
    time limits on event handler execution in the EventBus system.

    WARNING: This implementation uses PyThreadState_SetAsyncExc which is
    inherently unsafe and can cause deadlocks, resource leaks, and
    inconsistent interpreter state. Use with caution.

    Attributes
    ----------
    timeout : int
        Timeout duration in seconds
    thread_id : int
        Target thread identifier (from threading.get_ident())
    timer : threading.Timer
        Internal timer that triggers timeout_thread() after timeout seconds

    Notes
    -----
    **Safety Considerations:**
    - Uses PyThreadState_SetAsyncExc (unsafe, can corrupt interpreter state)
    - Can cause deadlocks if exception raised during lock acquisition
    - May leak resources if exception raised in finally blocks
    - No guarantee the exception will be raised successfully
    - Only affects Python code (C extensions may not be interrupted)

    **Usage Pattern:**
    - Used internally by EventBus for timeout enforcement
    - Automatically cancelled if execution completes before timeout
    - Timeout occurs in background timer thread, not target thread

    **Alternative Approaches:**
    Consider safer alternatives for production use:
    - Cooperative cancellation with threading.Event
    - Signal-based timeout (SIGALRM on Unix)
    - subprocess.run() with timeout parameter
    - concurrent.futures with timeout

    Examples
    --------
    Basic timeout enforcement:

    >>> def long_running_task():
    ...     time.sleep(10)
    ...
    >>> with TimerThread(timeout=5, thread_id=threading.get_ident()):
    ...     long_running_task()  # Raises TimeoutError after 5 seconds

    Handling timeout gracefully:

    >>> try:
    ...     with TimerThread(timeout=2, thread_id=threading.get_ident()):
    ...         # Critical operation with time limit
    ...         result = expensive_computation()
    ... except TimeoutError:
    ...     result = None  # Timeout occurred
    ...     logger.warning("Operation timed out")

    See Also
    --------
    EventBus._retry_with_timeout : Uses TimerThread for event timeout
    threading.Timer : Internal timer implementation
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

    def __enter__(self) -> "TimerThread":
        """
        Start the timer when entering the context.

        Returns
        -------
        TimerThread
            Self reference for context manager protocol
        """
        self.timer.start()
        return self

    def __exit__(self, _type: type | None, _value: Exception | None, _traceback: object | None) -> bool:
        """
        Cancel the timer when exiting the context.

        Parameters
        ----------
        _type : type
            Exception type (if raised)
        _value : Exception
            Exception value (if raised)
        _traceback : traceback
            Exception traceback (if raised)

        Returns
        -------
        bool
            False (does not suppress exceptions)
        """
        self.timer.cancel()
        return False

    def timeout_thread(self) -> None:
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
        logger = get_logger(__name__)

        # Asynchronously raise TimeoutError in target thread using ctypes
        # This is UNSAFE and may cause interpreter corruption
        result = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.thread_id),
            ctypes.py_object(TimeoutError),
        )

        # Check result to ensure operation was successful
        # Return values: 0 = thread not found, 1 = success, >1 = critical error
        if result == 0:
            # Thread ID not found - thread may have already exited
            logger.warning(
                "Failed to raise timeout exception - thread %d not found",
                self.thread_id,
            )
        elif result == 1:
            # Success - exactly one thread was affected
            logger.error("Timeout raised in thread %d", self.thread_id)
        else:
            # Critical error - multiple threads affected! Must undo the operation immediately
            # This should never happen but indicates serious API misuse
            logger.critical(
                "CRITICAL: Timeout exception affected %d threads! Attempting to undo...",
                result,
            )
            # Attempt to undo by clearing the exception from all affected threads
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.thread_id),
                None,
            )
            logger.critical("Exception cleared from affected threads")
