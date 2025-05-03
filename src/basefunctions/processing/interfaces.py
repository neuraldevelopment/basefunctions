"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Interface definitions for the unified task pool system
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import queue
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple
from .message_types import UnifiedTaskPoolMessage


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
@dataclass
class TaskContext:
    """
    Context object for passing data to tasklets.

    Attributes
    ----------
    thread_local_data : Any
        Thread-local storage.
    input_queue : queue.Queue
        Input queue for messages.
    thread_id : int
        ID of the executing thread.
    process_id : Optional[int]
        Process ID for corelets.
    process_object : Optional[subprocess.Popen]
        Reference to the subprocess for corelets.
    """

    thread_local_data: Any
    input_queue: queue.Queue
    thread_id: int = field(default_factory=threading.get_ident)
    process_id: Optional[int] = None
    process_object: Optional[subprocess.Popen] = None


class TaskletRequestInterface:
    """
    Interface for processing input messages in the UnifiedTaskPool.

    Implementations must override the process_request method
    to handle specific message types.
    """

    def process_request(
        self, context: TaskContext, message: UnifiedTaskPoolMessage
    ) -> Tuple[bool, Any]:
        """
        Processes an incoming request message.

        Parameters
        ----------
        context : TaskContext
            Context containing thread-local storage and queues.
        message : UnifiedTaskPoolMessage
            Message to process.

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data.
        """
        pass


class CoreletHandlerInterface:
    """
    Interface that all corelet handlers must implement.
    """

    def process_request(self, message: UnifiedTaskPoolMessage) -> Tuple[bool, Any]:
        """
        Process a corelet request.

        Parameters
        ----------
        message : UnifiedTaskPoolMessage
            The complete message to be processed

        Returns
        -------
        Tuple[bool, Any]
            A tuple containing (success_status, result_data)
        """
        pass

    @classmethod
    def get_handler(cls) -> "CoreletHandlerInterface":
        """
        Factory method to get an instance of this handler.

        Returns
        -------
        CoreletHandlerInterface
            An instance of a corelet handler
        """
        pass
