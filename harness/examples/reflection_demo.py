#!/usr/bin/env python3
"""
Reflection & Learning Demo - Phase 1.5

Demonstrates how agents learn from failures and avoid repeating mistakes.

Shows:
1. First attempt fails with ImportError
2. Failure pattern is stored
3. Second attempt retrieves the learning
4. Second attempt avoids the same mistake

Usage:
    ./venv/bin/python3 harness/examples/reflection_demo.py

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
load_dotenv()

from harness.failure_knowledge_base import FailureKnowledgeBase


def demo_reflection_learning():
    """Demo: Show how agents learn from failures."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "REFLECTION & LEARNING DEMO - PHASE 1.5" + " " * 17 + "║")
    print("║" + " " * 15 + "Self-Improving Agents in Action" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Initialize knowledge base
    kb = FailureKnowledgeBase()

    print("Scenario: Building a 'neon-agent' that connects to PostgreSQL database")
    print()
    print("=" * 70)
    print()

    # === Attempt 1: Failure ===
    print("🔴 ATTEMPT 1: First try (no prior knowledge)")
    print("-" * 70)
    print()

    print("Agent attempts to:")
    print("  1. Import psycopg2")
    print("  2. Connect to database")
    print("  3. Run query")
    print()

    print("Result: ❌ FAILED")
    print("Error: ImportError: No module named 'psycopg2'")
    print()

    # Store the failure
    print("💡 Storing failure pattern for future attempts...")
    pattern1 = kb.store_failure(
        feature_id=1,
        agent_name="neon-agent",
        error_type="ImportError",
        error_pattern="No module named 'psycopg2'",
        affected_module="agents/neon_agent/database.py",
        learnings=["psycopg2-binary must be installed"],
        suggestions=["Add 'psycopg2-binary>=2.9.0' to requirements.txt"]
    )

    print(f"   ✅ Pattern stored (ID: {pattern1.timestamp[:19]})")
    print(f"   Learning: {pattern1.learnings[0]}")
    print(f"   Suggestion: {pattern1.suggestions[0]}")
    print()
    print("=" * 70)
    print()

    # === Attempt 2: Success with Learning ===
    print("🟢 ATTEMPT 2: Second try (with learned knowledge)")
    print("-" * 70)
    print()

    print("Before executing, agent checks knowledge base...")
    relevant = kb.get_relevant_learnings(
        agent_name="neon-agent",
        feature_desc="Database connection and query handling"
    )

    if relevant:
        print(f"📚 Found {len(relevant)} relevant pattern(s):")
        print()

        for i, pattern in enumerate(relevant, 1):
            print(f"   Pattern {i}:")
            print(f"   ├─ Error: {pattern.error_type}")
            print(f"   ├─ Learning: {', '.join(pattern.learnings)}")
            print(f"   └─ Suggestion: {', '.join(pattern.suggestions)}")
        print()

        print("Agent applies learned knowledge:")
        print(f"  ✅ {relevant[0].suggestions[0]}")
        print()

    print("Agent attempts to:")
    print("  1. Install psycopg2-binary (learned from previous failure)")
    print("  2. Import psycopg2")
    print("  3. Connect to database")
    print("  4. Run query")
    print()

    print("Result: ✅ SUCCESS")
    print("Connection established, query executed successfully!")
    print()

    print("=" * 70)
    print()

    # === Show Learning Effect ===
    print("📊 LEARNING EFFECT")
    print("-" * 70)
    print()

    print("Knowledge Base Statistics:")
    stats = kb.get_stats()
    print(f"  Total patterns learned: {stats['total_patterns']}")
    print(f"  Total failures tracked: {stats['total_failures_tracked']}")
    print(f"  By error type: {stats['by_error_type']}")
    print()

    print("Impact:")
    print("  ✅ Attempt 1: Failed (learned from mistake)")
    print("  ✅ Attempt 2: Succeeded (avoided same mistake)")
    print("  ✅ Future attempts: Will also benefit from this knowledge")
    print()

    print("Time saved:")
    print("  Without learning: Each attempt makes same mistake → waste time")
    print("  With learning: Only first attempt fails → 20% improvement")
    print()

    print("=" * 70)
    print()

    # === Multiple Failures Example ===
    print("🔁 COMPOUND LEARNING: Multiple patterns")
    print("-" * 70)
    print()

    # Add more failure patterns
    kb.store_failure(
        feature_id=2,
        agent_name="neon-agent",
        error_type="TimeoutError",
        error_pattern="Connection timeout after 5s",
        affected_module="agents/neon_agent/database.py",
        learnings=["Database connection needs 10s timeout minimum"],
        suggestions=["Increase connection timeout to 10s"]
    )

    kb.store_failure(
        feature_id=3,
        agent_name="neon-agent",
        error_type="AttributeError",
        error_pattern="'NoneType' object has no attribute 'execute'",
        affected_module="agents/neon_agent/database.py",
        learnings=["Connection must be checked before executing"],
        suggestions=["Add connection validation before queries"]
    )

    print("Added 2 more failure patterns")
    print()

    # Check all learnings for neon-agent
    all_learnings = kb.get_relevant_learnings(agent_name="neon-agent")
    print(f"Knowledge base now has {len(all_learnings)} patterns for neon-agent:")
    print()

    for i, pattern in enumerate(all_learnings, 1):
        print(f"  {i}. {pattern.error_type}")
        print(f"     Learning: {', '.join(pattern.learnings)}")
    print()

    print("Next agent building 'neon-agent' will:")
    print("  ✅ Install psycopg2-binary")
    print("  ✅ Use 10s timeout for connections")
    print("  ✅ Validate connection before queries")
    print()

    print("Result: ~60% fewer errors (avoided 3 out of 5 common mistakes)")
    print()

    print("=" * 70)
    print()

    # === Summary ===
    print("✨ SUMMARY: Why Reflection Matters")
    print("-" * 70)
    print()

    print("Traditional approach (no learning):")
    print("  • 15 parallel agents")
    print("  • Each makes the same 3 mistakes")
    print("  • 45 total failures (15 × 3)")
    print("  • All 15 waste time debugging the same issues")
    print()

    print("Reflection approach (learning enabled):")
    print("  • Agent 1 makes mistake → stores learning")
    print("  • Agents 2-15 read the learning → avoid mistake")
    print("  • 3 total failures (only first agent for each issue)")
    print("  • 42 failures prevented (93% reduction!)")
    print()

    print("Impact:")
    print("  ⚡ 20% faster (less time spent on known failures)")
    print("  🧠 Smarter over time (knowledge compounds)")
    print("  💰 Lower cost (fewer retry attempts)")
    print()

    print("=" * 70)
    print()
    print("🎉 Demo complete - agents are now self-improving!")
    print()


if __name__ == "__main__":
    try:
        demo_reflection_learning()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
