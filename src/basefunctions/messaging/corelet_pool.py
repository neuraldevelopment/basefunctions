"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Process pool manager for corelet workers with load balancing
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import logging
import threading
import time
import copy
from typing import List, Dict, Any, Optional, Tuple
from multiprocessing import Process, Pipe
from concurrent.futures import Future

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


class WorkerInfo:
    """
    Information about a worker process.
    """

    __slots__ = (
        "worker_id",
        "process",
        "task_pipe",
        "result_pipe",
        "active_tasks",
        "total_tasks",
        "start_time",
        "last_activity",
    )

    def __init__(self, worker_id: str, process: Process, task_pipe, result_pipe):
        """
        Initialize worker info.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        process : Process
            Worker process.
        task_pipe : multiprocessing.Connection
            Pipe for sending tasks to worker.
        result_pipe : multiprocessing.Connection
            Pipe for receiving results from worker.
        """
        self.worker_id = worker_id
        self.process = process
        self.task_pipe = task_pipe
        self.result_pipe = result_pipe
        self.active_tasks = 0
        self.total_tasks = 0
        self.start_time = time.time()
        self.last_activity = time.time()

    def is_alive(self) -> bool:
        """
        Check if worker process is alive.

        Returns
        -------
        bool
            True if process is alive.
        """
        return self.process.is_alive()

    def get_load(self) -> float:
        """
        Get current worker load (active tasks).

        Returns
        -------
        float
            Current load factor.
        """
        return float(self.active_tasks)


