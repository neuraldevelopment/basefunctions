"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Default handler for corelet processing
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
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
class DefaultCoreletHandler(basefunctions.CoreletHandlerInterface):
    """
    Default implementation for handling corelet requests.
    Used when no specific handler is found.
    """

    def process_request(self, message: basefunctions.UnifiedTaskPoolMessage) -> Tuple[bool, Any]:
        """
        Default implementation for processing corelet requests.
        Parameters
        ----------
        data : Any
            Data from the UnifiedTaskPoolMessage
        Returns
        -------
        Tuple[bool, Any]
            Success status and resulting data
        """
        basefunctions.get_logger(__name__).warning(
            "using default corelet handler - no specific implementation found"
        )
        return False, RuntimeError("No specific handler implemented for this message type")

    @classmethod
    def get_handler(cls) -> "DefaultCoreletHandler":
        """
        Factory function to get an instance of the default handler.
        Returns
        -------
        DefaultCoreletHandler
            An instance of the default handler
        """
        return DefaultCoreletHandler()
