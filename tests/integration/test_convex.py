#!/usr/bin/env python3
"""
Quick test to verify Convex connection and agent setup.
"""

from convex_agent import ConvexAgent, load_env, ConvexClient
import os
import json

def test_convex_connection():
    """Test basic Convex connection."""
    print("\n" + "="*60)
    print("Testing Convex Connection")
    print("="*60 + "\n")

    # Load environment
    load_env()

    convex_url = os.environ.get("CONVEX_URL")
    auth_key = os.environ.get("SYNC_AUTH_KEY")

    print(f"Convex URL: {convex_url}")
    print(f"Auth Key: {'✅ Set' if auth_key else '❌ Missing'}\n")

    # Test direct Convex call
    print("Testing direct Convex API call...")
    convex = ConvexClient(convex_url, auth_key)

    try:
        result = convex.call_function("tasks/listTasks")
        print(f"✅ Connection successful!")
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}\n")
        return False


def test_agent():
    """Test the Convex agent."""
    print("="*60)
    print("Testing Convex Agent")
    print("="*60 + "\n")

    try:
        agent = ConvexAgent()
        print("✅ Agent initialized\n")

        print("Sending test message to agent...")
        response = agent.chat("How many tasks do we have? Just give me a quick count.")

        print(f"\n🤖 Agent Response:\n{response}\n")

        print("="*60)
        print("✅ Test completed successfully!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"❌ Agent test failed: {e}\n")
        return False


def main():
    """Run all tests."""
    print("\n🧪 Convex Agent Test Suite\n")

    # Load environment
    load_env()

    # Test 1: Connection
    connection_ok = test_convex_connection()

    if not connection_ok:
        print("⚠️  Connection test failed. Please check:")
        print("   1. CONVEX_URL is correct in .env")
        print("   2. Your Convex deployment is running")
        print("   3. The tasks/listTasks function exists")
        return

    # Test 2: Agent
    agent_ok = test_agent()

    if agent_ok:
        print("✅ All tests passed! Your Convex agent is ready to use.\n")
        print("Next steps:")
        print("  - Run examples: python convex_examples.py")
        print("  - Or run the demo: python convex_agent.py")
    else:
        print("⚠️  Agent test failed. Check your Anthropic API key.")


if __name__ == "__main__":
    main()
