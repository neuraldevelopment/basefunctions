import time
import basefunctions
from basefunctions import Event, EventBus, EventFactory, EventHandler, EventResult, EXECUTION_MODE_THREAD

class SimpleTestHandler(EventHandler):
    """Simple test handler that always succeeds."""

    def handle(self, event, context):
        print(f"Handling event: {event.event_id}")
        return EventResult.business_result(event.event_id, True, "OK")

# Setup
factory = EventFactory()
factory.register_event_type("test_event", SimpleTestHandler)

bus = EventBus()
bus.register_rate_limit("test_event", requests_per_second=5, burst=0)

# Publish events
start_time = time.time()
event_ids = []
for i in range(5):
    event = Event("test_event", event_exec_mode=EXECUTION_MODE_THREAD)
    event_id = bus.publish(event)
    event_ids.append(event_id)
    print(f"Published event {i+1}: {event_id}")

# Wait and check
print("Waiting for results...")
timeout = 10
while time.time() - start_time < timeout:
    results = bus.get_results(event_ids, join_before=False)
    print(f"Results so far: {len(results)} / {len(event_ids)}")
    if len(results) == len(event_ids):
        break
    time.sleep(0.5)

elapsed = time.time() - start_time
print(f"Elapsed time: {elapsed:.2f}s")
print(f"Final results: {len(results)} / {len(event_ids)}")

# Check metrics
metrics = bus.get_rate_limit_metrics("test_event")
print(f"Metrics: {metrics}")
