"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Example usage of the threadpool with handlers and Corelet process

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import uuid
import os
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


@basefunctions.thread_handler("task_A")
def task_a(message, **kwargs):
    """
    task a: simulate short processing.
    """
    print(f"[Task A] Received: {message.content}")
    time.sleep(2)
    return True, {"done": "A"}


@basefunctions.thread_handler("task_B")
def task_b(message, **kwargs):
    """
    task b: returns numeric value 2.
    """
    print(f"[Task B] Received: {message.content}")
    time.sleep(1)
    return True, 2


@basefunctions.thread_handler("task_C")
def task_c(message, **kwargs):
    """
    task c: simulate failure.
    """
    print(f"[Task C] Received: {message.content}")
    raise RuntimeError("demo exception")


@basefunctions.debug_task
def main():
    """
    main function to demonstrate threadpool usage.
    """
    pool = basefunctions.ThreadPool(num_of_threads=3)

    # Register the handler classes (not instances)
    pool.register_handler("task_A", task_a, "thread")
    pool.register_handler("task_B", task_b, "thread")
    pool.register_handler("task_C", task_c, "thread")

    # Register corelet handler
    corelet_path = os.path.join(os.path.dirname(__file__), "task_d.py")
    pool.register_handler("task_D", corelet_path, "core")

    # Submit tasks
    pool.submit_task("task_A", content="Payload A")
    pool.submit_task("task_B", content="Payload B")
    pool.submit_task("task_C", content="Payload C")
    pool.submit_task("task_D", content="Calculate sum 1 to 100000", timeout=30)

    print("Waiting for tasks to complete...")
    pool.wait_for_all()

    print("All tasks finished. Collecting results...")
    for result in pool.get_results_from_output_queue():
        print(
            f"Result for {result.message_type} "
            f"(id={result.id}): success={result.success}, data={result.data}, "
            f"retry_counter={result.retry_counter}"
        )

    print("Stopping...")
    pool.stop_threads()


if __name__ == "__main__":
    main()
