#!/usr/bin/env python3
"""
Quick test script to verify the Claude Agent SDK is working properly.
"""

import os
import sys
from pathlib import Path

# Load environment variables from project root .env file
from dotenv import load_dotenv

# Find and load .env from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  .env file not found at {env_path}, using environment variables")

# Import from legacy (agent_example was moved during reorganization)
sys.path.insert(0, str(project_root / 'legacy'))
try:
    from agent_example import ClaudeAgent
except ImportError:
    print("⚠️  agent_example not found, skipping this test")
    ClaudeAgent = None

import pytest

@pytest.mark.skipif(ClaudeAgent is None, reason="agent_example.py not available (moved to legacy)")
def test_basic_chat():
    """Test basic chat functionality"""
    print("\n" + "="*60)
    print("Testing Claude Agent SDK Setup")
    print("="*60 + "\n")

    # Try different models in order of preference
    models_to_try = [
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229"
    ]

    for model in models_to_try:
        try:
            print(f"Trying model: {model}...")
            agent = ClaudeAgent(model=model)
            print(f"✅ Agent initialized with {model}\n")

            print("🤖 Sending test message to Claude...\n")
            response = agent.chat("Say hello and tell me you're working! Keep it brief.")

            print(f"Agent Response:\n{response}\n")

            print("="*60)
            print(f"✅ Test completed successfully with {model}!")
            print("="*60 + "\n")

            print("Your agent is ready to use! Run the full examples with:")
            print("  python agent_example.py")
            return

        except Exception as e:
            print(f"❌ Failed with {model}: {e}\n")
            continue

    print("❌ All models failed. Please check your API key and account access.")
    print("\nTroubleshooting:")
    print("1. Check your API key in .env file")
    print("2. Verify you have access to Claude models in your Anthropic account")
    print("3. Visit https://console.anthropic.com/ to check your account status")
    sys.exit(1)

if __name__ == "__main__":
    test_basic_chat()
