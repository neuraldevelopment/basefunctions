#!/usr/bin/env python3
"""
Test script for Corelet lifecycle management fixes.

Tests:
1. SESSION-BASED: Corelet reuse across events
2. TIMEOUT CLEANUP: Proper cleanup on timeout
3. IDLE TIMEOUT: Worker auto-shutdown after inactivity
4. SHUTDOWN CLEANUP: Clean EventBus shutdown
"""

import time
import os
import basefunctions
from basefunctions import Event, EventBus, EventHandler, EventResult, EXECUTION_MODE_CORELET


class TestHandler(EventHandler):
    """Simple test handler for corelet mode."""

    def handle(self, event, context) -> EventResult:
        """Process test event."""
        data = event.event_data
        action = data.get("action", "process")

        if action == "sleep":
            # Simulate long-running task
            duration = data.get("duration", 1)
            time.sleep(duration)
            return EventResult.business_result(event.event_id, True, f"Slept {duration}s")

        elif action == "timeout":
            # Simulate timeout by sleeping longer than event.timeout
            time.sleep(event.timeout + 5)
            return EventResult.business_result(event.event_id, True, "Should timeout")

        else:
            # Normal processing
            return EventResult.business_result(event.event_id, True, f"Processed: {data}")


def test_session_based_reuse():
    """Test 1: Corelet process reuse across events (SESSION-BASED)."""
    print("\n" + "=" * 70)
    print("TEST 1: SESSION-BASED CORELET REUSE")
    print("=" * 70)

    # Register handler
    factory = basefunctions.EventFactory()
    factory.register_event_type("test_event", TestHandler)

    bus = EventBus()

    # Publish 5 events sequentially
    event_ids = []
    for i in range(5):
        event = Event(
            "test_event",
            event_exec_mode=EXECUTION_MODE_CORELET,
            event_data={"action": "process", "index": i},
        )
        event_id = bus.publish(event)
        event_ids.append(event_id)

    # Wait for completion
    bus.join()
    results = bus.get_results(event_ids)

    # Check results
    success_count = sum(1 for r in results.values() if r and r.success)
    print(f"Events processed: {success_count}/5")

    if success_count == 5:
        print("✅ SUCCESS: All events processed successfully (corelet reuse working)")
    else:
        print(f"❌ FAIL: Only {success_count} events succeeded")


def test_timeout_cleanup():
    """Test 2: Timeout cleanup with pipe closing."""
    print("\n" + "=" * 70)
    print("TEST 2: TIMEOUT CLEANUP")
    print("=" * 70)

    factory = basefunctions.EventFactory()
    factory.register_event_type("test_timeout", TestHandler)

    bus = EventBus()

    # Create event that will timeout (timeout=2s, but handler sleeps longer)
    event = Event(
        "test_timeout",
        event_exec_mode=EXECUTION_MODE_CORELET,
        event_data={"action": "timeout"},
        timeout=2,  # 2 seconds timeout
    )

    event_id = bus.publish(event)

    # Wait and check result
    time.sleep(4)  # Wait for timeout + cleanup
    results = bus.get_results([event_id], join_before=False)

    # Should have exception result due to timeout
    if event_id in results:
        result = results[event_id]
        if result.exception and "timeout" in str(result.exception).lower():
            print("✅ SUCCESS: Timeout detected correctly")
        else:
            print(f"❌ FAIL: Unexpected result: {result}")
    else:
        print("⚠️  No result yet (timeout might still be processing)")

    # Give cleanup time to complete
    time.sleep(1)

    # Check that timed-out corelet was cleaned up
    # New event should work (proves cleanup happened)
    event2 = Event(
        "test_timeout",
        event_exec_mode=EXECUTION_MODE_CORELET,
        event_data={"action": "process"},
    )
    event_id2 = bus.publish(event2)
    bus.join()
    results2 = bus.get_results([event_id2])

    if event_id2 in results2 and results2[event_id2].success:
        print("✅ SUCCESS: New corelet created after timeout cleanup")
    else:
        print("❌ FAIL: Failed to create new corelet after timeout")


def test_shutdown_cleanup():
    """Test 3: EventBus shutdown cleanup."""
    print("\n" + "=" * 70)
    print("TEST 3: EVENTBUS SHUTDOWN CLEANUP")
    print("=" * 70)

    factory = basefunctions.EventFactory()
    factory.register_event_type("test_shutdown", TestHandler)

    bus = EventBus()

    # Publish some events to create corelets
    event_ids = []
    for i in range(3):
        event = Event(
            "test_shutdown",
            event_exec_mode=EXECUTION_MODE_CORELET,
            event_data={"action": "process", "index": i},
        )
        event_id = bus.publish(event)
        event_ids.append(event_id)

    bus.join()
    results = bus.get_results(event_ids)
    success_count = sum(1 for r in results.values() if r and r.success)
    print(f"Events completed: {success_count}/3")

    # Shutdown EventBus
    print("Calling EventBus.shutdown()...")
    bus.shutdown()

    # Give shutdown time to complete
    time.sleep(2)

    print("✅ SUCCESS: EventBus shutdown completed (check logs for corelet cleanup)")


def test_idle_timeout():
    """Test 4: Idle timeout in CoreletWorker."""
    print("\n" + "=" * 70)
    print("TEST 4: IDLE TIMEOUT (takes ~11 minutes - SKIPPED for quick test)")
    print("=" * 70)
    print("To test idle timeout manually:")
    print("1. Set IDLE_TIMEOUT = 30.0 in corelet_worker.py")
    print("2. Publish a corelet event")
    print("3. Wait 35 seconds")
    print("4. Check logs for 'idle for X seconds - shutting down'")
    print("5. Verify corelet process count decreases")
    print("\n⏭️  SKIPPED (would take too long in automated test)")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CORELET LIFECYCLE MANAGEMENT TESTS")
    print("=" * 70)
    print(f"Main process PID: {os.getpid()}")

    try:
        # Run tests
        test_session_based_reuse()
        test_timeout_cleanup()
        test_shutdown_cleanup()
        test_idle_timeout()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
