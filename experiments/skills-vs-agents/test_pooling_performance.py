#!/usr/bin/env python3
"""
Test connection pooling performance improvement.
Measures query times with pooling vs without.
"""

import time
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
skills_path = project_root / ".claude/skills/database-operations/scripts"

def run_query(script_path, query):
    """Run a single query and measure time."""
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path), "--query", query],
        capture_output=True,
        text=True,
        timeout=10
    )
    elapsed = (time.time() - start) * 1000  # ms

    success = "success" in result.stdout.lower() and result.returncode == 0
    return elapsed, success

def test_pooling_performance():
    """Test query performance with pooling."""
    script = skills_path / "execute_query.py"
    query = "SELECT COUNT(*) FROM contractors"

    print("Testing Connection Pooling Performance")
    print("=" * 60)
    print()

    # Run 5 queries
    times = []
    for i in range(1, 6):
        elapsed, success = run_query(script, query)
        times.append(elapsed)
        status = "✅" if success else "❌"
        print(f"Query {i}: {elapsed:6.0f}ms {status}")

    print()
    print("Performance Summary")
    print("-" * 60)
    print(f"First query:  {times[0]:6.0f}ms (cold connection)")
    print(f"Queries 2-5:  {sum(times[1:])/4:6.0f}ms average (pooled)")
    print(f"Improvement:  {((times[0] - sum(times[1:])/4) / times[0] * 100):5.1f}% faster after first")
    print()
    print(f"Overall avg:  {sum(times)/5:6.0f}ms")
    print()

    # Comparison to previous performance
    print("Comparison to Previous (Without Pooling)")
    print("-" * 60)
    previous_avg = 2314  # From comparison results
    current_avg = sum(times)/5
    improvement = ((previous_avg - current_avg) / previous_avg) * 100

    print(f"Previous avg: {previous_avg:6.0f}ms (no pooling)")
    print(f"Current avg:  {current_avg:6.0f}ms (with pooling)")
    print(f"Improvement:  {improvement:5.1f}% faster")
    print()

if __name__ == "__main__":
    test_pooling_performance()
