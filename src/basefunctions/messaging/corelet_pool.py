"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Process pool manager with 3-pipe architecture and asynchronous task processing

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
import queue
import signal
import os
from typing import List, Dict, Any, Optional, Tuple
from multiprocessing import Process, Pipe, connection

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
SHUTDOWN_TIMEOUT_PER_TASK = 2.0  # Seconds per active task for shutdown
MIN_SHUTDOWN_TIMEOUT = 5.0  # Minimum shutdown timeout
MAX_SHUTDOWN_TIMEOUT = 60.0  # Maximum shutdown timeout
FORCE_KILL_TIMEOUT = 3.0  # Seconds before force kill

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class TaskInfo:
    """Information about a submitted task."""

    def __init__(
        self, task_id: str, event: "basefunctions.Event", handler: "basefunctions.EventHandler"
    ):
        self.task_id = task_id
        self.event = event
        self.handler = handler
        self.worker_id = None
        self.submitted_time = time.time()
        self.result_collector = None  # External result collector


class WorkerInfo:
    """
    Information about a corelet worker process with health tracking.
    """

    __slots__ = (
        "worker_id",
        "process",
        "task_pipe_a",
        "result_pipe_a",
        "health_pipe_a",
        "last_alive",
        "ping_failures",
        "is_healthy",
        "is_busy",
        "current_task_id",
        "_cleanup_attempted",
    )

    def __init__(
        self,
        worker_id: str,
        process: Process,
        task_pipe_a: connection.Connection,
        result_pipe_a: connection.Connection,
        health_pipe_a: connection.Connection,
    ):
        """
        Initialize worker info.

        Parameters
        ----------
        worker_id : str
            Unique worker identifier.
        process : Process
            Worker process.
        task_pipe_a : multiprocessing.Connection
            Pipe for sending business events to worker.
        result_pipe_a : multiprocessing.Connection
            Pipe for receiving business results from worker.
        health_pipe_a : multiprocessing.Connection
            Pipe for bidirectional health communication.
        """
        self.worker_id = worker_id
        self.process = process
        self.task_pipe_a = task_pipe_a
        self.result_pipe_a = result_pipe_a
        self.health_pipe_a = health_pipe_a
        self.last_alive = time.time()
        self.ping_failures = 0
        self.is_healthy = True
        self.is_busy = False
        self.current_task_id = None
        self._cleanup_attempted = False

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

    def is_available(self) -> bool:
        """
        Check if worker is available for new tasks.

        Returns
        -------
        bool
            True if worker is alive, healthy and not busy.
        """
        return self.is_alive() and self.is_healthy and not self.is_busy


