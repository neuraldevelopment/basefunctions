"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Runner script for executing corelets as standalone processes with file path support
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import importlib
import os
import pickle
import sys
from typing import Any, Dict, Optional, Type
import importlib.util
import basefunctions


# -------------------------------------------------------------
# HANDLER DISCOVERY FUNCTIONS
# -------------------------------------------------------------
def load_module_from_file_path(file_path: str):
    """
    Loads a Python module from a file path.
    """
    abs_path = os.path.abspath(file_path)
    module_name = os.path.basename(abs_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, abs_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from path: {abs_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def find_handler_class(module) -> Optional[Type]:
    """
    Finds a class in the module that implements CoreletHandlerInterface.
    """
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, basefunctions.CoreletHandlerInterface)
            and attr is not basefunctions.CoreletHandlerInterface
        ):
            return attr
    return None


def get_handler_for_message(message) -> basefunctions.CoreletHandlerInterface:
    """
    Central function to find the appropriate handler for a message.
    """
    logger = basefunctions.get_logger(__name__)
    handler_class = None

    # 1. Try to use an explicitly specified corelet path
    if message.corelet_path:
        # Check if it's a module path or file path
        if "." in message.corelet_path and (
            "/" not in message.corelet_path and "\\" not in message.corelet_path
        ):
            # Module path
            try:
                module = importlib.import_module(message.corelet_path)
                handler_class = find_handler_class(module)
                if handler_class:
                    logger.info(f"Loaded handler from module path: {message.corelet_path}")
            except ImportError as e:
                logger.warning(f"Could not import module: {e}")
        else:
            # File path
            # Add .py if necessary
            if not message.corelet_path.endswith(".py"):
                test_path = message.corelet_path + ".py"
                if os.path.exists(test_path):
                    message.corelet_path = test_path

            if os.path.exists(message.corelet_path):
                try:
                    module = load_module_from_file_path(message.corelet_path)
                    handler_class = find_handler_class(module)
                    if handler_class:
                        logger.info(f"Loaded handler from file path: {message.corelet_path}")
                except Exception as e:
                    logger.warning(f"Error loading from file path: {e}")

    # 2. Try standard structure based on message_type
    if not handler_class:
        try:
            module_path = f"basefunctions.processing.{message.message_type}"
            module = importlib.import_module(module_path)
            handler_class = find_handler_class(module)
            if handler_class:
                logger.info(f"Loaded handler from standard module: {module_path}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Standard module not found: {e}")

    # 3. Fallback to default handler
    if not handler_class:
        from basefunctions.default_handler import DefaultCoreletHandler

        handler_class = DefaultCoreletHandler
        logger.info(f"Using default handler for message type {message.message_type}")

    # Instantiate and validate handler
    handler = handler_class.get_handler()
    if not isinstance(handler, basefunctions.CoreletHandlerInterface):
        raise TypeError(
            f"Handler does not implement CoreletHandlerInterface: {type(handler).__name__}"
        )

    return handler


# -------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------
def main() -> None:
    """
    Main entry point for corelet execution.
    """
    logger = basefunctions.get_logger(__name__)
    result = {"success": False, "data": None}

    try:
        # Read serialized message from stdin
        message_data = sys.stdin.buffer.read()
        message = pickle.loads(message_data)

        logger.info(
            f"Corelet process started for message {message.id} (type: {message.message_type})"
        )

        # Find handler and process request
        try:
            handler = get_handler_for_message(message)
            success, data = handler.process_request(message)

            # Prepare result
            result = {
                "success": success,
                "data": data,
                "message_id": message.id,
                "message_type": message.message_type,
            }

            # Log success/failure
            if success:
                logger.info(f"Corelet processing successful for message {message.id}")
            else:
                logger.warning(
                    f"Corelet processing failed for message {message.id}: {str(data) if data else 'Unknown error'}"
                )

        except Exception as e:
            logger.error(f"Error in handler processing: {str(e)}")
            result = {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__,
                "data": None,
                "message_id": message.id if "message" in locals() else None,
                "message_type": message.message_type if "message" in locals() else None,
            }

    except Exception as e:
        logger.error(f"Exception in corelet execution: {str(e)}")
        result = {
            "success": False,
            "error": str(e),
            "exception_type": type(e).__name__,
            "data": None,
        }

    # Send result back via stdout
    try:
        serialized_result = pickle.dumps(result)
        sys.stdout.buffer.write(serialized_result)
        sys.stdout.flush()
    except Exception as e:
        # If result serialization fails, try to send a simple error
        fallback_result = {
            "success": False,
            "error": f"Failed to serialize result: {str(e)}",
            "exception_type": type(e).__name__,
            "data": None,
        }
        sys.stdout.buffer.write(pickle.dumps(fallback_result))
        sys.stdout.flush()

    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
