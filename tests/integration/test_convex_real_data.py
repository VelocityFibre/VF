#!/usr/bin/env python3
"""
Test Convex Agent with REAL data from all collections.
Tests contractors, projects, tasks, and sync data.
"""

import os
import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from convex_agent import ConvexAgent, load_env


def check_all_convex_data():
    """Check all collections in Convex database."""

    load_env()
    convex_url = os.environ.get("CONVEX_URL")

    print("="*70)
    print("CHECKING ALL CONVEX COLLECTIONS FOR REAL DATA")
    print("="*70)
    print(f"\nConvex URL: {convex_url}\n")

    # All possible collections/functions to check
    collections = [
        ("tasks:listTasks", "Tasks"),
        ("contractors:list", "Contractors"),
        ("contractors:listAll", "Contractors (alt)"),
        ("projects:list", "Projects"),
        ("projects:listAll", "Projects (alt)"),
        ("sync:getSyncStats", "Sync Stats"),
        ("syncRecords:list", "Sync Records"),
    ]

    found_data = {}

    for function_path, name in collections:
        try:
            payload = {"path": function_path, "args": {}}
            response = requests.post(
                f"{convex_url}/api/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                value = result.get("value", result)

                # Count items
                count = 0
                if isinstance(value, dict):
                    # Check common patterns
                    if "tasks" in value:
                        count = len(value["tasks"])
                    elif "contractors" in value:
                        count = len(value["contractors"])
                    elif "projects" in value:
                        count = len(value["projects"])
                    elif "total" in value:
                        count = value["total"]
                    else:
                        # Count items in all arrays
                        for v in value.values():
                            if isinstance(v, list):
                                count += len(v)
                elif isinstance(value, list):
                    count = len(value)

                if count > 0:
                    print(f"✅ {name:25} → {count} items")
                    found_data[name] = {
                        "function": function_path,
                        "count": count,
                        "sample": value
                    }
                else:
                    print(f"⚪ {name:25} → empty")
            else:
                print(f"❌ {name:25} → Error {response.status_code}")

        except Exception as e:
            print(f"❌ {name:25} → {str(e)[:50]}")

    return found_data


def test_with_real_data(agent, found_data):
    """Run tests with actual data found in Convex."""

    print("\n" + "="*70)
    print("TESTING AGENT WITH REAL DATA")
    print("="*70)

    test_results = []

    # Test based on what data we found
    if "Contractors" in found_data or "Contractors (alt)" in found_data:
        print("\n📋 Testing Contractor Queries...")

        queries = [
            "How many contractors do we have?",
            "List all contractors",
            "Show me contractor details",
        ]

        for query in queries:
            try:
                agent.reset_conversation()
                print(f"\n🔍 Query: '{query}'")
                response = agent.chat(query)
                print(f"✅ Response ({len(response)} chars):\n{response[:300]}...")
                test_results.append(("Contractors", query, True, len(response)))
            except Exception as e:
                print(f"❌ Error: {e}")
                test_results.append(("Contractors", query, False, str(e)))

    if "Projects" in found_data or "Projects (alt)" in found_data:
        print("\n📁 Testing Project Queries...")

        queries = [
            "How many projects do we have?",
            "List all projects",
            "Show me project statuses",
        ]

        for query in queries:
            try:
                agent.reset_conversation()
                print(f"\n🔍 Query: '{query}'")
                response = agent.chat(query)
                print(f"✅ Response ({len(response)} chars):\n{response[:300]}...")
                test_results.append(("Projects", query, True, len(response)))
            except Exception as e:
                print(f"❌ Error: {e}")
                test_results.append(("Projects", query, False, str(e)))

    if "Tasks" in found_data:
        print("\n✅ Testing Task Queries...")

        queries = [
            "Show me all tasks",
            "What tasks are in progress?",
            "Give me task statistics",
        ]

        for query in queries:
            try:
                agent.reset_conversation()
                print(f"\n🔍 Query: '{query}'")
                response = agent.chat(query)
                print(f"✅ Response ({len(response)} chars):\n{response[:300]}...")
                test_results.append(("Tasks", query, True, len(response)))
            except Exception as e:
                print(f"❌ Error: {e}")
                test_results.append(("Tasks", query, False, str(e)))

    # Complex multi-collection query
    print("\n🔄 Testing Complex Multi-Collection Query...")
    try:
        agent.reset_conversation()
        query = "Give me a comprehensive overview of our system - contractors, projects, and tasks"
        print(f"\n🔍 Query: '{query}'")
        response = agent.chat(query)
        print(f"✅ Response ({len(response)} chars):\n{response[:500]}...")
        test_results.append(("Multi-Collection", query, True, len(response)))
    except Exception as e:
        print(f"❌ Error: {e}")
        test_results.append(("Multi-Collection", query, False, str(e)))

    return test_results


def check_if_sync_needed():
    """Check if we need to sync data from Neon to Convex."""

    print("\n" + "="*70)
    print("CHECKING IF SYNC IS NEEDED")
    print("="*70)

    # Check if Neon has data
    try:
        import psycopg2
        neon_url = os.environ.get("NEON_DATABASE_URL")

        if not neon_url:
            print("⚠️  NEON_DATABASE_URL not set")
            return

        conn = psycopg2.connect(neon_url)
        cursor = conn.cursor()

        # Check contractors
        cursor.execute("SELECT COUNT(*) FROM contractors WHERE is_active = true")
        contractor_count = cursor.fetchone()[0]

        # Check projects
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'active'")
        project_count = cursor.fetchone()[0]

        print(f"\n📊 Neon Database:")
        print(f"   Active Contractors: {contractor_count}")
        print(f"   Active Projects: {project_count}")

        if contractor_count > 0 or project_count > 0:
            print(f"\n💡 RECOMMENDATION:")
            print(f"   Run sync to populate Convex with this data:")
            print(f"   ./venv/bin/python sync_neon_to_convex.py")

        conn.close()

    except Exception as e:
        print(f"⚠️  Could not check Neon database: {e}")


def main():
    print("\n" + "="*70)
    print("CONVEX AGENT - REAL DATA TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    load_env()

    # Step 1: Check what data exists
    found_data = check_all_convex_data()

    if not found_data:
        print("\n⚠️  NO DATA FOUND IN CONVEX")
        check_if_sync_needed()
        print("\n" + "="*70)
        print("CANNOT RUN TESTS - Database is empty")
        print("="*70)
        return 1

    # Step 2: Initialize agent
    print("\n" + "="*70)
    print("INITIALIZING AGENT")
    print("="*70)

    try:
        agent = ConvexAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return 1

    # Step 3: Run tests with real data
    test_results = test_with_real_data(agent, found_data)

    # Step 4: Generate report
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)

    passed = sum(1 for r in test_results if r[2])
    failed = sum(1 for r in test_results if not r[2])

    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")

    print(f"\n{'Category':<20} {'Query':<40} {'Status'}")
    print("-" * 70)
    for category, query, success, _ in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{category:<20} {query[:38]:<40} {status}")

    print("\n" + "="*70)

    if failed == 0:
        print("✅ ALL TESTS PASSED - Agent working with real data!")
    else:
        print(f"⚠️  {failed} test(s) failed")

    print("="*70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
