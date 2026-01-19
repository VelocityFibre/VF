#!/usr/bin/env python3
"""
Check ALL tables/collections in Convex deployment.
This will show if there's more data than what our agent can see.
"""

import os
import requests
import json

def load_env():
    """Load environment variables."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
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
print("CHECKING ALL TABLES IN CONVEX DEPLOYMENT")
print("="*70)
print(f"\nConvex URL: {convex_url}\n")

# List of possible table names based on FibreFlow schema
possible_tables = [
    # Our tables
    "tasks", "contractors", "projects", "syncRecords",

    # Potential FibreFlow tables
    "boqs", "rfqs", "quotes", "materials", "equipment",
    "meetings", "clients", "installations", "activations",
    "poles", "drops", "exports", "financials",

    # With different naming conventions
    "BOQs", "RFQs", "Quotes", "Materials", "Equipment",
    "lawley_activations", "mohadin_activations", "onemap_installations",
    "onemap_poles", "sow_poles", "sow_drops", "nokia_exports",
    "vps_servers", "vps_metrics", "vps_logs", "vps_services", "vps_alerts",
    "sync_mappings"
]

found_tables = []

for table in possible_tables:
    try:
        # Try to query the table
        payload = {
            "path": f"{table}:list",
            "args": {}
        }

        response = requests.post(
            f"{convex_url}/api/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            if "value" in result or "status" in result:
                print(f"✅ Found table: {table}")
                found_tables.append(table)

                # Try to count items
                if isinstance(result.get("value"), list):
                    print(f"   Items: {len(result['value'])}")
                elif isinstance(result.get("value"), dict):
                    if "total" in result["value"]:
                        print(f"   Total: {result['value']['total']}")
    except:
        pass

print(f"\n{'='*70}")
print(f"SUMMARY")
print("="*70)
print(f"Found {len(found_tables)} tables/collections:")
for table in found_tables:
    print(f"  - {table}")

print(f"\n{'='*70}")
print("RECOMMENDATION:")
print("="*70)

if len(found_tables) > 4:
    print("\n✅ Your Convex has MORE than just our 4 tables!")
    print("   This means your VPS sync data might still be there.")
    print("\n   Next step: Create agent tools to access these tables.")
else:
    print("\n⚠️  Only found our 4 tables (tasks, contractors, projects, syncRecords)")
    print("   Your VPS sync data might have been overwritten.")
    print("\n   Options:")
    print("   1. Check your VPS sync script")
    print("   2. Re-run the VPS sync to repopulate Convex")
    print("   3. Access data directly from Neon instead")
