#!/usr/bin/env python3
"""
Quick test to verify Neon connection and agent setup.
"""

from neon_agent import NeonAgent, load_env, PostgresClient
import os
import json


def test_database_connection():
    """Test basic Neon database connection."""
    print("\n" + "="*60)
    print("Testing Neon Database Connection")
    print("="*60 + "\n")

    # Load environment
    load_env()

    connection_string = os.environ.get("NEON_DATABASE_URL")

    if not connection_string:
        print("❌ NEON_DATABASE_URL not set in .env file\n")
        return False

    print(f"Database: Neon PostgreSQL")
    print(f"Connection: {'✅ Configured' if connection_string else '❌ Missing'}\n")

    # Test direct database connection
    print("Testing direct database connection...")
    db = PostgresClient(connection_string)

    try:
        db.connect()
        print(f"✅ Connection successful!\n")

        # Test listing tables
        print("Fetching table list...")
        tables = db.list_tables()
        print(f"Response: {json.dumps(tables, indent=2, default=str)}\n")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}\n")
        return False


def test_agent():
    """Test the Neon agent."""
    print("="*60)
    print("Testing Neon Agent")
    print("="*60 + "\n")

    try:
        agent = NeonAgent()
        print("✅ Agent initialized\n")

        print("Sending test message to agent...")
        response = agent.chat("What tables are in our database? Just list them briefly.")

        print(f"\n🤖 Agent Response:\n{response}\n")

        print("="*60)
        print("✅ Test completed successfully!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"❌ Agent test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_schema_discovery():
    """Test schema discovery capabilities."""
    print("="*60)
    print("Testing Schema Discovery")
    print("="*60 + "\n")

    try:
        agent = NeonAgent()

        print("Asking agent to explore database schema...")
        response = agent.chat(
            "Explore our database schema. Tell me what tables exist "
            "and describe the structure of each table."
        )

        print(f"\n🤖 Agent Response:\n{response}\n")

        print("="*60)
        print("✅ Schema discovery test completed!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"❌ Schema discovery test failed: {e}\n")
        return False


def main():
    """Run all tests."""
    print("\n🧪 Neon Agent Test Suite\n")

    # Load environment
    load_env()

    # Test 1: Connection
    connection_ok = test_database_connection()

    if not connection_ok:
        print("⚠️  Connection test failed. Please check:")
        print("   1. NEON_DATABASE_URL is set in .env")
        print("   2. Your Neon database is accessible")
        print("   3. Connection string format is correct")
        print("\nExpected format:")
        print("   postgresql://user:pass@host/dbname?sslmode=require")
        return

    # Test 2: Agent
    agent_ok = test_agent()

    if not agent_ok:
        print("⚠️  Agent test failed. Check your Anthropic API key.")
        return

    # Test 3: Schema Discovery
    schema_ok = test_schema_discovery()

    if agent_ok and schema_ok:
        print("✅ All tests passed! Your Neon agent is ready to use.\n")
        print("Next steps:")
        print("  - Run the demo: python neon_agent.py")
        print("  - Try: python demo_neon_agent.py")
        print("  - Or start chatting with your database!")
    else:
        print("⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
