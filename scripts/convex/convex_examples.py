#!/usr/bin/env python3
"""
Convex Agent Examples - Practical Use Cases
Shows how to use the Convex Agent for real-world scenarios.
"""

from convex_agent import ConvexAgent, load_env
import sys


def example_task_management():
    """Example: Using AI to manage tasks intelligently."""
    print("\n" + "="*60)
    print("Example: Intelligent Task Management")
    print("="*60 + "\n")

    agent = ConvexAgent()

    # Natural language task queries
    queries = [
        "What tasks do we have? Give me an overview.",
        "Are there any high-priority tasks that need attention?",
        "Show me tasks that are in progress.",
    ]

    for query in queries:
        print(f"💬 User: {query}")
        response = agent.chat(query)
        print(f"🤖 Agent: {response}\n")


def example_task_search():
    """Example: Searching and analyzing tasks."""
    print("\n" + "="*60)
    print("Example: Search and Analysis")
    print("="*60 + "\n")

    agent = ConvexAgent()

    print("💬 User: Search for tasks related to 'API' and tell me what we're working on.")
    response = agent.chat("Search for tasks related to 'API' and tell me what we're working on.")
    print(f"🤖 Agent: {response}\n")


def example_task_insights():
    """Example: Getting insights from task data."""
    print("\n" + "="*60)
    print("Example: Data Insights")
    print("="*60 + "\n")

    agent = ConvexAgent()

    queries = [
        "Give me statistics on our tasks. How are we doing overall?",
        "What percentage of tasks are completed?",
        "Which area needs the most attention based on task priorities?"
    ]

    for query in queries:
        print(f"💬 User: {query}")
        response = agent.chat(query)
        print(f"🤖 Agent: {response}\n")


def example_interactive():
    """Example: Interactive conversation with the agent."""
    print("\n" + "="*60)
    print("Interactive Mode")
    print("="*60 + "\n")
    print("Chat with your Convex database! Type 'exit' to quit.\n")

    agent = ConvexAgent()

    while True:
        try:
            user_input = input("💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!\n")
                break

            response = agent.chat(user_input)
            print(f"🤖 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def example_task_workflow():
    """Example: Complete workflow - create, update, complete."""
    print("\n" + "="*60)
    print("Example: Complete Task Workflow")
    print("="*60 + "\n")

    agent = ConvexAgent()

    # Step 1: Create a task
    print("💬 User: Create a new task: 'Review API documentation' with high priority")
    response = agent.chat("Create a new task titled 'Review API documentation' with high priority and status pending")
    print(f"🤖 Agent: {response}\n")

    # Step 2: List tasks to see it
    print("💬 User: Show me the tasks we just added")
    response = agent.chat("Show me all tasks")
    print(f"🤖 Agent: {response}\n")


def example_reporting():
    """Example: Generate a report from task data."""
    print("\n" + "="*60)
    print("Example: Automated Reporting")
    print("="*60 + "\n")

    agent = ConvexAgent()

    print("💬 User: Generate a status report for our team.")
    response = agent.chat(
        "Generate a comprehensive status report: "
        "1) Total tasks and their breakdown by status "
        "2) High-priority items that need attention "
        "3) Overall progress assessment "
        "4) Recommendations for what to focus on next"
    )
    print(f"🤖 Agent: {response}\n")


def main():
    """Run example demonstrations."""
    print("\n" + "="*70)
    print("  🤖 Convex Database Agent - Example Use Cases")
    print("="*70)

    # Load environment
    load_env()

    print("\nChoose an example to run:\n")
    print("1. Task Management - View and manage tasks")
    print("2. Search & Analysis - Search tasks and get insights")
    print("3. Data Insights - Get statistics and analytics")
    print("4. Interactive Mode - Chat with your database")
    print("5. Task Workflow - Complete CRUD workflow")
    print("6. Automated Reporting - Generate status reports")
    print("7. Run All Examples")
    print()

    try:
        choice = input("Enter choice (1-7): ").strip()

        if choice == "1":
            example_task_management()
        elif choice == "2":
            example_task_search()
        elif choice == "3":
            example_task_insights()
        elif choice == "4":
            example_interactive()
        elif choice == "5":
            example_task_workflow()
        elif choice == "6":
            example_reporting()
        elif choice == "7":
            example_task_management()
            example_task_search()
            example_task_insights()
            example_task_workflow()
            example_reporting()
        else:
            print("Invalid choice. Please run again and select 1-7.")
            sys.exit(1)

        if choice != "4":  # Interactive mode has its own goodbye
            print("\n" + "="*70)
            print("  ✅ Example completed!")
            print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
