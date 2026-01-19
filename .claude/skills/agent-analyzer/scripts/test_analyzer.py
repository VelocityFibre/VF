#!/usr/bin/env python3
"""
Test the agent behavior analyzer with simulated problematic patterns
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import time

# Log file path
log_file = Path("/home/louisdup/Agents/claude/logs/agent-commands.jsonl")
log_file.parent.mkdir(exist_ok=True)

def add_test_data():
    """Add test data with various problematic patterns"""

    now = datetime.now()
    test_patterns = []

    # Pattern 1: Loop - Same command repeated rapidly
    for i in range(5):
        test_patterns.append({
            "timestamp": (now - timedelta(seconds=120-i*2)).isoformat(),
            "command": "ps aux | grep node",
            "status": "auto_approved",
            "agent": "test"
        })

    # Pattern 2: Retry - Failed command being retried
    for i in range(4):
        test_patterns.append({
            "timestamp": (now - timedelta(seconds=90-i*5)).isoformat(),
            "command": "systemctl restart nginx",
            "status": "blocked" if i > 0 else "manual",
            "agent": "test"
        })

    # Pattern 3: Stuck - One category dominating
    for i in range(15):
        test_patterns.append({
            "timestamp": (now - timedelta(seconds=60-i)).isoformat(),
            "command": f"find /var -name file_{i}.txt",
            "status": "auto_approved",
            "agent": "test"
        })

    # Pattern 4: Rapid fire - Many commands per minute
    base_time = now - timedelta(seconds=30)
    for i in range(60):
        test_patterns.append({
            "timestamp": (base_time + timedelta(milliseconds=i*500)).isoformat(),
            "command": f"curl http://api.test/check_{i}",
            "status": "auto_approved",
            "agent": "test"
        })

    # Pattern 5: High manual review rate
    statuses = ["manual"] * 7 + ["auto_approved"] * 3
    for i in range(10):
        test_patterns.append({
            "timestamp": (now - timedelta(seconds=15-i)).isoformat(),
            "command": f"unknown_command_{i}",
            "status": statuses[i],
            "agent": "test"
        })

    # Write to log file
    with open(log_file, 'a') as f:
        for pattern in test_patterns:
            f.write(json.dumps(pattern) + '\n')

    print(f"✅ Added {len(test_patterns)} test commands with problematic patterns")
    print("\nTest patterns added:")
    print("1. LOOP: 'ps aux | grep node' repeated 5 times")
    print("2. RETRY: 'systemctl restart nginx' failed and retried 4 times")
    print("3. STUCK: 15 find commands (File_Ops dominance)")
    print("4. RAPID_FIRE: 60 curl commands in 30 seconds")
    print("5. INEFFICIENT: 70% manual review rate")

def run_analyzer():
    """Run the analyzer on the test data"""
    print("\n" + "="*60)
    print("Running analyzer on test data...")
    print("="*60 + "\n")

    # Run analyzer
    result = subprocess.run([
        "./venv/bin/python3",
        ".claude/skills/agent-analyzer/scripts/analyze.py",
        "--last", "5m",
        "--verbose"
    ], capture_output=False, text=True)

    return result.returncode

def run_monitor_demo():
    """Demo the real-time monitoring"""
    print("\n" + "="*60)
    print("Starting real-time monitor demo (5 seconds)...")
    print("="*60 + "\n")

    # Start monitor in background
    process = subprocess.Popen([
        "./venv/bin/python3",
        ".claude/skills/agent-analyzer/scripts/analyze.py",
        "--monitor"
    ])

    # Let it run for 5 seconds
    time.sleep(5)

    # Add more problematic data
    now = datetime.now()
    for i in range(10):
        with open(log_file, 'a') as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "command": "rm -rf /test",
                "status": "blocked",
                "agent": "test"
            }) + '\n')

    time.sleep(2)

    # Stop monitor
    process.terminate()
    print("\nMonitor demo completed")

if __name__ == "__main__":
    print("🔬 Agent Behavior Analyzer Test Suite")
    print("="*60)

    # Add test data
    add_test_data()

    # Run analyzer
    exit_code = run_analyzer()

    if exit_code == 1:
        print("\n✅ Analyzer correctly detected problems!")
    else:
        print("\n❌ Analyzer failed to detect problems")

    print("\nYou can also run:")
    print("  ./venv/bin/python3 .claude/skills/agent-analyzer/scripts/analyze.py --monitor")
    print("to see real-time monitoring in action")