class CoreletPool:
    """
    Process pool manager with 3-pipe architecture and asynchronous task processing.
    """

    __slots__ = (
        "_pool_size",
        "_workers",
        "_logger",
        "_running",
        "_next_worker_id",
        "_next_task_id",
        "_health_monitor_thread",
        "_task_dispatcher_thread",
        "_result_collector_thread",
        "_lock",
        "_pending_tasks",
        "_active_tasks",
        "_completed_results",
        "_cleanup_stats",
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
            pool_size = psutil.cpu_count(logical=False)

        self._pool_size = pool_size
        self._workers: List[WorkerInfo] = []
        self._logger = logging.getLogger(__name__)
        self._running = False
        self._next_worker_id = 0
        self._next_task_id = 0
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._task_dispatcher_thread: Optional[threading.Thread] = None
        self._result_collector_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Task management
        self._pending_tasks = queue.Queue()
        self._active_tasks: Dict[str, TaskInfo] = {}
        self._completed_results: List[Any] = []

        # Cleanup tracking
        self._cleanup_stats = {
            "workers_restarted": 0,
            "cleanup_failures": 0,
            "resources_leaked": 0,
        }

    def start(self) -> None:
        """
        Start the corelet pool and worker processes with readiness verification.
        """
        with self._lock:
            if self._running:
                return

            self._logger.info("Starting corelet pool with %d workers", self._pool_size)
            self._running = True

            # Start worker processes
            for _ in range(self._pool_size):
                self._create_worker()

            # Wait until all worker processes are actually running
            max_startup_wait = 30.0  # seconds
            startup_start = time.time()

            while time.time() - startup_start < max_startup_wait:
                alive_workers = sum(1 for w in self._workers if w.is_alive())
                if alive_workers == self._pool_size:
                    self._logger.info("All %d worker processes are alive", alive_workers)
                    break
                self._logger.debug(
                    "Waiting for workers to start: %d/%d alive", alive_workers, self._pool_size
                )
                time.sleep(0.2)
            else:
                alive_workers = sum(1 for w in self._workers if w.is_alive())
                self._logger.warning(
                    "Startup timeout: only %d/%d workers started", alive_workers, self._pool_size
                )

            # Start background threads
            self._health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop, name="CoreletHealthMonitor", daemon=True
            )
            self._health_monitor_thread.start()

            self._task_dispatcher_thread = threading.Thread(
                target=self._task_dispatcher_loop, name="CoreletTaskDispatcher", daemon=True
            )
            self._task_dispatcher_thread.start()

            self._result_collector_thread = threading.Thread(
                target=self._result_collector_loop, name="CoreletResultCollector", daemon=True
            )
            self._result_collector_thread.start()

            # Wait for worker readiness through health check
            self._logger.info("Waiting for workers to become ready...")
            ready_wait_start = time.time()
            max_ready_wait = 10.0  # seconds

            while time.time() - ready_wait_start < max_ready_wait:
                healthy_workers = sum(1 for w in self._workers if w.is_available())
                if healthy_workers >= max(1, self._pool_size // 2):  # At least half ready
                    self._logger.info("At least %d workers are ready for tasks", healthy_workers)
                    break
                self._logger.debug(
                    "Waiting for workers to become ready: %d available", healthy_workers
                )
                time.sleep(0.5)
            else:
                healthy_workers = sum(1 for w in self._workers if w.is_available())
                self._logger.warning("Ready timeout: only %d workers available", healthy_workers)

            # Final status
            final_stats = self.get_stats()
            self._logger.info("Corelet pool started - Stats: %s", final_stats)

            if final_stats["available_workers"] == 0:
                self._logger.error(
                    "CRITICAL: No workers available! Pool may not function correctly."
                )
                raise RuntimeError("Failed to start any available workers")

    def submit_task_async(
        self,
        event: "basefunctions.Event",
        handler: "basefunctions.EventHandler",
        result_collector=None,
    ) -> str:
        """
        Submit task to worker pool asynchronously.

        Parameters
        ----------
        event : basefunctions.Event
            Event to process.
        handler : basefunctions.EventHandler
            Handler for event processing.
        result_collector : object, optional
            External result collector for unified result handling.

        Returns
        -------
        str
            Task ID for tracking.
        """
        if not self._running:
            raise RuntimeError("Pool is not running")

        # Generate unique task ID
        task_id = f"task_{self._next_task_id}"
        self._next_task_id += 1

        # Create task info
        task_info = TaskInfo(task_id, event, handler)
        task_info.result_collector = result_collector  # Store external collector

        # Add to pending queue
        self._pending_tasks.put(task_info)

        self._logger.debug("Submitted async task %s", task_id)
        return task_id

    def collect_results(self) -> List[Any]:
        """
        Collect all completed results.

        Returns
        -------
        List[Any]
            List of completed results.
        """
        with self._lock:
            results = self._completed_results.copy()
            self._completed_results.clear()
            return results

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all active tasks to complete.

        Parameters
        ----------
        timeout : float, optional
            Maximum time to wait in seconds.

        Returns
        -------
        bool
            True if all tasks completed, False if timeout.
        """
        start_time = time.time()

        while True:
            with self._lock:
                if self._pending_tasks.empty() and not self._active_tasks:
                    return True

            if timeout and (time.time() - start_time) > timeout:
                return False

            time.sleep(0.1)

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
        task_pipe_a, task_pipe_b = Pipe()
        result_pipe_a, result_pipe_b = Pipe()
        health_pipe_a, health_pipe_b = Pipe()

        # Create worker process with signal handling
        process = Process(
            target=basefunctions.worker_main,
            args=(worker_id, task_pipe_b, result_pipe_b, health_pipe_b),
            name=f"CoreletWorker-{worker_id}",
            daemon=False,  # Non-daemon for graceful shutdown
        )

        # Start process
        process.start()

        # Create worker info
        worker_info = WorkerInfo(worker_id, process, task_pipe_a, result_pipe_a, health_pipe_a)
        self._workers.append(worker_info)

        self._logger.debug("Created worker %s (PID: %d)", worker_id, process.pid)
        return worker_info

    def _task_dispatcher_loop(self) -> None:
        """
        Background thread loop for dispatching tasks to available workers.
        """
        while self._running:
            try:
                # Get pending task with timeout
                try:
                    task_info = self._pending_tasks.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Find available worker
                worker = self._select_available_worker()
                if not worker:
                    # No worker available, put task back and wait
                    self._pending_tasks.put(task_info)
                    time.sleep(0.1)
                    continue

                # Dispatch task to worker
                self._dispatch_task_to_worker(task_info, worker)

            except Exception as e:
                self._logger.error("Error in task dispatcher: %s", str(e))

    def _dispatch_task_to_worker(self, task_info: TaskInfo, worker: WorkerInfo) -> None:
        """
        Dispatch a task to a specific worker.

        Parameters
        ----------
        task_info : TaskInfo
            Task to dispatch.
        worker : WorkerInfo
            Worker to dispatch to.
        """
        try:
            # Prepare event with handler path
            handler_path = (
                f"{task_info.handler.__class__.__module__}.{task_info.handler.__class__.__name__}"
            )
            task_info.event._handler_path = handler_path

            # Mark worker as busy
            with self._lock:
                worker.is_busy = True
                worker.current_task_id = task_info.task_id
                task_info.worker_id = worker.worker_id
                self._active_tasks[task_info.task_id] = task_info

                # Send event to worker
                pickled_event = pickle.dumps(task_info.event)
                worker.task_pipe_a.send(pickled_event)

            self._logger.debug(
                "Dispatched task %s to worker %s", task_info.task_id, worker.worker_id
            )

        except Exception as e:
            self._logger.error(
                "Failed to dispatch task %s to worker %s: %s",
                task_info.task_id,
                worker.worker_id,
                str(e),
            )
            # Mark worker as unhealthy and restart
            worker.is_healthy = False
            self._restart_worker(worker)

    def _result_collector_loop(self) -> None:
        """
        Background thread loop for collecting results from workers.
        """
        while self._running:
            try:
                with self._lock:
                    for worker in self._workers[:]:
                        if not worker.is_busy:
                            continue

                        # Check for results
                        if worker.result_pipe_a.poll(timeout=0.0):
                            self._collect_worker_result(worker)

                time.sleep(0.01)  # Small delay to prevent busy waiting

            except Exception as e:
                self._logger.error("Error in result collector: %s", str(e))

    def _collect_worker_result(self, worker: WorkerInfo) -> None:
        """
        Collect result from a worker.

        Parameters
        ----------
        worker : WorkerInfo
            Worker to collect result from.
        """
        try:
            # Get result from worker
            pickled_result = worker.result_pipe_a.recv()
            result_event = pickle.loads(pickled_result)

            # Process result
            task_id = worker.current_task_id
            if task_id and task_id in self._active_tasks:
                task_info = self._active_tasks.pop(task_id)

                if result_event.type == "corelet.result":
                    result = result_event.data.get("result")

                    # Use external collector if available, otherwise internal storage
                    if hasattr(task_info, "result_collector") and task_info.result_collector:
                        task_info.result_collector.add_result(result)
                    else:
                        self._completed_results.append(result)

                    self._logger.debug("Collected result for task %s", task_id)
                elif result_event.type == "corelet.error":
                    error_msg = result_event.data.get("error", "Unknown error")
                    error_result = f"exception: {error_msg}"

                    # Use external collector if available, otherwise internal storage
                    if hasattr(task_info, "result_collector") and task_info.result_collector:
                        task_info.result_collector.add_result(error_result)
                    else:
                        self._completed_results.append(error_result)

                    self._logger.error("Task %s failed: %s", task_id, error_msg)
                else:
                    self._logger.warning(
                        "Unexpected result type for task %s: %s", task_id, result_event.type
                    )

            # Mark worker as available
            worker.is_busy = False
            worker.current_task_id = None

        except Exception as e:
            self._logger.error(
                "Failed to collect result from worker %s: %s", worker.worker_id, str(e)
            )
            # Mark worker as unhealthy
            worker.is_healthy = False
            self._restart_worker(worker)

    def _select_available_worker(self) -> Optional[WorkerInfo]:
        """
        Select first available worker.

        Returns
        -------
        Optional[WorkerInfo]
            Selected worker or None if no workers available.
        """
        with self._lock:
            for worker in self._workers:
                if worker.is_available():
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
            while worker.health_pipe_a.poll(timeout=0.0):
                pickled_event = worker.health_pipe_a.recv()
                event = pickle.loads(pickled_event)

                if event.type == "corelet.pong":
                    self._logger.debug("Worker %s responded to ping", worker.worker_id)
                    worker.reset_health()
                elif event.type == "corelet.alive":
                    self._logger.debug("Worker %s sent alive signal", worker.worker_id)
                    worker.reset_health()
                elif event.type == "corelet.shutdown_complete":
                    self._logger.info("Worker %s confirmed shutdown", worker.worker_id)
                elif event.type == "corelet.died":
                    self._logger.error("Worker %s reported died status", worker.worker_id)
                    worker.is_healthy = False
                    self._restart_worker(worker)
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
            worker.health_pipe_a.send(pickled_ping)

            # Wait for pong response
            start_time = time.time()
            pong_received = False

            while time.time() - start_time < PING_TIMEOUT:
                if worker.health_pipe_a.poll(timeout=0.5):
                    pickled_response = worker.health_pipe_a.recv()
                    response_event = pickle.loads(pickled_response)

                    if response_event.type == "corelet.pong":
                        worker.reset_health()
                        pong_received = True
                        break
                    elif response_event.type == "corelet.alive":
                        worker.reset_health()
                        pong_received = True
                        break
                    elif response_event.type == "corelet.died":
                        self._logger.error("Worker %s reported died during ping", worker.worker_id)
                        worker.is_healthy = False
                        self._restart_worker(worker)
                        return

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

    def _cleanup_worker_resources(self, worker: WorkerInfo) -> bool:
        """
        Centralized resource cleanup for worker processes.

        Parameters
        ----------
        worker : WorkerInfo
            Worker to cleanup.

        Returns
        -------
        bool
            True if cleanup was successful, False otherwise.
        """
        if worker._cleanup_attempted:
            self._logger.warning("Cleanup already attempted for worker %s", worker.worker_id)
            return False

        worker._cleanup_attempted = True
        cleanup_success = True
        cleanup_errors = []

        # 1. Close pipes with individual error handling
        pipes = [
            ("task_pipe_a", worker.task_pipe_a),
            ("result_pipe_a", worker.result_pipe_a),
            ("health_pipe_a", worker.health_pipe_a),
        ]

        for pipe_name, pipe_obj in pipes:
            try:
                if pipe_obj and not pipe_obj.closed:
                    pipe_obj.close()
                    self._logger.debug("Closed %s for worker %s", pipe_name, worker.worker_id)
            except Exception as e:
                cleanup_success = False
                error_msg = f"Failed to close {pipe_name}: {str(e)}"
                cleanup_errors.append(error_msg)
                self._logger.error("Worker %s - %s", worker.worker_id, error_msg)

        # 2. Process termination with escalation
        try:
            if worker.process.is_alive():
                # Step 1: Graceful termination
                worker.process.terminate()
                self._logger.debug("Sent TERM signal to worker %s", worker.worker_id)

                # Step 2: Wait with timeout
                try:
                    worker.process.join(timeout=FORCE_KILL_TIMEOUT)
                except Exception as e:
                    cleanup_errors.append(f"Join failed: {str(e)}")

                # Step 3: Force kill if still alive
                if worker.process.is_alive():
                    self._logger.warning("Force killing worker %s", worker.worker_id)
                    worker.process.kill()
                    try:
                        worker.process.join(timeout=1.0)
                    except Exception as e:
                        cleanup_errors.append(f"Force kill join failed: {str(e)}")

                    if worker.process.is_alive():
                        cleanup_success = False
                        cleanup_errors.append("Process still alive after force kill")

        except Exception as e:
            cleanup_success = False
            error_msg = f"Process termination failed: {str(e)}"
            cleanup_errors.append(error_msg)
            self._logger.error("Worker %s - %s", worker.worker_id, error_msg)

        # Update cleanup statistics
        if not cleanup_success:
            self._cleanup_stats["cleanup_failures"] += 1
            self._cleanup_stats["resources_leaked"] += len(cleanup_errors)

        # Log cleanup result
        if cleanup_success:
            self._logger.info("Successfully cleaned up worker %s", worker.worker_id)
        else:
            self._logger.error(
                "Cleanup failed for worker %s. Errors: %s", worker.worker_id, cleanup_errors
            )

        return cleanup_success

    def _restart_worker(self, dead_worker: WorkerInfo) -> None:
        """
        Restart a dead or unhealthy worker with improved resource management.

        Parameters
        ----------
        dead_worker : WorkerInfo
            Worker to restart.
        """
        try:
            self._cleanup_stats["workers_restarted"] += 1
            self._logger.info("Restarting worker %s", dead_worker.worker_id)

            # Remove dead worker from active list
            if dead_worker in self._workers:
                self._workers.remove(dead_worker)

            # Handle active task if worker was busy
            if dead_worker.current_task_id and dead_worker.current_task_id in self._active_tasks:
                task_info = self._active_tasks.pop(dead_worker.current_task_id)
                # Re-queue the task
                self._pending_tasks.put(task_info)
                self._logger.info("Re-queued task %s after worker restart", task_info.task_id)

            # Cleanup resources with detailed logging
            cleanup_success = self._cleanup_worker_resources(dead_worker)
            if not cleanup_success:
                self._logger.warning(
                    "Resource cleanup incomplete for worker %s, potential leaks",
                    dead_worker.worker_id,
                )

            # Create new worker
            new_worker = self._create_worker()
            self._logger.info(
                "Restarted worker %s -> %s", dead_worker.worker_id, new_worker.worker_id
            )

        except Exception as e:
            self._logger.error("Failed to restart worker %s: %s", dead_worker.worker_id, str(e))
            self._cleanup_stats["cleanup_failures"] += 1

    def shutdown(self, timeout: Optional[float] = None) -> None:
        """
        Shutdown the corelet pool gracefully with adaptive timeouts.

        Parameters
        ----------
        timeout : float, optional
            Maximum timeout for shutdown. If None, calculates based on active tasks.
        """
        self._logger.info("Shutting down corelet pool")
        self._running = False

        # Calculate adaptive timeout based on active tasks
        if timeout is None:
            active_task_count = len(self._active_tasks)
            calculated_timeout = max(
                MIN_SHUTDOWN_TIMEOUT,
                min(MAX_SHUTDOWN_TIMEOUT, active_task_count * SHUTDOWN_TIMEOUT_PER_TASK),
            )
            self._logger.info(
                "Calculated shutdown timeout: %.1fs for %d active tasks",
                calculated_timeout,
                active_task_count,
            )
        else:
            calculated_timeout = timeout

        # Wait for active tasks to complete
        self._logger.info("Waiting for active tasks to complete...")
        task_completion_timeout = calculated_timeout * 0.6  # Use 60% of timeout for tasks
        completion_success = self.wait_for_completion(timeout=task_completion_timeout)

        if completion_success:
            self._logger.info("All tasks completed successfully")
        else:
            remaining_tasks = len(self._active_tasks)
            self._logger.warning("Shutdown timeout: %d tasks still active", remaining_tasks)

        # Send shutdown events to all workers
        shutdown_event = basefunctions.Event("corelet.shutdown")
        shutdown_confirmations = 0
        shutdown_timeout = calculated_timeout * 0.3  # Use 30% for shutdown messages

        for worker in self._workers:
            try:
                if worker.is_alive():
                    pickled_shutdown = pickle.dumps(shutdown_event)
                    worker.health_pipe_a.send(pickled_shutdown)
            except Exception as e:
                self._logger.warning(
                    "Failed to send shutdown to worker %s: %s", worker.worker_id, str(e)
                )

        # Wait for shutdown confirmations
        start_time = time.time()
        while (
            shutdown_confirmations < len(self._workers)
            and (time.time() - start_time) < shutdown_timeout
        ):
            for worker in self._workers:
                try:
                    if worker.health_pipe_a.poll(timeout=0.1):
                        pickled_response = worker.health_pipe_a.recv()
                        response_event = pickle.loads(pickled_response)
                        if response_event.type == "corelet.shutdown_complete":
                            shutdown_confirmations += 1
                            self._logger.debug(
                                "Worker %s confirmed shutdown",
                                response_event.data.get("worker_id"),
                            )
                except Exception as e:
                    self._logger.warning("Error reading shutdown confirmation: %s", str(e))

        self._logger.info(
            "Received %d/%d shutdown confirmations", shutdown_confirmations, len(self._workers)
        )

        # Force cleanup remaining workers
        cleanup_failures = 0
        for worker in self._workers[:]:  # Copy list to avoid modification during iteration
            try:
                cleanup_success = self._cleanup_worker_resources(worker)
                if not cleanup_success:
                    cleanup_failures += 1
            except Exception as e:
                self._logger.error("Cleanup error for worker %s: %s", worker.worker_id, str(e))
                cleanup_failures += 1

        self._workers.clear()

        # Log final cleanup statistics
        self._logger.info(
            "Corelet pool shutdown complete. Cleanup stats: %s, Failures: %d",
            self._cleanup_stats,
            cleanup_failures,
        )

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
            busy_workers = sum(1 for w in self._workers if w.is_busy)
            total_ping_failures = sum(w.ping_failures for w in self._workers)

            return {
                "pool_size": self._pool_size,
                "alive_workers": alive_workers,
                "healthy_workers": healthy_workers,
                "busy_workers": busy_workers,
                "available_workers": healthy_workers - busy_workers,
                "total_workers": len(self._workers),
                "pending_tasks": self._pending_tasks.qsize(),
                "active_tasks": len(self._active_tasks),
                "completed_results": len(self._completed_results),
                "total_ping_failures": total_ping_failures,
                "health_check_interval": HEALTH_CHECK_INTERVAL,
                "ping_timeout": PING_TIMEOUT,
                "max_ping_retries": MAX_PING_RETRIES,
                "cleanup_stats": self._cleanup_stats.copy(),
                "shutdown_config": {
                    "timeout_per_task": SHUTDOWN_TIMEOUT_PER_TASK,
                    "min_timeout": MIN_SHUTDOWN_TIMEOUT,
                    "max_timeout": MAX_SHUTDOWN_TIMEOUT,
                    "force_kill_timeout": FORCE_KILL_TIMEOUT,
                },
            }
