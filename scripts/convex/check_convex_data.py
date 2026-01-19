#!/usr/bin/env python3
"""
Direct check of Convex database data.
Bypasses agent to verify what's actually in the database.
"""

import os
import json
import requests
from convex_agent import load_env

def check_convex_direct():
    """Check Convex database directly via API."""

    load_env()

    convex_url = os.environ.get("CONVEX_URL")
    auth_key = os.environ.get("SYNC_AUTH_KEY")

    print("="*70)
    print("DIRECT CONVEX DATABASE CHECK")
    print("="*70)
    print(f"\nConvex URL: {convex_url}")
    print(f"Auth Key: {'Set' if auth_key else 'Not Set'}")

    # Try different function paths and endpoints
    functions_to_test = [
        ("tasks:listTasks", "Query"),
        ("tasks:list", "Query"),
        ("listTasks", "Query"),
        ("tasks/listTasks", "Query"),
    ]

    print("\n" + "="*70)
    print("Testing different function paths...")
    print("="*70)

    for function_path, endpoint_type in functions_to_test:
        print(f"\n🔍 Trying: {function_path} ({endpoint_type})")

        # Try query endpoint
        try:
            payload = {
                "path": function_path,
                "args": {}
            }

            headers = {"Content-Type": "application/json"}

            # Try without auth first
            response = requests.post(
                f"{convex_url}/api/query",
                json=payload,
                headers=headers,
                timeout=10
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS")
                print(f"   Response: {json.dumps(result, indent=2)[:500]}")

                # If we got data, show it
                if isinstance(result, dict) and 'value' in result:
                    data = result['value']
                    if isinstance(data, list):
                        print(f"   📊 Found {len(data)} items")
                        if len(data) > 0:
                            print(f"   First item: {json.dumps(data[0], indent=2)[:200]}")
                    return result
            else:
                print(f"   ❌ Failed: {response.text[:200]}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Try listing tables/schemas
    print("\n" + "="*70)
    print("Attempting to discover available functions...")
    print("="*70)

    # Common Convex patterns
    discovery_paths = [
        "listFunctions",
        "_system/listFunctions",
        "tables",
        "schema"
    ]

    for path in discovery_paths:
        try:
            payload = {"path": path, "args": {}}
            response = requests.post(
                f"{convex_url}/api/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                print(f"\n✅ {path}: {json.dumps(response.json(), indent=2)[:300]}")
        except:
            pass

    print("\n" + "="*70)
    print("Checking Convex deployment info...")
    print("="*70)

    # Try to get deployment info
    try:
        # Convex typically has a health/info endpoint
        response = requests.get(f"{convex_url}/api/health", timeout=10)
        if response.status_code == 200:
            print(f"Health check: {response.text}")
    except:
        pass

    print("\n" + "="*70)
    print("RECOMMENDATION:")
    print("="*70)
    print("\n1. Check Convex Dashboard: https://dashboard.convex.dev/")
    print(f"2. Verify deployment: quixotic-crow-802")
    print("3. Confirm these functions are deployed:")
    print("   - tasks:listTasks")
    print("   - tasks:addTask")
    print("   - tasks:getTaskStats")
    print("\n4. Check function definitions in convex/ directory")

if __name__ == "__main__":
    check_convex_direct()
