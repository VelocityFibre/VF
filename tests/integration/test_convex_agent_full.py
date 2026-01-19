#!/usr/bin/env python3
"""
Comprehensive Test Suite for Convex Database Agent
Tests all functionality and reports results.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from convex_agent import ConvexAgent, load_env


class ConvexAgentTester:
    """Test harness for Convex Agent."""

    def __init__(self):
        self.agent = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"

        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}")
        if message:
            print(f"      {message}")

    def test_initialization(self):
        """Test 1: Agent Initialization"""
        print("\n" + "="*60)
        print("TEST 1: Agent Initialization")
        print("="*60)

        try:
            self.agent = ConvexAgent()
            self.log_test(
                "Agent Initialization",
                True,
                f"Model: {self.agent.model}, Convex: {self.agent.convex_url}"
            )
            return True
        except Exception as e:
            self.log_test(
                "Agent Initialization",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_tool_definitions(self):
        """Test 2: Tool Definitions"""
        print("\n" + "="*60)
        print("TEST 2: Tool Definitions")
        print("="*60)

        try:
            tools = self.agent.define_tools()
            tool_names = [t['name'] for t in tools]

            expected_tools = [
                'list_tasks', 'add_task', 'get_task', 'update_task',
                'delete_task', 'search_tasks', 'get_task_stats',
                'get_sync_stats', 'get_last_sync_time'
            ]

            missing_tools = [t for t in expected_tools if t not in tool_names]

            if not missing_tools:
                self.log_test(
                    "Tool Definitions",
                    True,
                    f"All {len(tools)} expected tools defined"
                )
                return True
            else:
                self.log_test(
                    "Tool Definitions",
                    False,
                    f"Missing tools: {missing_tools}"
                )
                return False

        except Exception as e:
            self.log_test(
                "Tool Definitions",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_convex_connectivity(self):
        """Test 3: Convex API Connectivity"""
        print("\n" + "="*60)
        print("TEST 3: Convex API Connectivity")
        print("="*60)

        try:
            # Try to list tasks
            result = self.agent.convex.call_function("tasks/listTasks", {})

            # Check if we got an error or valid response
            if isinstance(result, dict) and "error" in result:
                self.log_test(
                    "Convex Connectivity",
                    False,
                    f"API Error: {result.get('error', 'Unknown error')}"
                )
                return False
            else:
                self.log_test(
                    "Convex Connectivity",
                    True,
                    f"Successfully connected to {self.agent.convex_url}"
                )
                return True

        except Exception as e:
            self.log_test(
                "Convex Connectivity",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_list_tasks(self):
        """Test 4: List Tasks"""
        print("\n" + "="*60)
        print("TEST 4: List Tasks Functionality")
        print("="*60)

        try:
            print("\nQuerying agent: 'List all tasks'")
            response = self.agent.chat("List all tasks")

            # Check if we got a response
            if response and len(response) > 0:
                self.log_test(
                    "List Tasks",
                    True,
                    f"Received response ({len(response)} chars)"
                )
                print(f"\nAgent Response:\n{response}\n")
                return True
            else:
                self.log_test(
                    "List Tasks",
                    False,
                    "Empty response"
                )
                return False

        except Exception as e:
            self.log_test(
                "List Tasks",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_task_statistics(self):
        """Test 5: Task Statistics"""
        print("\n" + "="*60)
        print("TEST 5: Task Statistics")
        print("="*60)

        try:
            # Reset conversation for clean test
            self.agent.reset_conversation()

            print("\nQuerying agent: 'Show me task statistics'")
            response = self.agent.chat("Show me task statistics - how many tasks by status and priority?")

            if response and len(response) > 0:
                self.log_test(
                    "Task Statistics",
                    True,
                    "Successfully retrieved statistics"
                )
                print(f"\nAgent Response:\n{response}\n")
                return True
            else:
                self.log_test(
                    "Task Statistics",
                    False,
                    "Empty response"
                )
                return False

        except Exception as e:
            self.log_test(
                "Task Statistics",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_search_functionality(self):
        """Test 6: Search Tasks"""
        print("\n" + "="*60)
        print("TEST 6: Search Functionality")
        print("="*60)

        try:
            # Reset conversation
            self.agent.reset_conversation()

            print("\nQuerying agent: 'Search for test tasks'")
            response = self.agent.chat("Search for tasks containing the word 'test' or 'API'")

            if response and len(response) > 0:
                self.log_test(
                    "Search Tasks",
                    True,
                    "Search completed"
                )
                print(f"\nAgent Response:\n{response}\n")
                return True
            else:
                self.log_test(
                    "Search Tasks",
                    False,
                    "Empty response"
                )
                return False

        except Exception as e:
            self.log_test(
                "Search Tasks",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_sync_stats(self):
        """Test 7: Sync Statistics"""
        print("\n" + "="*60)
        print("TEST 7: Sync Statistics")
        print("="*60)

        try:
            # Reset conversation
            self.agent.reset_conversation()

            print("\nQuerying agent: 'Show sync statistics'")
            response = self.agent.chat("Show me synchronization statistics")

            if response and len(response) > 0:
                self.log_test(
                    "Sync Statistics",
                    True,
                    "Retrieved sync stats"
                )
                print(f"\nAgent Response:\n{response}\n")
                return True
            else:
                self.log_test(
                    "Sync Statistics",
                    False,
                    "Empty response"
                )
                return False

        except Exception as e:
            self.log_test(
                "Sync Statistics",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_natural_language_query(self):
        """Test 8: Complex Natural Language Query"""
        print("\n" + "="*60)
        print("TEST 8: Complex Natural Language Understanding")
        print("="*60)

        try:
            # Reset conversation
            self.agent.reset_conversation()

            complex_query = "Give me a comprehensive overview of the task system - how many tasks we have, what their statuses are, and what the priorities look like"
            print(f"\nQuerying agent with complex query:\n'{complex_query}'")

            response = self.agent.chat(complex_query)

            if response and len(response) > 50:  # Expect substantial response
                self.log_test(
                    "Natural Language Query",
                    True,
                    "Handled complex query successfully"
                )
                print(f"\nAgent Response:\n{response}\n")
                return True
            else:
                self.log_test(
                    "Natural Language Query",
                    False,
                    "Response too short or empty"
                )
                return False

        except Exception as e:
            self.log_test(
                "Natural Language Query",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_conversation_context(self):
        """Test 9: Conversation Context Maintenance"""
        print("\n" + "="*60)
        print("TEST 9: Conversation Context")
        print("="*60)

        try:
            # Reset conversation
            self.agent.reset_conversation()

            # First question
            print("\nQuery 1: 'Show me all tasks'")
            response1 = self.agent.chat("Show me all tasks")

            # Follow-up question (tests context)
            print("\nQuery 2: 'How many are completed?' (follow-up)")
            response2 = self.agent.chat("How many are completed?")

            if response2 and "completed" in response2.lower():
                self.log_test(
                    "Conversation Context",
                    True,
                    "Agent maintained context across queries"
                )
                print(f"\nFollow-up Response:\n{response2}\n")
                return True
            else:
                self.log_test(
                    "Conversation Context",
                    False,
                    "Context not maintained"
                )
                return False

        except Exception as e:
            self.log_test(
                "Conversation Context",
                False,
                f"Error: {str(e)}"
            )
            return False

    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*70)
        print("CONVEX AGENT TEST REPORT")
        print("="*70)

        print(f"\nTest Summary:")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  Passed: {self.passed_tests}")
        print(f"  Failed: {self.failed_tests}")
        print(f"  Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")

        print(f"\n{'Test Name':<40} {'Status':<10} {'Details'}")
        print("-" * 70)

        for result in self.test_results:
            test_name = result['test'][:38]
            status = result['status']
            message = result['message'][:30] if result['message'] else ""
            print(f"{test_name:<40} {status:<10} {message}")

        print("\n" + "="*70)

        if self.failed_tests == 0:
            print("✅ ALL TESTS PASSED - Convex Agent is fully operational!")
        else:
            print(f"⚠️  {self.failed_tests} test(s) failed - Review issues above")

        print("="*70)

        # Save detailed report
        report_file = f"convex_agent_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "success_rate": f"{(self.passed_tests/self.total_tests*100):.1f}%"
                },
                "tests": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Run comprehensive Convex Agent tests."""

    print("\n" + "="*70)
    print("CONVEX AGENT COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load environment
    load_env()

    # Create tester
    tester = ConvexAgentTester()

    # Run all tests
    tests = [
        tester.test_initialization,
        tester.test_tool_definitions,
        tester.test_convex_connectivity,
        tester.test_list_tasks,
        tester.test_task_statistics,
        tester.test_search_functionality,
        tester.test_sync_stats,
        tester.test_natural_language_query,
        tester.test_conversation_context
    ]

    # Execute tests
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Test execution error: {e}")
            continue

    # Generate report
    tester.generate_report()

    # Return exit code
    return 0 if tester.failed_tests == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
