"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Unified task pool for handling both thread-based and process-based execution
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
import pickle
import subprocess
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
class CoreletManager:
    """
    Manages corelet execution via subprocesses.
    """

    def __init__(self):
        """
        Initialize the CoreletManager.
        """
        self.active_processes = {}  # message_id -> process_object

    def start_corelet(self, message: basefunctions.UnifiedTaskPoolMessage) -> subprocess.Popen:
        """
        Starts a corelet as a separate process.

        Parameters
        ----------
        message : UnifiedTaskPoolMessage
            Message containing execution details

        Returns
        -------
        subprocess.Popen
            Process object
        """
        # Serialisiere Nachricht für Subprocess
        message_data = pickle.dumps(message)

        # Hole Pfad zum Corelet-Runner-Skript
        corelet_runner = os.path.join(os.path.dirname(__file__), "corelet_runner.py")

        # Starte Prozess und übergebe serialisierte Nachricht via stdin
        process = subprocess.Popen(
            ["python", corelet_runner],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        # Sende Daten zum Subprocess
        process.stdin.write(message_data)
        process.stdin.flush()

        # Speichere Prozessobjekt
        self.active_processes[message.id] = process

        basefunctions.get_logger(__name__).info(
            "started corelet process for message %s with pid %d", message.id, process.pid
        )

        return process

    def terminate_corelet(self, message_id: str, grace_period: int = 3) -> None:
        """
        Terminates a corelet process when timeout occurs.

        Parameters
        ----------
        message_id : str
            ID of the message associated with the process
        grace_period : int
            Seconds to wait before force kill
        """
        process = self.active_processes.get(message_id)
        if not process:
            return

        try:
            # Sende SIGTERM
            process.terminate()

            # Warte auf Beendigung mit Timeout
            try:
                process.wait(timeout=grace_period)
                basefunctions.get_logger(__name__).info(
                    "process %d terminated gracefully", process.pid
                )
            except subprocess.TimeoutExpired:
                # Prozess reagiert nicht, sende SIGKILL
                process.kill()
                basefunctions.get_logger(__name__).warning(
                    "process %d killed after grace period", process.pid
                )
        except Exception as e:
            basefunctions.get_logger(__name__).error(
                "error terminating process %d: %s", process.pid, str(e)
            )
        finally:
            # Entferne aus aktiven Prozessen
            if message_id in self.active_processes:
                del self.active_processes[message_id]
