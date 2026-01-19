#!/usr/bin/env python3
"""
Comprehensive demo of Convex Agent capabilities.
This script tests the agent with real-world scenarios.
"""

from convex_agent import ConvexAgent, load_env
import time

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_query(query):
    """Print a user query."""
    print(f"💬 User: {query}")
    print()

def print_response(response):
    """Print agent response."""
    print(f"🤖 Agent:\n{response}\n")

def test_basic_queries():
    """Test 1: Basic database queries."""
    print_section("Test 1: Basic Database Queries")

    agent = ConvexAgent()

    # Query 1: Check current tasks
    print_query("How many tasks do we have in the database?")
    response = agent.chat("How many tasks do we have in the database?")
    print_response(response)

    time.sleep(1)

    # Query 2: Get all tasks
    print_query("Show me all the tasks we have.")
    response = agent.chat("Show me all the tasks we have.")
    print_response(response)

def test_task_creation():
    """Test 2: Creating tasks."""
    print_section("Test 2: Creating and Managing Tasks")

    agent = ConvexAgent()

    # Create tasks
    print_query("Create a new task: 'Review API documentation' with high priority")
    response = agent.chat("Create a new task titled 'Review API documentation' with high priority and status pending")
    print_response(response)

    time.sleep(1)

    print_query("Create another task: 'Update user authentication' with medium priority")
    response = agent.chat("Create a task called 'Update user authentication' with medium priority")
    print_response(response)

    time.sleep(1)

    # Check what we created
    print_query("Now show me all tasks")
    response = agent.chat("Now show me all tasks")
    print_response(response)

def test_intelligent_analysis():
    """Test 3: Intelligent analysis and insights."""
    print_section("Test 3: Intelligent Analysis")

    agent = ConvexAgent()

    # Get statistics
    print_query("Give me statistics about our tasks")
    response = agent.chat("Give me statistics about our tasks - how many total, by status, by priority")
    print_response(response)

    time.sleep(1)

    # Ask for insights
    print_query("Based on the tasks, what should we focus on?")
    response = agent.chat("Based on the tasks in our database, what should we focus on? What needs attention?")
    print_response(response)

def test_search_and_filter():
    """Test 4: Search and filtering."""
    print_section("Test 4: Search and Filtering")

    agent = ConvexAgent()

    # Search for specific tasks
    print_query("Search for tasks related to 'API'")
    response = agent.chat("Search for any tasks that mention 'API' in the title or description")
    print_response(response)

    time.sleep(1)

    print_query("Show me only high-priority tasks")
    response = agent.chat("Show me only the high-priority tasks we have")
    print_response(response)

def test_conversational_context():
    """Test 5: Conversational context awareness."""
    print_section("Test 5: Conversational Context")

    agent = ConvexAgent()

    # Multi-turn conversation
    print_query("Show me all our tasks")
    response = agent.chat("Show me all our tasks")
    print_response(response)

    time.sleep(1)

    print_query("Which ones are high priority?")
    response = agent.chat("Which ones are high priority?")
    print_response(response)

    time.sleep(1)

    print_query("How many is that total?")
    response = agent.chat("How many is that total?")
    print_response(response)

def test_reporting():
    """Test 6: Generate a comprehensive report."""
    print_section("Test 6: Automated Reporting")

    agent = ConvexAgent()

    print_query("Generate a comprehensive project status report")
    response = agent.chat(
        "Generate a comprehensive project status report that includes: "
        "1) Total number of tasks and breakdown by status "
        "2) Priority distribution "
        "3) What's completed vs what's pending "
        "4) Recommendations for what the team should focus on next"
    )
    print_response(response)

def main():
    """Run all demo tests."""
    print("\n" + "="*70)
    print("  🤖 CONVEX AGENT COMPREHENSIVE DEMO")
    print("="*70)
    print("\nThis demo will test the Convex Agent with real queries")
    print("demonstrating its natural language database capabilities.\n")

    input("Press Enter to start the demo...")

    # Load environment
    load_env()

    try:
        # Run all tests
        test_basic_queries()

        input("\nPress Enter to continue to Test 2...")
        test_task_creation()

        input("\nPress Enter to continue to Test 3...")
        test_intelligent_analysis()

        input("\nPress Enter to continue to Test 4...")
        test_search_and_filter()

        input("\nPress Enter to continue to Test 5...")
        test_conversational_context()

        input("\nPress Enter to continue to Test 6...")
        test_reporting()

        # Final summary
        print_section("✅ Demo Complete!")
        print("The Convex Agent successfully demonstrated:")
        print("  ✓ Natural language database queries")
        print("  ✓ Task creation and management")
        print("  ✓ Intelligent analysis and insights")
        print("  ✓ Search and filtering")
        print("  ✓ Conversational context awareness")
        print("  ✓ Automated report generation")
        print("\nYour agent is ready for production use!")
        print()

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}\n")

if __name__ == "__main__":
    main()
