"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Example of a Corelet implementation that calculates sum from 1 to 100000

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
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
class TaskD(basefunctions.CoreletBase):
    def process_request(self, context, message):
        """
        task d: calculate sum from 1 to 100000.
        """
        print(f"[Task D] Received: {message.content}")
        start_time = time.time()

        # Perform calculation
        total_sum = sum(range(1, 100001))
        end_time = time.time()
        execution_time = end_time - start_time

        # Return result with timing information
        return True, {"sum": total_sum, "calculation_time": execution_time}


if __name__ == "__main__":
    # This will be executed when run as a script by the ThreadPool
    TaskD().main()
