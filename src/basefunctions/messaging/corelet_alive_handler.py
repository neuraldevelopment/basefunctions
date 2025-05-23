"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Corelet alive handler for worker health monitoring
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import queue
import pickle
from typing import Any, Optional
from multiprocessing import connection

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


class CoreletAliveHandler(basefunctions.EventHandler):
    """
    Handler for alive events with health monitoring and ping response logic.
    """

    execution_mode = 1  # thread

    def __init__(
        self,
        worker_id: str,
        task_pipe_a: connection.Connection,
        health_pipe_b: connection.Connection,
    ):
        """
        Initialize corelet alive handler.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        health_pipe_b : multiprocessing.Connection
            Pipe for health communication with pool.
        """
        self._worker_id = worker_id
        self._health_pipe_b = health_pipe_b
        self._alive_queue = queue.Queue()
        self._logger = logging.getLogger(f"{__name__}.{worker_id}")
        self._running = True
        self._ping_without_alive_count = 0
        self.task_pipe_a = task_pipe_a

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Any:
        """
        Handle alive event and start health monitoring loop.

        Parameters
        ----------
        event : Event
            Alive event to process.
        context : EventContext, optional
            Event context.

        Returns
        -------
        Any
            None on success.
        """
        try:
            # Store alive event in queue
            self._alive_queue.put(event)
            self._logger.debug("Stored alive event with timestamp: %s", event.timestamp)

            # Health monitoring loop - blocking wait for health pipe
            while self._running:
                try:
                    # Blocking wait for health commands from pool
                    pickled_data = self._health_pipe_b.recv()
                    health_event = pickle.loads(pickled_data)

                    if health_event.type == "corelet.shutdown":
                        self._logger.info("Received shutdown signal")
                        self._send_shutdown_complete()
                        pickled_result = pickle.dumps(basefunctions.Event.shutdown())
                        self.task_pipe_a.send(pickled_result)
                        break
                    elif health_event.type == "corelet.ping":
                        self._handle_ping()

                except Exception as e:
                    self._logger.error("Error in health monitoring: %s", str(e))
                    break

            return None

        except Exception as e:
            self._logger.error("Error handling alive event: %s", str(e))
            raise

    def _handle_ping(self) -> None:
        """
        Handle ping request from pool with graceful first-time logic.
        """
        try:
            # Read and drain alive queue
            latest_event = None

            while not self._alive_queue.empty():
                try:
                    latest_event = self._alive_queue.get_nowait()
                except queue.Empty:
                    break

            if latest_event:
                # Got alive event - send pong with event timestamp
                self._send_pong(latest_event.timestamp, latest_event.data)
                self._ping_without_alive_count = 0  # Reset counter
                self._logger.debug("Sent pong with alive timestamp: %s", latest_event.timestamp)
            else:
                # No alive events in queue
                self._ping_without_alive_count += 1

                if self._ping_without_alive_count == 1:
                    # First ping without alive - be graceful
                    self._send_pong()
                    self._logger.warning("First ping without alive event - being graceful")
                else:
                    # Second ping without alive - worker is dead
                    self._send_died()
                    self._logger.error("Second ping without alive event - worker declared dead")

        except Exception as e:
            self._logger.error("Error handling ping: %s", str(e))

    def _send_pong(self, alive_timestamp=None, alive_data=None) -> None:
        """
        Send pong response via health pipe.

        Parameters
        ----------
        alive_timestamp : datetime, optional
            Timestamp from latest alive event.
        alive_data : dict, optional
            Data from latest alive event.
        """
        try:
            pong_data = {"worker_id": self._worker_id}

            if alive_timestamp:
                pong_data["last_alive_timestamp"] = alive_timestamp
            else:
                # Use current timestamp for graceful first ping
                import datetime

                pong_data["last_alive_timestamp"] = datetime.datetime.now()

            if alive_data:
                pong_data["computation_status"] = alive_data.get("computation_status")

            pong_event = basefunctions.Event("corelet.pong", data=pong_data)
            pickled_pong = pickle.dumps(pong_event)
            self._health_pipe_b.send(pickled_pong)

        except Exception as e:
            self._logger.error("Failed to send pong: %s", str(e))

    def _send_died(self) -> None:
        """
        Send died signal via health pipe.
        """
        try:
            died_event = basefunctions.Event("corelet.died", data={"worker_id": self._worker_id})
            pickled_died = pickle.dumps(died_event)
            self._health_pipe_b.send(pickled_died)

        except Exception as e:
            self._logger.error("Failed to send died signal: %s", str(e))

    def _send_shutdown_complete(self) -> None:
        """
        Send shutdown completion via health pipe.
        """
        try:
            shutdown_event = basefunctions.Event(
                "corelet.shutdown_complete", data={"worker_id": self._worker_id}
            )
            pickled_shutdown = pickle.dumps(shutdown_event)
            self._health_pipe_b.send(pickled_shutdown)

        except Exception as e:
            self._logger.error("Failed to send shutdown complete: %s", str(e))