class CoreletPool:
    """
    Process pool manager for corelet workers with load balancing and health monitoring.
    """

    __slots__ = (
        "_pool_size",
        "_workers",
        "_logger",
        "_running",
        "_next_worker_id",
        "_result_futures",
        "_result_collector_thread",
        "_health_monitor_thread",
        "_lock",
        "_stats",
    )

    def __init__(self, pool_size: int):
        """
        Initialize corelet pool.

        Parameters
        ----------
        pool_size : int
            Number of worker processes to maintain.
        """
        self._pool_size = pool_size
        self._workers: List[WorkerInfo] = []
        self._logger = logging.getLogger(__name__)
        self._running = True
        self._next_worker_id = 0
        self._result_futures: Dict[str, Future] = {}
        self._result_collector_thread: Optional[threading.Thread] = None
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "workers_restarted": 0,
        }

    def start(self) -> None:
        """
        Start the corelet pool and worker processes.
        """
        with self._lock:
            if not self._running:
                return

            self._logger.info("Starting corelet pool with %d workers", self._pool_size)

            # Start worker processes
            for _ in range(self._pool_size):
                self._create_worker()

            # Start background threads
            self._result_collector_thread = threading.Thread(
                target=self._result_collector_loop, name="CoreletResultCollector", daemon=True
            )
            self._result_collector_thread.start()

            self._health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop, name="CoreletHealthMonitor", daemon=True
            )
            self._health_monitor_thread.start()

            self._logger.info("Corelet pool started successfully")

    def submit_task(
        self, event: basefunctions.Event, handler: basefunctions.EventHandler
    ) -> Future:
        """
        Submit task to worker pool.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler for event processing.

        Returns
        -------
        Future
            Future for task result.
        """
        if not self._running:
            raise RuntimeError("Pool is not running")

        with self._lock:
            # Create future for result
            task_id = f"task_{self._stats['tasks_submitted']}"
            future = Future()
            self._result_futures[task_id] = future

            try:
                # Get handler path
                handler_path = f"{handler.__class__.__module__}.{handler.__class__.__name__}"

                # Select worker
                worker = self._select_worker()
                if not worker:
                    raise RuntimeError("No available workers")

                # Send task to worker - simple format without shared memory
                event_copy = copy.deepcopy(event)
                event_copy._task_id = task_id  # Add task ID for result matching

                task_data = (event_copy, handler_path)
                worker.task_pipe.send(task_data)
                worker.active_tasks += 1
                worker.total_tasks += 1
                worker.last_activity = time.time()

                self._stats["tasks_submitted"] += 1
                self._logger.debug("Submitted task %s to worker %s", task_id, worker.worker_id)

                return future

            except Exception as e:
                # Clean up on error
                if task_id in self._result_futures:
                    del self._result_futures[task_id]
                future.set_exception(e)
                return future

    def _create_worker(self) -> WorkerInfo:
        """
        Create and start a new worker process.

        Returns
        -------
        WorkerInfo
            Information about created worker.
        """
        worker_id = f"worker_{self._next_worker_id}"
        self._next_worker_id += 1

        # Create pipes for communication
        task_sender, task_receiver = Pipe()
        result_sender, result_receiver = Pipe()

        # Create worker process
        process = Process(
            target=basefunctions.worker_main,
            args=(worker_id, task_receiver, result_sender),
            name=f"CoreletWorker-{worker_id}",
            daemon=True,
        )

        # Start process
        process.start()

        # Create worker info
        worker_info = WorkerInfo(worker_id, process, task_sender, result_receiver)
        self._workers.append(worker_info)

        self._logger.debug("Created worker %s (PID: %d)", worker_id, process.pid)
        return worker_info

    def _select_worker(self) -> Optional[WorkerInfo]:
        """
        Select best available worker for task assignment.

        Returns
        -------
        Optional[WorkerInfo]
            Selected worker or None if no workers available.
        """
        if not self._workers:
            return None

        # Find worker with lowest load
        best_worker = None
        min_load = float("inf")

        for worker in self._workers:
            if worker.is_alive():
                load = worker.get_load()
                if load < min_load:
                    min_load = load
                    best_worker = worker

        return best_worker

    def _result_collector_loop(self) -> None:
        """
        Background thread loop for collecting results from workers.
        """
        while self._running:
            try:
                # Check all workers for results
                for worker in self._workers[:]:  # Copy list to avoid modification during iteration
                    if not worker.is_alive():
                        continue

                    # Check for available results
                    if worker.result_pipe.poll(timeout=0.1):
                        try:
                            result_event = worker.result_pipe.recv()
                            self._process_result(result_event, worker)
                        except Exception as e:
                            self._logger.error(
                                "Failed to receive result from worker %s: %s",
                                worker.worker_id,
                                str(e),
                            )

                time.sleep(0.1)  # Prevent busy waiting

            except Exception as e:
                self._logger.error("Error in result collector: %s", str(e))

    def _process_result(self, result_event: basefunctions.Event, worker: WorkerInfo) -> None:
        """
        Process result event from worker.

        Parameters
        ----------
        result_event : basefunctions.Event
            Result event from worker.
        worker : WorkerInfo
            Worker that sent the result.
        """
        try:
            # Extract task ID from result
            task_id = getattr(result_event, "_task_id", None)
            if not task_id:
                self._logger.warning(
                    "Received result without task ID from worker %s", worker.worker_id
                )
                return

            # Find corresponding future
            future = self._result_futures.get(task_id)
            if not future:
                self._logger.warning("No future found for task %s", task_id)
                return

            # Update worker stats
            worker.active_tasks = max(0, worker.active_tasks - 1)
            worker.last_activity = time.time()

            # Process result based on event type
            if result_event.type == "corelet.result":
                result_data = result_event.data.get("result")
                future.set_result(result_data)
                self._stats["tasks_completed"] += 1
            elif result_event.type == "corelet.error":
                error_message = result_event.data.get("error", "Unknown error")
                future.set_exception(Exception(error_message))
                self._stats["tasks_failed"] += 1
            else:
                future.set_exception(Exception(f"Unknown result type: {result_event.type}"))
                self._stats["tasks_failed"] += 1

            # Clean up
            del self._result_futures[task_id]

        except Exception as e:
            self._logger.error("Failed to process result: %s", str(e))

    def _health_monitor_loop(self) -> None:
        """
        Background thread loop for monitoring worker health.
        """
        while self._running:
            try:
                with self._lock:
                    # Check worker health
                    dead_workers = []
                    for worker in self._workers:
                        if not worker.is_alive():
                            self._logger.warning(
                                "Worker %s died (PID: %d)", worker.worker_id, worker.process.pid
                            )
                            dead_workers.append(worker)

                    # Restart dead workers
                    for dead_worker in dead_workers:
                        self._restart_worker(dead_worker)

                time.sleep(5.0)  # Health check interval

            except Exception as e:
                self._logger.error("Error in health monitor: %s", str(e))

    def _restart_worker(self, dead_worker: WorkerInfo) -> None:
        """
        Restart a dead worker.

        Parameters
        ----------
        dead_worker : WorkerInfo
            Dead worker to restart.
        """
        try:
            # Remove dead worker
            self._workers.remove(dead_worker)

            # Clean up dead worker resources
            try:
                dead_worker.task_pipe.close()
                dead_worker.result_pipe.close()
                dead_worker.process.join(timeout=1.0)
            except Exception:
                pass

            # Create new worker
            self._create_worker()
            self._stats["workers_restarted"] += 1

            self._logger.info("Restarted worker %s", dead_worker.worker_id)

        except Exception as e:
            self._logger.error("Failed to restart worker %s: %s", dead_worker.worker_id, str(e))

    def shutdown(self, timeout: float = 10.0) -> None:
        """
        Shutdown the corelet pool.

        Parameters
        ----------
        timeout : float
            Timeout for graceful shutdown.
        """
        self._logger.info("Shutting down corelet pool")
        self._running = False

        # Send shutdown signals to all workers
        shutdown_event = basefunctions.Event.shutdown()
        for worker in self._workers:
            try:
                if worker.is_alive():
                    worker.task_pipe.send(shutdown_event)
            except Exception:
                pass

        # Wait for workers to shutdown gracefully
        start_time = time.time()
        for worker in self._workers:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0:
                worker.process.join(timeout=remaining_time)

            # Force kill if still alive
            if worker.is_alive():
                worker.process.terminate()
                worker.process.join(timeout=1.0)
                if worker.is_alive():
                    worker.process.kill()

        # Clean up resources
        for worker in self._workers:
            try:
                worker.task_pipe.close()
                worker.result_pipe.close()
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
            total_load = sum(w.get_load() for w in self._workers if w.is_alive())

            return {
                "pool_size": self._pool_size,
                "alive_workers": alive_workers,
                "total_active_tasks": int(total_load),
                "tasks_submitted": self._stats["tasks_submitted"],
                "tasks_completed": self._stats["tasks_completed"],
                "tasks_failed": self._stats["tasks_failed"],
                "workers_restarted": self._stats["workers_restarted"],
                "pending_futures": len(self._result_futures),
            }
