#!/usr/bin/env python3
"""
Test universal Convex functions with real FibreFlow data.
"""

import os
import requests
import json
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)

convex_url = os.environ.get("CONVEX_URL")


# Test tables
TEST_TABLES = [
    ("BOQs", "boqs"),
    ("RFQs", "rfqs"),
    ("Materials", "materials"),
    ("Equipment", "equipment"),
    ("Quotes", "quotes"),
    ("Meetings", "meetings"),
    ("Clients", "clients"),
    ("VPS Servers", "vps_servers"),
]


@pytest.mark.skipif(not convex_url, reason="CONVEX_URL not set")
@pytest.mark.integration
def test_universal_convex_functions():
    """Test universal Convex functions with real FibreFlow data."""
    print("\n" + "="*70)
    print("TESTING UNIVERSAL CONVEX FUNCTIONS")
    print("="*70)
    print(f"\nConvex URL: {convex_url}\n")

    results = []

    for display_name, table_name in TEST_TABLES:
        print(f"{'─'*70}")
        print(f"Testing: {display_name} ({table_name})")
        print("─"*70)

        # Test universal function
        payload = {
            "path": "universal:listFromTable",
            "args": {"tableName": table_name, "limit": 3}
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
                value = result.get("value", result)

                if value.get("status") == "success":
                    data = value.get("data", [])
                    total = value.get("total", 0)
                    print(f"✅ SUCCESS: Found {total} records")
                    if data and len(data) > 0:
                        print(f"   Sample: {json.dumps(data[0], indent=2)[:200]}...")
                    results.append((display_name, True, total))
                else:
                    print(f"⚠️  Table exists but empty or error")
                    print(f"   {value.get('message', 'Unknown error')}")
                    results.append((display_name, False, 0))
            else:
                print(f"❌ HTTP {response.status_code}")
                results.append((display_name, False, 0))

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((display_name, False, 0))

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    success_count = sum(1 for _, success, _ in results if success)
    total_records = sum(count for _, success, count in results if success)

    print(f"\nTables tested: {len(results)}")
    print(f"Accessible: {success_count}")
    print(f"Total records found: {total_records}")

    print(f"\n{'Table':<20} {'Status':<15} {'Records'}")
    print("─"*70)
    for name, success, count in results:
        status = "✅ Accessible" if success else "❌ Failed"
        print(f"{name:<20} {status:<15} {count if success else '-'}")

    if success_count > 0:
        print(f"\n🎉 SUCCESS! {success_count} FibreFlow tables now accessible to agents!")
    else:
        print("\n⚠️  No tables accessible yet. May need schema adjustments.")

    # Assert at least some tables are accessible
    assert success_count > 0, "No Convex tables were accessible"


if __name__ == "__main__":
    # Allow running directly for manual testing
    test_universal_convex_functions()
