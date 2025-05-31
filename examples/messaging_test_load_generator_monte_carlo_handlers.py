"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Monte Carlo Pi calculation handlers for CPU-intensive performance testing

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import random
import logging
from typing import Optional, Any, Tuple
from datetime import datetime

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


class MonteCarloEvent(basefunctions.Event):
    """Event containing Monte Carlo Pi calculation parameters."""

    def __init__(self, iterations: int, task_id: int):
        """
        Initialize Monte Carlo event.

        Parameters
        ----------
        iterations : int
            Number of random points to generate for Pi calculation
        task_id : int
            Unique identifier for this calculation task
        """
        super().__init__(
            type="monte_carlo_pi",
            data={"iterations": iterations, "task_id": task_id},
        )


def calculate_pi_monte_carlo(iterations: int) -> float:
    """
    Calculate Pi using Monte Carlo method.

    Parameters
    ----------
    iterations : int
        Number of random points to generate

    Returns
    -------
    float
        Estimated value of Pi
    """
    points_in_circle = 0

    for _ in range(iterations):
        x = random.random()  # Random float between 0 and 1
        y = random.random()  # Random float between 0 and 1

        # Check if point is inside unit circle
        if x * x + y * y <= 1.0:
            points_in_circle += 1

    # Pi estimation: 4 * (points in circle / total points)
    pi_estimate = 4.0 * points_in_circle / iterations
    return pi_estimate


class MonteCarloSyncHandler(basefunctions.EventHandler):
    """Synchronous handler for Monte Carlo Pi calculation."""

    execution_mode = basefunctions.EXECUTION_MODE_SYNC

    def __init__(self):
        """Initialize the handler."""
        self.processed_count = 0
        self._logger = logging.getLogger(__name__)

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Tuple[bool, Any]:
        """
        Handle Monte Carlo event synchronously.

        Parameters
        ----------
        event : Event
            The event containing Monte Carlo parameters
        context : EventContext, optional
            Context (unused for sync)

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result containing Pi estimate and task info
        """
        try:
            if event.type == "monte_carlo_pi":
                iterations = event.data.get("iterations")
                task_id = event.data.get("task_id")

                if iterations is None or task_id is None:
                    return False, "Missing iterations or task_id in event data"

                start_time = datetime.now()
                pi_estimate = calculate_pi_monte_carlo(iterations)
                end_time = datetime.now()

                execution_time = (end_time - start_time).total_seconds()

                self.processed_count += 1

                result = {
                    "task_id": task_id,
                    "pi_estimate": pi_estimate,
                    "iterations": iterations,
                    "execution_time": execution_time,
                    "handler_type": "sync",
                }

                self._logger.info("Sync task %d: Pi=%.6f, time=%.2fs", task_id, pi_estimate, execution_time)
                return True, result
            else:
                return False, f"Invalid event type - expected monte_carlo_pi, got {event.type}"
        except Exception as e:
            return False, str(e)


class MonteCarloThreadHandler(basefunctions.EventHandler):
    """Thread-based handler for Monte Carlo Pi calculation."""

    execution_mode = basefunctions.EXECUTION_MODE_THREAD

    def handle(
        self, event: basefunctions.Event, context: Optional[basefunctions.EventContext] = None
    ) -> Tuple[bool, Any]:
        """
        Handle Monte Carlo event in thread.

        Parameters
        ----------
        event : Event
            The event containing Monte Carlo parameters
        context : EventContext
            Thread context with thread_local_data

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result containing Pi estimate and task info
        """
        try:
            if event.type == "monte_carlo_pi":
                iterations = event.data.get("iterations")
                task_id = event.data.get("task_id")

                if iterations is None or task_id is None:
                    return False, "Missing iterations or task_id in event data"

                # Initialize thread local logger if needed
                logger = logging.getLogger(f"{__name__}.thread")

                # Track thread local stats
                if context and context.thread_local_data:
                    if not hasattr(context.thread_local_data, "processed_count"):
                        context.thread_local_data.processed_count = 0
                    context.thread_local_data.processed_count += 1

                start_time = datetime.now()
                pi_estimate = calculate_pi_monte_carlo(iterations)
                end_time = datetime.now()

                execution_time = (end_time - start_time).total_seconds()

                result = {
                    "task_id": task_id,
                    "pi_estimate": pi_estimate,
                    "iterations": iterations,
                    "execution_time": execution_time,
                    "handler_type": "thread",
                    "thread_id": context.thread_id if context else None,
                }

                logger.info("Thread task %d: Pi=%.6f, time=%.2fs", task_id, pi_estimate, execution_time)
                return True, result
            else:
                return False, f"Invalid event type - expected monte_carlo_pi, got {event.type}"
        except Exception as e:
            return False, str(e)


class MonteCarloCoreletHandler(basefunctions.EventHandler):
    """Corelet-based handler for Monte Carlo Pi calculation."""

    execution_mode = basefunctions.EXECUTION_MODE_CORELET

    def handle(self, event, context=None) -> Tuple[bool, Any]:
        """
        Handle Monte Carlo event in corelet process.

        Parameters
        ----------
        event : Event
            The event containing Monte Carlo parameters
        context : EventContext
            Corelet context with worker reference

        Returns
        -------
        Tuple[bool, Any]
            Success flag and result containing Pi estimate and task info
        """
        try:
            logger = logging.getLogger(__name__)

            if event.type == "monte_carlo_pi":
                iterations = event.data.get("iterations")
                task_id = event.data.get("task_id")

                if iterations is None or task_id is None:
                    return False, "Missing iterations or task_id in event data"

                logger.info("Corelet task %d started: %d iterations", task_id, iterations)

                start_time = datetime.now()
                pi_estimate = calculate_pi_monte_carlo(iterations)
                end_time = datetime.now()

                execution_time = (end_time - start_time).total_seconds()

                result = {
                    "task_id": task_id,
                    "pi_estimate": pi_estimate,
                    "iterations": iterations,
                    "execution_time": execution_time,
                    "handler_type": "corelet",
                    "process_id": context.process_id if context else None,
                }

                logger.info("Corelet task %d: Pi=%.6f, time=%.2fs", task_id, pi_estimate, execution_time)
                return True, result
            else:
                return False, f"Invalid event type - expected monte_carlo_pi, got {event.type}"
        except Exception as e:
            return False, str(e)
