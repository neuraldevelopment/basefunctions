#!/usr/bin/env python3
"""
=============================================================================
  Licensed Materials, Property of neuraldevelopment, Munich
  Project : basefunctions
  Copyright (c) by neuraldevelopment
  All rights reserved.
  Description:
  HttpClient demonstration with standalone and EventBus usage
 =============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import time
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


def main():
    """Main demo function showcasing HttpClient capabilities."""

    # Initialize DemoRunner with custom settings
    demo = basefunctions.DemoRunner(max_width=120, error_width=100, log_level="INFO")

    print("🌐 HttpClient Demo - Standalone vs EventBus Usage")
    print("=" * 60)

    # Test 1: Standalone HttpClient Usage
    @demo.test("Standalone HTTP GET - httpbin.org")
    def test_standalone_get():
        with basefunctions.HttpClient(timeout=10, max_retries=2) as client:
            response = client.get("https://httpbin.org/get", params={"demo": "standalone"})
            assert response.status_code == 200
            data = response.json()
            assert "args" in data
            assert data["args"]["demo"] == "standalone"

    # Test 2: Standalone POST Request
    @demo.test("Standalone HTTP POST - JSON data")
    def test_standalone_post():
        with basefunctions.HttpClient() as client:
            payload = {"name": "HttpClient", "version": "1.0", "test": True}
            response = client.post("https://httpbin.org/post", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["json"]["name"] == "HttpClient"

    # Test 3: HTTP Headers and Authentication
    @demo.test("Standalone HTTP with custom headers")
    def test_standalone_headers():
        headers = {"User-Agent": "basefunctions-HttpClient/1.0", "X-Demo": "headers-test"}
        with basefunctions.HttpClient() as client:
            response = client.get("https://httpbin.org/headers", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "basefunctions-HttpClient" in data["headers"]["User-Agent"]

    # Test 4: Error Handling - 404 Not Found
    @demo.test("Standalone HTTP error handling - 404")
    def test_standalone_404():
        try:
            with basefunctions.HttpClient(max_retries=1) as client:
                response = client.get("https://httpbin.org/status/404")
        except basefunctions.HttpClientError as e:
            assert "404" in str(e)
        else:
            raise AssertionError("Expected HttpClientError for 404 status")

    # Test 5: Timeout Handling
    @demo.test("Standalone HTTP timeout - slow response")
    def test_standalone_timeout():
        try:
            with basefunctions.HttpClient(connect_timeout=1, read_timeout=1, max_retries=1) as client:
                response = client.get("https://httpbin.org/delay/3")
        except (basefunctions.HttpTimeoutError, basefunctions.HttpRetryExhaustedError, basefunctions.HttpClientError):
            pass  # Expected - any of these is fine
        else:
            raise AssertionError("Expected timeout/error")  # Register HTTP handlers for EventBus usage
        basefunctions.register_http_handlers()

    # Test 6: EventBus HTTP GET
    @demo.test("EventBus HTTP GET - via event system")
    def test_eventbus_get():
        event_bus = basefunctions.EventBus()

        # Create HTTP GET event
        http_event = basefunctions.Event(
            "http_get",
            data={"url": "https://httpbin.org/get", "params": {"demo": "eventbus", "timestamp": int(time.time())}},
            timeout=15,
            max_retries=2,
        )

        # Publish event and get ID
        event_id = event_bus.publish(http_event)
        event_bus.join()

        # Get results using new API
        results, errors = event_bus.get_results()

        assert len(errors) == 0, f"EventBus HTTP request failed: {[e.data['error'] for e in errors]}"
        assert len(results) == 1

        # Find our result by ID
        our_result = None
        for result in results:
            if result.id == event_id:
                our_result = result.data["result_data"]
                break

        assert our_result is not None, "Result not found for our event"
        assert our_result["status_code"] == 200
        assert "json" in our_result
        assert our_result["json"]["args"]["demo"] == "eventbus"

    # Test 7: EventBus HTTP POST
    @demo.test("EventBus HTTP POST - JSON API")
    def test_eventbus_post():
        event_bus = basefunctions.EventBus()

        # Create HTTP POST event
        http_event = basefunctions.Event(
            "http_json_api",
            data={
                "url": "https://httpbin.org/post",
                "method": "POST",
                "json": {
                    "framework": "basefunctions",
                    "component": "EventBus + HttpClient",
                    "features": ["timeout", "retry", "async"],
                },
            },
            timeout=10,
        )

        # Publish event and get ID
        event_id = event_bus.publish(http_event)
        event_bus.join()

        # Get results using new API
        results, errors = event_bus.get_results()

        assert len(errors) == 0, f"EventBus HTTP POST failed: {[e.data['error'] for e in errors]}"
        assert len(results) == 1

        # Find our result by ID
        our_result = None
        for result in results:
            if result.id == event_id:
                our_result = result.data["result_data"]
                break

        assert our_result is not None, "Result not found for our event"
        assert our_result["status_code"] == 200
        assert our_result["json"]["json"]["framework"] == "basefunctions"

    # Test 8: Multiple Parallel HTTP Requests via EventBus
    @demo.test("EventBus parallel HTTP requests")
    def test_eventbus_parallel():
        event_bus = basefunctions.EventBus()

        # Create multiple HTTP events and track IDs
        urls = ["https://httpbin.org/get?id=1", "https://httpbin.org/get?id=2", "https://httpbin.org/get?id=3"]
        event_ids = []

        for i, url in enumerate(urls):
            http_event = basefunctions.Event("http_get", data={"url": url}, timeout=10)
            event_id = event_bus.publish(http_event)
            event_ids.append(event_id)

        # Wait for all requests to complete
        event_bus.join()

        # Get results using new API
        results, errors = event_bus.get_results()

        assert len(errors) == 0, f"Parallel requests failed: {[e.data['error'] for e in errors]}"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

        # Verify all our events succeeded
        our_results = []
        for event_id in event_ids:
            for result in results:
                if result.id == event_id:
                    our_results.append(result.data["result_data"])
                    break

        assert len(our_results) == 3, "Not all events found in results"

        # Verify all requests succeeded
        for result in our_results:
            assert result["status_code"] == 200

    # Test 9: Performance Comparison
    @demo.test("Performance test - context detection")
    def test_performance():
        # Test standalone performance
        start_time = time.time()
        with basefunctions.HttpClient() as client:
            for _ in range(3):
                response = client.get("https://httpbin.org/get")
                assert response.status_code == 200
        standalone_time = time.time() - start_time

        # Test EventBus performance
        event_bus = basefunctions.EventBus()
        start_time = time.time()

        event_ids = []
        for i in range(3):
            http_event = basefunctions.Event("http_get", data={"url": "https://httpbin.org/get"}, timeout=10)
            event_id = event_bus.publish(http_event)
            event_ids.append(event_id)

        event_bus.join()
        results, errors = event_bus.get_results()
        eventbus_time = time.time() - start_time

        assert len(errors) == 0
        assert len(results) == 3

        # Verify our events completed
        our_results = []
        for event_id in event_ids:
            for result in results:
                if result.id == event_id:
                    our_results.append(result.data["result_data"])
                    break

        assert len(our_results) == 3

        # Performance is not the focus, just verify both work
        assert standalone_time > 0
        assert eventbus_time > 0

    # Run all tests
    demo.run_all_tests()

    # Print results
    demo.print_results("🌐 HttpClient Demo Results")

    # Print performance metrics
    performance_data = [
        ("HttpClient Features", "Context-aware resilience"),
        ("Standalone Mode", "Own timeout/retry logic"),
        ("EventBus Mode", "Leverages EventBus timeout/retry"),
        ("Threading", "Non-blocking via EventBus threads"),
        ("Error Handling", "Comprehensive exception hierarchy"),
        ("Connection Pooling", "Session-based reuse"),
    ]

    demo.print_performance_table(performance_data, "📊 HttpClient Features")

    # Get summary
    passed, total = demo.get_summary()

    print(f"\n🎯 Demo Summary:")
    print(f"   • {passed}/{total} tests passed")
    print(f"   • Context detection: {'✓ Working' if passed > 5 else '✗ Issues'}")
    print(f"   • EventBus integration: {'✓ Working' if passed > 7 else '✗ Issues'}")

    if demo.has_failures():
        print("\n❌ Some tests failed. Check the error details above.")
        failed_tests = demo.get_failed_tests()
        for test_name, error in failed_tests:
            print(f"   • {test_name}: {error}")
        return 1
    else:
        print("\n✅ All tests passed! HttpClient is working correctly.")
        return 0


if __name__ == "__main__":
    exit(main())
