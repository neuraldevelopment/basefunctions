"""
=============================================================================

  Licensed Materials, Property of Ralph Vogl, Munich

  Project : unified_task_pool

  Copyright (c) by Ralph Vogl

  All rights reserved.

  Description:

  TaskLoader class for loading tasks from YAML or JSON files
  into the unified task execution system.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import yaml
import json
import os


# -------------------------------------------------------------
# CLASS DEFINITIONS
# -------------------------------------------------------------


class TaskLoader:
    """
    Loads tasks from YAML or JSON files into the unified pool.
    """

    def __init__(self, unified_pool):
        self.unified_pool = unified_pool

    def load_from_yaml(self, filename):
        """
        Loads tasks from a YAML file and submits them to the pool.

        Parameters:
            filename (str): Path to the YAML file.
        """
        if not os.path.exists(filename):
            print(f"[Loader] YAML file {filename} not found")
            return

        with open(filename, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        tasks = data.get("tasks", [])
        for task in tasks:
            self.unified_pool.submit_message(
                msg_type=task["msg_type"],
                content=task["content"],
                priority=task.get("priority", 100),
            )
        print(f"[Loader] Loaded {len(tasks)} tasks from YAML {filename}")

    def load_from_json(self, filename):
        """
        Loads tasks from a JSON file and submits them to the pool.

        Parameters:
            filename (str): Path to the JSON file.
        """
        if not os.path.exists(filename):
            print(f"[Loader] JSON file {filename} not found")
            return

        with open(filename, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        for task in tasks:
            self.unified_pool.submit_message(
                msg_type=task["msg_type"],
                content=task["content"],
                priority=task.get("priority", 100),
            )
        print(f"[Loader] Loaded {len(tasks)} tasks from JSON {filename}")
