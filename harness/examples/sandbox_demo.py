#!/usr/bin/env python3
"""
Sandbox Manager Demo - Phase 1 Example

Demonstrates E2B sandbox creation, execution, and cleanup for parallel agent builds.

Usage:
    # Make sure E2B_API_KEY is set in .env
    ./venv/bin/python3 harness/examples/sandbox_demo.py

Part of Vibe Coding Transformation - see docs/VIBE_CODING_TRANSFORMATION.md
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from harness.sandbox_manager import SandboxManager, SandboxInfo
from harness.sandbox_config import (
    get_template,
    get_template_for_agent,
    estimate_cost,
    SandboxProfile
)


def demo_single_sandbox():
    """Demo: Create single sandbox and execute feature."""
    print("=" * 70)
    print("Demo 1: Single Sandbox Execution")
    print("=" * 70)
    print()

    # Initialize manager
    manager = SandboxManager(agent_name="demo_agent")

    try:
        # Create sandbox
        print("📦 Creating sandbox...")
        sandbox_info = manager.create_sandbox(feature_id=1, timeout=180)
        print(f"   Sandbox ID: {sandbox_info.sandbox_id[:8]}...")
        print(f"   Status: {sandbox_info.status}")
        print(f"   Created: {sandbox_info.created_at}")
        print()

        # Setup environment
        print("🔧 Setting up environment...")
        setup_start = time.time()

        if manager.setup_environment(sandbox_info):
            elapsed = time.time() - setup_start
            print(f"   ✅ Environment ready ({elapsed:.1f}s)")
        else:
            print(f"   ❌ Setup failed: {sandbox_info.error}")
            return
        print()

        # Execute feature
        print("🚀 Executing feature...")
        feature_context = {
            "feature_id": 1,
            "feature_description": "Create health check endpoint",
            "validation_steps": [
                "Run pytest tests/test_health.py",
                "Verify endpoint returns 200 OK"
            ],
            "learned_patterns": []
        }

        exec_start = time.time()

        if manager.execute_feature(sandbox_info, feature_context):
            elapsed = time.time() - exec_start
            print(f"   ✅ Feature completed ({elapsed:.1f}s)")
        else:
            print(f"   ❌ Execution failed: {sandbox_info.error}")
        print()

        # Extract results
        print("📊 Extracting results...")
        results = manager.extract_results(sandbox_info)
        print(f"   Status: {results['status']}")
        print(f"   Execution time: {results['execution_time']:.1f}s")
        print()

    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        manager.cleanup_all()
        print("   ✅ Done")
        print()


def demo_parallel_sandboxes():
    """Demo: Create multiple sandboxes in parallel."""
    print("=" * 70)
    print("Demo 2: Parallel Sandbox Execution")
    print("=" * 70)
    print()

    # Get template and estimate cost
    template = get_template(SandboxProfile.STANDARD)
    print(f"📦 Using template: {template.name}")
    print(f"   Timeout: {template.resources.timeout_seconds}s")
    print(f"   Memory: {template.resources.max_memory_mb}MB")
    print(f"   CPU: {template.resources.max_cpu_cores} cores")
    print()

    num_sandboxes = 3  # Demo with 3 sandboxes (use 15 in production)
    cost = estimate_cost(template, num_sandboxes, concurrent=True)
    print(f"💰 Estimated cost for {num_sandboxes} concurrent sandboxes:")
    print(f"   Per sandbox: ${cost['per_sandbox']:.4f}")
    print(f"   Total: ${cost['total']:.4f}")
    print(f"   Duration: {cost['duration_minutes']:.1f} minutes")
    print()

    # Initialize manager
    manager = SandboxManager(agent_name="parallel_demo")

    try:
        # Create multiple sandboxes
        print(f"📦 Creating {num_sandboxes} sandboxes...")
        sandboxes = []

        for i in range(num_sandboxes):
            info = manager.create_sandbox(feature_id=i+1, timeout=180)
            sandboxes.append(info)
            print(f"   [{i+1}/{num_sandboxes}] Sandbox {info.sandbox_id[:8]}... created")

        print(f"   ✅ {num_sandboxes} sandboxes ready")
        print()

        # Setup environments (simulating parallel setup)
        print(f"🔧 Setting up {num_sandboxes} environments in parallel...")
        setup_start = time.time()

        for i, info in enumerate(sandboxes):
            print(f"   [{i+1}/{num_sandboxes}] Setting up sandbox {info.sandbox_id[:8]}...")
            # In production, this would use ThreadPoolExecutor for true parallelism
            manager.setup_environment(info)

        elapsed = time.time() - setup_start
        print(f"   ✅ All environments ready ({elapsed:.1f}s)")
        print()

        # Get stats
        print("📊 Sandbox statistics:")
        stats = manager.get_stats()
        print(f"   Total sandboxes: {stats['total_sandboxes']}")
        print(f"   Active sandboxes: {stats['active_sandboxes']}")
        print(f"   Status counts: {stats['status_counts']}")
        print()

    finally:
        # Cleanup
        print(f"🧹 Cleaning up {num_sandboxes} sandboxes...")
        manager.cleanup_all()
        print("   ✅ Done")
        print()


def demo_agent_templates():
    """Demo: Show template selection for different agent types."""
    print("=" * 70)
    print("Demo 3: Agent-Specific Templates")
    print("=" * 70)
    print()

    test_agents = [
        ("vps-monitor", "Simple health check agent"),
        ("neon-agent", "Database query agent"),
        ("vlm-evaluator", "Image evaluation with ML"),
        ("qfield-sync", "QField data synchronization"),
        ("knowledge-base", "Knowledge base agent")
    ]

    print("Agent type recommendations:")
    print()

    for agent_name, description in test_agents:
        template = get_template_for_agent(agent_name)

        print(f"🤖 {agent_name}")
        print(f"   Description: {description}")
        print(f"   Template: {template.profile.value}")
        print(f"   Resources: {template.resources.max_memory_mb}MB RAM, "
              f"{template.resources.max_cpu_cores} CPU, "
              f"{template.resources.timeout_seconds}s timeout")

        # Cost for 15 concurrent
        cost = estimate_cost(template, 15, concurrent=True)
        print(f"   Cost (15 concurrent): ${cost['total']:.3f}")
        print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SANDBOX MANAGER DEMO - PHASE 1" + " " * 22 + "║")
    print("║" + " " * 14 + "E2B Sandboxes for Parallel Agents" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    try:
        # Demo 1: Single sandbox
        demo_single_sandbox()
        print()

        # Demo 2: Parallel sandboxes
        demo_parallel_sandboxes()
        print()

        # Demo 3: Agent templates
        demo_agent_templates()
        print()

        print("=" * 70)
        print("✅ All demos completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Set E2B_API_KEY in .env (get from https://e2b.dev/dashboard)")
        print("2. Run: ./harness/runner.py --agent test_agent --use-sandboxes")
        print("3. Scale to 15 workers: --workers 15")
        print()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("- Check E2B_API_KEY is set in .env")
        print("- Ensure e2b-code-interpreter is installed")
        print("- Verify E2B API key is valid at https://e2b.dev/dashboard")
        sys.exit(1)


if __name__ == "__main__":
    main()
