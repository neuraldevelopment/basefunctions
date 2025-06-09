"""
=============================================================================

  Licensed Materials, Property of neuraldevelopment , Munich

  Project : basefunctions

  Copyright (c) by neuraldevelopment

  All rights reserved.

  Description:

  Event handler interface for the messaging system with execution modes

 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Tuple, Any, Optional
from datetime import datetime
import subprocess

import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
EXECUTION_MODE_SYNC = "sync"
EXECUTION_MODE_THREAD = "thread"
EXECUTION_MODE_CORELET = "corelet"
EXECUTION_MODE_EXEC = "exec"

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class EventContext:
    """
    Context data for event processing across different execution modes.
    """

    __slots__ = (
        "execution_mode",
        "thread_local_data",
        "thread_id",
        "process_id",
        "timestamp",
        "event_data",
        "worker",
    )

    def __init__(self, execution_mode: str, **kwargs):
        """
        Initialize event context.

        Parameters
        ----------
        execution_mode : str
            The execution mode (sync, thread, corelet).
        **kwargs
            Additional context data specific to execution mode.
        """
        self.execution_mode = execution_mode

        # Thread-specific context
        self.thread_local_data = kwargs.get("thread_local_data")
        self.thread_id = kwargs.get("thread_id")

        # Corelet-specific context
        self.process_id = kwargs.get("process_id")
        self.timestamp = kwargs.get("timestamp", datetime.now())
        self.event_data = kwargs.get("event_data")

        # Worker reference for corelet mode
        self.worker = kwargs.get("worker")


class EventHandler(ABC):
    """
    Interface for event handlers in the messaging system.

    Event handlers are responsible for processing events. They are registered
    with an EventBus to receive and handle specific types of events.
    """

    execution_mode = EXECUTION_MODE_SYNC  # Default execution mode: sync, thread, corelet

    @classmethod
    def get_execution_mode(cls):
        return cls.execution_mode

    @abstractmethod
    def handle(
        self,
        event: "basefunctions.Event",
        context: Optional[EventContext] = None,
        *args,
        **kwargs,
    ) -> Tuple[bool, Any]:
        """
        Handle an event.

        This method is called by the EventBus when an event of the type
        this handler is registered for is published.

        Parameters
        ----------
        event : Event
            The event to handle.
        context : EventContext, optional
            Context data for event processing. None for sync mode,
            contains thread_local_data for thread mode, and process
            info for corelet mode.

        Returns
        -------
        Tuple[bool, Any]
            A tuple containing:
            - bool: Success flag, True for successful execution, False for unsuccessful execution
            - Any: Result data on success, None indicates success with no data

        Raises
        ------
        Exception
            Any exception raised during event processing will be caught and handled by the EventBus
        """
        raise NotImplementedError("Subclasses must implement handle method")


class DefaultExecHandler(EventHandler):
    """
    Default handler for EXEC mode events.
    Executes subprocess commands based on event data.
    """

    execution_mode = EXECUTION_MODE_EXEC

    def handle(self, event: "basefunctions.Event", context: Optional[EventContext] = None) -> Tuple[bool, Any]:
        """
        Execute subprocess command from event data.

        Parameters
        ----------
        event : basefunctions.Event
            Event containing executable, args, and cwd
        context : EventContext, optional
            Execution context (unused for exec mode)

        Returns
        -------
        Tuple[bool, Any]
            Success flag and execution result dictionary
        """
        try:
            # Extract subprocess parameters from event.data
            executable = event.data.get("executable")
            args = event.data.get("args", [])
            cwd = event.data.get("cwd")

            if not executable:
                return False, {
                    "success": False,
                    "stdout": "",
                    "stderr": "Missing executable in event data",
                    "returncode": -1,
                }

            # Build command
            cmd = [executable] + args

            # Execute subprocess
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

            # Build return dict
            exec_result = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

            return True, exec_result

        except subprocess.TimeoutExpired:
            return False, {"success": False, "stdout": "", "stderr": "Process timeout", "returncode": -1}
        except FileNotFoundError:
            return False, {
                "success": False,
                "stdout": "",
                "stderr": f"Executable not found: {executable}",
                "returncode": -2,
            }
        except Exception as e:
            return False, {"success": False, "stdout": "", "stderr": f"Execution error: {str(e)}", "returncode": -3}
