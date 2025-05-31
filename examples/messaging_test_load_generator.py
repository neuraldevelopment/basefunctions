"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 CPU-intensive performance comparison between sync, thread, corelet modes

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
import statistics
from datetime import datetime

import basefunctions
from examples.messaging_test_load_generator_monte_carlo_handlers import (
    MonteCarloEvent,
    MonteCarloSyncHandler,
    MonteCarloThreadHandler,
    MonteCarloCoreletHandler,
    calculate_pi_monte_carlo,
)

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# Number of tasks and iterations to target ~5 seconds per task
NUM_TASKS = 6
ITERATIONS_PER_TASK = 50_000_000  # Adjust this to get ~5 seconds per task

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


def method1_sync_messaging() -> tuple:
    """Process Monte Carlo tasks using sync messaging framework."""
    print("METHOD 1: Using Sync Messaging Framework")
    print(f"Processing {NUM_TASKS} tasks with {ITERATIONS_PER_TASK:,} iterations each")

    # Setup messaging system
    event_bus = basefunctions.EventBus()
    event_bus.clear_handlers()  # Clear any previous handlers

    # Register handler with event type
    basefunctions.EventFactory.register_event_type("monte_carlo_pi", MonteCarloSyncHandler)

    handler = MonteCarloSyncHandler()
    event_bus.register("monte_carlo_pi", handler)

    # Run the test
    start_time = time.time()

    for task_id in range(NUM_TASKS):
        event = MonteCarloEvent(ITERATIONS_PER_TASK, task_id)
        event.timeout = 10
        event_bus.publish(event)

    # Wait for completion
    event_bus.join()

    # Wait a moment for cleanup to complete
    time.sleep(0.1)

    # Collect results from output queue
    success_results = []
    error_results = []

    while not event_bus._output_queue.empty():
        result_event = event_bus._output_queue.get()
        if result_event.type == "result":
            success_results.append(result_event.data["result_data"])
        elif result_event.type == "error":
            error_results.append(result_event.data["error"])

    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate statistics
    pi_estimates = [result["pi_estimate"] for result in success_results if isinstance(result, dict)]
    avg_pi = statistics.mean(pi_estimates) if pi_estimates else 0
    pi_error = abs(avg_pi - 3.141592653589793) if pi_estimates else 0

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Tasks completed: {len(success_results)}")
    print(f"Failed tasks: {len(error_results)}")
    print(f"Average Pi estimate: {avg_pi:.6f}")
    print(f"Pi estimation error: {pi_error:.6f}")
    print(f"Tasks per second: {NUM_TASKS/execution_time:.2f}")

    return execution_time, NUM_TASKS, len(success_results), avg_pi


def method2_thread_messaging() -> tuple:
    """Process Monte Carlo tasks using thread messaging framework."""
    print("METHOD 2: Using Thread Messaging Framework")
    print(f"Processing {NUM_TASKS} tasks with {ITERATIONS_PER_TASK:,} iterations each")

    # Setup messaging system with threads
    event_bus = basefunctions.EventBus()
    event_bus.clear_handlers()  # Clear any previous handlers

    # Register handler with event type
    basefunctions.EventFactory.register_event_type("monte_carlo_pi", MonteCarloThreadHandler)

    handler = MonteCarloThreadHandler()
    event_bus.register("monte_carlo_pi", handler)

    # Run the test
    start_time = time.time()

    for task_id in range(NUM_TASKS):
        event = MonteCarloEvent(ITERATIONS_PER_TASK, task_id)
        event.timeout = 10
        event_bus.publish(event)

    # Wait for completion
    event_bus.join()

    # Wait a moment for cleanup to complete
    time.sleep(0.1)

    # Collect results from output queue
    success_results = []
    error_results = []

    while not event_bus._output_queue.empty():
        result_event = event_bus._output_queue.get()
        if result_event.type == "result":
            success_results.append(result_event.data["result_data"])
        elif result_event.type == "error":
            error_results.append(result_event.data["error"])

    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate statistics
    pi_estimates = [result["pi_estimate"] for result in success_results if isinstance(result, dict)]
    avg_pi = statistics.mean(pi_estimates) if pi_estimates else 0
    pi_error = abs(avg_pi - 3.141592653589793) if pi_estimates else 0

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Tasks completed: {len(success_results)}")
    print(f"Failed tasks: {len(error_results)}")
    print(f"Average Pi estimate: {avg_pi:.6f}")
    print(f"Pi estimation error: {pi_error:.6f}")
    print(f"Tasks per second: {NUM_TASKS/execution_time:.2f}")

    return execution_time, NUM_TASKS, len(success_results), avg_pi


