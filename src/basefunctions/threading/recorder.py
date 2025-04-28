"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  Recorder class for saving task snapshots, recording task batches,
  and replaying tasks from file for testing and recovery purposes.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import json
import os
from datetime import datetime


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class Recorder:
    """
    Provides functionality to record and replay tasks,
    as well as save debug snapshots for executed tasks.
    """

    def __init__(self, snapshot_folder="task_snapshots"):
        self.snapshot_folder = snapshot_folder
        os.makedirs(self.snapshot_folder, exist_ok=True)

    def save_snapshot(self, message, result):
        """
        Saves a snapshot of a completed task to a JSON file.

        Parameters:
            message (TaskMessage): The original task message.
            result (TaskResult): The result of the task execution.
        """
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        filename = f"{self.snapshot_folder}/{message.msg_type}_{timestamp}.json"
        data = {
            "task_id": message.task_id,
            "msg_type": message.msg_type,
            "content": message.content,
            "result_success": result.success,
            "result_data": result.result,
            "error": result.error,
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"[Recorder] Snapshot saved: {filename}")

    def record_tasks(self, filename, tasks):
        """
        Records a list of tasks to a JSON file.

        Parameters:
            filename (str): The file to write to.
            tasks (list): List of tasks (as dictionaries).
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4)
        print(f"[Recorder] Recorded {len(tasks)} tasks into {filename}")

    def replay_tasks(self, unified_pool, filename):
        """
        Replays recorded tasks from a JSON file into the unified pool.

        Parameters:
            unified_pool (UnifiedTaskPool): The task pool to submit tasks to.
            filename (str): The file containing recorded tasks.
        """
        if not os.path.exists(filename):
            print(f"[Recorder] File {filename} not found")
            return

        with open(filename, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        for task in tasks:
            unified_pool.submit_message(
                task["msg_type"],
                task["content"],
                priority=task.get("priority", 100),
            )
        print(f"[Recorder] Replayed {len(tasks)} tasks from {filename}")
