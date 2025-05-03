"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Example implementation of a corelet handler
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
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
class ExampleCoreletHandler:
    """
    Example implementation of a corelet request handler.
    This should be placed in basefunctions/corelets/example_core.py
    """

    def process_request(self, data: Any) -> Tuple[bool, Any]:
        """
        Process a corelet request.

        Parameters
        ----------
        data : Any
            Data from the UnifiedTaskPoolMessage

        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data
        """
        basefunctions.get_logger(__name__).info(
            "processing corelet request with data: %s", str(data)
        )

        # Simulate CPU-intensive work
        result = 0
        for i in range(1000000):
            result += i

        # Additional processing specific to the data
        if isinstance(data, dict) and "data" in data:
            processed_data = data["data"].upper()
        else:
            processed_data = "Unknown data format"

        # Return success and processed data
        return True, {
            "processed_by": "corelet",
            "original_data": data,
            "processed_data": processed_data,
            "calculation_result": result,
        }


def get_handler() -> ExampleCoreletHandler:
    """
    Factory function to get an instance of this handler.

    Returns
    -------
    ExampleCoreletHandler
        An instance of the example corelet handler
    """
    return ExampleCoreletHandler()
