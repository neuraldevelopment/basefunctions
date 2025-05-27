"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Base class for Corelets - process-based execution in ThreadPool

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import pickle
import sys
from typing import Any, Tuple
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


class CoreletBase(basefunctions.ThreadPoolRequestInterface):
    """
    Base class for Corelets that can be executed in separate processes.
    """

    def process_request(self, context: Any, message: Any) -> Tuple[bool, Any]:
        """
        Processes an incoming request message. To be overridden by subclasses.

        Parameters
        ----------
        context : ThreadPoolContext
            Context object with execution-specific data.
        message : ThreadPoolMessage
            Message to process.

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data.
        """
        return False, RuntimeError("process_request() not implemented")

    def start(self):
        """
        Initializes corelet processing by reading input from stdin.

        Returns
        -------
        Tuple[Any, Any]
            Context and message objects for processing.
        """
        try:
            # read serialized message from stdin
            message_data = sys.stdin.buffer.read()
            message = pickle.loads(message_data)

            # create empty context for process
            context = basefunctions.ThreadPoolContext(
                process_info={"pid": os.getpid(), "argv": sys.argv}
            )

            return context, message

        except Exception as e:
            # handle errors
            basefunctions.get_logger(__name__).error("exception in corelet process: %s", str(e))
            return None, None

    def stop(self, success, data, message):
        """
        Finalizes corelet processing by sending result through stdout.

        Parameters
        ----------
        success : bool
            Success status of processing.
        data : Any
            Result data from processing.
        message : ThreadPoolMessage
            Original message that was processed.
        """
        try:
            # create result
            result = basefunctions.ThreadPoolResult(
                message_type=message.message_type if message else "unknown",
                id=message.id if message else "unknown",
                success=success,
                data=data,
                original_message=message,
            )

            # send result back through stdout
            sys.stdout.buffer.write(pickle.dumps(result))
            sys.stdout.buffer.flush()

        except Exception as e:
            # handle errors
            basefunctions.get_logger(__name__).critical("failed to send result: %s", str(e))

        # ensure process exits
        sys.exit(0)

    def main(self):
        """
        Main entry point for running a corelet process.
        Handles the entire request processing lifecycle.
        """
        # start processing
        context, message = self.start()

        # process the request
        success, data = self.process_request(context, message)

        # stop processing
        self.stop(success, data, message)
