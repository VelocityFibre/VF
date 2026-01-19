#!/usr/bin/env python3
"""
Test script for FF_React skill
"""

import os
import sys
import subprocess

def run_test(command, description):
    """Run a test command and report results"""
    print(f"\n🧪 Testing: {description}")
    print("-" * 40)

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Success")
        if result.stdout:
            print(result.stdout[:200])
    else:
        print(f"❌ Failed (exit code: {result.returncode})")
        if result.stderr:
            print(f"Error: {result.stderr[:200]}")

    return result.returncode == 0

def main():
    print("🔍 FF_React Skill Test Suite")
    print("=" * 50)

    scripts_dir = os.path.dirname(os.path.abspath(__file__)) + "/scripts"

    tests = [
        (f"{scripts_dir}/status.py --help", "Status script help"),
        (f"{scripts_dir}/logs.py --help", "Logs script help"),
        (f"{scripts_dir}/deploy.py --help", "Deploy script help"),
        (f"python3 {scripts_dir}/query.py --help", "Query script help (using venv python)"),
    ]

    passed = 0
    failed = 0

    for command, description in tests:
        if run_test(command, description):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")

if __name__ == '__main__':
    main()