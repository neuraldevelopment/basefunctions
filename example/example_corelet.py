"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 example corelet handler implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import basefunctions
from typing import Any, Tuple


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
class ExampleCoreletHandler(basefunctions.CoreletHandlerInterface):
    """
    example implementation of a corelet request handler
    """

    def process_request(self, message: basefunctions.UnifiedTaskPoolMessage) -> Tuple[bool, Any]:
        """
        process a corelet request
        """
        basefunctions.get_logger(__name__).info(
            "processing corelet request with message id: %s", message.id
        )

        # get the content data from the message
        data = message.content

        # simulate cpu-intensive work
        result = 0
        for i in range(1000000):
            result += i

        # additional processing specific to the data
        if isinstance(data, dict) and "data" in data:
            processed_data = data["data"].upper()
        else:
            processed_data = "unknown data format"

        # return success and processed data
        return True, {
            "processed_by": "corelet",
            "original_data": data,
            "processed_data": processed_data,
            "calculation_result": result,
            "message_id": message.id,
            "message_type": message.message_type,
        }

    @classmethod
    def get_handler(cls) -> "ExampleCoreletHandler":
        """
        factory method to get an instance of this handler
        """
        return ExampleCoreletHandler()
