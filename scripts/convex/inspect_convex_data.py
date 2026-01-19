#!/usr/bin/env python3
"""
Inspect Convex data structure directly to understand schema.
We'll query the raw data to see what fields exist.
"""

import os
import requests
import json

def load_env():
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()
convex_url = os.environ.get("CONVEX_URL")

print("="*70)
print("INSPECTING CONVEX DATA STRUCTURE")
print("="*70)

tables = [
    "contractors", "projects", "boqs", "rfqs", "quotes",
    "materials", "equipment", "meetings", "lawley_activations",
    "mohadin_activations"
]

for table in tables:
    print(f"\n{'─'*70}")
    print(f"Table: {table}")
    print("─"*70)

    # Try to use Convex's internal query endpoint to get raw data
    payload = {
        "path": f"_system:queryInternal",
        "args": {
            "tableName": table,
            "limit": 1
        }
    }

    try:
        response = requests.post(
            f"{convex_url}/api/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Can access table")
            print(f"Response: {json.dumps(result, indent=2)[:500]}")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*70)
print("RECOMMENDATION:")
print("="*70)
print("\nThe VPS sync created tables but not query functions.")
print("Solution: Deploy Convex functions that wrap the raw data.")
