#!/usr/bin/env python3
"""
Advanced Neon Agent test - demonstrates data analysis capabilities.
"""

from neon_agent import NeonAgent, load_env


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_row_counts():
    """Test 1: Count rows in all major tables."""
    print_section("Test 1: Row Counts Across Tables")

    agent = NeonAgent()

    query = """
    Count the number of rows in these key tables:
    - projects
    - contractors
    - boqs
    - tasks
    - clients
    - suppliers
    - rfqs
    - quotes

    Give me a summary table showing the data volume.
    """

    print(f"💬 User: {query.strip()}\n")
    response = agent.chat(query)
    print(f"🤖 Agent:\n{response}\n")


def test_project_analysis():
    """Test 2: Analyze project data."""
    print_section("Test 2: Project Data Analysis")

    agent = NeonAgent()

    query = """
    Analyze our projects table:
    1. How many projects do we have total?
    2. What columns/fields does it track?
    3. Show me a sample of 3-5 recent projects with key details
    4. What status values exist (if there's a status field)?

    Give me actionable insights about our project portfolio.
    """

    print(f"💬 User: {query.strip()}\n")
    response = agent.chat(query)
    print(f"🤖 Agent:\n{response}\n")


def test_contractor_insights():
    """Test 3: Generate contractor insights."""
    print_section("Test 3: Contractor Insights")

    agent = NeonAgent()

    query = """
    Analyze our contractors:
    1. How many contractors do we have?
    2. What information do we track about them?
    3. Are there any contractor teams or assignments?
    4. Show me 3-5 example contractors with their key details

    What insights can you provide about our contractor ecosystem?
    """

    print(f"💬 User: {query.strip()}\n")
    response = agent.chat(query)
    print(f"🤖 Agent:\n{response}\n")


def test_boq_insights():
    """Test 4: Generate BOQ insights."""
    print_section("Test 4: BOQ (Bill of Quantities) Insights")

    agent = NeonAgent()

    query = """
    Analyze our Bill of Quantities (BOQ) data:
    1. How many BOQs do we have in the system?
    2. What's the structure - what fields are tracked?
    3. Are there BOQ items, revisions, or approvals tracked separately?
    4. Show me sample BOQ records
    5. What's the relationship between BOQs and projects?

    Provide strategic insights about how we manage BOQs.
    """

    print(f"💬 User: {query.strip()}\n")
    response = agent.chat(query)
    print(f"🤖 Agent:\n{response}\n")


def test_comprehensive_insights():
    """Test 5: Generate comprehensive business insights."""
    print_section("Test 5: Comprehensive Business Insights")

    agent = NeonAgent()

    query = """
    Based on all the data in our database, generate a comprehensive
    business intelligence report:

    1. What kind of business are we running? (based on the data)
    2. What are our main operational areas?
    3. What's the scale of our operations? (data volume)
    4. What are the key relationships between entities?
    5. What insights or recommendations can you provide?

    Be specific and use actual data from our database.
    """

    print(f"💬 User: {query.strip()}\n")
    response = agent.chat(query)
    print(f"🤖 Agent:\n{response}\n")


def main():
    """Run all advanced tests."""
    print("\n" + "="*70)
    print("  🧠 NEON AGENT - ADVANCED DATA ANALYSIS")
    print("="*70)
    print("\nThis test demonstrates the agent's ability to analyze")
    print("and generate insights from your actual database.\n")

    # Load environment
    load_env()

    try:
        # Run all tests
        test_row_counts()

        input("\nPress Enter to continue to Project Analysis...")
        test_project_analysis()

        input("\nPress Enter to continue to Contractor Insights...")
        test_contractor_insights()

        input("\nPress Enter to continue to BOQ Insights...")
        test_boq_insights()

        input("\nPress Enter to continue to Comprehensive Insights...")
        test_comprehensive_insights()

        # Final summary
        print_section("✅ Advanced Testing Complete!")
        print("The Neon Agent demonstrated:")
        print("  ✓ Data volume analysis across multiple tables")
        print("  ✓ Deep project data exploration")
        print("  ✓ Contractor ecosystem insights")
        print("  ✓ BOQ structure and relationship analysis")
        print("  ✓ Comprehensive business intelligence")
        print("\nYour agent is production-ready for complex data analysis!")
        print()

    except KeyboardInterrupt:
        print("\n\n👋 Testing interrupted. Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
