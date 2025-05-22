"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Base class for Corelets with dynamic handler import
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import sys
import pickle
import os
import importlib
import threading
from datetime import datetime

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


class CoreletBase:
    """
    Base class for Corelets that execute event handlers in separate processes.
    """

    def __init__(self, handler_path: str):
        """
        Initialize corelet with dynamic handler import.

        Parameters
        ----------
        handler_path : str
            Import path for handler class (e.g., "user_module.MyHandler").
        """
        self.handler = self._import_handler(handler_path)

    def _import_handler(self, handler_path: str) -> basefunctions.EventHandler:
        """
        Dynamically import and instantiate handler class.

        Parameters
        ----------
        handler_path : str
            Import path for handler class.

        Returns
        -------
        EventHandler
            Instantiated handler object.
        """
        try:
            module_name, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            handler_class = getattr(module, class_name)
            return handler_class()
        except Exception as e:
            basefunctions.get_logger(__name__).error(
                "Failed to import handler %s: %s", handler_path, str(e)
            )
            raise

    def process_event(self):
        """
        Process a single event from stdin and return result to stdout.
        """
        try:
            # Read pickled event from stdin
            basefunctions.get_logger(__name__).info("Corelet waiting for data from stdin")
            data = sys.stdin.buffer.read()
            basefunctions.get_logger(__name__).info(f"Corelet received {len(data)} bytes")

            event = pickle.loads(data)
            basefunctions.get_logger(__name__).info(
                f"Event unpickled: type={getattr(event, 'type', 'UNKNOWN')}, "
                f"has_dataframe={hasattr(event, 'dataframe')}, "
                f"has_current_date={hasattr(event, 'current_date')}"
            )

            # Create context for corelet processing
            context = basefunctions.EventContext(
                execution_mode="corelet",
                process_id=os.getpid(),
                thread_id=threading.get_ident(),
                timestamp=datetime.now(),
            )

            # Process event with handler - exception-based
            result = self.handler.handle(event, context)
            basefunctions.get_logger(__name__).info(f"Handler returned: {result}")
            self._send_response(result)

        except Exception as e:
            basefunctions.get_logger(__name__).error("Exception in corelet process: %s", str(e))
            self._send_response(f"exception: {str(e)}")

    def _send_response(self, data):
        """
        Send response back to parent process.

        Parameters
        ----------
        data : Any
            Result data from processing.
        """
        try:
            result = pickle.dumps(data)
            sys.stdout.buffer.write(result)
            sys.stdout.buffer.flush()
        except Exception as e:
            basefunctions.get_logger(__name__).critical("Failed to send result: %s", str(e))


def main():
    """
    Main entry point for corelet execution.
    """
    if len(sys.argv) != 2:
        print("Usage: python corelet_base.py <handler_path>", file=sys.stderr)
        sys.exit(1)

    handler_path = sys.argv[1]

    try:
        corelet = CoreletBase(handler_path)
        corelet.process_event()
    except Exception as e:
        print(f"Corelet error: {str(e)}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
