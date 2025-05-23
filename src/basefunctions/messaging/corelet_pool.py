"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment , Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  Process pool manager with 3-pipe architecture and robust health monitoring
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import threading
import time
import pickle
import psutil
from typing import List, Dict, Any, Optional
from multiprocessing import Process, Pipe

import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------
HEALTH_CHECK_INTERVAL = 300.0  # Seconds between health checks
PING_TIMEOUT = 10.0  # Seconds to wait for ping response
MAX_PING_RETRIES = 3  # Number of ping attempts before kill

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class WorkerInfo:
    """
    Information about a corelet worker process with health tracking.
    """

    __slots__ = (
        "worker_id",
        "process",
        "task_pipe",
        "result_pipe",
        "health_pipe",
        "last_alive",
        "ping_failures",
        "is_healthy",
    )

    def __init__(self, worker_id: str, process: Process, task_pipe, result_pipe, health_pipe):
        """
        Initialize worker info.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        process : Process
            Worker process.
        task_pipe : multiprocessing.Connection
            Pipe for sending business events to worker.
        result_pipe : multiprocessing.Connection
            Pipe for receiving business results from worker.
        health_pipe : multiprocessing.Connection
            Pipe for bidirectional health communication.
        """
        self.worker_id = worker_id
        self.process = process
        self.task_pipe = task_pipe
        self.result_pipe = result_pipe
        self.health_pipe = health_pipe
        self.last_alive = time.time()
        self.ping_failures = 0
        self.is_healthy = True

    def is_alive(self) -> bool:
        """
        Check if worker process is alive.

        Returns
        -------
        bool
            True if process is alive.
        """
        return self.process.is_alive()

    def reset_health(self) -> None:
        """
        Reset health status after successful communication.
        """
        self.last_alive = time.time()
        self.ping_failures = 0
        self.is_healthy = True


