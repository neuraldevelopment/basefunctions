"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Simple EXEC demo - Directory listing with ls command
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
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


class DummyExecHandler(basefunctions.EventHandler):
    """Dummy handler for EXEC mode - not actually used."""

    execution_mode = basefunctions.EXECUTION_MODE_EXEC

    def handle(self, event, context=None):
        return True, "dummy"


def main():
    """Main demo function."""
    runner = basefunctions.DemoRunner()

    # Setup
    event_bus = basefunctions.EventBus()
    basefunctions.EventFactory.register_event_type("list_directory", DummyExecHandler)

    @runner.test("List /usr directory")
    def test_usr():
        event = basefunctions.Event("list_directory", data={"executable": "ls", "args": ["-la", "/usr"], "cwd": "/"})
        event_bus.publish(event)
        event_bus.join()

        results, errors = event_bus.get_results()
        if errors:
            raise Exception(f"Errors: {errors}")

        if results and results[0].get("success"):
            lines = len(results[0]["stdout"].strip().split("\n")) if results[0]["stdout"] else 0
            print(f"/usr contains {lines} entries")
            return True
        raise Exception("No results from /usr")

    @runner.test("List /bin directory")
    def test_bin():
        event = basefunctions.Event("list_directory", data={"executable": "ls", "args": ["-la", "/bin"], "cwd": "/"})
        event_bus.publish(event)
        event_bus.join()

        results, errors = event_bus.get_results()
        if errors:
            raise Exception(f"Errors: {errors}")

        if results and results[0].get("success"):
            lines = len(results[0]["stdout"].strip().split("\n")) if results[0]["stdout"] else 0
            print(f"/bin contains {lines} entries")
            return True
        raise Exception("No results from /bin")

    @runner.test("List /tmp directory")
    def test_tmp():
        event = basefunctions.Event("list_directory", data={"executable": "ls", "args": ["-la", "/tmp"], "cwd": "/"})
        event_bus.publish(event)
        event_bus.join()

        results, errors = event_bus.get_results()
        if errors:
            raise Exception(f"Errors: {errors}")

        if results and results[0].get("success"):
            lines = len(results[0]["stdout"].strip().split("\n")) if results[0]["stdout"] else 0
            print(f"/tmp contains {lines} entries")
            return True
        raise Exception("No results from /tmp")

    # Run tests
    runner.run_all_tests()
    runner.print_results("EXEC Mode Directory Listing Demo")

    # Cleanup
    event_bus.shutdown()


if __name__ == "__main__":
    main()
