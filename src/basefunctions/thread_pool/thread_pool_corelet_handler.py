"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Corelet handler for process-based thread pool task execution

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import os
import pickle
import subprocess
import threading
from typing import Dict
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


class ThreadPoolCoreletHandler(basefunctions.EventHandler):
    """
    Event handler for executing corelet-based tasks in separate processes.

    This handler processes ThreadPoolTaskEvents by launching separate Python
    processes and communicating with them via pipes.
    """

    __slots__ = ("_corelet_registry", "_logger")

    def __init__(self):
        """
        Initialize a new thread pool corelet handler.
        """
        self._corelet_registry: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)

    def register_corelet_handler(self, task_type: str, corelet_path: str) -> None:
        """
        Register a corelet handler for a specific task type.

        Parameters
        ----------
        task_type : str
            The type of tasks this corelet can process
        corelet_path : str
            Path to the corelet Python file

        Raises
        ------
        FileNotFoundError
            If the corelet file does not exist
        """
        if not os.path.exists(corelet_path):
            raise FileNotFoundError(f"Corelet file not found: {corelet_path}")

        self._corelet_registry[task_type] = corelet_path
        self._logger.info(
            f"Registered corelet handler at '{corelet_path}' for task type '{task_type}'"
        )

    def handle(self, event: basefunctions.Event) -> None:
        """
        Handle a task request event by launching a corelet process.

        Parameters
        ----------
        event : basefunctions.Event
            The event to handle (should be a ThreadPoolTaskEvent)
        """
        if not isinstance(event, basefunctions.ThreadPoolTaskEvent):
            return

        task_type = event.task_type
        thread_id = threading.get_ident()

        # Determine corelet path (from event or registry)
        corelet_path = event.corelet_filename
        if not corelet_path and task_type in self._corelet_registry:
            corelet_path = self._corelet_registry[task_type]

        if not corelet_path:
            self._logger.error(f"No corelet handler registered for task type: {task_type}")

            # Create error result
            result = basefunctions.ThreadPoolResultEvent(
                original_task=event,
                success=False,
                error=f"No corelet handler registered for task type: {task_type}",
            )

            # Publish result
            basefunctions.get_event_bus().publish(result)
            return

        # Verify corelet exists
        if not os.path.exists(corelet_path):
            self._logger.error(f"Corelet file not found: {corelet_path}")

            # Create error result
            result = basefunctions.ThreadPoolResultEvent(
                original_task=event, success=False, error=f"Corelet file not found: {corelet_path}"
            )

            # Publish result
            basefunctions.get_event_bus().publish(result)
            return

        # Initialize result variables
        success = False
        result_data = None
        error = None
        exception_type = None
        exception = None
        process = None

        # Process with retry
        for attempt in range(event.retry_max):
            # Update retry count
            event.increment_retry()

            try:
                # Create thread pool message for backward compatibility
                message = basefunctions.ThreadPoolMessage(
                    id=event.task_id,
                    message_type=event.task_type,
                    content=event.content,
                    retry=event.retry_count,
                    retry_max=event.retry_max,
                    timeout=event.timeout,
                    corelet_filename=corelet_path,
                )

                # Prepare message data
                message_data = pickle.dumps(message)

                # Create subprocess with pipes for communication
                process = subprocess.Popen(
                    ["python", corelet_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                # Create timer for timeout enforcement
                timer = threading.Timer(
                    interval=event.timeout,
                    function=lambda p: p.kill() if p.poll() is None else None,
                    args=[process],
                )

                # Start timeout timer
                timer.start()

                try:
                    # Send message data to subprocess
                    process.stdin.write(message_data)
                    process.stdin.flush()
                    process.stdin.close()

                    # Read result from stdout
                    result_data_bytes = process.stdout.read()

                    # Wait for process to complete
                    return_code = process.wait()

                    # Check process exit code
                    if return_code != 0:
                        error_output = process.stderr.read()
                        self._logger.error(
                            f"Corelet process exited with code {return_code}: {error_output}"
                        )
                        success = False
                        result_data = None
                        error = f"Corelet process failed with exit code {return_code}"
                        continue  # Try next attempt

                    # Check if we got a result
                    if result_data_bytes:
                        result_obj = pickle.loads(result_data_bytes)
                        success = result_obj.success
                        result_data = result_obj.data
                    else:
                        success = False
                        result_data = None
                        error = "No result received from corelet process"
                        continue  # Try next attempt

                finally:
                    # Cancel timeout timer
                    timer.cancel()

                    # Ensure process is terminated
                    if process and process.poll() is None:
                        process.kill()

                # If successful, break the retry loop
                if success:
                    break

            except Exception as e:
                success = False
                result_data = None
                error = str(e)
                exception_type = type(e).__name__
                exception = e
                self._logger.error(
                    f"Error processing corelet task {event.task_id} (attempt {attempt+1}/{event.retry_max}): {error}"
                )

                # Ensure process is terminated if it exists
                if process and process.poll() is None:
                    process.kill()

            # If we're not retrying or max retries reached, break
            if success or attempt >= event.retry_max - 1:
                break

            self._logger.info(
                f"Retrying corelet task {event.task_id} ({attempt+1}/{event.retry_max})"
            )

        # Create result
        result = basefunctions.ThreadPoolResultEvent(
            original_task=event,
            success=success,
            data=result_data,
            error=error,
            exception_type=exception_type,
            exception=exception,
        )

        # Publish result
        basefunctions.get_event_bus().publish(result)

    def can_handle(self, event: basefunctions.Event) -> bool:
        """
        Check if this handler can handle the given event.

        Parameters
        ----------
        event : basefunctions.Event
            The event to check

        Returns
        -------
        bool
            True if this handler can handle the event, False otherwise
        """
        if not isinstance(event, basefunctions.ThreadPoolTaskEvent):
            return False

        # Can handle if it has a corelet filename
        if event.is_corelet_task():
            return True

        # Can handle if task type is in registry
        return event.task_type in self._corelet_registry

    def get_priority(self) -> int:
        """
        Get the priority of this handler.

        Returns
        -------
        int
            The priority of this handler (higher is executed first)
        """
        return 50  # Medium priority for corelet handler
