"""
Demo script for testing AliveProgressTracker with EventBus.
Processes 100 events with random delays (0-4 seconds).
"""

import basefunctions
import time
import random


# Simple test handler
class DelayHandler(basefunctions.EventHandler):
    """Handler that simulates work with random delay."""

    def handle(self, event, context):
        delay = event.event_data.get("delay", 1)
        time.sleep(delay)
        return basefunctions.EventResult.business_result(event.event_id, True, f"Processed after {delay}s")


def main():
    # Register handler
    basefunctions.EventFactory().register_event_type("delay_task", DelayHandler)

    # Create EventBus
    bus = basefunctions.EventBus()

    # Use tracker with context manager
    with basefunctions.AliveProgressTracker(total=100, desc="Processing tasks") as tracker:
        # Set tracker for EventBus
        bus.set_progress_tracker(tracker, progress_steps=1)

        # Publish 100 events with random delays
        event_ids = []
        for i in range(100):
            delay = random.uniform(0, 4)
            event = basefunctions.Event(
                event_type="delay_task",
                event_exec_mode=basefunctions.EXECUTION_MODE_THREAD,
                event_data={"delay": delay, "task_id": i},
            )
            event_id = bus.publish(event)
            event_ids.append(event_id)

        # Wait and get results
        results = bus.get_results(event_ids)

        # Clear progress tracker before context exit
        bus.clear_progress_tracker()

    # Show summary (after tracker is closed)
    success = sum(1 for r in results.values() if r.success)
    print(f"\nDone! {success}/{len(results)} tasks successful")

    # Shutdown
    bus.shutdown()


if __name__ == "__main__":
    main()
