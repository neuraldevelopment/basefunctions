"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Simple CMD demo - Directory listing with ls command
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


def main():
    """Main demo function."""
    runner = basefunctions.DemoRunner()

    # Setup
    event_bus = basefunctions.EventBus()
    basefunctions.EventFactory.register_event_type("list_directory", basefunctions.DefaultCmdHandler)

    @runner.test("List /usr directory")
    def test_usr():
        event = basefunctions.Event(
            "list_directory",
            event_exec_mode=basefunctions.EXECUTION_MODE_CMD,
            event_data={"executable": "ls", "args": ["-la", "/usr"], "cwd": "/"},
        )
        event_id = event_bus.publish(event)
        event_bus.join()

        results = event_bus.get_results()

        # Find result for our event
        our_result = None
        for result_event in results:
            if result_event.event_id == event_id:
                our_result = result_event
                break

        if our_result and our_result.success:
            lines = len(our_result.data["stdout"].strip().split("\n")) if our_result.data["stdout"] else 0
            print(f"/usr contains {lines} entries")
            return True
        elif our_result and not our_result.success:
            raise Exception(f"Command failed: {our_result.data}")
        else:
            raise Exception("No results from /usr")

    @runner.test("List /bin directory")
    def test_bin():
        event = basefunctions.Event(
            "list_directory",
            event_exec_mode=basefunctions.EXECUTION_MODE_CMD,
            event_data={"executable": "ls", "args": ["-la", "/bin"], "cwd": "/"},
        )
        event_id = event_bus.publish(event)
        event_bus.join()

        results = event_bus.get_results()

        # Find result for our event
        our_result = None
        for result_event in results:
            if result_event.event_id == event_id:
                our_result = result_event
                break

        if our_result and our_result.success:
            lines = len(our_result.data["stdout"].strip().split("\n")) if our_result.data["stdout"] else 0
            print(f"/bin contains {lines} entries")
            return True
        elif our_result and not our_result.success:
            raise Exception(f"Command failed: {our_result.data}")
        else:
            raise Exception("No results from /bin")

    @runner.test("List /tmp directory")
    def test_tmp():
        event = basefunctions.Event(
            "list_directory",
            event_exec_mode=basefunctions.EXECUTION_MODE_CMD,
            event_data={"executable": "ls", "args": ["-la", "/tmp"], "cwd": "/"},
        )
        event_id = event_bus.publish(event)
        event_bus.join()

        results = event_bus.get_results()

        # Find result for our event
        our_result = None
        for result_event in results:
            if result_event.event_id == event_id:
                our_result = result_event
                break

        if our_result and our_result.success:
            lines = len(our_result.data["stdout"].strip().split("\n")) if our_result.data["stdout"] else 0
            print(f"/tmp contains {lines} entries")
            return True
        elif our_result and not our_result.success:
            raise Exception(f"Command failed: {our_result.data}")
        else:
            raise Exception("No results from /tmp")

    # Run tests
    runner.run_all_tests()
    runner.print_results("CMD Mode Directory Listing Demo")

    # Cleanup
    event_bus.shutdown()


if __name__ == "__main__":
    main()
