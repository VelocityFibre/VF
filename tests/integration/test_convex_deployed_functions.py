#!/usr/bin/env python3
"""
Test what functions are actually deployed in Convex and test with those.
"""

import os
import json
import requests
from convex_agent import load_env, ConvexAgent


def discover_convex_functions():
    """Try to discover what functions are actually deployed."""

    load_env()
    convex_url = os.environ.get("CONVEX_URL")

    print("="*70)
    print("DISCOVERING DEPLOYED CONVEX FUNCTIONS")
    print("="*70)
    print(f"\nConvex URL: {convex_url}\n")

    # All possible function patterns to test
    test_functions = [
        # Tasks
        "tasks:list", "tasks:listTasks", "tasks:getAll",
        "tasks:add", "tasks:addTask", "tasks:create",
        "tasks:get", "tasks:getTask", "tasks:getById",
        "tasks:update", "tasks:updateTask",
        "tasks:delete", "tasks:deleteTask",
        "tasks:search", "tasks:searchTasks",
        "tasks:stats", "tasks:getTaskStats", "tasks:getStats",

        # Contractors
        "contractors:list", "contractors:listAll", "contractors:getAll",
        "contractors:create", "contractors:add",

        # Projects
        "projects:list", "projects:listAll", "projects:getAll",
        "projects:create", "projects:add",

        # Sync
        "sync:getStats", "sync:getSyncStats",
        "sync:getLastSync", "sync:getLastSyncTime",

        # System
        "listTasks", "getTasks", "getAllTasks",
    ]

    working_functions = []
    failed_functions = []

    for function_path in test_functions:
        try:
            payload = {"path": function_path, "args": {}}

            # Try query endpoint
            response = requests.post(
                f"{convex_url}/api/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()

                # Check if it's a valid response
                if "value" in result or "status" in result:
                    print(f"✅ {function_path:40} → Working!")
                    working_functions.append({
                        "path": function_path,
                        "response": result
                    })
                else:
                    failed_functions.append(function_path)
            elif response.status_code == 400:
                # Function exists but wrong args
                error_msg = response.json().get("error", "")
                if "not found" not in error_msg.lower():
                    print(f"⚠️  {function_path:40} → Exists but needs args")
                    working_functions.append({
                        "path": function_path,
                        "response": {"note": "exists", "error": error_msg}
                    })
            else:
                failed_functions.append(function_path)

        except Exception as e:
            failed_functions.append(function_path)

    print(f"\n" + "="*70)
    print(f"SUMMARY")
    print("="*70)
    print(f"Working functions: {len(working_functions)}")
    print(f"Not found: {len(failed_functions)}")

    return working_functions


def test_agent_with_deployed_functions(working_functions):
    """Test agent with only the functions that actually work."""

    print("\n" + "="*70)
    print("TESTING AGENT WITH DEPLOYED FUNCTIONS")
    print("="*70)

    if not working_functions:
        print("\n❌ No working functions found - Convex may not be properly deployed")
        return []

    # Initialize agent
    agent = ConvexAgent()
    test_results = []

    # Get the function paths that work
    function_paths = [f["path"] for f in working_functions]

    # Test based on what functions exist
    if any("task" in f.lower() and ("list" in f.lower() or "get" in f.lower()) for f in function_paths):
        print("\n📋 Testing Task Listing...")
        queries = [
            "Show me all tasks",
            "List tasks",
            "How many tasks do we have?",
        ]

        for query in queries:
            try:
                agent.reset_conversation()
                print(f"\n🔍 Query: '{query}'")
                response = agent.chat(query)
                print(f"✅ Response: {response[:200]}...")
                test_results.append((query, True, response))
            except Exception as e:
                print(f"❌ Error: {e}")
                test_results.append((query, False, str(e)))

    if any("stats" in f.lower() for f in function_paths):
        print("\n📊 Testing Statistics...")
        queries = [
            "Give me task statistics",
            "Show me stats",
        ]

        for query in queries:
            try:
                agent.reset_conversation()
                print(f"\n🔍 Query: '{query}'")
                response = agent.chat(query)
                print(f"✅ Response: {response[:200]}...")
                test_results.append((query, True, response))
            except Exception as e:
                print(f"❌ Error: {e}")
                test_results.append((query, False, str(e)))

    # Test add function if it exists
    if any("add" in f.lower() or "create" in f.lower() for f in function_paths):
        print("\n➕ Testing Add Function...")
        try:
            agent.reset_conversation()
            query = "Add a test task called 'Test Agent Integration' with high priority"
            print(f"\n🔍 Query: '{query}'")
            response = agent.chat(query)
            print(f"✅ Response: {response[:200]}...")
            test_results.append((query, True, response))

            # Now try to list again
            agent.reset_conversation()
            response2 = agent.chat("Show me all tasks now")
            print(f"✅ After adding: {response2[:200]}...")
            test_results.append(("List after add", True, response2))

        except Exception as e:
            print(f"❌ Error: {e}")
            test_results.append((query, False, str(e)))

    return test_results


def main():
    print("\n" + "="*70)
    print("CONVEX AGENT - DEPLOYED FUNCTIONS TEST")
    print("="*70)

    load_env()

    # Step 1: Discover what's deployed
    working_functions = discover_convex_functions()

    if not working_functions:
        print("\n⚠️  WARNING: No Convex functions found!")
        print("\nPossible issues:")
        print("1. Convex backend not deployed")
        print("2. Functions have different names than expected")
        print("3. Authentication required")
        print("\nCheck: https://dashboard.convex.dev/deployment/quixotic-crow-802")
        return 1

    # Save discovered functions
    with open("convex_discovered_functions.json", "w") as f:
        json.dump(working_functions, f, indent=2)
    print(f"\n💾 Saved discovered functions to: convex_discovered_functions.json")

    # Step 2: Test agent with what we found
    test_results = test_agent_with_deployed_functions(working_functions)

    # Step 3: Report
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)

    if test_results:
        passed = sum(1 for _, success, _ in test_results if success)
        failed = sum(1 for _, success, _ in test_results if not success)

        print(f"\nTotal Tests: {len(test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        for query, success, result in test_results:
            status = "✅" if success else "❌"
            print(f"{status} {query[:60]}")

        if failed == 0:
            print("\n✅ ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            return 1
    else:
        print("\n⚠️  No tests could be run")
        return 1


if __name__ == "__main__":
    exit(main())