class CoreletPool:
    """
    Process pool manager with 3-pipe architecture and robust health monitoring.
    """

    __slots__ = (
        "_pool_size",
        "_workers",
        "_logger",
        "_running",
        "_next_worker_id",
        "_health_monitor_thread",
        "_lock",
    )

    def __init__(self, pool_size: Optional[int] = None):
        """
        Initialize corelet pool.

        Parameters
        ----------
        pool_size : int, optional
            Number of worker processes. If None, auto-detects CPU cores.
        """
        if pool_size is None:
            pool_size = min(psutil.cpu_count(logical=False), 8)

        self._pool_size = pool_size
        self._workers: List[WorkerInfo] = []
        self._logger = logging.getLogger(__name__)
        self._running = False
        self._next_worker_id = 0
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def start(self) -> None:
        """
        Start the corelet pool and worker processes.
        """
        with self._lock:
            if self._running:
                return

            self._logger.info("Starting corelet pool with %d workers", self._pool_size)
            self._running = True

            # Start worker processes
            for _ in range(self._pool_size):
                self._create_worker()

            # Start health monitor
            self._health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop, name="CoreletHealthMonitor", daemon=True
            )
            self._health_monitor_thread.start()

            self._logger.info("Corelet pool started successfully")

    def submit_task(self, event: basefunctions.Event, handler: basefunctions.EventHandler) -> Any:
        """
        Submit task to worker pool and wait for result.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler for event processing.

        Returns
        -------
        Any
            Result from handler execution.
        """
        if not self._running:
            raise RuntimeError("Pool is not running")

        with self._lock:
            # Select worker
            worker = self._select_worker()
            if not worker:
                raise RuntimeError("No available workers")

            try:
                # Prepare event with handler path
                handler_path = f"{handler.__class__.__module__}.{handler.__class__.__name__}"
                event._handler_path = handler_path

                # Send event to worker via task pipe
                pickled_event = pickle.dumps(event)
                worker.task_pipe.send(pickled_event)

                # Wait for result via result pipe
                pickled_result = worker.result_pipe.recv()
                result_event = pickle.loads(pickled_result)

                # Process result event
                if result_event.type == "corelet.result":
                    return result_event.data.get("result")
                elif result_event.type == "corelet.error":
                    error_msg = result_event.data.get("error", "Unknown error")
                    raise Exception(error_msg)
                else:
                    raise Exception(f"Unexpected result type: {result_event.type}")

            except Exception as e:
                self._logger.error("Task submission failed: %s", str(e))
                # Mark worker as unhealthy and restart
                worker.is_healthy = False
                self._restart_worker(worker)
                raise

    def _create_worker(self) -> WorkerInfo:
        """
        Create and start a new worker process with 3-pipe architecture.

        Returns
        -------
        WorkerInfo
            Information about created worker.
        """
        worker_id = f"worker_{self._next_worker_id}"
        self._next_worker_id += 1

        # Create 3 pipes for communication
        task_sender, task_receiver = Pipe()
        result_sender, result_receiver = Pipe()
        health_pool, health_worker = Pipe()

        # Create worker process
        process = Process(
            target=basefunctions.worker_main,
            args=(worker_id, task_receiver, result_sender, health_worker),
            name=f"CoreletWorker-{worker_id}",
            daemon=True,
        )

        # Start process
        process.start()

        # Create worker info
        worker_info = WorkerInfo(worker_id, process, task_sender, result_receiver, health_pool)
        self._workers.append(worker_info)

        self._logger.debug("Created worker %s (PID: %d)", worker_id, process.pid)
        return worker_info

    def _select_worker(self) -> Optional[WorkerInfo]:
        """
        Select first available healthy worker.

        Returns
        -------
        Optional[WorkerInfo]
            Selected worker or None if no workers available.
        """
        for worker in self._workers:
            if worker.is_alive() and worker.is_healthy:
                return worker
        return None

    def _health_monitor_loop(self) -> None:
        """
        Background thread loop for monitoring worker health.
        """
        while self._running:
            try:
                with self._lock:
                    current_time = time.time()

                    for worker in self._workers[:]:
                        if not worker.is_alive():
                            self._logger.warning("Worker %s died", worker.worker_id)
                            self._restart_worker(worker)
                            continue

                        # Check for health events from workers
                        self._check_health_events(worker)

                        # Send ping if no activity for too long
                        if current_time - worker.last_alive > HEALTH_CHECK_INTERVAL:
                            self._ping_worker(worker)

                time.sleep(5.0)  # Health monitor interval

            except Exception as e:
                self._logger.error("Error in health monitor: %s", str(e))

    def _check_health_events(self, worker: WorkerInfo) -> None:
        """
        Check for incoming health events from worker.

        Parameters
        ----------
        worker : WorkerInfo
            Worker to check.
        """
        try:
            # Check for health events without blocking
            while worker.health_pipe.poll(timeout=0.0):
                pickled_event = worker.health_pipe.recv()
                event = pickle.loads(pickled_event)

                if event.type == "corelet.pong":
                    self._logger.debug("Worker %s responded to ping", worker.worker_id)
                    worker.reset_health()
                elif event.type == "corelet.alive":
                    self._logger.debug("Worker %s sent alive signal", worker.worker_id)
                    worker.reset_health()
                elif event.type == "corelet.shutdown_complete":
                    self._logger.info("Worker %s confirmed shutdown", worker.worker_id)
                else:
                    self._logger.warning(
                        "Unknown health event from worker %s: %s", worker.worker_id, event.type
                    )

        except Exception as e:
            self._logger.error(
                "Failed to check health events for worker %s: %s", worker.worker_id, str(e)
            )

    def _ping_worker(self, worker: WorkerInfo) -> None:
        """
        Send ping to worker with retry logic.

        Parameters
        ----------
        worker : WorkerInfo
            Worker to ping.
        """
        try:
            # Send ping event
            ping_event = basefunctions.Event("corelet.ping")
            pickled_ping = pickle.dumps(ping_event)
            worker.health_pipe.send(pickled_ping)

            # Wait for pong response
            start_time = time.time()
            pong_received = False

            while time.time() - start_time < PING_TIMEOUT:
                if worker.health_pipe.poll(timeout=0.5):
                    pickled_response = worker.health_pipe.recv()
                    response_event = pickle.loads(pickled_response)

                    if response_event.type == "corelet.pong":
                        worker.reset_health()
                        pong_received = True
                        break
                    elif response_event.type == "corelet.alive":
                        worker.reset_health()
                        pong_received = True
                        break

            if not pong_received:
                worker.ping_failures += 1
                self._logger.warning(
                    "Worker %s ping timeout (attempt %d/%d)",
                    worker.worker_id,
                    worker.ping_failures,
                    MAX_PING_RETRIES,
                )

                # Kill worker after max retries
                if worker.ping_failures >= MAX_PING_RETRIES:
                    self._logger.error(
                        "Worker %s failed %d pings, restarting", worker.worker_id, MAX_PING_RETRIES
                    )
                    worker.is_healthy = False
                    self._restart_worker(worker)

        except Exception as e:
            self._logger.error("Failed to ping worker %s: %s", worker.worker_id, str(e))
            worker.ping_failures += 1
            if worker.ping_failures >= MAX_PING_RETRIES:
                worker.is_healthy = False
                self._restart_worker(worker)

    def _restart_worker(self, dead_worker: WorkerInfo) -> None:
        """
        Restart a dead or unhealthy worker.

        Parameters
        ----------
        dead_worker : WorkerInfo
            Worker to restart.
        """
        try:
            # Remove dead worker
            if dead_worker in self._workers:
                self._workers.remove(dead_worker)

            # Clean up dead worker resources
            try:
                dead_worker.task_pipe.close()
                dead_worker.result_pipe.close()
                dead_worker.health_pipe.close()
                if dead_worker.process.is_alive():
                    dead_worker.process.terminate()
                    dead_worker.process.join(timeout=2.0)
                    if dead_worker.process.is_alive():
                        dead_worker.process.kill()
            except Exception:
                pass

            # Create new worker
            self._create_worker()
            self._logger.info("Restarted worker %s", dead_worker.worker_id)

        except Exception as e:
            self._logger.error("Failed to restart worker %s: %s", dead_worker.worker_id, str(e))

    def shutdown(self, timeout: float = 30.0) -> None:
        """
        Shutdown the corelet pool gracefully.

        Parameters
        ----------
        timeout : float
            Timeout for graceful shutdown.
        """
        self._logger.info("Shutting down corelet pool")
        self._running = False

        # Send shutdown events to all workers
        shutdown_event = basefunctions.Event("corelet.shutdown")
        shutdown_confirmations = 0

        for worker in self._workers:
            try:
                if worker.is_alive():
                    pickled_shutdown = pickle.dumps(shutdown_event)
                    worker.health_pipe.send(pickled_shutdown)
            except Exception:
                pass

        # Wait for shutdown confirmations
        start_time = time.time()
        while shutdown_confirmations < len(self._workers) and (time.time() - start_time) < timeout:
            for worker in self._workers:
                try:
                    if worker.health_pipe.poll(timeout=0.1):
                        pickled_response = worker.health_pipe.recv()
                        response_event = pickle.loads(pickled_response)
                        if response_event.type == "corelet.shutdown_complete":
                            shutdown_confirmations += 1
                            self._logger.debug(
                                "Worker %s confirmed shutdown",
                                response_event.data.get("worker_id"),
                            )
                except Exception:
                    pass

        # Force kill remaining workers
        for worker in self._workers:
            try:
                if worker.process.is_alive():
                    worker.process.terminate()
                    worker.process.join(timeout=1.0)
                    if worker.process.is_alive():
                        worker.process.kill()
                worker.task_pipe.close()
                worker.result_pipe.close()
                worker.health_pipe.close()
            except Exception:
                pass

        self._workers.clear()
        self._logger.info("Corelet pool shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.

        Returns
        -------
        Dict[str, Any]
            Pool statistics.
        """
        with self._lock:
            alive_workers = sum(1 for w in self._workers if w.is_alive())
            healthy_workers = sum(1 for w in self._workers if w.is_alive() and w.is_healthy)
            total_ping_failures = sum(w.ping_failures for w in self._workers)

            return {
                "pool_size": self._pool_size,
                "alive_workers": alive_workers,
                "healthy_workers": healthy_workers,
                "total_workers": len(self._workers),
                "total_ping_failures": total_ping_failures,
                "health_check_interval": HEALTH_CHECK_INTERVAL,
                "ping_timeout": PING_TIMEOUT,
                "max_ping_retries": MAX_PING_RETRIES,
            }
