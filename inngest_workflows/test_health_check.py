#!/usr/bin/env python3
"""
Test script for the health check Inngest workflow

This script demonstrates how to:
1. Trigger manual health checks
2. Simulate high resource usage
3. Test the WhatsApp alerting
4. View workflow results
"""

import os
import sys
import json
import time
import requests
import psutil
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Inngest Dev Server URL
INNGEST_DEV_URL = "http://localhost:8288"
INNGEST_API_URL = "http://localhost:3000/api/inngest"

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_services():
    """Check if required services are running."""
    print_section("Checking Services")

    # Check FastAPI
    try:
        response = requests.get("http://localhost:3000/", timeout=2)
        print("✅ FastAPI server is running on port 3000")
    except:
        print("❌ FastAPI server not running - run: cd inngest_workflows && ./dev.sh")
        return False

    # Check Inngest Dev Server
    try:
        response = requests.get(INNGEST_DEV_URL, timeout=2)
        print("✅ Inngest Dev Server is running on port 8288")
    except:
        print("❌ Inngest Dev Server not running - run: cd inngest_workflows && ./dev.sh")
        return False

    return True

def trigger_manual_health_check(target="local"):
    """Trigger a manual health check via Inngest."""
    print_section(f"Triggering Health Check for '{target}'")

    event_data = {
        "name": "health/check.scheduled",
        "data": {
            "target": target,
            "triggered_by": "test_script",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    try:
        # Send event to Inngest
        response = requests.post(
            f"{INNGEST_DEV_URL}/e/fibreflow-agents/health.check.scheduled",
            json=event_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in [200, 201, 202]:
            print(f"✅ Health check triggered successfully!")
            result = response.json() if response.text else {}
            print(f"   Event ID: {result.get('ids', ['N/A'])[0] if result.get('ids') else 'N/A'}")
            return True
        else:
            print(f"❌ Failed to trigger health check: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error triggering health check: {e}")
        return False

def simulate_high_resource_usage():
    """Simulate high CPU/memory to trigger alerts."""
    print_section("Simulating High Resource Usage")

    print("This would normally spike CPU/memory to trigger alerts.")
    print("For testing, we'll trigger an event with high metrics...")

    # Send a mock event with high metrics
    event_data = {
        "name": "health/check.scheduled",
        "data": {
            "target": "mock-high-usage",
            "mock_metrics": {
                "cpu_percent": 92.5,  # Above threshold
                "memory_percent": 88.3,  # Above threshold
                "disk_percent": 75.0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    try:
        response = requests.post(
            f"{INNGEST_DEV_URL}/e/fibreflow-agents/health.check.scheduled",
            json=event_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in [200, 201, 202]:
            print("✅ High resource usage event sent!")
            print("   This should trigger a WhatsApp alert...")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_current_metrics():
    """Display current system metrics."""
    print_section("Current System Metrics")

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    print(f"📊 CPU Usage:     {cpu:.1f}%")
    print(f"💾 Memory Usage:  {memory.percent:.1f}% ({memory.available / (1024**3):.1f} GB available)")
    print(f"💿 Disk Usage:    {disk.percent:.1f}% ({disk.free / (1024**3):.1f} GB free)")

    # Check against thresholds
    print("\n📋 Alert Thresholds:")
    print(f"   CPU:    > 80% (Currently: {'⚠️ ALERT' if cpu > 80 else '✅ OK'})")
    print(f"   Memory: > 85% (Currently: {'⚠️ ALERT' if memory.percent > 85 else '✅ OK'})")
    print(f"   Disk:   > 90% (Currently: {'⚠️ ALERT' if disk.percent > 90 else '✅ OK'})")

def test_workflow_steps():
    """Test the complete health check workflow."""
    print_section("Testing Complete Workflow")

    steps = [
        ("1. Trigger health check", lambda: trigger_manual_health_check("local")),
        ("2. Wait for processing", lambda: time.sleep(3) or True),
        ("3. Check Inngest UI", lambda: print("   → Open http://localhost:8288 to see the workflow") or True),
        ("4. Simulate high usage", lambda: simulate_high_resource_usage()),
    ]

    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if step_func():
            print(f"   ✅ {step_name} completed")
        else:
            print(f"   ❌ {step_name} failed")
            break

def main():
    """Run the test suite."""
    print("\n" + "🏥 " * 20)
    print("     INNGEST HEALTH CHECK MODULE TEST")
    print("🏥 " * 20)

    # Check services are running
    if not check_services():
        print("\n⚠️  Please start the services first:")
        print("   cd inngest_workflows && ./dev.sh")
        return

    # Show current metrics
    show_current_metrics()

    # Interactive menu
    while True:
        print_section("Test Options")
        print("1. Trigger manual health check (local)")
        print("2. Trigger health check (VF server)")
        print("3. Simulate high resource usage (triggers alert)")
        print("4. Run complete workflow test")
        print("5. Show current metrics")
        print("0. Exit")

        choice = input("\nSelect option (0-5): ").strip()

        if choice == "1":
            trigger_manual_health_check("local")
        elif choice == "2":
            trigger_manual_health_check("vf-server")
        elif choice == "3":
            simulate_high_resource_usage()
        elif choice == "4":
            test_workflow_steps()
        elif choice == "5":
            show_current_metrics()
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

        print("\n🔍 Check the Inngest UI at http://localhost:8288 to see your workflows!")

if __name__ == "__main__":
    main()