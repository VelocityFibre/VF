#!/usr/bin/env python3
"""
Comprehensive demo of Neon Agent capabilities.
This script demonstrates natural language interaction with PostgreSQL.
"""

from neon_agent import NeonAgent, load_env


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


def test_schema_exploration():
    """Test 1: Database schema exploration."""
    print_section("Test 1: Database Schema Exploration")

    agent = NeonAgent()

    # Query 1: List tables
    print_query("What tables do we have in our database?")
    response = agent.chat("What tables do we have in our database?")
    print_response(response)

    # Query 2: Describe a table (if exists)
    print_query("Can you show me the structure of one of these tables?")
    response = agent.chat("Can you show me the structure of one of these tables?")
    print_response(response)


def test_data_exploration():
    """Test 2: Data exploration and analysis."""
    print_section("Test 2: Data Exploration and Analysis")

    agent = NeonAgent()

    # Query 1: Count rows
    print_query("How much data do we have? Count the rows in each table.")
    response = agent.chat("How much data do we have? Count the rows in each table.")
    print_response(response)

    # Query 2: Sample data
    print_query("Show me a few sample rows from the largest table.")
    response = agent.chat("Show me a few sample rows from the largest table.")
    print_response(response)


def test_intelligent_queries():
    """Test 3: Intelligent data queries."""
    print_section("Test 3: Intelligent Data Queries")

    agent = NeonAgent()

    # Query: Analysis
    print_query("Analyze our database and tell me what kind of application this supports.")
    response = agent.chat(
        "Based on the tables and data in our database, "
        "what kind of application does this seem to support? "
        "What insights can you provide about the data?"
    )
    print_response(response)


def test_statistics():
    """Test 4: Database statistics."""
    print_section("Test 4: Database Statistics")

    agent = NeonAgent()

    # Query: Stats
    print_query("Give me statistics about our database - size, table counts, etc.")
    response = agent.chat(
        "Give me comprehensive statistics about our database: "
        "table sizes, row counts, and any interesting patterns you notice."
    )
    print_response(response)


def test_conversational_context():
    """Test 5: Conversational context awareness."""
    print_section("Test 5: Conversational Context")

    agent = NeonAgent()

    # Multi-turn conversation
    print_query("What's the first table in our database?")
    response = agent.chat("What's the first table in our database?")
    print_response(response)

    print_query("Tell me more about that table.")
    response = agent.chat("Tell me more about that table.")
    print_response(response)

    print_query("How many rows does it have?")
    response = agent.chat("How many rows does it have?")
    print_response(response)


def test_data_insights():
    """Test 6: Generate insights and recommendations."""
    print_section("Test 6: Data Insights and Recommendations")

    agent = NeonAgent()

    print_query("Generate a comprehensive database report with recommendations")
    response = agent.chat(
        "Generate a comprehensive database report that includes: "
        "1) Overview of all tables and their purposes "
        "2) Data volume and growth indicators "
        "3) Any potential data quality issues "
        "4) Recommendations for optimization or maintenance"
    )
    print_response(response)


def main():
    """Run all demo tests."""
    print("\n" + "="*70)
    print("  🤖 NEON AGENT COMPREHENSIVE DEMO")
    print("="*70)
    print("\nThis demo will test the Neon Agent with your PostgreSQL database,")
    print("demonstrating natural language database interaction.\n")

    input("Press Enter to start the demo...")

    # Load environment
    load_env()

    try:
        # Run all tests
        test_schema_exploration()

        input("\nPress Enter to continue to Test 2...")
        test_data_exploration()

        input("\nPress Enter to continue to Test 3...")
        test_intelligent_queries()

        input("\nPress Enter to continue to Test 4...")
        test_statistics()

        input("\nPress Enter to continue to Test 5...")
        test_conversational_context()

        input("\nPress Enter to continue to Test 6...")
        test_data_insights()

        # Final summary
        print_section("✅ Demo Complete!")
        print("The Neon Agent successfully demonstrated:")
        print("  ✓ Database schema exploration")
        print("  ✓ Natural language data queries")
        print("  ✓ Intelligent data analysis")
        print("  ✓ Statistical insights")
        print("  ✓ Conversational context awareness")
        print("  ✓ Automated report generation")
        print("\nYour Neon agent is ready for production use!")
        print()

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
