"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Event handler interface for the messaging system with execution modes
 Log:
 v1.5 : Added corelet lifecycle management with tracking and monitoring
 v1.4 : Removed ExceptionResult, fixed race conditions
 v1.3 : Added terminate interface for process cleanup
 v1.2 : Centralized subprocess execution with timeout support
 v1.1 : Added file logging support for DefaultCmdHandler
 v1.0 : Initial implementation
=============================================================================
"""

from __future__ import annotations

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Any
from abc import ABC, abstractmethod
from multiprocessing import Process
from multiprocessing.connection import Connection
import subprocess
import pickle
import threading
import multiprocessing
from basefunctions.utils.logging import setup_logger, get_logger
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
setup_logger(__name__)
logger = get_logger(__name__)

# -------------------------------------------------------------
# TYPE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# EXCEPTION DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS OR FUNCTION DEFINITIONS
# -------------------------------------------------------------


class EventResult:
    """
    Unified result container for event processing outcomes.

    EventResult encapsulates the outcome of event processing, supporting both
    successful operations and failures (business errors or technical exceptions).
    It uses a unified structure with separate fields to distinguish between
    business results and technical exceptions.

    Attributes
    ----------
    event_id : str
        Event ID for tracking and correlation
    success : bool
        True for successful operations, False for errors/exceptions
    data : Any
        Result data for success=True or business error data for success=False
    exception : Exception
        Exception object when technical error occurred

    Notes
    -----
    **Result Types:**
    - Business Success: success=True, data=result, exception=None
    - Business Failure: success=False, data=error_info, exception=None
    - Technical Exception: success=False, data=None, exception=Exception

    **Usage Pattern:**
    - Use `business_result()` for normal processing outcomes (success or failure)
    - Use `exception_result()` for technical exceptions (timeouts, crashes, etc.)

    Examples
    --------
    Create successful business result:

    >>> result = EventResult.business_result(
    ...     event_id="abc-123",
    ...     success=True,
    ...     data={"processed": 100, "errors": 0}
    ... )

    Create business failure (validation error):

    >>> result = EventResult.business_result(
    ...     event_id="abc-123",
    ...     success=False,
    ...     data="Invalid input: missing required field 'name'"
    ... )

    Create technical exception result:

    >>> try:
    ...     # ... processing code ...
    ...     pass
    ... except Exception as e:
    ...     result = EventResult.exception_result("abc-123", e)
    """

    __slots__ = ("event_id", "success", "data", "exception")

    def __init__(
        self,
        event_id: str,
        success: bool,
        data: Any = None,
        exception: Exception = None,
    ):
        """
        Initialize event result.

        Parameters
        ----------
        event_id : str
            Event ID for tracking and correlation
        success : bool
            True for successful operations, False for errors/exceptions
        data : Any, optional
            Result data for success=True or business error data for success=False
        exception : Exception, optional
            Exception when technical error occurred
        """
        self.event_id = event_id
        self.success = success
        self.data = data
        self.exception = exception

    @classmethod
    def business_result(
        cls,
        event_id: str,
        success: bool,
        data: Any = None,
        exception: Exception = None,
    ) -> EventResult:
        """
        Create business result (success or error).

        Parameters
        ----------
        event_id : str
            Event ID for tracking
        success : bool
            Success flag
        data : Any, optional
            Business data or error data
        exception : Exception, optional
            Exception information

        Returns
        -------
        EventResult
            Business result instance
        """
        return cls(event_id=event_id, success=success, data=data, exception=exception)

    @classmethod
    def exception_result(cls, event_id: str, exception: Exception) -> EventResult:
        """
        Create exception result.

        Parameters
        ----------
        event_id : str
            Event ID for tracking
        exception : Exception
            The exception that occurred

        Returns
        -------
        EventResult
            Exception result instance
        """
        return cls(event_id=event_id, success=False, exception=exception)

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        data_preview = str(self.data)[:50] + "..." if self.data else "None"
        exception_info = str(self.exception) if self.exception else "None"
        return f"EventResult({self.event_id}, {status}, data={data_preview}, exception={exception_info})"


class EventHandler(ABC):
    """
    Abstract base class for event handlers in the messaging system.

    Event handlers are responsible for processing events of specific types.
    Handlers are registered with the EventFactory and invoked by the EventBus
    when matching events are published. Each handler implements the `handle()`
    method to define event processing logic.

    Handlers can run in different execution contexts (SYNC, THREAD, CORELET)
    and should be stateless to support concurrent execution. Thread-local
    storage is available via EventContext for handler-specific caching.

    Notes
    -----
    **Handler Lifecycle:**
    - Handlers are created once per thread (cached in thread-local storage)
    - Handlers must be thread-safe if used in THREAD mode
    - Handlers in CORELET mode run in isolated processes

    **Best Practices:**
    - Keep handlers stateless (use context for state)
    - Implement idempotent operations when possible
    - Use EventResult.business_result() for expected failures
    - Use EventResult.exception_result() for unexpected errors
    - Override terminate() if handler spawns subprocesses

    **Context Usage:**
    - context.thread_local_data: For thread-specific caching
    - context.process_id: For corelet process identification
    - context.worker: Reference to CoreletWorker (corelet mode only)

    Examples
    --------
    Simple synchronous handler:

    >>> class DataProcessor(EventHandler):
    ...     def handle(self, event, context):
    ...         data = event.event_data
    ...         result = process_data(data)
    ...         return EventResult.business_result(
    ...             event.event_id, True, result
    ...         )

    Handler with caching using thread-local storage:

    >>> class CachedHandler(EventHandler):
    ...     def handle(self, event, context):
    ...         # Use thread-local cache
    ...         if not hasattr(context.thread_local_data, 'cache'):
    ...             context.thread_local_data.cache = {}
    ...
    ...         cache = context.thread_local_data.cache
    ...         key = event.event_data['key']
    ...
    ...         if key not in cache:
    ...             cache[key] = expensive_operation(key)
    ...
    ...         return EventResult.business_result(
    ...             event.event_id, True, cache[key]
    ...         )

    Handler with subprocess that implements terminate:

    >>> class SubprocessHandler(EventHandler):
    ...     def handle(self, event, context):
    ...         # Start subprocess and store reference
    ...         proc = subprocess.Popen(...)
    ...         context.thread_local_data.subprocess = proc
    ...         # ... wait for completion ...
    ...
    ...     def terminate(self, context):
    ...         # Clean up subprocess on timeout
    ...         if hasattr(context.thread_local_data, 'subprocess'):
    ...             proc = context.thread_local_data.subprocess
    ...             proc.terminate()
    """

    @abstractmethod
    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> EventResult:
        """
        Handle an event.

        This method is called by the EventBus when an event of the type
        this handler is registered for is published.

        Parameters
        ----------
        event : Event
            The event to handle.
        context : basefunctions.EventContext
            Context data for event processing. Contains thread_local_data
            for thread mode, and process info for corelet mode.

        Returns
        -------
        EventResult
            Unified result containing success flag, data, and optional exception info.
        """
        return EventResult.exception_result(
            event.event_id,
            NotImplementedError("Subclasses must implement handle method"),
        )

    def terminate(self, context: basefunctions.EventContext) -> None:
        """
        Terminate any running processes managed by this handler.

        This method is called by EventBus when a timeout occurs to clean up
        any subprocess or corelet processes that might still be running.
        Default implementation does nothing - handlers with processes should override.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing process data and thread_local_data
        """
        pass


class DefaultCmdHandler(EventHandler):
    """
    Default handler for CMD mode events with timeout support.
    Executes subprocess commands based on event data.
    """

    def handle(
        self,
        event: basefunctions.Event,
        context: basefunctions.EventContext,
    ) -> EventResult:
        """
        Execute subprocess command from event data with timeout support.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing executable, args, cwd, and optional stdout_file/stderr_file in event_data
        context : basefunctions.EventContext
            Execution context with cmd mode information

        Returns
        -------
        EventResult
            Success flag and execution result dictionary
        """
        try:
            # Extract subprocess parameters from event.event_data
            executable = event.event_data.get("executable")
            args = event.event_data.get("args", [])
            cwd = event.event_data.get("cwd")
            stdout_file = event.event_data.get("stdout_file")
            stderr_file = event.event_data.get("stderr_file")

            if not executable:
                return EventResult.business_result(event.event_id, False, "Missing executable in event data")

            # Build command
            cmd = [executable] + args

            # Initialize file handles outside try block
            stdout_handle = None
            stderr_handle = None

            try:
                # Determine stdout/stderr configuration inside try block for safe cleanup
                if not stdout_file and not stderr_file:
                    stdout = subprocess.PIPE
                    stderr = subprocess.PIPE
                else:
                    # Open file handles safely inside try block
                    if stdout_file:
                        stdout_handle = open(stdout_file, "w")
                        stdout = stdout_handle
                    else:
                        stdout = None

                    if stderr_file:
                        stderr_handle = open(stderr_file, "w")
                        stderr = stderr_handle
                    elif stdout_file:
                        # Use stdout file for stderr if only stdout specified
                        stderr = stdout_handle
                    else:
                        stderr = None

                # Start subprocess with Popen for process tracking
                current_process = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr, text=True)

                # Store process reference in context
                context.thread_local_data.current_subprocess = current_process

                # Wait for completion with timeout
                stdout_data, stderr_data = current_process.communicate(timeout=event.timeout)
                result_returncode = current_process.returncode

                # Build result dictionary
                if stdout_file or stderr_file:
                    cmd_result = {
                        "stdout": stdout_file if stdout_file else "",
                        "stderr": stderr_file if stderr_file else "",
                        "returncode": result_returncode,
                    }
                else:
                    cmd_result = {
                        "stdout": stdout_data or "",
                        "stderr": stderr_data or "",
                        "returncode": result_returncode,
                    }

                # Clean up process reference only on normal completion
                if hasattr(context.thread_local_data, "current_subprocess"):
                    delattr(context.thread_local_data, "current_subprocess")

            finally:
                # Close file handles safely
                if stdout_handle:
                    try:
                        stdout_handle.close()
                    except Exception:
                        pass
                if stderr_handle and stderr_handle != stdout_handle:
                    try:
                        stderr_handle.close()
                    except Exception:
                        pass

            # Shell convention: 0 = success, != 0 = error
            if result_returncode == 0:
                return EventResult.business_result(event.event_id, True, cmd_result)
            else:
                return EventResult.business_result(event.event_id, False, cmd_result)

        except subprocess.TimeoutExpired as e:
            logger.warning(f"Subprocess timeout after {event.timeout}s: {executable}")
            return EventResult.exception_result(event.event_id, e)
        except FileNotFoundError as e:
            logger.error(f"Executable not found: {executable}")
            return EventResult.exception_result(event.event_id, e)
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            return EventResult.exception_result(event.event_id, e)

    def terminate(self, context: basefunctions.EventContext) -> None:
        """
        Terminate the currently running subprocess from context.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing subprocess reference in thread_local_data
        """
        if hasattr(context.thread_local_data, "current_subprocess"):
            current_process = context.thread_local_data.current_subprocess
            if current_process and current_process.poll() is None:
                try:
                    current_process.terminate()
                    # Give process time to terminate gracefully
                    try:
                        current_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Force kill if terminate didn't work
                        current_process.kill()
                        current_process.wait()
                except Exception as e:
                    logger.warning(f"Failed to terminate subprocess: {e}")
                finally:
                    # Clean up process reference after termination
                    delattr(context.thread_local_data, "current_subprocess")


class CoreletHandle:
    """
    Wrapper for corelet process communication via bidirectional pipes.

    CoreletHandle encapsulates the process reference and communication pipes
    for a corelet worker process, providing a simple interface for the EventBus
    to send events and receive results from isolated worker processes.

    Attributes
    ----------
    process : multiprocessing.Process
        The corelet worker process instance
    input_pipe : multiprocessing.Connection
        Pipe for sending pickled events to the corelet
    output_pipe : multiprocessing.Connection
        Pipe for receiving pickled results from the corelet

    Notes
    -----
    - Handles are stored in thread-local storage (one per thread)
    - Communication uses pickle serialization for events and results
    - Pipes must be properly closed to avoid resource leaks
    - Process should be terminated when no longer needed

    See Also
    --------
    CoreletWorker : The worker process implementation
    CoreletForwardingHandler : Handler that manages CoreletHandle lifecycle
    """

    __slots__ = ("process", "input_pipe", "output_pipe")

    def __init__(
        self,
        process: Process,
        input_pipe: Connection,
        output_pipe: Connection,
    ):
        """
        Initialize corelet handle.

        Parameters
        ----------
        process : multiprocessing.Process
            Corelet worker process.
        input_pipe : multiprocessing.Connection
            Pipe for sending events to corelet.
        output_pipe : multiprocessing.Connection
            Pipe for receiving results from corelet.
        """
        self.process = process
        self.input_pipe = input_pipe
        self.output_pipe = output_pipe


class CoreletForwardingHandler(EventHandler):
    """
    Handler for forwarding events to corelet processes via pipe communication.
    Manages corelet lifecycle and communication.

    CORELET LIFECYCLE MANAGEMENT:
    =============================
    This handler implements SESSION-BASED lifecycle with IDLE TIMEOUT for corelet processes.

    LIFECYCLE PHASES:
    ----------------
    1. CREATION: Corelet created on first CORELET event for worker thread
       - One corelet per worker thread (max = num_worker_threads)
       - Process stored in thread_local_data.corelet_handle
       - Registered in EventBus._active_corelets tracking

    2. REUSE: Corelet reused for subsequent events in same thread
       - Reduces process creation overhead
       - Handler cache maintained in corelet process
       - Bidirectional pipe communication

    3. IDLE TIMEOUT: Corelet auto-terminates after 10 minutes idle
       - CoreletWorker monitors activity timestamps
       - Graceful shutdown on timeout
       - Process removed from tracking

    4. EXPLICIT CLEANUP: Corelet terminated on worker thread shutdown
       - EventBus._cleanup_corelet() called on shutdown event
       - Graceful shutdown signal sent to corelet
       - Pipes closed and process terminated
       - Removed from tracking

    PROCESS COUNT MONITORING:
    ------------------------
    - EventBus.get_corelet_count() returns active corelet count
    - EventBus.get_corelet_metrics() provides detailed metrics
    - Expected count: 0 to num_worker_threads
    - Process leaks detected if count exceeds num_worker_threads

    RESOURCE GUARANTEES:
    -------------------
    ✅ No process leaks - All corelets cleaned up on shutdown
    ✅ Bounded memory - Max corelets = worker_threads
    ✅ Idle timeout - Unused corelets auto-cleanup after 10 minutes
    ✅ Process tracking - Full visibility into active corelets
    ✅ Thread-safe - Lock-protected tracking dictionary

    See Also
    --------
    EventBus._cleanup_corelet : Worker thread shutdown cleanup
    EventBus.get_corelet_metrics : Process monitoring API
    CoreletWorker.run : Idle timeout implementation
    """

    def handle(self, event: basefunctions.Event, context: basefunctions.EventContext) -> EventResult:
        """
        Forward event to corelet process for execution.

        Parameters
        ----------
        event : basefunctions.Event
            Event to forward to corelet
        context : basefunctions.EventContext
            Context with thread_local_data for corelet management

        Returns
        -------
        EventResult
            Result from corelet execution
        """
        try:
            # Ensure corelet is running
            corelet_handle = self._get_corelet(context)

            # Send pickled event to corelet via input pipe
            # Corelet worker handles handler registration automatically via corelet_meta
            pickled_event = pickle.dumps(event)
            corelet_handle.input_pipe.send(pickled_event)

            # Wait for result with timeout using poll (non-blocking check)
            if corelet_handle.output_pipe.poll(timeout=event.timeout):
                pickled_result = corelet_handle.output_pipe.recv()
                result = pickle.loads(pickled_result)

                # SESSION-BASED LIFECYCLE: Keep corelet alive for thread session
                # Corelet handle remains in thread_local_data for reuse by subsequent events
                # Cleanup handled by EventBus on thread shutdown via _cleanup_corelet()

                return result
            else:
                # Timeout - cleanup corrupted corelet
                thread_id = threading.get_ident()
                logger.warning(
                    "Corelet timeout after %ds (Thread: %d, PID: %d) - terminating process",
                    event.timeout,
                    thread_id,
                    corelet_handle.process.pid,
                )

                if hasattr(context.thread_local_data, "corelet_handle"):
                    try:
                        # Terminate unresponsive process
                        corelet_handle.process.terminate()

                        # Wait for termination
                        try:
                            corelet_handle.process.join(timeout=2)
                        except Exception:
                            corelet_handle.process.kill()

                        # Close pipes (File Descriptor Leak Fix)
                        try:
                            corelet_handle.input_pipe.close()
                        except Exception:
                            pass
                        try:
                            corelet_handle.output_pipe.close()
                        except Exception:
                            pass

                        # Remove from tracking
                        event_bus = basefunctions.EventBus()
                        with event_bus._corelet_lock:
                            event_bus._active_corelets.pop(thread_id, None)

                        logger.info(
                            "Cleaned up timed-out corelet (Thread: %d, remaining: %d)",
                            thread_id,
                            event_bus.get_corelet_count(),
                        )
                    except Exception as e:
                        logger.error(f"Cleanup failed: {e}")
                    finally:
                        delattr(context.thread_local_data, "corelet_handle")

                raise TimeoutError(f"No response from corelet within {event.timeout} seconds")

        except TimeoutError as e:
            raise e
        except Exception as e:
            return EventResult.exception_result(event.event_id, e)

    def terminate(self, context: basefunctions.EventContext) -> None:
        """
        Terminate corelet process using context data.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing thread_local_data with corelet_handle
        """
        if hasattr(context.thread_local_data, "corelet_handle"):
            corelet_handle = context.thread_local_data.corelet_handle
            thread_id = threading.get_ident()
            try:
                corelet_handle.process.terminate()
                corelet_handle.input_pipe.close()
                corelet_handle.output_pipe.close()

                # Remove from tracking
                event_bus = basefunctions.EventBus()
                with event_bus._corelet_lock:
                    event_bus._active_corelets.pop(thread_id, None)

                logger.info(
                    "Terminated corelet via handler.terminate() (Thread: %d, remaining: %d)",
                    thread_id,
                    event_bus.get_corelet_count(),
                )
            except Exception as e:
                logger.warning(f"Failed to terminate corelet process: {e}")
            finally:
                # Clean up corelet reference after termination
                delattr(context.thread_local_data, "corelet_handle")

    def _stop_all_corelet_processes(self) -> None:
        """
        Stop all corelet processes gracefully.

        This method is called during EventBus shutdown to ensure all
        corelet processes are properly terminated and don't become zombies.
        """
        # Note: This is a placeholder for global cleanup
        # Actual cleanup happens per thread via terminate() method
        # This method exists to provide a hook for future global process tracking
        pass

    def _get_corelet(self, context: basefunctions.EventContext) -> CoreletHandle:
        """
        Get corelet worker is running for current thread.

        Parameters
        ----------
        context : basefunctions.EventContext
            Event context containing thread_local_data

        Returns
        -------
        CoreletHandle
            Corelet handle for process communication
        """
        # Check if corelet already exists for this thread
        if hasattr(context.thread_local_data, "corelet_handle"):
            return context.thread_local_data.corelet_handle

        # Create new corelet worker
        corelet_handle = self._create_corelet_worker()
        context.thread_local_data.corelet_handle = corelet_handle
        return corelet_handle

    def _create_corelet_worker(self) -> CoreletHandle:
        """
        Create a new corelet worker process and register with EventBus.

        Returns
        -------
        CoreletHandle
            New corelet handle for process communication
        """
        # Create pipes for bidirectional communication
        input_pipe_a, input_pipe_b = multiprocessing.Pipe()
        output_pipe_a, output_pipe_b = multiprocessing.Pipe()

        # Create corelet process as daemon
        # daemon=True ensures automatic cleanup when main process exits (safety net),
        # but does NOT auto-cleanup during runtime - explicit lifecycle management required
        thread_id = threading.get_ident()
        process = Process(
            target=basefunctions.worker_main,
            args=(f"corelet_{thread_id}", input_pipe_b, output_pipe_b),
            daemon=True,  # Safety: Auto-terminate on parent process exit
        )
        process.start()

        # Register corelet with EventBus for tracking
        event_bus = basefunctions.EventBus()
        event_bus._register_corelet(thread_id, process.pid)

        logger.info(
            "Created corelet process (Thread: %d, PID: %d, Total: %d)",
            thread_id,
            process.pid,
            event_bus.get_corelet_count(),
        )

        return CoreletHandle(process, input_pipe_a, output_pipe_a)
