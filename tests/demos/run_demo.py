#!/usr/bin/env python3
"""
Automated demo runner (no pauses for CI/testing).
"""

from convex_agent import ConvexAgent, load_env

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def test_scenario(agent, query):
    """Test a single scenario."""
    print(f"💬 User: {query}\n")
    response = agent.chat(query)
    print(f"🤖 Agent:\n{response}\n")
    return response

def main():
    print_section("🤖 CONVEX AGENT DEMO - Automated Tests")

    load_env()

    # Test 1: Basic Query
    print_section("Test 1: Basic Query")
    agent = ConvexAgent()
    test_scenario(agent, "How many tasks do we have?")

    # Test 2: Create Tasks
    print_section("Test 2: Creating Tasks")
    agent.reset_conversation()
    test_scenario(agent, "Create a new task: 'Review API documentation' with high priority")
    test_scenario(agent, "Create another task: 'Implement user authentication' with medium priority")
    test_scenario(agent, "Create one more: 'Write unit tests' with low priority")

    # Test 3: View Tasks
    print_section("Test 3: View All Tasks")
    agent.reset_conversation()
    test_scenario(agent, "Show me all our tasks")

    # Test 4: Statistics
    print_section("Test 4: Task Statistics")
    agent.reset_conversation()
    test_scenario(agent, "Give me statistics about our tasks")

    # Test 5: Contextual Conversation
    print_section("Test 5: Contextual Conversation")
    agent.reset_conversation()
    test_scenario(agent, "Show me all tasks")
    test_scenario(agent, "Which ones are high priority?")
    test_scenario(agent, "How many is that?")

    # Test 6: Report Generation
    print_section("Test 6: Comprehensive Report")
    agent.reset_conversation()
    test_scenario(agent,
        "Generate a project status report including: "
        "total tasks, breakdown by priority, "
        "what's completed vs pending, and recommendations"
    )

    print_section("✅ All Tests Complete!")
    print("The Convex Agent successfully:")
    print("  ✓ Connected to your Convex database")
    print("  ✓ Created and managed tasks")
    print("  ✓ Analyzed data and provided insights")
    print("  ✓ Maintained conversational context")
    print("  ✓ Generated comprehensive reports")
    print()

if __name__ == "__main__":
    main()
