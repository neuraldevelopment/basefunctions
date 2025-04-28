"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Inspector class for live status reporting of the UnifiedTaskPool,
  including thread, process, queue and scheduled task monitoring.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import threading
import time


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class Inspector:
    """
    Provides live monitoring and status inspection of the UnifiedTaskPool.
    """

    def __init__(self, unified_pool):
        self.unified_pool = unified_pool
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)

    def start(self):
        """
        Starts the inspector thread.
        """
        self.thread.start()

    def _worker(self):
        """
        Inspector worker thread that periodically prints pool status.
        """
        while self.running:
            print("\n[Inspector] Unified Task Pool Status:")
            print("---------------------------------------")
            print(f"Threads: {len(self.unified_pool.thread_pool.threads)}")
            print(f"ThreadQueue size: {self.unified_pool.thread_pool.input_queue.qsize()}")
            print(f"Processes: {len(self.unified_pool.process_pool.processes)}")
            print(f"Scheduled tasks: {len(self.unified_pool.scheduler.scheduled_tasks)}")
            print(f"Registered handlers: {list(self.unified_pool.handler_registry.keys())}")
            print("---------------------------------------\n")
            time.sleep(5)

    def stop(self):
        """
        Stops the inspector thread gracefully.
        """
        self.running = False
        self.thread.join()
