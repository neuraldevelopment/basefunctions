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
from typing import Any, Dict, Tuple
import importlib.util
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
def load_module_from_file_path(file_path: str):
    """
    Loads a Python module from a file path.

    Args:
        file_path: Absolute or relative path to the Python file

    Returns:
        Loaded module object
    """
    # Konvertiere relativen Pfad in absoluten Pfad
    abs_path = os.path.abspath(file_path)

    module_name = os.path.basename(abs_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from path: {abs_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # Registriere Modul im sys.modules
    spec.loader.exec_module(module)
    return module


def is_module_path(path: str) -> bool:
    """
    Determines if the given path is a module import path or a file path.

    Args:
        path: Path to check

    Returns:
        True if it's a module path, False if it's a file path
    """
    # Einfache Heuristik: Wenn der Pfad mit . oder enthält oder keine / oder \ enthält,
    # behandeln wir ihn als Modul-Import-Pfad
    return "." in path and ("/" not in path and "\\" not in path)


def main() -> None:
    """
    Main entry point for corelet execution.
    Reads serialized message from stdin, processes it,
    and writes serialized result to stdout.
    """
    try:
        # Read serialized message from stdin
        message_data = sys.stdin.buffer.read()
        message = pickle.loads(message_data)

        # Log process start
        basefunctions.get_logger(__name__).info(
            "corelet process started for message %s (type: %s)", message.id, message.message_type
        )

        # Find appropriate handler
        try:
            if message.corelet_path:  # Hier wurde der Name geändert
                if is_module_path(message.corelet_path):  # Und hier
                    # Standard-Python-Import-Pfad
                    handler_module = importlib.import_module(message.corelet_path)  # Und hier
                    handler = handler_module.get_handler()
                    basefunctions.get_logger(__name__).info(
                        "using handler from module path: %s", message.corelet_path  # Und hier
                    )
                else:
                    # Dateipfad (absolut oder relativ)
                    if not os.path.exists(message.corelet_path):  # Und hier
                        # Prüfe, ob die Datei mit .py endet
                        if not message.corelet_path.endswith(".py"):  # Und hier
                            test_path = message.corelet_path + ".py"  # Und hier
                            if os.path.exists(test_path):
                                message.corelet_path = test_path  # Und hier
                            else:
                                raise FileNotFoundError(
                                    f"File not found: {message.corelet_path}"
                                )  # Und hier
                        else:
                            raise FileNotFoundError(
                                f"File not found: {message.corelet_path}"
                            )  # Und hier

                    handler_module = load_module_from_file_path(message.corelet_path)  # Und hier
                    handler = handler_module.get_handler()
                    basefunctions.get_logger(__name__).info(
                        "using handler from file path: %s", message.corelet_path  # Und hier
                    )
            else:
                # Fallback auf Standard-Struktur
                try:
                    # First try to import a dedicated module
                    module_path = f"basefunctions.processing.{message.message_type}"
                    handler_module = importlib.import_module(module_path)
                    handler = handler_module.get_handler()
                    basefunctions.get_logger(__name__).info(
                        "using dedicated handler from %s", module_path
                    )
                except (ImportError, AttributeError):
                    # If not found, try to use a generic handler
                    from basefunctions import default_handler

                    handler = default_handler.get_handler()
                    basefunctions.get_logger(__name__).info(
                        "using default handler for message type %s", message.message_type
                    )
        except Exception as e:
            basefunctions.get_logger(__name__).error("failed to load handler: %s", str(e))
            raise
        # Execute request processing
        success, data = handler.process_request(message.content)

        # Prepare result
        result: Dict[str, Any] = {
            "success": success,
            "data": data,
            "message_id": message.id,
            "message_type": message.message_type,
        }

        # Log success/failure
        if success:
            basefunctions.get_logger(__name__).info(
                "corelet processing successful for message %s", message.id
            )
        else:
            basefunctions.get_logger(__name__).warning(
                "corelet processing failed for message %s: %s",
                message.id,
                str(data) if data else "Unknown error",
            )

    except Exception as e:
        # Handle exceptions
        basefunctions.get_logger(__name__).error("exception in corelet execution: %s", str(e))
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
        sys.exit(1)

    # Exit with appropriate code
    if result.get("success", False):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
