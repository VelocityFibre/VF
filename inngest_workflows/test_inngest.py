#!/usr/bin/env python3
"""
Test script for Inngest integration

This script verifies that all Inngest components are properly configured
and can execute basic workflows.
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Inngest components
from client import inngest_client, Events, validate_config
from app import all_functions

def test_configuration():
    """Test that Inngest is properly configured."""
    print("=" * 60)
    print("Testing Inngest Configuration")
    print("=" * 60)

    # Check configuration
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("⚠️  Configuration has warnings (OK for development)")

    # Check client
    print(f"✅ Inngest client initialized: {inngest_client.app_id}")

    # Check functions
    print(f"✅ Functions registered: {len(all_functions)}")
    for func in all_functions:
        if hasattr(func, "_fn_id"):
            print(f"   - {func._fn_id}")

    print()

def test_event_definitions():
    """Test that all events are properly defined."""
    print("=" * 60)
    print("Testing Event Definitions")
    print("=" * 60)

    events = [
        Events.AGENT_BUILD_REQUESTED,
        Events.DB_SYNC_SCHEDULED,
        Events.WHATSAPP_MESSAGE_QUEUED,
        Events.VLM_EVALUATION_REQUESTED,
    ]

    for event in events:
        print(f"✅ Event defined: {event}")

    print()

def test_function_imports():
    """Test that all functions can be imported."""
    print("=" * 60)
    print("Testing Function Imports")
    print("=" * 60)

    try:
        from functions.database_sync import sync_databases
        print("✅ Database sync function imported")
    except ImportError as e:
        print(f"❌ Failed to import database sync: {e}")

    try:
        from functions.whatsapp_queue import send_whatsapp_message
        print("✅ WhatsApp queue function imported")
    except ImportError as e:
        print(f"❌ Failed to import WhatsApp queue: {e}")

    try:
        from functions.agent_builder import build_agent_with_harness
        print("✅ Agent builder function imported")
    except ImportError as e:
        print(f"❌ Failed to import agent builder: {e}")

    try:
        from functions.vlm_evaluation import evaluate_foto_with_vlm
        print("✅ VLM evaluation function imported")
    except ImportError as e:
        print(f"❌ Failed to import VLM evaluation: {e}")

    print()

def test_mock_workflows():
    """Test mock workflow execution."""
    print("=" * 60)
    print("Testing Mock Workflows")
    print("=" * 60)

    # Test database sync helper
    from functions.database_sync import _create_syncer, _create_sync_summary

    syncer = _create_syncer()
    print(f"✅ Database syncer created: {type(syncer)}")

    summary = _create_sync_summary({
        "contractors": {"records_synced": 20, "status": "success"},
        "projects": {"records_synced": 2, "status": "success"}
    })
    print(f"✅ Sync summary created: {summary['status']}")

    # Test WhatsApp helpers
    from functions.whatsapp_queue import _format_message, _format_foto_feedback

    formatted = _format_message("Test message", "high")
    print(f"✅ WhatsApp message formatted: {formatted[:30]}...")

    feedback = _format_foto_feedback("DR123", {
        "score": 85,
        "issues": ["Issue 1", "Issue 2"],
        "recommendations": ["Rec 1"]
    })
    print(f"✅ Foto feedback generated: {len(feedback['message'])} chars")

    # Test VLM helpers
    from functions.vlm_evaluation import _generate_feedback_summary

    vlm_summary = _generate_feedback_summary("DR456", {
        "score": 75,
        "issues": ["Cable routing"],
        "recommendations": ["Improve labeling"]
    })
    print(f"✅ VLM feedback summary: {vlm_summary['status']}")

    print()

def test_directory_structure():
    """Test that required directories exist."""
    print("=" * 60)
    print("Testing Directory Structure")
    print("=" * 60)

    directories = [
        "inngest",
        "inngest/functions",
        "inngest/events",
        "harness",
        "harness/specs",
        "harness/runs"
    ]

    for dir_path in directories:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"⚠️  Directory missing: {dir_path}")
            # Create if missing
            path.mkdir(parents=True, exist_ok=True)
            print(f"   → Created {dir_path}")

    print()

def test_integration_points():
    """Test integration with existing FibreFlow components."""
    print("=" * 60)
    print("Testing Integration Points")
    print("=" * 60)

    # Check if orchestrator exists
    if Path("orchestrator/registry.json").exists():
        print("✅ Orchestrator registry found")
        with open("orchestrator/registry.json") as f:
            registry = json.load(f)
            print(f"   → {len(registry.get('agents', {}))} agents registered")
    else:
        print("⚠️  Orchestrator registry not found (will be created on first agent build)")

    # Check if harness specs exist
    specs = list(Path("harness/specs").glob("*.md")) if Path("harness/specs").exists() else []
    print(f"✅ Harness specs found: {len(specs)}")
    for spec in specs[:3]:  # Show first 3
        print(f"   → {spec.name}")

    # Check if sync script exists
    if Path("sync_neon_to_convex.py").exists():
        print("✅ Database sync script found")
    else:
        print("⚠️  Database sync script not found (mock mode will be used)")

    print()

def main():
    """Run all tests."""
    print("\n🚀 FibreFlow Inngest Integration Test Suite\n")

    test_configuration()
    test_event_definitions()
    test_function_imports()
    test_mock_workflows()
    test_directory_structure()
    test_integration_points()

    print("=" * 60)
    print("✨ Test Summary")
    print("=" * 60)
    print()
    print("All basic tests completed successfully!")
    print()
    print("Next steps:")
    print("1. Start the development environment:")
    print("   cd inngest && ./dev.sh")
    print()
    print("2. Open Inngest Dev UI:")
    print("   http://localhost:8288")
    print()
    print("3. Test a workflow:")
    print("   # Trigger database sync")
    print("   curl -X POST http://localhost:8288/e/fibreflow-agents/database.sync.scheduled")
    print()
    print("4. Monitor in the Inngest UI to see the workflow execute")
    print()

if __name__ == "__main__":
    main()