def method3_corelet_messaging() -> tuple:
    """Process Monte Carlo tasks using corelet messaging framework."""
    print("METHOD 3: Using Corelet Messaging Framework")
    print(f"Processing {NUM_TASKS} tasks with {ITERATIONS_PER_TASK:,} iterations each")

    # Setup messaging system with corelets
    event_bus = basefunctions.EventBus()
    event_bus.clear_handlers()  # Clear any previous handlers

    # Register handler with event type
    basefunctions.EventFactory.register_event_type("monte_carlo_pi", MonteCarloCoreletHandler)

    handler = MonteCarloCoreletHandler()
    event_bus.register("monte_carlo_pi", handler)

    # Run the test
    start_time = time.time()

    for task_id in range(NUM_TASKS):
        event = MonteCarloEvent(ITERATIONS_PER_TASK, task_id)
        event.timeout = 10
        event_bus.publish(event)

    # Wait for completion
    event_bus.join()

    # Wait a moment for cleanup to complete
    time.sleep(0.1)

    # Collect results from output queue
    success_results = []
    error_results = []

    while not event_bus._output_queue.empty():
        result_event = event_bus._output_queue.get()
        if result_event.type == "result":
            success_results.append(result_event.data["result_data"])
        elif result_event.type == "error":
            error_results.append(result_event.data["error"])

    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate statistics
    pi_estimates = [result["pi_estimate"] for result in success_results if isinstance(result, dict)]
    avg_pi = statistics.mean(pi_estimates) if pi_estimates else 0
    pi_error = abs(avg_pi - 3.141592653589793) if pi_estimates else 0

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Tasks completed: {len(success_results)}")
    print(f"Failed tasks: {len(error_results)}")
    print(f"Average Pi estimate: {avg_pi:.6f}")
    print(f"Pi estimation error: {pi_error:.6f}")
    print(f"Tasks per second: {NUM_TASKS/execution_time:.2f}")

    return execution_time, NUM_TASKS, len(success_results), avg_pi


def method4_brute_force() -> tuple:
    """Process Monte Carlo tasks using brute force (direct calculation)."""
    print("METHOD 4: Using Brute Force")
    print(f"Processing {NUM_TASKS} tasks with {ITERATIONS_PER_TASK:,} iterations each")

    # Run the test
    start_time = time.time()
    pi_estimates = []

    for task_id in range(NUM_TASKS):
        pi_estimate = calculate_pi_monte_carlo(ITERATIONS_PER_TASK)
        pi_estimates.append(pi_estimate)
        print(f"Completed task {task_id}: Pi = {pi_estimate:.6f}")

    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate statistics
    avg_pi = statistics.mean(pi_estimates)
    pi_error = abs(avg_pi - 3.141592653589793)

    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Tasks completed: {NUM_TASKS}")
    print(f"Average Pi estimate: {avg_pi:.6f}")
    print(f"Pi estimation error: {pi_error:.6f}")
    print(f"Tasks per second: {NUM_TASKS/execution_time:.2f}")

    return execution_time, NUM_TASKS, NUM_TASKS, avg_pi


def calibrate_iterations() -> int:
    """
    Calibrate the number of iterations to achieve ~5 seconds per task.

    Returns
    -------
    int
        Optimal number of iterations for ~5 seconds execution time
    """
    print("Calibrating iterations for ~5 second execution time...")

    # Test with initial guess
    test_iterations = 10_000_000
    start_time = time.time()
    calculate_pi_monte_carlo(test_iterations)
    test_time = time.time() - start_time

    # Scale to target 5 seconds
    target_time = 1.0
    optimal_iterations = int(test_iterations * (target_time / test_time))

    print(f"Test run: {test_iterations:,} iterations took {test_time:.2f} seconds")
    print(f"Optimal iterations for 5 seconds: {optimal_iterations:,}")

    return optimal_iterations


def run_cpu_performance_comparison():
    """Run CPU-intensive performance comparison between all methods."""
    print("Starting CPU-intensive performance comparison...")
    print("=" * 80)

    # Calibrate iterations for consistent timing
    global ITERATIONS_PER_TASK
    ITERATIONS_PER_TASK = calibrate_iterations()

    print(f"\nUsing {ITERATIONS_PER_TASK:,} iterations per task")
    print(f"Expected total computation time per method: ~{NUM_TASKS * 5} seconds")

    # Store results
    results = {}

    # Run method 1: Sync Messaging
    print("\n" + "=" * 80)
    time1, tasks1, completed1, pi1 = method1_sync_messaging()
    results["Sync"] = (time1, tasks1, completed1, pi1)

    # Run method 2: Thread Messaging
    print("\n" + "=" * 80)
    time2, tasks2, completed2, pi2 = method2_thread_messaging()
    results["Thread"] = (time2, tasks2, completed2, pi2)

    # Run method 3: Corelet Messaging
    print("\n" + "=" * 80)
    time3, tasks3, completed3, pi3 = method3_corelet_messaging()
    results["Corelet"] = (time3, tasks3, completed3, pi3)

    # Run method 4: Brute Force
    print("\n" + "=" * 80)
    time4, tasks4, completed4, pi4 = method4_brute_force()
    results["Brute Force"] = (time4, tasks4, completed4, pi4)

    # Compare results
    print("\n" + "=" * 80)
    print("COMPREHENSIVE CPU-INTENSIVE PERFORMANCE COMPARISON")
    print("=" * 80)

    baseline_time = results["Brute Force"][0]

    for method, (exec_time, total_tasks, completed_tasks, avg_pi) in results.items():
        speedup = baseline_time / exec_time if exec_time > 0 else 0
        efficiency = completed_tasks / total_tasks * 100 if total_tasks > 0 else 0
        pi_error = abs(avg_pi - 3.141592653589793)

        print(
            f"{method:12}: {exec_time:8.2f}s | {completed_tasks:2d}/{total_tasks:2d} tasks | "
            f"Pi: {avg_pi:.6f} | Error: {pi_error:.6f} | Speedup: {speedup:.2f}x"
        )

    # Print system stats
    print("\n" + "=" * 80)
    print("SYSTEM STATISTICS")
    print("=" * 80)

    event_bus = basefunctions.EventBus()
    stats = event_bus.get_stats()

    for key, value in stats.items():
        print(f"{key}: {value}")

    # Shutdown
    event_bus.shutdown()


if __name__ == "__main__":
    run_cpu_performance_comparison()
